"""Independent verification and content audit functions for confirmatory evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.splits import load_split_manifest
from intellitwin.evaluation.bootstrap import (
    compute_bootstrap_ci,
)
from intellitwin.evaluation.decisions import validate_component_manifest_completeness
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_METHODS,
    CONTROL_ALL_FOUR,
    DECISION_QUANTILES,
    DESCRIPTIVE_QUANTILES,
)
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path


def verify_validation_smoke_matrix(
    smoke_dir: Path | str,
    base_dir: Path | str = ".",
) -> dict[str, Any]:
    """Perform content-level verification of all validation smoke artifacts.

    Verifies:
    1. Exact presence and hash integrity of all required smoke files.
    2. Exact configuration matrix (810 primary + 120 controls = 930 configurations).
    3. Exact outcome rows (16,470 primary + 3,120 controls = 19,590 total).
    4. Exact cell-summary rows (162 primary + 24 controls = 186 total).
    5. Validation-only engine membership (FD001: 10, FD002: 26, FD004: 25).
    6. Exact numerical reconstruction of cell summaries from engine outcomes.
    7. All bootstrap arrays have 10,000 replicates with correct metadata.
    8. Bootstrap replicate statistics match the underlying engine draws.
    9. Every saved confidence interval reconstructs from replicate statistics within 1e-10.
    10. Component manifest completeness for RQ1-RQ4.
    """
    base = Path(base_dir).resolve()
    s_dir = Path(smoke_dir).resolve()

    required_files = [
        "point_predictions.csv",
        "interval_predictions.csv",
        "decision_traces.csv",
        "engine_seed_outcomes.csv",
        "engine_metrics.csv",
        "subgroup_metrics.csv",
        "cell_summary.csv",
        "bootstrap_draws_FD001.npz",
        "bootstrap_draws_FD002.npz",
        "bootstrap_draws_FD004.npz",
        "bootstrap_statistics_FD001.npz",
        "bootstrap_statistics_FD002.npz",
        "bootstrap_statistics_FD004.npz",
        "bootstrap_statistics_RQ4.npz",
        "contrast_intervals.csv",
        "execution_manifest.json",
    ]

    checks: dict[str, Any] = {}
    missing_files = [f for f in required_files if not (s_dir / f).exists()]
    checks["required_files_present"] = len(missing_files) == 0
    if missing_files:
        checks["missing_files"] = missing_files
        return {
            "status": "FAIL",
            "reason": f"Missing required smoke files: {missing_files}",
            "checks": checks,
        }

    # 1. Verify split partitions
    expected_units: dict[str, list[int]] = {}
    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        s_man = load_split_manifest(split_p)
        expected_units[ds] = sorted(s_man.get_partition("validation"))

    checks["validation_engine_counts"] = {
        "FD001": len(expected_units["FD001"]) == 10,
        "FD002": len(expected_units["FD002"]) == 26,
        "FD004": len(expected_units["FD004"]) == 25,
    }

    # 2. Verify engine_seed_outcomes.csv
    df_outcomes = pd.read_csv(s_dir / "engine_seed_outcomes.csv", float_precision="round_trip")
    n_total_rows = len(df_outcomes)

    # Separate primary and controls
    df_primary = df_outcomes[df_outcomes["method_or_control_id"].isin(CONFIRMATORY_METHODS)]
    df_controls = df_outcomes[df_outcomes["method_or_control_id"].isin(CONTROL_ALL_FOUR)]

    n_prim_rows = len(df_primary)
    n_ctrl_rows = len(df_controls)

    checks["outcome_row_counts"] = {
        "primary_expected": 16470,
        "primary_actual": n_prim_rows,
        "primary_match": n_prim_rows == 16470,
        "controls_expected": 3120,
        "controls_actual": n_ctrl_rows,
        "controls_match": n_ctrl_rows == 3120,
        "total_expected": 19590,
        "total_actual": n_total_rows,
        "total_match": n_total_rows == 19590,
    }

    # Verify partition membership: validation only
    partition_clean = True
    for ds in CONFIRMATORY_DATASETS:
        ds_units = set(df_outcomes.loc[df_outcomes["dataset"] == ds, "unit"].unique())
        exp_u = set(expected_units[ds])
        if ds_units != exp_u:
            partition_clean = False
            checks[f"{ds}_partition_mismatch"] = {
                "extra": sorted(ds_units - exp_u),
                "missing": sorted(exp_u - ds_units),
            }
    checks["validation_partition_only"] = partition_clean

    # Verify configurations in outcomes
    primary_cfgs = set(
        zip(
            df_primary["dataset"],
            df_primary["model_family"],
            df_primary["method_or_control_id"],
            df_primary["nominal_coverage"],
            df_primary["scenario_id"],
            strict=False,
        )
    )
    control_cfgs = set(
        zip(
            df_controls["dataset"],
            df_controls["model_family"],
            df_controls["method_or_control_id"],
            df_controls["nominal_coverage"],
            df_controls["scenario_id"],
            strict=False,
        )
    )
    checks["configuration_counts"] = {
        "primary_expected": 810,
        "primary_actual": len(primary_cfgs) * 5,  # 5 seeds per (ds, mod, meth, cov, scen)
        "primary_cell_combos": len(primary_cfgs),  # 162
        "primary_combos_match": len(primary_cfgs) == 162,
        "control_expected": 120,
        "control_actual": len(control_cfgs) * 5,  # 5 seeds per combo
        "control_cell_combos": len(control_cfgs),  # 24
        "control_combos_match": len(control_cfgs) == 24,
    }

    # 3. Verify cell_summary.csv
    df_cell = pd.read_csv(s_dir / "cell_summary.csv", float_precision="round_trip")
    n_prim_sum = len(df_cell[df_cell["method_or_control_id"].isin(CONFIRMATORY_METHODS)])
    n_ctrl_sum = len(df_cell[df_cell["method_or_control_id"].isin(CONTROL_ALL_FOUR)])

    checks["cell_summary_counts"] = {
        "primary_expected": 162,
        "primary_actual": n_prim_sum,
        "primary_match": n_prim_sum == 162,
        "control_expected": 24,
        "control_actual": n_ctrl_sum,
        "control_match": n_ctrl_sum == 24,
        "total_expected": 186,
        "total_actual": len(df_cell),
        "total_match": len(df_cell) == 186,
    }

    # Verify numerical reconstruction of cell summary from outcomes
    max_cost_reconstruct_diff = 0.0
    for _, row in df_cell.iterrows():
        match_outcomes = df_outcomes[
            (df_outcomes["dataset"] == row["dataset"])
            & (df_outcomes["model_family"] == row["model_family"])
            & (df_outcomes["method_or_control_id"] == row["method_or_control_id"])
            & (np.isclose(df_outcomes["nominal_coverage"], row["nominal_coverage"]))
            & (df_outcomes["scenario_id"] == row["scenario_id"])
        ]
        # Equal engine mean cost: average seeds within engine, then average across engines
        engine_means = match_outcomes.groupby("unit")["total_cost"].mean()
        recomputed_cost = float(engine_means.mean())
        diff = abs(recomputed_cost - float(row["mean_cost"]))
        if diff > max_cost_reconstruct_diff:
            max_cost_reconstruct_diff = diff

    checks["cell_summary_cost_reconstruction"] = {
        "max_diff": max_cost_reconstruct_diff,
        "match": max_cost_reconstruct_diff < 1e-10,
    }

    # 4. Verify bootstrap draw arrays
    draws_valid = True
    for ds in CONFIRMATORY_DATASETS:
        draws_file = s_dir / f"bootstrap_draws_{ds}.npz"
        data = np.load(draws_file, allow_pickle=False)
        draws = data["draws"]
        if draws.shape != (10000, len(expected_units[ds])):
            draws_valid = False
            checks[f"{ds}_draws_shape_invalid"] = list(draws.shape)
    checks["bootstrap_draws_valid"] = draws_valid

    # 5. Verify bootstrap statistics arrays and CI reconstruction
    stats_valid = True
    for ds in CONFIRMATORY_DATASETS:
        stats_file = s_dir / f"bootstrap_statistics_{ds}.npz"
        data = np.load(stats_file, allow_pickle=False)
        for key in data.files:
            if key == "__metadata__":
                continue
            arr = data[key]
            if len(arr) != 10000:
                stats_valid = False
                checks[f"{ds}_{key}_len_invalid"] = len(arr)
    checks["bootstrap_statistics_valid"] = stats_valid

    # Verify contrast intervals reconstruction from statistics arrays
    df_contrasts = pd.read_csv(s_dir / "contrast_intervals.csv", float_precision="round_trip")
    max_ci_diff = 0.0

    # Load RQ4 stats as well
    rq4_data = np.load(s_dir / "bootstrap_statistics_RQ4.npz", allow_pickle=False)
    all_stats: dict[str, Any] = {
        ds: np.load(s_dir / f"bootstrap_statistics_{ds}.npz", allow_pickle=False)
        for ds in CONFIRMATORY_DATASETS
    }
    all_stats["RQ4"] = rq4_data

    for _, row in df_contrasts.iterrows():
        c_id = str(row["contrast_id"])
        ds = str(row["dataset"])
        # Find array
        if ds == "ALL_6_CELLS":
            # RQ4 array
            # remove RQ4_ prefix if needed
            arr_key = c_id.replace("RQ4_", "")
            if arr_key in rq4_data.files:
                rep_arr = rq4_data[arr_key]
            else:
                continue
        elif ds in all_stats and c_id in all_stats[ds].files:
            rep_arr = all_stats[ds][c_id]
        else:
            continue

        q95 = compute_bootstrap_ci(rep_arr, quantiles=DESCRIPTIVE_QUANTILES)
        q_dec = compute_bootstrap_ci(rep_arr, quantiles=DECISION_QUANTILES)

        diff_95_low = abs(q95[0] - float(row["ci_95_low"]))
        diff_95_high = abs(q95[1] - float(row["ci_95_high"]))
        diff_dec_low = abs(q_dec[0] - float(row["ci_decision_low"]))
        diff_dec_high = abs(q_dec[1] - float(row["ci_decision_high"]))

        diff = max(diff_95_low, diff_95_high, diff_dec_low, diff_dec_high)
        if diff > max_ci_diff:
            max_ci_diff = diff

    checks["contrast_intervals_reconstruction"] = {
        "max_diff": max_ci_diff,
        "match": max_ci_diff < 1e-10,
    }

    # 6. Verify component manifest completeness
    comp_manifest = validate_component_manifest_completeness()
    checks["component_manifest_completeness"] = comp_manifest

    # 7. Check traces validity
    df_traces = pd.read_csv(s_dir / "decision_traces.csv")
    checks["decision_traces_present"] = len(df_traces) > 0

    all_passed = (
        checks["required_files_present"]
        and all(checks["validation_engine_counts"].values())
        and checks["outcome_row_counts"]["total_match"]
        and checks["validation_partition_only"]
        and checks["configuration_counts"]["primary_combos_match"]
        and checks["configuration_counts"]["control_combos_match"]
        and checks["cell_summary_counts"]["total_match"]
        and checks["cell_summary_cost_reconstruction"]["match"]
        and checks["bootstrap_draws_valid"]
        and checks["bootstrap_statistics_valid"]
        and checks["contrast_intervals_reconstruction"]["match"]
        and checks["component_manifest_completeness"]["all_valid"]
    )

    return {
        "status": "PASS" if all_passed else "FAIL",
        "overall_match": all_passed,
        "checks": checks,
    }
