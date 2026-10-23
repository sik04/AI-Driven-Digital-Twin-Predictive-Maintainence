"""Sequential engine replay session engine for IntelliTwin validation dashboard.

Enforces:
- 1 observation consumed per advance request
- warming_up for cycles 1..29 (no prediction, no bounds, no action)
- cycle 30..T:
  * float32 30x17 window using only observations through cycle t
  * GBR row-major 510-flattening, LSTM sequence
  * frozen calibrator interval bounds
  * lower_bound_one_cycle_policy with observable PredictionState
  * Maintain when lower_rul <= 1.0; stop at first maintenance action
  * Failure takes precedence at final cycle (no maintenance action at terminal cycle T)
- Thread-safe advance under lock with expected_cycle validation
- Replay state never exposes oracle/future fields (failure cycle, rul_true, lifecycle_stage)
"""

from __future__ import annotations

import csv
import io
import math
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

from intellitwin.data.schema import FEATURE_COLUMNS, LOOKBACK, SENSOR_COLUMNS
from intellitwin.decision.policies import lower_bound_one_cycle_policy
from intellitwin.simulator.types import MaintenanceAction, PredictionState
from intellitwin.twin.artifacts import ActiveArtifacts, ArtifactManager
from intellitwin.twin.schemas import ProvenanceInfo, SessionStateResponse


class ReplayConflictError(Exception):
    """Raised when replay request encounters a cycle mismatch or invalid state."""


class SessionNotFoundError(Exception):
    """Raised when session ID does not match the active session."""


@dataclass
class CycleRecord:
    """Historical record for a consumed cycle."""

    cycle: int
    state: str
    regime: str | None
    sensors: dict[str, float]
    prediction: float | None
    lower_rul: float | None
    upper_rul: float | None
    action: str | None
    explanation: str


class ReplaySession:
    """In-memory active replay session executing cycle-by-cycle replay under a lock."""

    def __init__(
        self,
        session_id: str,
        dataset: str,
        engine_id: int,
        model_family: str,
        method_id: str,
        artifacts: ActiveArtifacts,
        telemetry: pd.DataFrame,
    ) -> None:
        self.session_id = session_id
        self.dataset = dataset
        self.engine_id = engine_id
        self.model_family = model_family
        self.method_id = method_id
        self.seed = artifacts.seed
        self.nominal_coverage = artifacts.nominal_coverage

        self.artifacts = artifacts
        self.telemetry = telemetry
        self._total_cycles = len(telemetry)

        self._lock = threading.Lock()
        self.current_cycle = 0
        self.state: Literal["ready", "warming_up", "active", "maintained", "failed"] = "ready"
        self.history: list[CycleRecord] = []

        # Current observable values
        self.current_regime: str | None = None
        self.current_sensors: dict[str, float] | None = None
        self.current_prediction: float | None = None
        self.current_lower_rul: float | None = None
        self.current_upper_rul: float | None = None
        self.current_action: Literal["CONTINUE", "MAINTAIN_NOW"] | None = None
        self.current_explanation: str = "Session initialized at cycle 0. Ready to advance."

    @property
    def provenance_info(self) -> ProvenanceInfo:
        return ProvenanceInfo(
            model_id=self.artifacts.model_id,
            model_configuration_id=self.artifacts.model_config_id,
            model_checkpoint_sha256=self.artifacts.model_checkpoint_sha256,
            model_metadata_sha256=self.artifacts.model_metadata_sha256,
            calibrator_bundle_id=self.artifacts.calibrator_bundle_id,
            calibrator_artifact_sha256=self.artifacts.calibrator_artifact_sha256,
            calibrator_candidate_id=self.artifacts.calibrator_candidate_id,
            preprocessor_sha256=self.artifacts.preprocessor_sha256,
            split_manifest_sha256=self.artifacts.split_manifest_sha256,
        )

    def get_state_response(self) -> SessionStateResponse:
        """Produce read-only view of current state."""
        with self._lock:
            return SessionStateResponse(
                session_id=self.session_id,
                dataset=self.dataset,
                engine_id=self.engine_id,
                model_family=self.model_family,
                method_id=self.method_id,
                seed=self.seed,
                nominal_coverage=self.nominal_coverage,
                cycle=self.current_cycle,
                state=self.state,
                regime=self.current_regime,
                sensors=self.current_sensors,
                prediction=self.current_prediction,
                lower_rul=self.current_lower_rul,
                upper_rul=self.current_upper_rul,
                action=self.current_action,
                explanation=self.current_explanation,
                artifact_provenance=self.provenance_info,
            )

    def advance(self, expected_cycle: int) -> SessionStateResponse:
        """Advance replay by exactly one cycle under lock, rejecting stale expected_cycle."""
        with self._lock:
            if expected_cycle != self.current_cycle:
                raise ReplayConflictError(
                    f"Stale advance request: expected cycle {expected_cycle}, "
                    f"but current cycle is {self.current_cycle}"
                )

            if self.state in ("maintained", "failed"):
                raise ReplayConflictError(
                    f"Cannot advance session in terminal state '{self.state}'. "
                    "Reset session to cycle 0 to restart."
                )

            next_cycle = self.current_cycle + 1
            if next_cycle > self._total_cycles:
                raise ReplayConflictError(
                    f"No further observations available for engine {self.engine_id}"
                )

            row = self.telemetry.iloc[next_cycle - 1]
            sensors_dict = {col: float(row[col]) for col in SENSOR_COLUMNS}
            self.current_sensors = sensors_dict
            self.current_cycle = next_cycle

            # Check if this cycle is terminal failure cycle T
            if next_cycle == self._total_cycles:
                # Failure cycle takes precedence: no maintenance at final cycle!
                self.state = "failed"
                if next_cycle >= LOOKBACK:
                    pred, low, upp, reg = self._compute_inference(next_cycle)
                    self.current_prediction = pred
                    self.current_lower_rul = low
                    self.current_upper_rul = upp
                    self.current_regime = reg
                else:
                    self.current_prediction = None
                    self.current_lower_rul = None
                    self.current_upper_rul = None
                    self.current_regime = None

                self.current_action = None
                self.current_explanation = (
                    f"Trajectory reached terminal failure cycle {next_cycle}. "
                    "Engine failed. Replay stopped."
                )

                self._record_history()
                return self._build_response()

            # Warm-up phase: cycles 1..29
            if next_cycle < LOOKBACK:
                self.state = "warming_up"
                self.current_prediction = None
                self.current_lower_rul = None
                self.current_upper_rul = None
                self.current_regime = None
                self.current_action = None
                self.current_explanation = (
                    f"Collecting observations: {next_cycle}/{LOOKBACK} cycles"
                )
                self._record_history()
                return self._build_response()

            # Active phase: cycle >= 30
            pred, low, upp, reg = self._compute_inference(next_cycle)
            self.current_prediction = pred
            self.current_lower_rul = low
            self.current_upper_rul = upp
            self.current_regime = reg

            # Evaluate policy
            state_obj = PredictionState(
                engine_id=self.engine_id,
                cycle=next_cycle,
                point_rul=pred,
                lower_rul=low,
                upper_rul=upp,
                regime=None,
            )
            action = lower_bound_one_cycle_policy(state_obj)

            if action == MaintenanceAction.MAINTAIN_NOW:
                self.state = "maintained"
                self.current_action = "MAINTAIN_NOW"
                self.current_explanation = (
                    f"Maintenance triggered at cycle {next_cycle}: "
                    f"90% lower bound ({low:.2f}) <= 1.0 cycle threshold."
                )
            else:
                self.state = "active"
                self.current_action = "CONTINUE"
                self.current_explanation = (
                    f"Operation continuing at cycle {next_cycle}: "
                    f"90% lower bound ({low:.2f}) > 1.0 cycle threshold."
                )

            self._record_history()
            return self._build_response()

    def _compute_inference(self, cycle: int) -> tuple[float, float, float, str]:
        """Compute window inference using observations strictly through cycle."""
        # Use strictly observations up to current cycle (anti-leakage)
        window_raw = self.telemetry.iloc[cycle - LOOKBACK : cycle].copy()
        if len(window_raw) != LOOKBACK:
            raise RuntimeError(f"Window length {len(window_raw)} != {LOOKBACK}")

        trans_df = self.artifacts.model.preprocessor.transform(window_raw)
        feat_mat = trans_df[list(FEATURE_COLUMNS)].to_numpy(dtype=np.float32)

        if self.model_family == "GBR":
            flat_x = feat_mat.reshape(1, LOOKBACK * len(FEATURE_COLUMNS))
            preds = self.artifacts.model.predict(flat_x)
        elif self.model_family == "LSTM":
            seq_x = feat_mat.reshape(1, LOOKBACK, len(FEATURE_COLUMNS))
            preds = self.artifacts.model.predict(seq_x)
        else:
            raise ValueError(f"Unknown model family: {self.model_family}")

        pred_val = float(preds[0])
        if not math.isfinite(pred_val):
            raise ValueError(f"Inference produced non-finite prediction: {pred_val}")

        regime_val = str(trans_df["regime"].iloc[-1])
        lows, upps, _ = self.artifacts.calibrator.predict_intervals(
            predictions=np.array([pred_val], dtype=np.float64),
            regimes=[regime_val],
            nominal_coverage=self.nominal_coverage,
        )

        low_val = float(lows[0])
        upp_val = float(upps[0])
        if not (math.isfinite(low_val) and math.isfinite(upp_val)):
            raise ValueError(
                f"Inference produced non-finite interval bounds: [{low_val}, {upp_val}]"
            )

        return pred_val, low_val, upp_val, regime_val

    def _record_history(self) -> None:
        rec = CycleRecord(
            cycle=self.current_cycle,
            state=self.state,
            regime=self.current_regime,
            sensors=dict(self.current_sensors) if self.current_sensors else {},
            prediction=self.current_prediction,
            lower_rul=self.current_lower_rul,
            upper_rul=self.current_upper_rul,
            action=self.current_action,
            explanation=self.current_explanation,
        )
        self.history.append(rec)

    def _build_response(self) -> SessionStateResponse:
        return SessionStateResponse(
            session_id=self.session_id,
            dataset=self.dataset,
            engine_id=self.engine_id,
            model_family=self.model_family,
            method_id=self.method_id,
            seed=self.seed,
            nominal_coverage=self.nominal_coverage,
            cycle=self.current_cycle,
            state=self.state,
            regime=self.current_regime,
            sensors=self.current_sensors,
            prediction=self.current_prediction,
            lower_rul=self.current_lower_rul,
            upper_rul=self.current_upper_rul,
            action=self.current_action,
            explanation=self.current_explanation,
            artifact_provenance=self.provenance_info,
        )

    def reset(self) -> SessionStateResponse:
        """Reset the replay session to cycle 0 and clear history."""
        with self._lock:
            self.current_cycle = 0
            self.state = "ready"
            self.history.clear()
            self.current_regime = None
            self.current_sensors = None
            self.current_prediction = None
            self.current_lower_rul = None
            self.current_upper_rul = None
            self.current_action = None
            self.current_explanation = "Session reset to cycle 0. Ready to advance."
            return self._build_response()

    def generate_trace_csv(self) -> str:
        """Export consumed history as CSV (strictly without oracle/future fields)."""
        with self._lock:
            output = io.StringIO()
            fieldnames = [
                "cycle",
                "state",
                "regime",
                "prediction",
                "lower_rul",
                "upper_rul",
                "action",
                "explanation",
            ] + list(SENSOR_COLUMNS)

            writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()

            for rec in self.history:
                row_dict: dict[str, Any] = {
                    "cycle": rec.cycle,
                    "state": rec.state,
                    "regime": rec.regime or "",
                    "prediction": f"{rec.prediction:.4f}" if rec.prediction is not None else "",
                    "lower_rul": f"{rec.lower_rul:.4f}" if rec.lower_rul is not None else "",
                    "upper_rul": f"{rec.upper_rul:.4f}" if rec.upper_rul is not None else "",
                    "action": rec.action or "",
                    "explanation": rec.explanation,
                }
                for scol in SENSOR_COLUMNS:
                    row_dict[scol] = (
                        f"{rec.sensors.get(scol, ''):.6g}" if scol in rec.sensors else ""
                    )
                writer.writerow(row_dict)

            return output.getvalue()


class SessionRegistry:
    """Manages the single active replay session in memory."""

    def __init__(self, artifact_manager: ArtifactManager) -> None:
        self.artifact_manager = artifact_manager
        self._lock = threading.Lock()
        self._active_session: ReplaySession | None = None

    def get_active_session(self) -> ReplaySession | None:
        with self._lock:
            return self._active_session

    def get_session_by_id(self, session_id: str) -> ReplaySession:
        with self._lock:
            if self._active_session is None or self._active_session.session_id != session_id:
                raise SessionNotFoundError(f"Session '{session_id}' not found or inactive")
            return self._active_session

    def create_session(
        self,
        dataset: str,
        engine_id: int,
        model_family: str,
        method_id: str,
    ) -> ReplaySession:
        """Create a new session, returning 409 conflict if an active session already exists."""
        with self._lock:
            if self._active_session is not None:
                raise ReplayConflictError(
                    f"An active session '{self._active_session.session_id}' already exists. "
                    "Delete the existing session before creating a new one."
                )

            # Validate selection
            self.artifact_manager.validate_selection(
                dataset=dataset,
                engine_id=engine_id,
                model_family=model_family,
                method_id=method_id,
            )

            # Load artifacts and telemetry
            artifacts = self.artifact_manager.load_artifacts(
                dataset=dataset,
                model_family=model_family,
                method_id=method_id,
            )
            telemetry = self.artifact_manager.load_engine_telemetry(
                dataset=dataset,
                engine_id=engine_id,
            )

            session_id = str(uuid.uuid4())
            session = ReplaySession(
                session_id=session_id,
                dataset=dataset,
                engine_id=engine_id,
                model_family=model_family,
                method_id=method_id,
                artifacts=artifacts,
                telemetry=telemetry,
            )
            self._active_session = session
            return session

    def delete_session(self, session_id: str) -> None:
        """Release the active session and in-memory artifacts."""
        with self._lock:
            if self._active_session is None or self._active_session.session_id != session_id:
                raise SessionNotFoundError(f"Session '{session_id}' not found or inactive")
            self._active_session = None
