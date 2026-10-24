"""Tests for IntelliTwin replay engine, causal windowing, and invariants."""

import numpy as np
import pandas as pd
import pytest

from intellitwin.data.schema import SENSOR_COLUMNS
from intellitwin.decision.policies import lower_bound_one_cycle_policy
from intellitwin.simulator.types import MaintenanceAction, PredictionState
from intellitwin.twin.artifacts import ArtifactManager
from intellitwin.twin.replay import ReplayConflictError, ReplaySession


def test_forbidden_partition_ids_rejected() -> None:
    """Verify that train, calibration, and test partition engine IDs are rejected."""
    mgr = ArtifactManager()
    # In FD002, engine 1 is train, 2 is calibration, 7 is test
    with pytest.raises(PermissionError, match="strictly limited to validation partition engines"):
        mgr.validate_selection("FD002", 1, "GBR", "decision_aware_hcp")

    with pytest.raises(PermissionError, match="strictly limited to validation partition engines"):
        mgr.validate_selection("FD002", 2, "GBR", "decision_aware_hcp")

    with pytest.raises(PermissionError, match="strictly limited to validation partition engines"):
        mgr.validate_selection("FD002", 7, "GBR", "decision_aware_hcp")

    # Engine 999 doesn't exist
    with pytest.raises(ValueError, match="not in validation partition"):
        mgr.validate_selection("FD002", 999, "GBR", "decision_aware_hcp")


def test_cycle_warmup_and_30_window() -> None:
    """Verify that cycle 29 has no prediction/bounds, and cycle 30 uses exactly 30 observations."""
    mgr = ArtifactManager()
    artifacts = mgr.load_artifacts("FD002", "GBR", "decision_aware_hcp")
    telemetry = mgr.load_engine_telemetry("FD002", 9)

    session = ReplaySession(
        session_id="test-session-1",
        dataset="FD002",
        engine_id=9,
        model_family="GBR",
        method_id="decision_aware_hcp",
        artifacts=artifacts,
        telemetry=telemetry,
    )

    # Initial state
    assert session.current_cycle == 0
    assert session.state == "ready"

    # Advance through cycle 29
    for c in range(29):
        resp = session.advance(expected_cycle=c)
        assert resp.cycle == c + 1
        assert resp.state == "warming_up"
        assert resp.prediction is None
        assert resp.lower_rul is None
        assert resp.upper_rul is None
        assert resp.action is None
        assert "Collecting observations:" in resp.explanation

    # Advance to cycle 30
    resp_30 = session.advance(expected_cycle=29)
    assert resp_30.cycle == 30
    assert resp_30.state == "active"
    assert resp_30.prediction is not None
    assert resp_30.lower_rul is not None
    assert resp_30.upper_rul is not None
    assert resp_30.action in ("CONTINUE", "MAINTAIN_NOW")
    assert resp_30.regime is not None


def test_anti_leakage_future_rows_do_not_affect_earlier_inference() -> None:
    """Verify that altering future rows does not change earlier predictions or actions."""
    mgr = ArtifactManager()
    artifacts = mgr.load_artifacts("FD002", "GBR", "decision_aware_hcp")
    telemetry_orig = mgr.load_engine_telemetry("FD002", 9)

    session_orig = ReplaySession(
        session_id="session-orig",
        dataset="FD002",
        engine_id=9,
        model_family="GBR",
        method_id="decision_aware_hcp",
        artifacts=artifacts,
        telemetry=telemetry_orig,
    )

    # Corrupt future rows in a copy
    telemetry_mutated = telemetry_orig.copy()
    telemetry_mutated.loc[telemetry_mutated["cycle"] > 35, list(SENSOR_COLUMNS)] = 9999.0

    session_mutated = ReplaySession(
        session_id="session-mutated",
        dataset="FD002",
        engine_id=9,
        model_family="GBR",
        method_id="decision_aware_hcp",
        artifacts=artifacts,
        telemetry=telemetry_mutated,
    )

    for c in range(35):
        resp_orig = session_orig.advance(expected_cycle=c)
        resp_mut = session_mutated.advance(expected_cycle=c)
        assert resp_orig.cycle == resp_mut.cycle
        assert resp_orig.prediction == resp_mut.prediction
        assert resp_orig.lower_rul == resp_mut.lower_rul
        assert resp_orig.upper_rul == resp_mut.upper_rul
        assert resp_orig.action == resp_mut.action


def test_stale_expected_cycle_rejection() -> None:
    """Verify that stale expected_cycle is rejected with ReplayConflictError."""
    mgr = ArtifactManager()
    artifacts = mgr.load_artifacts("FD002", "GBR", "decision_aware_hcp")
    telemetry = mgr.load_engine_telemetry("FD002", 9)

    session = ReplaySession(
        session_id="test-session-conflict",
        dataset="FD002",
        engine_id=9,
        model_family="GBR",
        method_id="decision_aware_hcp",
        artifacts=artifacts,
        telemetry=telemetry,
    )

    session.advance(expected_cycle=0)
    assert session.current_cycle == 1

    # Attempting to advance with stale expected_cycle=0 must fail
    with pytest.raises(ReplayConflictError, match="Stale advance request"):
        session.advance(expected_cycle=0)

    # Correct advance with expected_cycle=1 succeeds
    session.advance(expected_cycle=1)
    assert session.current_cycle == 2


def test_reset_clears_state() -> None:
    """Verify that reset clears all replay state back to cycle 0."""
    mgr = ArtifactManager()
    artifacts = mgr.load_artifacts("FD002", "GBR", "decision_aware_hcp")
    telemetry = mgr.load_engine_telemetry("FD002", 9)

    session = ReplaySession(
        session_id="test-session-reset",
        dataset="FD002",
        engine_id=9,
        model_family="GBR",
        method_id="decision_aware_hcp",
        artifacts=artifacts,
        telemetry=telemetry,
    )

    for c in range(32):
        session.advance(expected_cycle=c)
    assert session.current_cycle == 32
    assert len(session.history) == 32

    reset_resp = session.reset()
    assert reset_resp.cycle == 0
    assert reset_resp.state == "ready"
    assert reset_resp.prediction is None
    assert reset_resp.lower_rul is None
    assert reset_resp.action is None
    assert len(session.history) == 0


def test_trace_csv_never_contains_oracle_fields() -> None:
    """Verify that CSV export contains only consumed history and strictly no oracle fields."""
    mgr = ArtifactManager()
    artifacts = mgr.load_artifacts("FD002", "GBR", "decision_aware_hcp")
    telemetry = mgr.load_engine_telemetry("FD002", 9)

    session = ReplaySession(
        session_id="test-session-csv",
        dataset="FD002",
        engine_id=9,
        model_family="GBR",
        method_id="decision_aware_hcp",
        artifacts=artifacts,
        telemetry=telemetry,
    )

    for c in range(31):
        session.advance(expected_cycle=c)

    csv_text = session.generate_trace_csv()
    header_line = csv_text.strip().split("\n")[0]
    headers = [h.strip() for h in header_line.split(",")]

    forbidden_fields = ["failure_cycle", "rul_true", "rul_target", "lifecycle_stage", "target"]
    for field in forbidden_fields:
        assert field not in headers
        assert field not in csv_text


def test_maintenance_stops_advance() -> None:
    """Verify that reaching maintenance terminates replay and rejects advance."""
    mgr = ArtifactManager()
    artifacts = mgr.load_artifacts("FD002", "GBR", "decision_aware_hcp")
    telemetry = mgr.load_engine_telemetry("FD002", 9)

    session = ReplaySession(
        session_id="test-session-pm",
        dataset="FD002",
        engine_id=9,
        model_family="GBR",
        method_id="decision_aware_hcp",
        artifacts=artifacts,
        telemetry=telemetry,
    )

    # We know engine 9 PM occurs at cycle 173
    for c in range(173):
        resp = session.advance(expected_cycle=c)
        if resp.state == "maintained":
            break

    assert session.state == "maintained"
    assert session.current_cycle == 173
    assert session.current_action == "MAINTAIN_NOW"

    # Further advance without reset must be rejected
    with pytest.raises(ReplayConflictError, match="Cannot advance session in terminal state"):
        session.advance(expected_cycle=173)


def test_failure_precedes_maintenance_at_final_cycle() -> None:
    """Verify that if trajectory reaches its failure cycle first, failure takes precedence."""
    mgr = ArtifactManager()
    artifacts = mgr.load_artifacts("FD002", "GBR", "decision_aware_hcp")
    # Truncate telemetry at cycle 35 (before PM would trigger at 173)
    telemetry_short = mgr.load_engine_telemetry("FD002", 9).iloc[:35].copy()

    session = ReplaySession(
        session_id="test-session-fail",
        dataset="FD002",
        engine_id=9,
        model_family="GBR",
        method_id="decision_aware_hcp",
        artifacts=artifacts,
        telemetry=telemetry_short,
    )

    for c in range(35):
        resp = session.advance(expected_cycle=c)

    assert resp.cycle == 35
    assert resp.state == "failed"
    assert resp.action is None
    assert "reached terminal failure cycle 35" in resp.explanation


@pytest.mark.integration
def test_real_prediction_parity_and_calibrators_across_all_cells() -> None:
    """Run real prediction parity checks across all 18 benchmark cells."""
    mgr = ArtifactManager()
    datasets = ["FD001", "FD002", "FD004"]
    models = ["GBR", "LSTM"]
    methods = ["global_hcp", "regime_hcp", "decision_aware_hcp"]

    for ds in datasets:
        val_engines = mgr.get_validation_engines(ds)
        min_engine = min(val_engines)

        for mod in models:
            # Load cached validation predictions to verify numerical match
            val_preds_p = f"experiments/base_models/{ds}/{mod}/seed_2026/validation_predictions.csv"
            df_val_preds = pd.read_csv(val_preds_p)
            engine_cached = df_val_preds[df_val_preds["unit"] == min_engine]

            for meth in methods:
                artifacts = mgr.load_artifacts(ds, mod, meth)
                telemetry = mgr.load_engine_telemetry(ds, min_engine)

                session = ReplaySession(
                    session_id=f"parity-{ds}-{mod}-{meth}",
                    dataset=ds,
                    engine_id=min_engine,
                    model_family=mod,
                    method_id=meth,
                    artifacts=artifacts,
                    telemetry=telemetry,
                )

                # Advance to cycle 30
                for c in range(30):
                    resp = session.advance(expected_cycle=c)

                # Check prediction at cycle 30 matches cached prediction within atol=1e-4, rtol=0
                cached_row = engine_cached[engine_cached["endpoint_cycle"] == 30].iloc[0]
                cached_pred = float(cached_row["prediction"])

                assert resp.prediction is not None
                diff = abs(resp.prediction - cached_pred)
                assert diff < 1e-4, (
                    f"Mismatch {ds} {mod} {meth}: {resp.prediction} vs {cached_pred} (diff {diff})"
                )

                # Check interval bounds are valid and lower <= pred <= upper
                assert resp.lower_rul is not None
                assert resp.upper_rul is not None
                assert 0.0 <= resp.lower_rul <= resp.prediction + 1e-6
                assert resp.prediction - 1e-6 <= resp.upper_rul

                # Check interval bounds match direct frozen-calibrator calculations
                assert resp.regime is not None
                direct_lows, direct_upps, _ = artifacts.calibrator.predict_intervals(
                    predictions=np.array([cached_pred], dtype=np.float64),
                    regimes=[resp.regime],
                    nominal_coverage=0.90,
                )
                assert abs(resp.lower_rul - direct_lows[0]) < 1e-4, (
                    f"Lower bound mismatch: {resp.lower_rul} vs {direct_lows[0]}"
                )
                assert abs(resp.upper_rul - direct_upps[0]) < 1e-4, (
                    f"Upper bound mismatch: {resp.upper_rul} vs {direct_upps[0]}"
                )

                # Check action agrees with existing lower-bound maintenance policy
                state_obj = PredictionState(
                    engine_id=min_engine,
                    cycle=30,
                    point_rul=resp.prediction,
                    lower_rul=resp.lower_rul,
                    upper_rul=resp.upper_rul,
                    regime=None,
                )
                expected_act = lower_bound_one_cycle_policy(state_obj)
                expected_act_str = (
                    "MAINTAIN_NOW" if expected_act == MaintenanceAction.MAINTAIN_NOW else "CONTINUE"
                )
                assert resp.action == expected_act_str

                # Check future-row changes do not affect earlier outputs
                telem_corrupt = telemetry.copy()
                telem_corrupt.loc[telem_corrupt["cycle"] > 30, list(SENSOR_COLUMNS)] = 9999.0
                sess_corrupt = ReplaySession(
                    session_id=f"parity-corrupt-{ds}-{mod}-{meth}",
                    dataset=ds,
                    engine_id=min_engine,
                    model_family=mod,
                    method_id=meth,
                    artifacts=artifacts,
                    telemetry=telem_corrupt,
                )
                for c in range(30):
                    resp_corrupt = sess_corrupt.advance(expected_cycle=c)
                assert resp_corrupt.prediction == resp.prediction
                assert resp_corrupt.lower_rul == resp.lower_rul
                assert resp_corrupt.upper_rul == resp.upper_rul
                assert resp_corrupt.action == resp.action
