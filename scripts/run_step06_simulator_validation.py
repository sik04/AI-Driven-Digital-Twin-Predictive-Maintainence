"""Validation-only numerical decision pilot for Step 6 Sequential Maintenance Simulator.

This script executes a validation-only pilot using the 26 VALIDATION engines
defined in data/splits/fd002_engine_split_seed_2026.json.

Raw C-MAPSS FD002 data is parsed and hashed, then filtered strictly to the 26 frozen
validation engines. No training or held-out test engines are evaluated or used for
parameter selection.

This script produces descriptive simulator behavior to supply evidence for the
researcher to freeze numerical cost parameters and practical-effect thresholds.
"""

# ruff: noqa: E402
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np
import pandas as pd

from intellitwin.simulator.costs import MaintenanceCostConfig
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

# Test-fixture cost configuration for validation pilot calculations
# (NOT approved economic parameters)
TEST_FIXTURE_COST_CONFIG = MaintenanceCostConfig(
    preventive_cost=100.0,
    failure_cost=500.0,
    wasted_rul_cost_per_cycle=10.0,
)


def compute_file_sha256(filepath: Path) -> str:
    """Compute exact byte SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_source_hash(filepath: Path) -> str:
    """Compute SHA-256 of UTF-8 source after normalizing CRLF/CR line endings to LF.

    Recorded under source_hash_scheme = 'sha256-utf8-lf-v1'.
    """
    content = filepath.read_text(encoding="utf-8")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _get_git_commit_info() -> tuple[str, bool]:
    """Retrieve current git commit hash and dirty status before generation."""
    try:
        commit_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, stderr=subprocess.DEVNULL
            )
            .decode("utf-8")
            .strip()
        )
        status = (
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=REPO_ROOT, stderr=subprocess.DEVNULL
            )
            .decode("utf-8")
            .strip()
        )
        is_dirty = len(status) > 0
        return commit_sha, is_dirty
    except Exception:
        return "unknown", True


def pilot_threshold_policy(state: PredictionState) -> MaintenanceAction:
    """Validation-only threshold policy fixture: MAINTAIN_NOW if lower_rul <= 5.0.

    NOTE: The threshold 5 is a VALIDATION FIXTURE ONLY for simulator sanity checking.
    It is NOT an approved research maintenance policy.
    """
    if state.lower_rul <= 5.0:
        return MaintenanceAction.MAINTAIN_NOW
    return MaintenanceAction.CONTINUE


def build_synthetic_prediction_states(
    df_unit_sorted: pd.DataFrame,
    failure_cycle: int,
    stream_type: str,
    start_cycle: int = 30,
) -> list[PredictionState]:
    """Construct deterministic synthetic prediction states for a validation engine.

    States start at cycle 30 and run through failure_cycle - 1.

    Synthetic Stream Formulations:
    - PERFECT: point = y, lower = y, upper = y
    - OPTIMISTIC: point = y + 20, lower = point - 5, upper = point + 5
    - PESSIMISTIC: point = max(y - 20, 0), lower = max(point - 5, 0), upper = point + 5
    """
    states: list[PredictionState] = []
    unit_id = int(df_unit_sorted["unit"].iloc[0])

    for _, row in df_unit_sorted.iterrows():
        t = int(row["cycle"])
        if t < start_cycle:
            continue
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


def run_validation_pilot(
    data_path: Path | None = None,
    split_manifest_path: Path | None = None,
    output_json_path: Path | None = None,
) -> dict[str, Any]:
    """Execute validation-only pilot across the 26 validation engines.

    Parameters
    ----------
    data_path : Path | None
        Override path to raw C-MAPSS dataset. Defaults to DATA_PATH.
    split_manifest_path : Path | None
        Override path to split manifest. Defaults to SPLIT_MANIFEST_PATH.
    output_json_path : Path | None
        Override output JSON path. Defaults to OUTPUT_JSON_PATH.

    Returns
    -------
    dict[str, Any]
        Audit summary dictionary.
    """
    target_data_path = data_path or DATA_PATH
    target_manifest_path = split_manifest_path or SPLIT_MANIFEST_PATH
    target_output_path = output_json_path or OUTPUT_JSON_PATH

    if not target_data_path.exists():
        raise FileNotFoundError(f"Missing required raw data file at '{target_data_path}'")

    if not target_manifest_path.exists():
        raise FileNotFoundError(f"Missing split manifest at '{target_manifest_path}'")

    # Capture commit and dirty status before running calculations
    commit_sha, is_dirty = _get_git_commit_info()

    # Exact byte hashes for data and manifest
    data_hash = compute_file_sha256(target_data_path)
    manifest_hash = compute_file_sha256(target_manifest_path)

    # Source hashes normalized with sha256-utf8-lf-v1
    simulator_engine_path = REPO_ROOT / "src" / "intellitwin" / "simulator" / "engine.py"
    simulator_costs_path = REPO_ROOT / "src" / "intellitwin" / "simulator" / "costs.py"
    simulator_types_path = REPO_ROOT / "src" / "intellitwin" / "simulator" / "types.py"

    source_hashes = {
        "runner": compute_source_hash(Path(__file__)),
        "engine": compute_source_hash(simulator_engine_path),
        "costs": compute_source_hash(simulator_costs_path),
        "types": compute_source_hash(simulator_types_path),
    }

    # Load split manifest and extract VALIDATION engines ONLY
    with open(target_manifest_path, encoding="utf-8") as f:
        split_data = json.load(f)

    val_engines = sorted(split_data["partitions"]["validation"])
    if len(val_engines) != 26:
        raise ValueError(f"Expected 26 validation engines, found {len(val_engines)}")

    # Load raw data unit and cycle columns only
    df_raw = pd.read_csv(
        target_data_path,
        sep=r"\s+",
        header=None,
        usecols=[0, 1],
        names=["unit", "cycle"],
    )

    # Filter raw data strictly to the frozen validation partition
    df_val = df_raw[df_raw["unit"].isin(val_engines)].copy()

    # Validate and sort trajectories per engine; reject T <= 30
    sorted_validation_dfs: dict[int, pd.DataFrame] = {}
    engine_failure_cycles: dict[int, int] = {}
    for unit_id in val_engines:
        unit_df = df_val[df_val["unit"] == unit_id].sort_values("cycle").reset_index(drop=True)
        cycles = unit_df["cycle"].to_numpy()
        if len(cycles) == 0:
            raise ValueError(f"Validation engine {unit_id} has empty trajectory")
        if cycles[0] != 1:
            raise ValueError(f"Validation engine {unit_id} trajectory does not start at cycle 1")
        if not np.array_equal(cycles, np.arange(1, len(cycles) + 1)):
            raise ValueError(f"Validation engine {unit_id} trajectory is not strictly consecutive")
        f_cycle = int(cycles[-1])
        if f_cycle <= 30:
            raise ValueError(
                f"Validation engine {unit_id} has lifetime T={f_cycle} <= 30; "
                "cannot construct valid decision window starting at cycle 30"
            )
        engine_failure_cycles[unit_id] = f_cycle
        sorted_validation_dfs[unit_id] = unit_df

    stream_results: dict[str, Any] = {}

    for stream_type in ["PERFECT", "OPTIMISTIC", "PESSIMISTIC"]:
        trajectories = []
        for unit_id in val_engines:
            unit_df = sorted_validation_dfs[unit_id]
            f_cycle = engine_failure_cycles[unit_id]
            states = build_synthetic_prediction_states(
                unit_df, f_cycle, stream_type, start_cycle=30
            )
            trajectories.append((unit_id, f_cycle, states))

        results = simulate_fleet(trajectories, pilot_threshold_policy, TEST_FIXTURE_COST_CONFIG)

        n_engines = len(results)
        pm_count = sum(r.preventive_maintenance_indicator for r in results)
        fail_count = sum(r.failure_indicator for r in results)

        pm_rate = pm_count / n_engines
        fail_rate = fail_count / n_engines

        wasted_ruls_all = [r.wasted_rul for r in results]
        mean_wasted_all = float(np.mean(wasted_ruls_all))

        wasted_ruls_pm = [r.wasted_rul for r in results if r.preventive_maintenance_indicator == 1]
        if wasted_ruls_pm:
            mean_wasted_pm: float | None = round(float(np.mean(wasted_ruls_pm)), 4)
            median_wasted_pm: float | None = round(float(np.median(wasted_ruls_pm)), 4)
        else:
            mean_wasted_pm = None
            median_wasted_pm = None

        intervention_cycles = [
            r.intervention_cycle for r in results if r.intervention_cycle is not None
        ]
        if intervention_cycles:
            intervention_summary: dict[str, Any] | None = {
                "min": int(np.min(intervention_cycles)),
                "mean": round(float(np.mean(intervention_cycles)), 2),
                "median": round(float(np.median(intervention_cycles)), 2),
                "max": int(np.max(intervention_cycles)),
            }
        else:
            intervention_summary = None

        stream_results[stream_type] = {
            "label": "SIMULATOR VALIDATION ONLY — NOT MODEL PERFORMANCE",
            "engine_count": n_engines,
            "preventive_maintenance_count": pm_count,
            "failure_count": fail_count,
            "preventive_maintenance_rate": round(pm_rate, 4),
            "failure_rate": round(fail_rate, 4),
            "mean_wasted_rul_all_engines": round(mean_wasted_all, 4),
            "mean_wasted_rul_preventive_only": mean_wasted_pm,
            "median_wasted_rul_preventive_only": median_wasted_pm,
            "intervention_cycle_summary": intervention_summary,
        }

    summary = {
        "title": "Step 6 Validation-Only Numerical Decision Pilot Summary",
        "notice": "SIMULATOR VALIDATION ONLY — NOT MODEL PERFORMANCE OR RESEARCH RESULTS",
        "provenance": {
            "dataset": "FD002",
            "dataset_sha256": data_hash,
            "split_manifest_sha256": manifest_hash,
            "source_hash_scheme": "sha256-utf8-lf-v1",
            "source_hashes": source_hashes,
            "git_commit_sha": commit_sha,
            "git_dirty": is_dirty,
            "start_cycle": 30,
            "software_versions": {
                "python": sys.version.split()[0],
                "numpy": np.__version__,
                "pandas": pd.__version__,
            },
            "synthetic_stream_formulas": {
                "PERFECT": "point=y, lower=y, upper=y",
                "OPTIMISTIC": "point=y+20, lower=point-5, upper=point+5",
                "PESSIMISTIC": "point=max(y-20,0), lower=max(point-5,0), upper=point+5",
            },
            "policy_fixture": {
                "description": "MAINTAIN_NOW if lower_rul <= 5.0 else CONTINUE",
                "threshold": 5.0,
                "notice": "Validation fixture only — not an approved research policy",
            },
            "cost_fixture": {
                "preventive_cost": TEST_FIXTURE_COST_CONFIG.preventive_cost,
                "failure_cost": TEST_FIXTURE_COST_CONFIG.failure_cost,
                "wasted_rul_cost_per_cycle": TEST_FIXTURE_COST_CONFIG.wasted_rul_cost_per_cycle,
                "notice": "Validation fixtures only — not approved economic parameters",
            },
        },
        "validation_engine_count": len(val_engines),
        "validation_engine_ids": val_engines,
        "held_out_test_engines_inspected": 0,
        "data_processing_notes": (
            "Raw dataset file is parsed and hashed; records are strictly filtered to the 26 "
            "frozen validation engines before trajectory validation and simulation. "
            "Held-out test engines are never evaluated or used for parameter selection."
        ),
        "stream_results": stream_results,
    }

    target_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Successfully generated validation pilot summary at: {target_output_path}")
    return summary


if __name__ == "__main__":
    try:
        run_validation_pilot()
    except Exception as e:
        print(f"Error running validation pilot: {e}", file=sys.stderr)
        sys.exit(1)
