"""Validation-only numerical decision pilot for Step 6 Sequential Maintenance Simulator.

This script executes a validation-only pilot using the 26 VALIDATION engines
defined in data/splits/fd002_engine_split_seed_2026.json.

No training or held-out test engines are inspected or used.
This script produces descriptive simulator behavior to supply evidence for the
researcher to freeze numerical cost parameters and practical-effect thresholds.
"""

# ruff: noqa: E402
import json
import sys
from pathlib import Path
from typing import Any

# Define repository paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np
import pandas as pd

from intellitwin.simulator.engine import simulate_fleet
from intellitwin.simulator.types import (
    MaintenanceAction,
    PredictionState,
)

DATA_PATH = REPO_ROOT / "data" / "raw" / "cmapss" / "train_FD002.txt"
SPLIT_MANIFEST_PATH = REPO_ROOT / "data" / "splits" / "fd002_engine_split_seed_2026.json"
OUTPUT_JSON_PATH = (
    REPO_ROOT / "research" / "research_design" / "step06_validation_pilot_summary.json"
)

# C-MAPSS column names
COLUMNS = [
    "unit",
    "cycle",
    "setting1",
    "setting2",
    "setting3",
] + [f"s{i}" for i in range(1, 22)]


def pilot_threshold_policy(state: PredictionState) -> MaintenanceAction:
    """Validation-only threshold policy fixture: MAINTAIN_NOW if lower_rul <= 5.

    NOTE: The threshold 5 is a VALIDATION FIXTURE ONLY for simulator sanity checking.
    It is NOT a research maintenance policy threshold.
    """
    if state.lower_rul <= 5.0:
        return MaintenanceAction.MAINTAIN_NOW
    return MaintenanceAction.CONTINUE


def build_synthetic_prediction_states(
    df_unit: pd.DataFrame, failure_cycle: int, stream_type: str
) -> list[PredictionState]:
    """Construct deterministic synthetic prediction states for a validation engine.

    Streams:
    - PERFECT: point = true_rul, interval = [true_rul, true_rul]
    - OPTIMISTIC: point = true_rul + 20, interval = [point - 5, point + 5]
    - PESSIMISTIC: point = max(true_rul - 20, 0), interval = [max(point - 5, 0), point + 5]
    """
    states: list[PredictionState] = []
    unit_id = int(df_unit["unit"].iloc[0])

    for _, row in df_unit.iterrows():
        t = int(row["cycle"])
        if t >= failure_cycle:
            break

        true_rul = float(failure_cycle - t)

        if stream_type == "PERFECT":
            point_rul = true_rul
            lower_rul = true_rul
            upper_rul = true_rul
        elif stream_type == "OPTIMISTIC":
            point_rul = true_rul + 20.0
            lower_rul = point_rul - 5.0
            upper_rul = point_rul + 5.0
        elif stream_type == "PESSIMISTIC":
            point_rul = max(true_rul - 20.0, 0.0)
            lower_rul = max(point_rul - 5.0, 0.0)
            upper_rul = point_rul + 5.0
        else:
            raise ValueError(f"Unknown stream_type: {stream_type}")

        state = PredictionState(
            engine_id=unit_id,
            cycle=t,
            point_rul=point_rul,
            lower_rul=lower_rul,
            upper_rul=upper_rul,
            regime=None,
        )
        states.append(state)

    return states


def run_validation_pilot() -> dict[str, Any]:
    """Execute validation-only pilot across the 26 validation engines."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing required raw data file at '{DATA_PATH}'")

    if not SPLIT_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing split manifest at '{SPLIT_MANIFEST_PATH}'")

    # Load split manifest and extract VALIDATION engines ONLY
    with open(SPLIT_MANIFEST_PATH, encoding="utf-8") as f:
        split_data = json.load(f)

    val_engines = sorted(split_data["partitions"]["validation"])
    assert len(val_engines) == 26, f"Expected 26 validation engines, found {len(val_engines)}"

    # Load raw data and filter to VALIDATION engines ONLY
    df_raw = pd.read_csv(DATA_PATH, sep=r"\s+", header=None, names=COLUMNS, engine="python")
    df_val = df_raw[df_raw["unit"].isin(val_engines)].copy()

    # Calculate true failure cycle for each validation engine
    engine_failure_cycles: dict[int, int] = {}
    for unit_id in val_engines:
        unit_df = df_val[df_val["unit"] == unit_id]
        engine_failure_cycles[unit_id] = int(unit_df["cycle"].max())

    # Mock test-fixture cost configuration for validation output calculations
    # NOTE: Cost parameters in cost_scenarios.yaml remain UNLOCKED (null).
    # This dummy config is used strictly to structure pilot JSON output format.
    from intellitwin.simulator.costs import MaintenanceCostConfig

    dummy_cost_config = MaintenanceCostConfig(
        preventive_cost=100.0, failure_cost=500.0, wasted_rul_cost_per_cycle=10.0
    )

    stream_results: dict[str, Any] = {}

    for stream_type in ["PERFECT", "OPTIMISTIC", "PESSIMISTIC"]:
        trajectories = []
        for unit_id in val_engines:
            unit_df = df_val[df_val["unit"] == unit_id]
            f_cycle = engine_failure_cycles[unit_id]
            states = build_synthetic_prediction_states(unit_df, f_cycle, stream_type)
            trajectories.append((unit_id, f_cycle, states))

        results = simulate_fleet(trajectories, pilot_threshold_policy, dummy_cost_config)

        n_engines = len(results)
        pm_count = sum(r.preventive_maintenance_indicator for r in results)
        fail_count = sum(r.failure_indicator for r in results)

        pm_rate = pm_count / n_engines
        fail_rate = fail_count / n_engines

        wasted_ruls_all = [r.wasted_rul for r in results]
        mean_wasted_all = float(np.mean(wasted_ruls_all))

        wasted_ruls_pm = [r.wasted_rul for r in results if r.preventive_maintenance_indicator == 1]
        mean_wasted_pm = float(np.mean(wasted_ruls_pm)) if wasted_ruls_pm else 0.0
        median_wasted_pm = float(np.median(wasted_ruls_pm)) if wasted_ruls_pm else 0.0

        intervention_cycles = [
            r.intervention_cycle for r in results if r.intervention_cycle is not None
        ]

        stream_results[stream_type] = {
            "label": "SIMULATOR VALIDATION ONLY — NOT MODEL PERFORMANCE",
            "engine_count": n_engines,
            "preventive_maintenance_count": pm_count,
            "failure_count": fail_count,
            "preventive_maintenance_rate": round(pm_rate, 4),
            "failure_rate": round(fail_rate, 4),
            "mean_wasted_rul_all_engines": round(mean_wasted_all, 4),
            "mean_wasted_rul_preventive_only": round(mean_wasted_pm, 4),
            "median_wasted_rul_preventive_only": round(median_wasted_pm, 4),
            "intervention_cycle_summary": {
                "min": int(np.min(intervention_cycles)) if intervention_cycles else None,
                "mean": round(float(np.mean(intervention_cycles)), 2)
                if intervention_cycles
                else None,
                "max": int(np.max(intervention_cycles)) if intervention_cycles else None,
            },
        }

    summary = {
        "title": "Step 6 Validation-Only Numerical Decision Pilot Summary",
        "notice": "SIMULATOR VALIDATION ONLY — NOT MODEL PERFORMANCE OR RESEARCH RESULTS",
        "validation_engine_count": len(val_engines),
        "validation_engine_ids": val_engines,
        "held_out_test_engines_inspected": 0,
        "stream_results": stream_results,
    }

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Successfully generated validation pilot summary at: {OUTPUT_JSON_PATH}")
    return summary


if __name__ == "__main__":
    try:
        run_validation_pilot()
    except Exception as e:
        print(f"Error running validation pilot: {e}", file=sys.stderr)
        sys.exit(1)
