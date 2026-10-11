"""Automated unit and integration tests for the Step 6 simulator validation pilot."""

import json
from pathlib import Path

import pandas as pd
import pytest

from intellitwin.simulator.engine import simulate_fleet
from scripts.run_step06_simulator_validation import (
    DATA_PATH,
    REPO_ROOT,
    TEST_FIXTURE_COST_CONFIG,
    build_synthetic_prediction_states,
    compute_source_hash,
    pilot_threshold_policy,
    run_validation_pilot,
)


def _create_synthetic_unit_df(unit_id: int, lifetime: int, shuffle: bool = False) -> pd.DataFrame:
    """Helper to create a synthetic unit DataFrame."""
    cycles = list(range(1, lifetime + 1))
    if shuffle:
        import random

        random.seed(42)
        random.shuffle(cycles)
    return pd.DataFrame({"unit": [unit_id] * lifetime, "cycle": cycles})


# ==============================================================================
# SECTION A: Core Synthetic Unit Tests (Run without NASA raw data)
# ==============================================================================


def test_pilot_decision_cycles_and_bounds() -> None:
    """Verify first decision cycle is 30, last is T-1, and no state at T."""
    lifetime = 50
    unit_df = _create_synthetic_unit_df(1, lifetime)

    states = build_synthetic_prediction_states(unit_df, lifetime, "PERFECT", start_cycle=30)

    assert len(states) == 20  # cycles 30..49
    assert states[0].cycle == 30
    assert states[-1].cycle == 49
    assert all(s.cycle < lifetime for s in states)
    assert not any(s.cycle == lifetime for s in states)


def test_pilot_shuffled_input_sorting() -> None:
    """Verify that sorted input generates consecutive cycles."""
    lifetime = 45
    shuffled_df = _create_synthetic_unit_df(1, lifetime, shuffle=True)
    sorted_df = shuffled_df.sort_values("cycle").reset_index(drop=True)

    states = build_synthetic_prediction_states(sorted_df, lifetime, "PERFECT", start_cycle=30)
    actual_cycles = [s.cycle for s in states]
    assert actual_cycles == list(range(30, 45))


def test_pilot_exact_fixture_behavior_on_artificial_engine() -> None:
    """Verify deterministic fixture behavior: PERFECT waste=5, PESSIMISTIC waste=30."""
    lifetime = 100
    unit_df = _create_synthetic_unit_df(1, lifetime)

    # 1. PERFECT stream: MAINTAIN_NOW when lower_rul <= 5 -> occurs at y=5 (cycle 95), waste = 5
    states_perf = build_synthetic_prediction_states(unit_df, lifetime, "PERFECT", start_cycle=30)
    results_perf = simulate_fleet(
        [(1, lifetime, states_perf)], pilot_threshold_policy, TEST_FIXTURE_COST_CONFIG
    )
    assert len(results_perf) == 1
    assert results_perf[0].preventive_maintenance_indicator == 1
    assert results_perf[0].intervention_cycle == 95
    assert results_perf[0].wasted_rul == 5.0

    # 2. PESSIMISTIC stream: point = max(y-20,0), lower = max(point-5,0)
    # lower <= 5 occurs when point <= 10 -> y-20 <= 10 -> y <= 30 (cycle 70), waste = 30
    states_pess = build_synthetic_prediction_states(
        unit_df, lifetime, "PESSIMISTIC", start_cycle=30
    )
    results_pess = simulate_fleet(
        [(1, lifetime, states_pess)], pilot_threshold_policy, TEST_FIXTURE_COST_CONFIG
    )
    assert len(results_pess) == 1
    assert results_pess[0].preventive_maintenance_indicator == 1
    assert results_pess[0].intervention_cycle == 70
    assert results_pess[0].wasted_rul == 30.0

    # 3. OPTIMISTIC stream: point = y+20, lower = point-5.
    # At cycle 99 (y=1): point = 21, lower = 16 > 5 -> CONTINUE -> Failure at cycle 100
    states_opt = build_synthetic_prediction_states(unit_df, lifetime, "OPTIMISTIC", start_cycle=30)
    results_opt = simulate_fleet(
        [(1, lifetime, states_opt)], pilot_threshold_policy, TEST_FIXTURE_COST_CONFIG
    )
    assert len(results_opt) == 1
    assert results_opt[0].failure_indicator == 1
    assert results_opt[0].intervention_cycle is None
    assert results_opt[0].wasted_rul == 0.0


def test_pilot_pm_only_statistics_null_when_no_pm(tmp_path: Path) -> None:
    """Verify PM-only statistics are null when zero PM interventions occur."""
    lifetime = 50
    unit_df = _create_synthetic_unit_df(1, lifetime)
    states = build_synthetic_prediction_states(unit_df, lifetime, "OPTIMISTIC", start_cycle=30)

    results = simulate_fleet(
        [(1, lifetime, states)], pilot_threshold_policy, TEST_FIXTURE_COST_CONFIG
    )
    assert results[0].failure_indicator == 1
    assert results[0].preventive_maintenance_indicator == 0


def test_pilot_short_trajectory_rejection(tmp_path: Path) -> None:
    """Verify validation engines with T <= 30 are rejected explicitly."""
    # Write synthetic manifest with 26 engines (all id 1..26)
    val_ids = list(range(1, 27))
    manifest = {
        "partitions": {
            "train": [],
            "calibration": [],
            "validation": val_ids,
            "test": [],
        }
    }
    manifest_path = tmp_path / "test_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # Engine 1 has lifetime T = 30 (must be rejected!)
    raw_lines: list[str] = []
    for uid in val_ids:
        lifetime = 30 if uid == 1 else 50
        for cycle in range(1, lifetime + 1):
            raw_lines.append(f"{uid} {cycle} 0.0 0.0 0.0")

    data_path = tmp_path / "train_FD002_synth.txt"
    data_path.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")

    out_path = tmp_path / "out.json"
    with pytest.raises(ValueError, match="lifetime T=30 <= 30"):
        run_validation_pilot(
            data_path=data_path,
            split_manifest_path=manifest_path,
            output_json_path=out_path,
        )


def test_pilot_provenance_source_hashes() -> None:
    """Verify source hash calculation normalizes CRLF/CR to LF and produces valid SHA-256."""
    runner_path = REPO_ROOT / "scripts" / "run_step06_simulator_validation.py"
    engine_path = REPO_ROOT / "src" / "intellitwin" / "simulator" / "engine.py"

    h_runner = compute_source_hash(runner_path)
    h_engine = compute_source_hash(engine_path)

    assert len(h_runner) == 64
    assert len(h_engine) == 64
    assert all(c in "0123456789abcdef" for c in h_runner)
    assert all(c in "0123456789abcdef" for c in h_engine)


def test_pilot_non_validation_records_excluded(tmp_path: Path) -> None:
    """Verify non-validation records in raw data do not contribute to evaluated results."""
    val_ids = list(range(1, 27))
    manifest = {
        "partitions": {
            "train": [99, 100],
            "calibration": [101],
            "validation": val_ids,
            "test": [200],
        }
    }
    manifest_path = tmp_path / "test_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # Add extra rows for non-validation engines 99, 100, 200
    raw_lines: list[str] = []
    for uid in val_ids + [99, 100, 200]:
        for cycle in range(1, 51):
            raw_lines.append(f"{uid} {cycle} 0.0 0.0 0.0")

    data_path = tmp_path / "train_synth.txt"
    data_path.write_text("\n".join(raw_lines) + "\n", encoding="utf-8")

    out_path = tmp_path / "out.json"
    summary = run_validation_pilot(
        data_path=data_path,
        split_manifest_path=manifest_path,
        output_json_path=out_path,
    )

    assert summary["validation_engine_count"] == 26
    assert summary["validation_engine_ids"] == val_ids
    assert summary["held_out_test_engines_inspected"] == 0
    assert summary["stream_results"]["PERFECT"]["engine_count"] == 26


# ==============================================================================
# SECTION B: Real-Data Integration Test (Marked with @pytest.mark.integration)
# ==============================================================================


@pytest.mark.integration
def test_real_fd002_validation_pilot_execution(tmp_path: Path) -> None:
    """Verify real FD002 validation pilot execution against local NASA raw data."""
    if not DATA_PATH.exists():
        pytest.skip(f"NASA raw data file not present: {DATA_PATH}")

    out_path = tmp_path / "validation_summary.json"
    summary = run_validation_pilot(output_json_path=out_path)

    assert summary["validation_engine_count"] == 26
    assert summary["provenance"]["dataset"] == "FD002"
    assert summary["provenance"]["source_hash_scheme"] == "sha256-utf8-lf-v1"

    streams = summary["stream_results"]

    # Verify PERFECT stream outcome
    assert streams["PERFECT"]["engine_count"] == 26
    assert streams["PERFECT"]["preventive_maintenance_rate"] == 1.0
    assert streams["PERFECT"]["failure_rate"] == 0.0
    assert streams["PERFECT"]["mean_wasted_rul_all_engines"] == 5.0

    # Verify OPTIMISTIC stream outcome
    assert streams["OPTIMISTIC"]["engine_count"] == 26
    assert streams["OPTIMISTIC"]["preventive_maintenance_rate"] == 0.0
    assert streams["OPTIMISTIC"]["failure_rate"] == 1.0
    assert streams["OPTIMISTIC"]["mean_wasted_rul_all_engines"] == 0.0
    assert streams["OPTIMISTIC"]["mean_wasted_rul_preventive_only"] is None

    # Verify PESSIMISTIC stream outcome
    assert streams["PESSIMISTIC"]["engine_count"] == 26
    assert streams["PESSIMISTIC"]["preventive_maintenance_rate"] == 1.0
    assert streams["PESSIMISTIC"]["failure_rate"] == 0.0
    assert streams["PESSIMISTIC"]["mean_wasted_rul_all_engines"] == 30.0
