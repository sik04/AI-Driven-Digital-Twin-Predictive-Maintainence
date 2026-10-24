"""Pydantic schemas and data contracts for IntelliTwin validation-replay API and dashboard."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ErrorResponse(BaseModel):
    """Structured API error response."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error explanation")


class HealthResponse(BaseModel):
    """Service health and readiness response."""

    status: str = Field(..., description="Service status: ok or unhealthy")
    dependencies_ready: bool = Field(
        ..., description="Whether required runtime dependencies are ready"
    )
    artifacts_ready: bool = Field(
        ..., description="Whether required model/calibrator registries are available"
    )
    active_session_id: str | None = Field(
        None, description="Active session ID if currently held in memory"
    )


class CatalogResponse(BaseModel):
    """Catalog of supported configurations and validation engine IDs."""

    datasets: list[str] = Field(..., description="Supported dataset names")
    models: list[str] = Field(..., description="Supported model families")
    methods: list[str] = Field(..., description="Supported calibration method identifiers")
    seed: int = Field(2026, description="Fixed seed for demo validation replay")
    nominal_coverage: float = Field(
        0.90, description="Fixed nominal coverage for demo validation replay"
    )
    default_dataset: str = Field("FD002", description="Default dataset selection")
    default_model: str = Field("GBR", description="Default model family selection")
    default_method: str = Field(
        "decision_aware_hcp", description="Default calibration method selection"
    )
    default_engine: int = Field(
        9, description="Default engine ID (smallest validation engine in default dataset)"
    )
    validation_engines: dict[str, list[int]] = Field(
        ..., description="Permitted validation engine IDs per dataset"
    )


class SessionCreateRequest(BaseModel):
    """Request body for creating a validation replay session."""

    dataset: Literal["FD001", "FD002", "FD004"]
    engine_id: int
    model_family: Literal["GBR", "LSTM"]
    method_id: Literal["global_hcp", "regime_hcp", "decision_aware_hcp"]


class AdvanceRequest(BaseModel):
    """Request body for advancing a replay session by one cycle."""

    expected_cycle: int = Field(..., description="Expected current cycle before advancing")


class ProvenanceInfo(BaseModel):
    """Provenance and audit metadata for the active session artifacts."""

    model_id: str
    model_configuration_id: str
    model_checkpoint_sha256: str
    model_metadata_sha256: str
    calibrator_bundle_id: str
    calibrator_artifact_sha256: str
    calibrator_candidate_id: str | None = None
    preprocessor_sha256: str
    split_manifest_sha256: str


class SessionStateResponse(BaseModel):
    """Current state response for an active validation replay session."""

    session_id: str
    dataset: str
    engine_id: int
    model_family: str
    method_id: str
    seed: int
    nominal_coverage: float
    cycle: int
    state: Literal["ready", "warming_up", "active", "maintained", "failed"]
    regime: str | None = None
    sensors: dict[str, float] | None = None
    prediction: float | None = None
    lower_rul: float | None = None
    upper_rul: float | None = None
    action: Literal["CONTINUE", "MAINTAIN_NOW"] | None = None
    explanation: str
    artifact_provenance: ProvenanceInfo

    @model_validator(mode="before")
    @classmethod
    def sanitize_finite_floats(cls, data: Any) -> Any:
        """Enforce finite float values across all numeric fields."""
        if isinstance(data, dict):
            float_fields = ("prediction", "lower_rul", "upper_rul")
            for f in float_fields:
                val = data.get(f)
                if val is not None:
                    try:
                        f_val = float(val)
                        import math

                        if not math.isfinite(f_val):
                            raise ValueError(f"Non-finite float value in field '{f}': {val}")
                        data[f] = f_val
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"Invalid numeric value in field '{f}': {val}") from exc
            sensors = data.get("sensors")
            if isinstance(sensors, dict):
                import math

                for k, v in sensors.items():
                    if v is not None:
                        f_v = float(v)
                        if not math.isfinite(f_v):
                            raise ValueError(f"Non-finite float in sensor '{k}': {v}")
                        sensors[k] = f_v
        return data
