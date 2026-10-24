"""FastAPI application serving the IntelliTwin validation-replay API and dashboard.

Endpoints:
- GET /api/health
- GET /api/catalog
- POST /api/sessions
- GET /api/sessions/{id}
- POST /api/sessions/{id}/advance
- POST /api/sessions/{id}/reset
- DELETE /api/sessions/{id}
- GET /api/sessions/{id}/trace.csv
- Static frontend served at /
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from intellitwin.twin.artifacts import (
    ALLOWED_DATASETS,
    ALLOWED_METHODS,
    ALLOWED_MODELS,
    FIXED_NOMINAL_COVERAGE,
    FIXED_SEED,
    ArtifactManager,
)
from intellitwin.twin.replay import ReplayConflictError, SessionNotFoundError, SessionRegistry
from intellitwin.twin.schemas import (
    AdvanceRequest,
    CatalogResponse,
    HealthResponse,
    SessionCreateRequest,
    SessionStateResponse,
)

logger = logging.getLogger("intellitwin.twin.api")

app = FastAPI(
    title="IntelliTwin Engine Replay API",
    description="Telemetry-replay digital-twin prototype for validation trajectory inspection",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory state
REPO_ROOT = Path(".").resolve()
artifact_manager = ArtifactManager(base_dir=REPO_ROOT)
session_registry = SessionRegistry(artifact_manager=artifact_manager)


# Custom structured exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    err_msg = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    return Response(
        content=f'{{"code":"UNPROCESSABLE_ENTITY","message":"{err_msg}"}}',
        status_code=422,
        media_type="application/json",
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_409_CONFLICT:
        code = "CONFLICT"
    elif exc.status_code == 422:
        code = "UNPROCESSABLE_ENTITY"
    elif exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        code = "SERVICE_UNAVAILABLE"

    detail = str(exc.detail) if exc.detail else "An error occurred"
    # Hide server tracebacks
    return Response(
        content=f'{{"code":"{code}","message":"{detail}"}}',
        status_code=exc.status_code,
        media_type="application/json",
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> Response:
    logger.exception("Unhandled server error: %s", exc)
    msg = "An internal error occurred during request processing"
    return Response(
        content=f'{{"code":"INTERNAL_SERVER_ERROR","message":"{msg}"}}',
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/json",
    )


@app.get("/api/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Check service availability and dependency/artifact readiness."""
    artifacts_ready = False
    try:
        model_reg = REPO_ROOT / "experiments/base_models/model_registry.json"
        calib_reg = REPO_ROOT / "experiments/calibration/calibration_registry.json"
        split_regs = [
            REPO_ROOT / f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
            for ds in ALLOWED_DATASETS
        ]
        if model_reg.exists() and calib_reg.exists() and all(p.exists() for p in split_regs):
            artifacts_ready = True
    except Exception:
        artifacts_ready = False

    active_sess = session_registry.get_active_session()
    return HealthResponse(
        status="ok" if artifacts_ready else "degraded",
        dependencies_ready=True,
        artifacts_ready=artifacts_ready,
        active_session_id=active_sess.session_id if active_sess else None,
    )


@app.get("/api/catalog", response_model=CatalogResponse)
def get_catalog() -> CatalogResponse:
    """Return supported configurations, validation engine IDs, seed, and nominal coverage."""
    return CatalogResponse(
        datasets=list(ALLOWED_DATASETS),
        models=list(ALLOWED_MODELS),
        methods=list(ALLOWED_METHODS),
        seed=FIXED_SEED,
        nominal_coverage=FIXED_NOMINAL_COVERAGE,
        default_dataset="FD002",
        default_model="GBR",
        default_method="decision_aware_hcp",
        default_engine=9,
        validation_engines=artifact_manager.get_all_validation_engines(),
    )


@app.post("/api/sessions", response_model=SessionStateResponse, status_code=status.HTTP_201_CREATED)
def create_session(body: SessionCreateRequest) -> SessionStateResponse:
    """Create a new validation replay session."""
    try:
        session = session_registry.create_session(
            dataset=body.dataset,
            engine_id=body.engine_id,
            model_family=body.model_family,
            method_id=body.method_id,
        )
        return session.get_state_response()
    except ReplayConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Artifact missing: {exc}"
        ) from exc


@app.get("/api/sessions/{session_id}", response_model=SessionStateResponse)
def get_session(session_id: str) -> SessionStateResponse:
    """Return current session state without advancing."""
    try:
        session = session_registry.get_session_by_id(session_id)
        return session.get_state_response()
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/advance", response_model=SessionStateResponse)
def advance_session(session_id: str, body: AdvanceRequest) -> SessionStateResponse:
    """Advance replay by exactly one cycle, validating expected cycle to prevent skips."""
    try:
        session = session_registry.get_session_by_id(session_id)
        return session.advance(expected_cycle=body.expected_cycle)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ReplayConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Inference error during advance: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Advance failed: {exc}"
        ) from exc


@app.post("/api/sessions/{session_id}/reset", response_model=SessionStateResponse)
def reset_session(session_id: str) -> SessionStateResponse:
    """Reset the replay session to cycle 0."""
    try:
        session = session_registry.get_session_by_id(session_id)
        return session.reset()
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.delete("/api/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str) -> None:
    """Release active session and resources."""
    try:
        session_registry.delete_session(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.get("/api/sessions/{session_id}/trace.csv")
def download_trace(session_id: str) -> Response:
    """Download consumed observations and prediction/action history as CSV."""
    try:
        session = session_registry.get_session_by_id(session_id)
        csv_content = session.generate_trace_csv()
        filename = f"replay_{session.dataset}_engine_{session.engine_id}_trace.csv"
        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# Dashboard Static Files Mounting
DASHBOARD_DIR = REPO_ROOT / "apps/twin_dashboard"
if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")

    @app.get("/")
    async def serve_index() -> FileResponse:
        index_p = DASHBOARD_DIR / "index.html"
        return FileResponse(str(index_p))
