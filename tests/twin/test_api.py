"""API unit and integration tests using HTTPX AsyncClient and anyio."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import anyio
import pytest
from httpx import ASGITransport, AsyncClient

from intellitwin.twin.api import app, session_registry


@pytest.fixture(autouse=True)
def clean_session_registry() -> Generator[None, None, None]:
    """Ensure session registry has no active session before and after tests."""
    with session_registry._lock:
        session_registry._active_session = None
    yield
    with session_registry._lock:
        session_registry._active_session = None


def test_api_health() -> None:
    """Verify /api/health endpoint structure."""

    async def run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert "status" in data
            assert "dependencies_ready" in data
            assert "artifacts_ready" in data
            assert data["dependencies_ready"] is True

    anyio.run(run)


def test_api_catalog() -> None:
    """Verify /api/catalog endpoint returns supported configurations and validation engine IDs."""

    async def run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/catalog")
            assert resp.status_code == 200
            data = resp.json()
            assert set(data["datasets"]) == {"FD001", "FD002", "FD004"}
            assert set(data["models"]) == {"GBR", "LSTM"}
            assert set(data["methods"]) == {"global_hcp", "regime_hcp", "decision_aware_hcp"}
            assert data["seed"] == 2026
            assert data["nominal_coverage"] == 0.90
            assert "validation_engines" in data
            assert len(data["validation_engines"]["FD002"]) == 26
            assert 9 in data["validation_engines"]["FD002"]

    anyio.run(run)


def test_api_session_lifecycle_with_mock() -> None:
    """Fast unit test of session creation, advance, reset, and delete using mocks."""

    async def run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with (
                patch.object(session_registry.artifact_manager, "load_artifacts") as mock_artifacts,
                patch.object(
                    session_registry.artifact_manager, "load_engine_telemetry"
                ) as mock_telem,
            ):
                # Setup mock artifacts & telemetry
                mock_art_obj = MagicMock()
                mock_art_obj.seed = 2026
                mock_art_obj.nominal_coverage = 0.90
                mock_art_obj.model_id = "mock_model"
                mock_art_obj.model_config_id = "mock_cfg"
                mock_art_obj.model_checkpoint_sha256 = "mock_ckpt_sha"
                mock_art_obj.model_metadata_sha256 = "mock_meta_sha"
                mock_art_obj.calibrator_bundle_id = "mock_bundle"
                mock_art_obj.calibrator_artifact_sha256 = "mock_calib_sha"
                mock_art_obj.calibrator_candidate_id = "mock_cand"
                mock_art_obj.preprocessor_sha256 = "mock_prep_sha"
                mock_art_obj.split_manifest_sha256 = "mock_split_sha"
                mock_artifacts.return_value = mock_art_obj

                import pandas as pd

                from intellitwin.data.schema import SENSOR_COLUMNS

                df_rows = [
                    {"cycle": c, **dict.fromkeys(SENSOR_COLUMNS, 1.0)} for c in range(1, 100)
                ]
                mock_telem.return_value = pd.DataFrame(df_rows)

                # 1. Create session
                create_payload = {
                    "dataset": "FD002",
                    "engine_id": 9,
                    "model_family": "GBR",
                    "method_id": "decision_aware_hcp",
                }
                res_create = await client.post("/api/sessions", json=create_payload)
                assert res_create.status_code == 201
                sess_data = res_create.json()
                sess_id = sess_data["session_id"]
                assert sess_data["cycle"] == 0
                assert sess_data["state"] == "ready"

                # 2. Duplicate session creation should return 409 Conflict
                res_dup = await client.post("/api/sessions", json=create_payload)
                assert res_dup.status_code == 409
                assert res_dup.json()["code"] == "CONFLICT"

                # 3. Get session
                res_get = await client.get(f"/api/sessions/{sess_id}")
                assert res_get.status_code == 200
                assert res_get.json()["session_id"] == sess_id

                # 4. Advance with wrong cycle returns 409
                res_wrong = await client.post(
                    f"/api/sessions/{sess_id}/advance", json={"expected_cycle": 5}
                )
                assert res_wrong.status_code == 409
                assert res_wrong.json()["code"] == "CONFLICT"

                # 5. Advance with correct cycle 0
                res_adv = await client.post(
                    f"/api/sessions/{sess_id}/advance", json={"expected_cycle": 0}
                )
                assert res_adv.status_code == 200
                adv_data = res_adv.json()
                assert adv_data["cycle"] == 1
                assert adv_data["state"] == "warming_up"

                # 6. Reset
                res_reset = await client.post(f"/api/sessions/{sess_id}/reset")
                assert res_reset.status_code == 200
                assert res_reset.json()["cycle"] == 0
                assert res_reset.json()["state"] == "ready"

                # 7. Trace download
                res_trace = await client.get(f"/api/sessions/{sess_id}/trace.csv")
                assert res_trace.status_code == 200
                assert "text/csv" in res_trace.headers["content-type"]

                # 8. Delete session
                res_del = await client.delete(f"/api/sessions/{sess_id}")
                assert res_del.status_code == 204

                # 9. Get after delete returns 404
                res_notfound = await client.get(f"/api/sessions/{sess_id}")
                assert res_notfound.status_code == 404
                assert res_notfound.json()["code"] == "NOT_FOUND"

    anyio.run(run)


def test_api_forbidden_engine_rejection() -> None:
    """Verify API returns 422 for a forbidden partition engine."""

    async def run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "dataset": "FD002",
                "engine_id": 1,  # Engine 1 is in train partition
                "model_family": "GBR",
                "method_id": "decision_aware_hcp",
            }
            resp = await client.post("/api/sessions", json=payload)
            assert resp.status_code == 422
            err_data = resp.json()
            assert err_data["code"] == "UNPROCESSABLE_ENTITY"
            assert (
                "forbidden" in err_data["message"].lower()
                or "strictly limited" in err_data["message"].lower()
            )

    anyio.run(run)


def test_api_disallowed_parameters_rejection() -> None:
    """Verify API returns 422 for disallowed datasets, models, or methods."""

    async def run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Invalid dataset
            resp1 = await client.post(
                "/api/sessions",
                json={
                    "dataset": "FD003",
                    "engine_id": 1,
                    "model_family": "GBR",
                    "method_id": "global_hcp",
                },
            )
            assert resp1.status_code == 422

            # Invalid model
            resp2 = await client.post(
                "/api/sessions",
                json={
                    "dataset": "FD001",
                    "engine_id": 3,
                    "model_family": "RANDOM_FOREST",
                    "method_id": "global_hcp",
                },
            )
            assert resp2.status_code == 422

            # Invalid method
            resp3 = await client.post(
                "/api/sessions",
                json={
                    "dataset": "FD001",
                    "engine_id": 3,
                    "model_family": "GBR",
                    "method_id": "standard_conformal",
                },
            )
            assert resp3.status_code == 422

    anyio.run(run)


@pytest.mark.integration
def test_api_real_session_advance_warmup_and_inference() -> None:
    """Integration test: create real session for FD002/GBR/engine 9 and advance through cycle 30."""

    async def run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "dataset": "FD002",
                "engine_id": 9,
                "model_family": "GBR",
                "method_id": "decision_aware_hcp",
            }
            resp_init = await client.post("/api/sessions", json=payload)
            assert resp_init.status_code == 201
            sess_data = resp_init.json()
            sess_id = sess_data["session_id"]

            # Advance 30 cycles
            for c in range(30):
                adv_res = await client.post(
                    f"/api/sessions/{sess_id}/advance", json={"expected_cycle": c}
                )
                assert adv_res.status_code == 200
                s_state = adv_res.json()

            assert s_state["cycle"] == 30
            assert s_state["state"] == "active"
            assert s_state["prediction"] is not None
            assert s_state["lower_rul"] is not None
            assert s_state["upper_rul"] is not None
            assert s_state["action"] == "CONTINUE"

            # Verify no oracle fields exist in response
            response_keys = set(s_state.keys())
            forbidden_fields = {"failure_cycle", "rul_true", "rul_target", "lifecycle_stage"}
            assert len(response_keys.intersection(forbidden_fields)) == 0

            # Clean up
            del_res = await client.delete(f"/api/sessions/{sess_id}")
            assert del_res.status_code == 204

    anyio.run(run)
