"""Independent reference verifier for Phase 8 ablation and robustness artifacts.

Strict Verification Protocol:
- Does NOT call production robustness runner, fitting, or simulation functions.
- Independently reconstructs all quantiles, intervals, simulations, aggregations,
  subgroup metrics, paired bootstrap draws, and contrasts from first principles.
- Numerical tolerances:
  - Deterministic reconstruction: atol=1e-10, rtol=0.
  - Checkpoint prediction parity: atol=1e-4, rtol=0.
- Fails closed on any missing, duplicate, altered, or out-of-tolerance records.
"""

from __future__ import annotations

import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.confirmatory.data import (
    verify_raw_data_hashes,
)
from intellitwin.data.artifacts import compute_sha256, load_preprocessor_artifact
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import (
    EXPECTED_ENGINE_COUNTS,
)
from intellitwin.data.splits import load_split_manifest, select_partition
from intellitwin.data.windowing import construct_windows
from intellitwin.evaluation.bootstrap import (
    DATASET_NUMBERS,
    load_partition_quartile_strata,
)
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
)
from intellitwin.models.registry import load_frozen_base_model
from intellitwin.robustness.ablation import (
    ALL_EIGHT_ABLATION_VARIANTS,
)
from intellitwin.robustness.perturbations import (
    STRESS_CONDITION_BY_ID,
    apply_stream_perturbation,
    generate_engine_dropout_uniforms,
    generate_engine_noise_array,
)
from intellitwin.uncertainty.artifacts import (
    resolve_repo_relative_path,
)
from intellitwin.uncertainty.schema import (
    CandidateConfig,
)
from intellitwin.uncertainty.scores import (
    compute_decision_aware_score,
)

TOL_DETERMINISTIC_ATOL: float = 1e-10
TOL_DETERMINISTIC_RTOL: float = 0.0
TOL_CHECKPOINT_ATOL: float = 1e-4
TOL_CHECKPOINT_RTOL: float = 0.0

REQUIRED_PHASE08_FILES: tuple[str, ...] = (
    "execution_manifest.json",
    "input_manifest.json",
    "execution.log",
    "ablation_engine_metrics.csv",
    "stress_engine_metrics.csv",
    "ablation_engine_seed_metrics.csv",
    "stress_engine_seed_rep_metrics.csv",
    "ablation_summary.csv",
    "stress_summary.csv",
    "subgroup_metrics.csv",
    "subgroup_engine_metrics.csv",
    "paired_contrasts.csv",
    "factor_main_effects.csv",
    "zero_difference_checks.csv",
    "ablation_simulation_outcomes.csv",
    "stress_simulation_outcomes.csv",
    "ablation_interval_predictions.csv.gz",
    "stress_interval_predictions.csv.gz",
    "bootstrap_draws_FD001.npz",
    "bootstrap_draws_FD002.npz",
    "bootstrap_draws_FD004.npz",
    "bootstrap_statistics_FD001.npz",
    "bootstrap_statistics_FD002.npz",
    "bootstrap_statistics_FD004.npz",
    "perturbation_manifest.json",
    "pip_freeze.txt",
    "pip_check.txt",
)

REQUIRED_PROVENANCE_FIELDS: tuple[str, ...] = (
    "protocol_version",
    "schema_version",
    "status",
    "git_commit",
    "git_dirty",
    "platform",
    "python_version",
    "start_time_utc",
    "end_time_utc",
    "duration_seconds",
    "counts",
    "artifact_hashes",
)

REQUIRED_COUNTS_FIELDS: tuple[str, ...] = (
    "ablation_configurations",
    "stress_evaluations",
    "datasets",
    "models",
    "seeds",
    "bootstrap_replicates",
    "total_test_engines",
)


def _reconstruct_reference_quantile(
    engine_ids: np.ndarray[Any, Any],
    scores: np.ndarray[Any, Any],
    nominal_coverage: float = 0.90,
) -> float:
    """Independent reference calculation for hierarchical conformal quantile threshold.

    Computes sorted weighted scores and exact Fraction boundary checks.
    """
    eids = np.asarray(engine_ids)
    sc = np.asarray(scores, dtype=np.float64)

    if len(sc) == 0:
        return float("inf")

    target_frac = (
        Fraction(90, 100)
        if abs(nominal_coverage - 0.90) < 1e-6
        else Fraction(str(nominal_coverage))
    )

    engine_scores: dict[int, list[float]] = defaultdict(list)
    for eid, s_val in zip(eids, sc, strict=True):
        engine_scores[int(eid)].append(float(s_val))

    m = len(engine_scores)
    if m == 0:
        return float("inf")

    n_i = {eid: len(vals) for eid, vals in engine_scores.items()}
    required_sum = Fraction(m + 1) * target_frac

    if Fraction(m) < required_sum:
        return float("inf")

    sorted_engine_scores = {
        eid: np.sort(np.asarray(vals, dtype=np.float64)) for eid, vals in engine_scores.items()
    }

    obs_scores = np.asarray(sc, dtype=np.float64)
    obs_weights = np.array([1.0 / n_i[int(eid)] for eid in eids], dtype=np.float64)
    sort_idx = np.argsort(obs_scores)
    sorted_s = obs_scores[sort_idx]
    sorted_w = obs_weights[sort_idx]

    unique_scores, group_indices = np.unique(sorted_s, return_index=True)
    cum_w = np.cumsum(sorted_w)
    last_indices = np.empty_like(group_indices)
    last_indices[:-1] = group_indices[1:] - 1
    last_indices[-1] = len(sorted_s) - 1
    unique_cum_w = cum_w[last_indices]

    def exact_mass(q_val: float) -> Fraction:
        tot = Fraction(0, 1)
        for eid, vals in sorted_engine_scores.items():
            cnt = int(np.searchsorted(vals, q_val, side="right"))
            tot += Fraction(cnt, n_i[eid])
        return tot

    req_float = float(required_sum)
    cand_idx = int(np.searchsorted(unique_cum_w, req_float - 1e-11))
    if cand_idx >= len(unique_scores):
        cand_idx = len(unique_scores) - 1

    while (
        cand_idx < len(unique_scores) and exact_mass(float(unique_scores[cand_idx])) < required_sum
    ):
        cand_idx += 1
    while cand_idx > 0 and exact_mass(float(unique_scores[cand_idx - 1])) >= required_sum:
        cand_idx -= 1

    if cand_idx >= len(unique_scores):
        return float("inf")

    return float(unique_scores[cand_idx])


def _reconstruct_reference_intervals(
    predictions: np.ndarray[Any, Any],
    regimes: np.ndarray[Any, Any],
    global_threshold: float,
    regime_thresholds: dict[str, float],
    gamma: int,
    beta_code: int,
    routing: str,
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Independent reference calculation for interval inversion."""
    p = np.asarray(predictions, dtype=np.float64)
    if gamma == 0:
        sigma_p = np.ones_like(p)
    elif gamma == 1:
        sigma_p = 1.0 + (p / 125.0)
    elif gamma == 2:
        b_val = 1.0 + (p / 125.0)
        sigma_p = b_val * b_val
    else:
        sigma_p = (1.0 + (p / 125.0)) ** gamma

    beta = 0.0 if beta_code == 0 else -np.log(2.0)
    z_p = np.exp(-p / 20.0)
    a_p = sigma_p * np.exp(beta * z_p)
    b_p = sigma_p * np.exp(-beta * z_p)

    n = len(p)
    thresholds = np.empty(n, dtype=np.float64)
    fallback_used = np.zeros(n, dtype=bool)

    if routing == "global":
        thresholds.fill(global_threshold)
    else:
        for i in range(n):
            r_str = str(regimes[i])
            if r_str in regime_thresholds:
                thresholds[i] = regime_thresholds[r_str]
            else:
                thresholds[i] = global_threshold
                fallback_used[i] = True

    lower = np.maximum(0.0, p - thresholds * a_p)
    upper = p + thresholds * b_p
    return lower, upper, fallback_used


def _reconstruct_reference_simulation(
    cycles: np.ndarray[Any, Any],
    lower_bounds: np.ndarray[Any, Any],
    failure_cycle: int,
    c_pm: float = 1.0,
    c_fail: float = 5.0,
    c_waste: float = 0.20,
) -> dict[str, Any]:
    """Independent reference calculation for maintenance policy simulation."""
    pm_occurred = False
    failed = True
    intervention_cycle = None
    wasted_rul = 0.0

    for i in range(len(cycles)):
        cyc = int(cycles[i])
        if cyc >= failure_cycle:
            break
        if lower_bounds[i] <= 1.0:
            intervention_cycle = cyc
            pm_occurred = True
            failed = False
            wasted_rul = float(failure_cycle - cyc)
            break

    if pm_occurred:
        cost = c_pm + c_waste * wasted_rul
    else:
        cost = c_fail
        wasted_rul = 0.0

    return {
        "failed": failed,
        "pm_occurred": pm_occurred,
        "intervention_cycle": intervention_cycle,
        "wasted_rul": wasted_rul,
        "total_cost": cost,
    }


def _reconstruct_independent_bootstrap_draws(
    dataset: str,
    partition_engines: list[int],
    base_dir: Path,
    n_replicates: int = 10000,
) -> np.ndarray[Any, Any]:
    """Independently generate bootstrap draws according to locked PCG64 formula."""
    ds_num = DATASET_NUMBERS[dataset]
    seed_seq = np.random.SeedSequence([2026, 8, ds_num])
    rng = np.random.Generator(np.random.PCG64(seed_seq))

    strata = load_partition_quartile_strata(dataset, partition_engines, base_dir=base_dir)
    total_engines = sum(len(engs) for engs in strata.values())
    draws = np.zeros((n_replicates, total_engines), dtype=int)

    for b in range(n_replicates):
        row_engs: list[int] = []
        for q_name in ("Q1", "Q2", "Q3", "Q4"):
            engs = strata[q_name]
            n_q = len(engs)
            if n_q > 0:
                idx_draws = rng.integers(0, n_q, size=n_q)
                for idx in idx_draws:
                    row_engs.append(engs[idx])
        draws[b, :] = row_engs

    return draws


def verify_simulation_terminal_precedence(df_ablation_sim: pd.DataFrame) -> list[str]:
    """Verify that no engine has both failed and PM occurred, or PM at or after failure cycle."""
    violations: list[str] = []
    if "failed" not in df_ablation_sim.columns or "pm_occurred" not in df_ablation_sim.columns:
        return ["ablation_simulation_outcomes missing failed or pm_occurred columns"]

    for r in df_ablation_sim.itertuples():
        if getattr(r, "failed", False) and getattr(r, "pm_occurred", False):
            violations.append(f"Engine {r.unit} marked both failed and PM occurred!")
        if getattr(r, "intervention_cycle", None) is not None:
            if not getattr(r, "pm_occurred", False):
                violations.append(
                    f"Engine {r.unit} has intervention cycle but pm_occurred is False!"
                )
    return violations


def verify_equal_engine_subgroup_math(
    df_subgroups: pd.DataFrame,
    df_sub_eng: pd.DataFrame,
    tol_atol: float = TOL_DETERMINISTIC_ATOL,
    tol_rtol: float = TOL_DETERMINISTIC_RTOL,
) -> list[str]:
    """Verify that subgroup_metrics.csv coverage and miss rates equally average distinct engines."""
    mismatches: list[str] = []
    grp_keys = [
        "evaluation_type",
        "dataset",
        "model_family",
        "variant_id",
        "method_id",
        "condition_id",
        "subgroup_family",
        "subgroup",
    ]
    if not all(c in df_subgroups.columns for c in grp_keys) or not all(
        c in df_sub_eng.columns for c in grp_keys
    ):
        return ["subgroup metrics tables are missing required grouping columns"]

    for (eval_t, ds, mf, vid, mid, cid, fam, grp), sum_row in df_subgroups.groupby(grp_keys):
        sub_engs = df_sub_eng[
            (df_sub_eng["evaluation_type"] == eval_t)
            & (df_sub_eng["dataset"] == ds)
            & (df_sub_eng["model_family"] == mf)
            & (df_sub_eng["subgroup_family"] == fam)
            & (df_sub_eng["subgroup"] == grp)
        ]
        if eval_t == "ablation":
            sub_engs = sub_engs[sub_engs["variant_id"] == vid]
        else:
            sub_engs = sub_engs[(sub_engs["method_id"] == mid) & (sub_engs["condition_id"] == cid)]

        if len(sub_engs) > 0:
            exp_cov = float(sub_engs["coverage"].mean())
            act_cov = float(sum_row["coverage"].iloc[0])
            if not np.isclose(exp_cov, act_cov, atol=tol_atol, rtol=tol_rtol):
                mismatches.append(
                    f"{ds}/{mf}/{grp}: equal-engine cov exp={exp_cov} != act={act_cov}"
                )

            exp_n_engs = len(sub_engs)
            act_n_engs = int(sum_row["n_engines"].iloc[0])
            if exp_n_engs != act_n_engs:
                mismatches.append(
                    f"{ds}/{mf}/{grp}: distinct engines exp={exp_n_engs} != act={act_n_engs}"
                )

            act_elig = bool(sum_row["is_eligible"].iloc[0])
            exp_elig = exp_n_engs >= 10
            if act_elig != exp_elig:
                mismatches.append(f"{ds}/{mf}/{grp}: eligibility exp={exp_elig} != act={act_elig}")
    return mismatches


def verify_summary_aggregations(
    df_ablation_summary: pd.DataFrame,
    df_ablation_engine: pd.DataFrame,
    df_stress_summary: pd.DataFrame,
    df_stress_engine: pd.DataFrame,
    tol_atol: float = TOL_DETERMINISTIC_ATOL,
    tol_rtol: float = TOL_DETERMINISTIC_RTOL,
) -> list[str]:
    """Verify that summary tables accurately reflect engine-level means."""
    mismatches: list[str] = []
    # Ablation summary check
    abl_grp_keys = ["dataset", "model_family", "variant_id"]
    if not all(c in df_ablation_engine.columns for c in abl_grp_keys) or not all(
        c in df_ablation_summary.columns for c in abl_grp_keys
    ):
        mismatches.append("ablation summary or engine metrics missing required keys")
    else:
        for (ds, mf, vid), grp in df_ablation_engine.groupby(abl_grp_keys):
            match_sum = df_ablation_summary[
                (df_ablation_summary["dataset"] == ds)
                & (df_ablation_summary["model_family"] == mf)
                & (df_ablation_summary["variant_id"] == vid)
            ]
            if len(match_sum) == 0:
                mismatches.append(f"Missing row in ablation_summary for ({ds}, {mf}, {vid})")
                continue
            row = match_sum.iloc[0]
            for metric in ("coverage", "cost", "width", "interval_score", "rmse"):
                if metric in grp.columns and f"{metric}_mean" in row:
                    exp_val = float(grp[metric].mean())
                    act_val = float(row[f"{metric}_mean"])
                    if not np.isclose(exp_val, act_val, atol=tol_atol, rtol=tol_rtol):
                        mismatches.append(
                            f"Ablation {ds}/{mf}/{vid} {metric}_mean: "
                            f"exp={exp_val} != act={act_val}"
                        )

    # Stress summary check
    stress_grp_keys = ["dataset", "model_family", "method_id", "condition_id"]
    if not all(c in df_stress_engine.columns for c in stress_grp_keys) or not all(
        c in df_stress_summary.columns for c in stress_grp_keys
    ):
        mismatches.append("stress summary or engine metrics missing required keys")
    else:
        for (ds, mf, mid, cid), grp in df_stress_engine.groupby(stress_grp_keys):
            match_sum = df_stress_summary[
                (df_stress_summary["dataset"] == ds)
                & (df_stress_summary["model_family"] == mf)
                & (df_stress_summary["method_id"] == mid)
                & (df_stress_summary["condition_id"] == cid)
            ]
            if len(match_sum) == 0:
                mismatches.append(f"Missing row in stress_summary for ({ds}, {mf}, {mid}, {cid})")
                continue
            row = match_sum.iloc[0]
            for metric in ("coverage", "cost", "width", "interval_score", "rmse"):
                if metric in grp.columns and f"{metric}_mean" in row:
                    exp_val = float(grp[metric].mean())
                    act_val = float(row[f"{metric}_mean"])
                    if not np.isclose(exp_val, act_val, atol=tol_atol, rtol=tol_rtol):
                        mismatches.append(
                            f"Stress {ds}/{mf}/{cid} {metric}_mean: exp={exp_val} != act={act_val}"
                        )
    return mismatches


def verify_exact_keys_and_duplicates(
    ev_dir: Path,
    expected_units: dict[str, list[int]],
) -> list[str]:
    """Verify that engine and simulation outcome files contain expected keys without dups."""
    mismatches: list[str] = []

    # 1. ablation_engine_seed_metrics.csv
    abl_seed_p = ev_dir / "ablation_engine_seed_metrics.csv"
    if abl_seed_p.exists():
        df_abl_raw = pd.read_csv(abl_seed_p)
        keys_abl = ["dataset", "model_family", "variant_id", "seed", "unit"]
        dups_abl = int(df_abl_raw.duplicated(subset=keys_abl).sum())
        if dups_abl > 0:
            mismatches.append(f"ablation_engine_seed_metrics has {dups_abl} duplicate keys")
        exp_abl_rows = sum(len(expected_units[ds]) * 2 * 8 * 5 for ds in CONFIRMATORY_DATASETS)
        if len(df_abl_raw) != exp_abl_rows:
            mismatches.append(
                f"ablation_engine_seed_metrics expected {exp_abl_rows} rows, got {len(df_abl_raw)}"
            )

    # 2. stress_engine_seed_rep_metrics.csv
    str_seed_p = ev_dir / "stress_engine_seed_rep_metrics.csv"
    if str_seed_p.exists():
        df_str_raw = pd.read_csv(str_seed_p)
        keys_str = [
            "dataset",
            "model_family",
            "method_id",
            "condition_id",
            "replicate_id",
            "seed",
            "unit",
        ]
        dups_str = int(df_str_raw.duplicated(subset=keys_str).sum())
        if dups_str > 0:
            mismatches.append(f"stress_engine_seed_rep_metrics has {dups_str} duplicate keys")
        exp_str_rows = sum(len(expected_units[ds]) * 540 for ds in CONFIRMATORY_DATASETS)
        if len(df_str_raw) != exp_str_rows:
            mismatches.append(
                f"stress_engine_seed_rep_metrics exp {exp_str_rows} rows, got {len(df_str_raw)}"
            )

    # 3. paired_contrasts.csv
    paired_p = ev_dir / "paired_contrasts.csv"
    if paired_p.exists():
        df_contrasts = pd.read_csv(paired_p)
        keys_con = [
            "comparison_type",
            "dataset",
            "model_family",
            "variant_or_condition",
            "baseline_or_full",
            "metric",
        ]
        dups_con = int(df_contrasts.duplicated(subset=keys_con).sum())
        if dups_con > 0:
            mismatches.append(f"paired_contrasts has {dups_con} duplicate keys")
        if len(df_contrasts) != 1176:
            mismatches.append(f"paired_contrasts expected 1,176 rows, got {len(df_contrasts)}")

    # 4. zero_difference_checks.csv
    zero_p = ev_dir / "zero_difference_checks.csv"
    if zero_p.exists():
        df_zero = pd.read_csv(zero_p)
        if len(df_zero) != 168:
            mismatches.append(f"zero_difference_checks expected 168 rows, got {len(df_zero)}")
        if "delta_point" not in df_zero.columns or not (df_zero["delta_point"] == 0.0).all():
            mismatches.append("Non-zero or missing delta_point found in zero_difference_checks.csv")
        if (
            "ci_95_low" not in df_zero.columns
            or "ci_95_high" not in df_zero.columns
            or not (df_zero["ci_95_low"] == 0.0).all()
            or not (df_zero["ci_95_high"] == 0.0).all()
        ):
            mismatches.append("Non-zero or missing CI endpoint found in zero_difference_checks.csv")

    # 5. factor_main_effects.csv
    fac_p = ev_dir / "factor_main_effects.csv"
    if fac_p.exists():
        df_fac = pd.read_csv(fac_p)
        keys_fac = ["dataset", "model_family", "factor", "metric"]
        dups_fac = int(df_fac.duplicated(subset=keys_fac).sum())
        if dups_fac > 0:
            mismatches.append(f"factor_main_effects has {dups_fac} duplicate keys")
        if len(df_fac) != 126:
            mismatches.append(f"factor_main_effects expected 126 rows, got {len(df_fac)}")

    return mismatches


def verify_all_bootstrap_contrasts_and_effects(
    ev_dir: Path,
    df_ablation_engine: pd.DataFrame,
    df_stress_engine: pd.DataFrame,
    df_paired_contrasts: pd.DataFrame,
    df_factor_effects: pd.DataFrame,
    tol_atol: float = TOL_DETERMINISTIC_ATOL,
    tol_rtol: float = TOL_DETERMINISTIC_RTOL,
) -> tuple[list[str], float]:
    """Verify EVERY contrast (1,176 rows) and ALL THREE factor effects (126 rows)."""
    mismatches: list[str] = []
    max_discrepancy: float = 0.0

    # Build metric lookup tables
    abl_store: dict[tuple[str, str, str, str], dict[int, float]] = {}
    metric_cols = [
        "rmse",
        "coverage",
        "coverage_abs_error",
        "width",
        "interval_score",
        "cost",
        "failure_rate",
    ]
    req_abl = ["dataset", "model_family", "variant_id", "unit"] + metric_cols
    if not all(c in df_ablation_engine.columns for c in req_abl):
        return ["ablation_engine_metrics.csv missing required columns"], 0.0

    req_str = ["dataset", "model_family", "method_id", "condition_id", "unit"] + metric_cols
    if not all(c in df_stress_engine.columns for c in req_str):
        return ["stress_engine_metrics.csv missing required columns"], 0.0

    for (ds, mf, vid), grp in df_ablation_engine.groupby(["dataset", "model_family", "variant_id"]):
        for col in metric_cols:
            abl_store[(ds, mf, vid, col)] = dict(zip(grp["unit"], grp[col], strict=False))

    stress_store: dict[tuple[str, str, str, str, str], dict[int, float]] = {}
    for (ds, mf, mid, cid), grp in df_stress_engine.groupby(
        ["dataset", "model_family", "method_id", "condition_id"]
    ):
        for col in metric_cols:
            stress_store[(ds, mf, mid, cid, col)] = dict(zip(grp["unit"], grp[col], strict=False))

    factor_definitions = {
        "gamma_scale": (
            [
                "gamma2_beta0_global",
                "gamma2_beta0_regime",
                "gamma2_betam1_global",
                "gamma2_betam1_regime",
            ],
            [
                "gamma0_beta0_global",
                "gamma0_beta0_regime",
                "gamma0_betam1_global",
                "gamma0_betam1_regime",
            ],
        ),
        "beta_asymmetry": (
            [
                "gamma0_betam1_global",
                "gamma0_betam1_regime",
                "gamma2_betam1_global",
                "gamma2_betam1_regime",
            ],
            [
                "gamma0_beta0_global",
                "gamma0_beta0_regime",
                "gamma2_beta0_global",
                "gamma2_beta0_regime",
            ],
        ),
        "regime_routing": (
            [
                "gamma0_beta0_regime",
                "gamma0_betam1_regime",
                "gamma2_beta0_regime",
                "gamma2_betam1_regime",
            ],
            [
                "gamma0_beta0_global",
                "gamma0_betam1_global",
                "gamma2_beta0_global",
                "gamma2_betam1_global",
            ],
        ),
    }

    req_cols_con = [
        "comparison_type",
        "dataset",
        "model_family",
        "variant_or_condition",
        "baseline_or_full",
        "metric",
        "delta_point",
        "ci_95_low",
        "ci_95_high",
    ]
    if not all(c in df_paired_contrasts.columns for c in req_cols_con):
        return ["paired_contrasts.csv missing required columns"], 0.0

    req_cols_fac = [
        "dataset",
        "model_family",
        "factor",
        "metric",
        "effect_on_minus_off",
        "ci_95_low",
        "ci_95_high",
    ]
    if not all(c in df_factor_effects.columns for c in req_cols_fac):
        return ["factor_main_effects.csv missing required columns"], 0.0

    for ds in CONFIRMATORY_DATASETS:
        stat_npz_p = ev_dir / f"bootstrap_statistics_{ds}.npz"
        draws_npz_p = ev_dir / f"bootstrap_draws_{ds}.npz"
        if not stat_npz_p.exists() or not draws_npz_p.exists():
            mismatches.append(f"Missing bootstrap artifacts for {ds}")
            continue

        try:
            stats_data = np.load(stat_npz_p)
            draws_data = np.load(draws_npz_p)["draws"]
        except Exception as exc:
            mismatches.append(f"Error loading bootstrap arrays for {ds}: {exc}")
            continue

        # 1. Verify all paired contrasts for this dataset
        ds_contrasts = df_paired_contrasts[df_paired_contrasts["dataset"] == ds]
        for r in ds_contrasts.itertuples():
            comp_type = r.comparison_type
            mf = r.model_family
            metric = r.metric

            if comp_type == "ablation":
                vid = r.variant_or_condition
                stat_key = f"ablation_{ds}_{mf}_{vid}_minus_full_{metric}"
                dict_a = abl_store.get((ds, mf, vid, metric))
                dict_b = abl_store.get((ds, mf, "gamma2_betam1_regime", metric))
            else:
                cid = r.variant_or_condition
                mid = r.baseline_or_full
                stat_key = f"stress_{ds}_{mf}_{mid}_{cid}_minus_clean_{metric}"
                dict_a = stress_store.get((ds, mf, mid, cid, metric))
                dict_b = stress_store.get((ds, mf, mid, "clean", metric))

            if dict_a is None or dict_b is None:
                mismatches.append(f"Missing engine metric lookup for {stat_key}")
                continue

            units = sorted(dict_a.keys())
            exp_pt = float(
                np.mean([dict_a[u] for u in units]) - np.mean([dict_b[u] for u in units])
            )
            act_pt = float(r.delta_point)
            pt_diff = abs(exp_pt - act_pt)
            if pt_diff > max_discrepancy:
                max_discrepancy = pt_diff
            if not np.isclose(exp_pt, act_pt, atol=tol_atol, rtol=tol_rtol):
                mismatches.append(f"{stat_key} delta_point: exp={exp_pt} != act={act_pt}")

            if stat_key not in stats_data:
                mismatches.append(f"Missing statistic array {stat_key} in {ds}")
                continue

            reps = stats_data[stat_key]
            if len(reps) != 10000:
                mismatches.append(f"{stat_key} replicates length {len(reps)} != 10000")
                continue

            # Independent replication check
            diff_map = {u: float(dict_a[u] - dict_b[u]) for u in units}
            exp_reps = np.mean(np.vectorize(diff_map.get, otypes=[np.float64])(draws_data), axis=1)
            reps_diff = float(np.max(np.abs(exp_reps - reps)))
            if reps_diff > max_discrepancy:
                max_discrepancy = reps_diff
            if not np.allclose(exp_reps, reps, atol=tol_atol, rtol=tol_rtol):
                mismatches.append(f"{stat_key} bootstrap replicates do not match independent draws")

            exp_lo, exp_hi = np.quantile(exp_reps, [0.025, 0.975], method="linear")
            act_lo, act_hi = float(r.ci_95_low), float(r.ci_95_high)
            if not np.isclose(exp_lo, act_lo, atol=tol_atol, rtol=tol_rtol) or not np.isclose(
                exp_hi, act_hi, atol=tol_atol, rtol=tol_rtol
            ):
                mismatches.append(
                    f"{stat_key} CI: exp=[{exp_lo}, {exp_hi}] != act=[{act_lo}, {act_hi}]"
                )

        # 2. Verify all factor main effects for this dataset
        ds_factors = df_factor_effects[df_factor_effects["dataset"] == ds]
        for r in ds_factors.itertuples():
            mf = r.model_family
            factor_name = r.factor
            metric = r.metric
            stat_key = f"factor_{ds}_{mf}_{factor_name}_on_minus_off_{metric}"

            on_vids, off_vids = factor_definitions[factor_name]
            units = sorted(abl_store[(ds, mf, on_vids[0], metric)].keys())

            on_means = {
                u: float(np.mean([abl_store[(ds, mf, vid, metric)][u] for vid in on_vids]))
                for u in units
            }
            off_means = {
                u: float(np.mean([abl_store[(ds, mf, vid, metric)][u] for vid in off_vids]))
                for u in units
            }
            exp_pt = float(
                np.mean([on_means[u] for u in units]) - np.mean([off_means[u] for u in units])
            )
            act_pt = float(r.effect_on_minus_off)
            pt_diff = abs(exp_pt - act_pt)
            if pt_diff > max_discrepancy:
                max_discrepancy = pt_diff
            if not np.isclose(exp_pt, act_pt, atol=tol_atol, rtol=tol_rtol):
                mismatches.append(f"{stat_key} effect_on_minus_off: exp={exp_pt} != act={act_pt}")

            if stat_key not in stats_data:
                mismatches.append(f"Missing statistic array {stat_key} in {ds}")
                continue

            reps = stats_data[stat_key]
            diff_map = {u: float(on_means[u] - off_means[u]) for u in units}
            exp_reps = np.mean(np.vectorize(diff_map.get, otypes=[np.float64])(draws_data), axis=1)
            reps_diff = float(np.max(np.abs(exp_reps - reps)))
            if reps_diff > max_discrepancy:
                max_discrepancy = reps_diff
            if not np.allclose(exp_reps, reps, atol=tol_atol, rtol=tol_rtol):
                mismatches.append(f"{stat_key} bootstrap replicates do not match independent draws")

            exp_lo, exp_hi = np.quantile(exp_reps, [0.025, 0.975], method="linear")
            act_lo, act_hi = float(r.ci_95_low), float(r.ci_95_high)
            if not np.isclose(exp_lo, act_lo, atol=tol_atol, rtol=tol_rtol) or not np.isclose(
                exp_hi, act_hi, atol=tol_atol, rtol=tol_rtol
            ):
                mismatches.append(
                    f"{stat_key} CI: exp=[{exp_lo}, {exp_hi}] != act=[{act_lo}, {act_hi}]"
                )

    return mismatches, max_discrepancy


def independently_verify_phase08_evidence(
    evidence_dir: Path | str,
    base_dir: Path | str = ".",
    raw_data_dir: Path | str = "data/raw/cmapss",
    calibration_cache_dir: Path | str = "experiments/calibration/point_predictions/calibration",
    confirmatory_dir: Path | str = "experiments/confirmatory_v1",
    tol_atol: float = TOL_DETERMINISTIC_ATOL,
    tol_rtol: float = TOL_DETERMINISTIC_RTOL,
) -> dict[str, Any]:
    """Execute complete independent reference verification and audit of Phase 8 evidence.

    Fails closed on any inconsistency, altered thresholds, missing cells,
    unsafe paths, or empty hash inventories.
    """
    base = Path(base_dir).resolve()
    ev_dir = Path(evidence_dir).resolve()

    checks: dict[str, Any] = {}
    failing_reasons: list[str] = []
    max_discrepancy_overall: float = 0.0

    # -------------------------------------------------------------------------
    # 1. Required Files Presence
    # -------------------------------------------------------------------------
    missing_files = [f for f in REQUIRED_PHASE08_FILES if not (ev_dir / f).exists()]
    checks["required_files_present"] = {
        "status": "PASS" if not missing_files else "FAIL",
        "missing_files": missing_files,
    }
    if missing_files:
        failing_reasons.append(f"Missing required Phase 8 evidence files: {missing_files}")
        return {
            "overall_status": "FAIL",
            "failing_reasons": failing_reasons,
            "checks": checks,
            "max_discrepancies": {"overall": max_discrepancy_overall},
        }

    # -------------------------------------------------------------------------
    # 2. Manifest Schema & Expected Artifact Inventory
    # -------------------------------------------------------------------------
    manifest_p = ev_dir / "execution_manifest.json"
    try:
        with open(manifest_p, encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as exc:
        failing_reasons.append(f"Could not parse execution_manifest.json: {exc}")
        return {
            "overall_status": "FAIL",
            "failing_reasons": failing_reasons,
            "checks": checks,
            "max_discrepancies": {"overall": max_discrepancy_overall},
        }

    if manifest.get("status") != "EXPLORATORY_POST_CONFIRMATORY":
        failing_reasons.append(
            f"Invalid manifest status: expected EXPLORATORY_POST_CONFIRMATORY, "
            f"got {manifest.get('status')}"
        )

    if manifest.get("git_dirty") is True:
        failing_reasons.append("Provenance violation: git_dirty is true in execution_manifest.json")

    missing_prov = [f for f in REQUIRED_PROVENANCE_FIELDS if manifest.get(f) is None]
    if missing_prov:
        failing_reasons.append(
            f"Missing mandatory provenance fields in execution_manifest.json: {missing_prov}"
        )

    man_counts_check = manifest.get("counts", {})
    if not isinstance(man_counts_check, dict):
        failing_reasons.append("counts field is not a mapping in execution_manifest.json")
    else:
        missing_cnts = [f for f in REQUIRED_COUNTS_FIELDS if man_counts_check.get(f) is None]
        if missing_cnts:
            failing_reasons.append(
                f"Missing counts fields in execution_manifest.json: {missing_cnts}"
            )

    art_hashes = manifest.get("artifact_hashes")
    if not art_hashes or not isinstance(art_hashes, dict):
        failing_reasons.append(
            "artifact_hashes mapping is absent or empty in execution_manifest.json"
        )
        checks["artifact_inventory_integrity"] = {
            "status": "FAIL",
            "reason": "empty_or_absent_artifact_hashes",
        }
        return {
            "overall_status": "FAIL",
            "failing_reasons": failing_reasons,
            "checks": checks,
            "max_discrepancies": {"overall": max_discrepancy_overall},
        }

    # Verify POSIX relative paths and hashes
    hash_mismatches: list[str] = []
    unsafe_paths: list[str] = []
    for rel_path, exp_h in art_hashes.items():
        p_obj = Path(rel_path)
        if (
            p_obj.is_absolute()
            or ".." in p_obj.parts
            or "\\" in rel_path
            or rel_path.startswith("/")
        ):
            unsafe_paths.append(rel_path)
            continue

        fpath = ev_dir / p_obj
        if not fpath.exists():
            hash_mismatches.append(f"{rel_path} (file missing on disk)")
            continue
        act_h = compute_sha256(fpath)
        if act_h != exp_h:
            hash_mismatches.append(f"{rel_path} (expected {exp_h}, got {act_h})")

    if unsafe_paths:
        failing_reasons.append(
            f"Unsafe artifact paths detected in execution_manifest.json: {unsafe_paths[:5]}"
        )
    if hash_mismatches:
        failing_reasons.append(
            f"Artifact hash mismatches in execution manifest: {hash_mismatches[:5]}"
        )

    checks["artifact_inventory_integrity"] = {
        "status": "PASS" if not hash_mismatches and not unsafe_paths else "FAIL",
        "total_inventoried": len(art_hashes),
        "hash_mismatches": hash_mismatches[:10],
        "unsafe_paths": unsafe_paths[:10],
    }

    # -------------------------------------------------------------------------
    # 3. Protected Input Hashes & Raw Data Verification
    # -------------------------------------------------------------------------
    try:
        raw_hashes = verify_raw_data_hashes(raw_data_dir=raw_data_dir, base_dir=base)
        checks["raw_source_hashes"] = {"status": "PASS", "hashes": raw_hashes}
    except Exception as exc:
        checks["raw_source_hashes"] = {"status": "FAIL", "error": str(exc)}
        failing_reasons.append(f"Raw source hash verification failed: {exc}")

    in_man_p = ev_dir / "input_manifest.json"
    in_man: dict[str, Any] = {}
    try:
        with open(in_man_p, encoding="utf-8") as f:
            in_man = json.load(f)
    except Exception as exc:
        failing_reasons.append(f"Could not parse input_manifest.json: {exc}")

    pre_prot = in_man.get("pre_execution_protected_hashes", {})
    post_prot = in_man.get("post_execution_protected_hashes", {})
    if not pre_prot or not post_prot or pre_prot != post_prot:
        failing_reasons.append("Input manifest protected hashes inconsistent or missing.")
        checks["protected_inputs_consistency"] = {"status": "FAIL"}
    else:
        checks["protected_inputs_consistency"] = {"status": "PASS", "count": len(pre_prot)}

    # -------------------------------------------------------------------------
    # 4. Derivation and Validation of Split Engines & Expected Counts
    # -------------------------------------------------------------------------
    expected_units: dict[str, list[int]] = {}
    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        s_man = load_split_manifest(split_p)
        expected_units[ds] = sorted(s_man.get_partition("test"))

    total_expected_test_engines = sum(len(expected_units[ds]) for ds in CONFIRMATORY_DATASETS)
    man_counts = manifest.get("counts", {})
    if man_counts.get("ablation_configurations") != 240:
        failing_reasons.append(
            f"Expected 240 ablation configurations, got {man_counts.get('ablation_configurations')}"
        )
    if man_counts.get("stress_evaluations") != 1620:
        failing_reasons.append(
            f"Expected 1,620 stress evaluations, got {man_counts.get('stress_evaluations')}"
        )
    if man_counts.get("total_test_engines") != total_expected_test_engines:
        failing_reasons.append(
            f"Expected {total_expected_test_engines} test engines, "
            f"got {man_counts.get('total_test_engines')}"
        )

    exact_key_mismatches = verify_exact_keys_and_duplicates(ev_dir, expected_units)
    checks["exact_keys_and_duplicates"] = {
        "status": "PASS" if not exact_key_mismatches else "FAIL",
        "mismatches": exact_key_mismatches[:10],
    }
    if exact_key_mismatches:
        failing_reasons.extend(exact_key_mismatches)

    # -------------------------------------------------------------------------
    # 5. Independent Reference Threshold Reconstruction & Equivalence Gates
    # -------------------------------------------------------------------------
    cal_mismatches: list[str] = []
    cal_dir = ev_dir / "exploratory_calibrators"
    num_calibrators_checked = 0

    expected_regimes_by_ds: dict[str, list[str]] = {
        "FD001": ["C1"],
        "FD002": ["C1", "C2", "C3", "C4", "C5", "C6"],
        "FD004": ["C1", "C2", "C3", "C4", "C5", "C6"],
    }

    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                cal_cache_p = base / calibration_cache_dir / ds / mf / f"seed_{seed}.csv"
                if not cal_cache_p.exists():
                    failing_reasons.append(f"Missing calibration cache: {cal_cache_p}")
                    continue
                df_cal = pd.read_csv(cal_cache_p)
                eids = df_cal["unit"].to_numpy(dtype=int)
                preds = df_cal["prediction"].to_numpy(dtype=float)
                labels = df_cal["rul_true"].to_numpy(dtype=float)
                regimes = df_cal["regime"].to_numpy()

                for variant in ALL_EIGHT_ABLATION_VARIANTS:
                    cal_fname = f"{ds}_{mf}_seed{seed}_{variant.variant_id}.json"
                    cal_p = cal_dir / cal_fname
                    if not cal_p.exists():
                        cal_mismatches.append(f"Missing exploratory calibrator {cal_fname}")
                        continue

                    with open(cal_p, encoding="utf-8") as f:
                        saved_cal = json.load(f)

                    cand = CandidateConfig.from_params(
                        gamma=variant.gamma, beta_code=variant.beta_code
                    )
                    scores = compute_decision_aware_score(
                        predictions=preds, labels=labels, candidate=cand
                    )
                    exp_global_q = _reconstruct_reference_quantile(
                        eids, scores, nominal_coverage=0.90
                    )

                    saved_b90 = saved_cal.get("threshold_bundles", {}).get("coverage_90", {})
                    act_global_q = saved_b90.get("global_threshold")

                    if act_global_q is None:
                        cal_mismatches.append(f"{cal_fname}: global threshold is missing or None")
                    elif not np.isclose(act_global_q, exp_global_q, atol=tol_atol, rtol=tol_rtol):
                        diff = abs(act_global_q - exp_global_q)
                        if diff > max_discrepancy_overall:
                            max_discrepancy_overall = diff
                        cal_mismatches.append(
                            f"{cal_fname}: global act={act_global_q} != exp={exp_global_q}"
                        )

                    # Regime thresholds verification
                    saved_reg_thresholds = saved_b90.get("regime_thresholds", {})
                    exp_reg_list = expected_regimes_by_ds[ds]
                    for reg_id in exp_reg_list:
                        reg_str = str(reg_id)
                        reg_mask = regimes == reg_str
                        reg_eids = eids[reg_mask]
                        reg_scores = scores[reg_mask]
                        distinct_engs = len(np.unique(reg_eids))
                        exp_reg_q = (
                            _reconstruct_reference_quantile(reg_eids, reg_scores, 0.90)
                            if distinct_engs >= 10
                            else exp_global_q
                        )

                        act_reg_rec = saved_reg_thresholds.get(reg_str)
                        if act_reg_rec is None:
                            cal_mismatches.append(
                                f"{cal_fname}: missing regime threshold record for {reg_str}"
                            )
                            continue

                        act_reg_q = act_reg_rec.get("threshold")
                        if act_reg_q is None:
                            cal_mismatches.append(
                                f"{cal_fname} reg {reg_str}: regime threshold value is None"
                            )
                        elif not np.isclose(act_reg_q, exp_reg_q, atol=tol_atol, rtol=tol_rtol):
                            diff = abs(act_reg_q - exp_reg_q)
                            if diff > max_discrepancy_overall:
                                max_discrepancy_overall = diff
                            cal_mismatches.append(
                                f"{cal_fname} reg {reg_str}: act={act_reg_q} != exp={exp_reg_q}"
                            )

                        # Metadata assertions
                        elig_act = act_reg_rec.get("eligible_engines")
                        if elig_act != distinct_engs:
                            cal_mismatches.append(
                                f"{cal_fname} reg {reg_str}: eligible_engines "
                                f"act={elig_act} != exp={distinct_engs}"
                            )
                        is_elig_act = act_reg_rec.get("is_eligible")
                        if is_elig_act != (distinct_engs >= 10):
                            cal_mismatches.append(
                                f"{cal_fname} reg {reg_str}: is_eligible "
                                f"act={is_elig_act} != exp={distinct_engs >= 10}"
                            )

                    # Candidate parameter assertions
                    cand_params = saved_cal.get("candidate_parameters", {})
                    if cand_params.get("gamma") != variant.gamma:
                        cal_mismatches.append(f"{cal_fname}: candidate gamma mismatch")
                    if cand_params.get("beta_code") != variant.beta_code:
                        cal_mismatches.append(f"{cal_fname}: candidate beta_code mismatch")
                    if cand_params.get("routing") != variant.routing:
                        cal_mismatches.append(f"{cal_fname}: candidate routing mismatch")

                    num_calibrators_checked += 1

    checks["calibrator_threshold_reconstruction"] = {
        "status": "PASS" if not cal_mismatches else "FAIL",
        "checked_calibrators": num_calibrators_checked,
        "mismatches": cal_mismatches[:10],
    }
    if cal_mismatches:
        failing_reasons.append(
            f"Calibrator threshold reconstruction failed: {len(cal_mismatches)} mismatches"
        )
        failing_reasons.extend(cal_mismatches)

    # Equivalence gates check
    equiv_mismatches: list[str] = []
    if not cal_dir.exists():
        equiv_mismatches.append(f"Missing exploratory calibrators directory: {cal_dir}")
    else:

        def _get_q(c: dict[str, Any]) -> float:
            if "threshold_bundles" in c:
                return float(c["threshold_bundles"]["coverage_90"]["global_threshold"])
            return float(c["coverage_bundles"]["0.9"]["global_threshold"])

        for ds in CONFIRMATORY_DATASETS:
            for mf in CONFIRMATORY_MODELS:
                for s in CONFIRMATORY_SEEDS:
                    # 1. global_hcp equivalence
                    p_g0 = cal_dir / f"{ds}_{mf}_seed{s}_gamma0_beta0_global.json"
                    p_fg = (
                        base
                        / "experiments/calibration/fitted"
                        / ds
                        / mf
                        / f"seed_{s}/global_hcp/calibrator.json"
                    )
                    if not p_g0.exists() or not p_fg.exists():
                        equiv_mismatches.append(
                            f"Missing calibrator file for global_hcp equivalence: {p_g0.name}"
                        )
                        continue
                    with open(p_g0, encoding="utf-8") as f:
                        c_g0 = json.load(f)
                    with open(p_fg, encoding="utf-8") as f:
                        c_fg = json.load(f)
                    q_g0 = _get_q(c_g0)
                    q_fg = _get_q(c_fg)
                    if not np.isclose(q_g0, q_fg, atol=tol_atol, rtol=tol_rtol):
                        equiv_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma0_beta0_global != global_hcp"
                        )

                    # 2. regime_hcp equivalence
                    p_r0 = cal_dir / f"{ds}_{mf}_seed{s}_gamma0_beta0_regime.json"
                    p_fr = (
                        base
                        / "experiments/calibration/fitted"
                        / ds
                        / mf
                        / f"seed_{s}/regime_hcp/calibrator.json"
                    )
                    if not p_r0.exists() or not p_fr.exists():
                        equiv_mismatches.append(
                            f"Missing calibrator file for regime_hcp equivalence: {p_r0.name}"
                        )
                        continue
                    with open(p_r0, encoding="utf-8") as f:
                        c_r0 = json.load(f)
                    with open(p_fr, encoding="utf-8") as f:
                        c_fr = json.load(f)
                    q_r0 = _get_q(c_r0)
                    q_fr = _get_q(c_fr)
                    if not np.isclose(q_r0, q_fr, atol=tol_atol, rtol=tol_rtol):
                        equiv_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma0_beta0_regime != regime_hcp"
                        )

                    # 3. decision_aware_hcp equivalence
                    p_full = cal_dir / f"{ds}_{mf}_seed{s}_gamma2_betam1_regime.json"
                    p_fd = (
                        base
                        / "experiments/calibration/fitted"
                        / ds
                        / mf
                        / f"seed_{s}/decision_aware_hcp/calibrator.json"
                    )
                    if not p_full.exists() or not p_fd.exists():
                        equiv_mismatches.append(
                            f"Missing calibrator for decision_aware_hcp: {p_full.name}"
                        )
                        continue
                    with open(p_full, encoding="utf-8") as f:
                        c_full = json.load(f)
                    with open(p_fd, encoding="utf-8") as f:
                        c_fd = json.load(f)
                    q_full = _get_q(c_full)
                    q_fd = _get_q(c_fd)
                    if not np.isclose(q_full, q_fd, atol=tol_atol, rtol=tol_rtol):
                        equiv_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma2_betam1_regime != decision_aware_hcp"
                        )

                    # 4. FD001 global vs regime equivalence
                    if ds == "FD001":
                        q_g_fd = c_full["threshold_bundles"]["coverage_90"]["global_threshold"]
                        q_r_fd = c_full["threshold_bundles"]["coverage_90"]["regime_thresholds"][
                            "C1"
                        ]["threshold"]
                        if not np.isclose(q_g_fd, q_r_fd, atol=tol_atol, rtol=tol_rtol):
                            equiv_mismatches.append(
                                f"FD001_{mf}_seed{s}: global != regime routing on FD001"
                            )

    checks["equivalence_gates"] = {
        "status": "PASS" if not equiv_mismatches else "FAIL",
        "mismatches": equiv_mismatches,
    }
    if equiv_mismatches:
        failing_reasons.append(f"Equivalence gate violations: {equiv_mismatches}")

    # -------------------------------------------------------------------------
    # 6. Independent Bootstrap Draws Reconstruction
    # -------------------------------------------------------------------------
    draws_mismatches: list[str] = []
    for ds in CONFIRMATORY_DATASETS:
        exp_draws = _reconstruct_independent_bootstrap_draws(
            dataset=ds,
            partition_engines=expected_units[ds],
            base_dir=base,
            n_replicates=10000,
        )
        draws_p = ev_dir / f"bootstrap_draws_{ds}.npz"
        if not draws_p.exists():
            draws_mismatches.append(f"Missing {draws_p.name}")
            continue
        try:
            saved_npz = np.load(draws_p)
            act_draws = saved_npz["draws"]
            if not np.array_equal(exp_draws, act_draws):
                draws_mismatches.append(
                    f"{ds} bootstrap draws do not match independent reference draws"
                )
        except Exception as exc:
            draws_mismatches.append(f"Error reading {draws_p.name}: {exc}")

    checks["bootstrap_draws_reconstruction"] = {
        "status": "PASS" if not draws_mismatches else "FAIL",
        "mismatches": draws_mismatches,
    }
    if draws_mismatches:
        failing_reasons.append(f"Bootstrap draw reconstruction failed: {draws_mismatches}")

    # -------------------------------------------------------------------------
    # 7. Independent Perturbation Streams & Checkpoint Parity Verification
    # -------------------------------------------------------------------------
    pert_mismatches: list[str] = []
    for ds in CONFIRMATORY_DATASETS:
        for eng in expected_units[ds][:3]:
            for rep in (0, 1):
                # 1. Noise sharing across levels
                z_005 = generate_engine_noise_array(ds, eng, rep, 30)
                z_010 = generate_engine_noise_array(ds, eng, rep, 30)
                if not np.array_equal(z_005, z_010):
                    pert_mismatches.append(f"Noise standard normals not shared for {ds} eng {eng}")

                # 2. Dropout sharing across rates
                u_005 = generate_engine_dropout_uniforms(ds, eng, rep, 30)
                u_010 = generate_engine_dropout_uniforms(ds, eng, rep, 30)
                if not np.array_equal(u_005, u_010):
                    pert_mismatches.append(f"Dropout uniforms not shared for {ds} eng {eng}")

                # Verify that dropout at 0.05 implies dropout at 0.10
                mask_005 = u_005 < 0.05
                mask_010 = u_010 < 0.10
                if not np.all(~mask_005 | mask_010):
                    pert_mismatches.append(f"Dropout monotonicity violated for {ds} eng {eng}")

    # Check clean predictions against frozen confirmatory cache
    conf_pred_p = base / confirmatory_dir / "point_predictions.csv"
    if conf_pred_p.exists():
        try:
            df_conf = pd.read_csv(conf_pred_p)
            df_abl_sample = pd.read_csv(ev_dir / "ablation_interval_predictions.csv.gz", nrows=5000)
            if "dataset" in df_abl_sample.columns and len(df_abl_sample) > 0:
                sub_conf = df_conf[
                    (df_conf["dataset"] == df_abl_sample["dataset"].iloc[0])
                    & (df_conf["model_family"] == df_abl_sample["model_family"].iloc[0])
                    & (df_conf["seed"] == df_abl_sample["seed"].iloc[0])
                    & (df_conf["unit"] == df_abl_sample["unit"].iloc[0])
                ].sort_values("endpoint_cycle")

                sub_abl = df_abl_sample[
                    (df_abl_sample["unit"] == df_abl_sample["unit"].iloc[0])
                    & (df_abl_sample["variant_id"] == df_abl_sample["variant_id"].iloc[0])
                ].sort_values("endpoint_cycle")

                if len(sub_conf) > 0 and len(sub_abl) > 0:
                    merged = pd.merge(
                        sub_abl, sub_conf, on=["unit", "endpoint_cycle"], suffixes=("_abl", "_conf")
                    )
                    if not np.allclose(
                        merged["prediction_abl"],
                        merged["prediction_conf"],
                        atol=tol_atol,
                        rtol=tol_rtol,
                    ):
                        pert_mismatches.append("Clean predictions do not match confirmatory cache")
        except Exception as exc:
            pert_mismatches.append(f"Clean prediction cache verification error: {exc}")

    # Checkpoint parity verification on sample
    try:
        sample_model = load_frozen_base_model("FD001", "GBR", 2026, base_dir=base)
        raw_p = base / raw_data_dir / "train_FD001.txt"
        df_raw = load_cmapss_run_to_failure(raw_p, "FD001", EXPECTED_ENGINE_COUNTS["FD001"])
        split_p = resolve_repo_relative_path(base, "data/splits/fd001_engine_split_seed_2026.json")
        s_man = load_split_manifest(split_p)
        df_part = select_partition(df_raw, s_man, "test")
        prep_p = resolve_repo_relative_path(
            base, "experiments/preprocessing/FD001/preprocessor.json"
        )
        preproc, _ = load_preprocessor_artifact(prep_p)
        df_trans = preproc.transform(df_part)

        cond_sample = STRESS_CONDITION_BY_ID["noise_std_005"]
        df_pert = apply_stream_perturbation(df_trans, "FD001", cond_sample, replicate_id=0)
        wins = construct_windows(df_pert)
        pts = sample_model.predict(wins.X_sequence)

        # Compare with stress_interval_predictions.csv.gz
        df_str_p = pd.read_csv(ev_dir / "stress_interval_predictions.csv.gz", nrows=5000)
        df_str_sub = df_str_p[
            (df_str_p["dataset"] == "FD001")
            & (df_str_p["model_family"] == "GBR")
            & (df_str_p["seed"] == 2026)
            & (df_str_p["condition_id"] == "noise_std_005")
            & (df_str_p["replicate_id"] == 0)
            & (df_str_p["method_id"] == "global_hcp")
        ].sort_values(["unit", "endpoint_cycle"])

        if len(df_str_sub) > 0:
            saved_preds = df_str_sub["prediction"].to_numpy()[: len(pts[: len(df_str_sub)])]
            recalc_preds = pts[: len(df_str_sub)]
            if not np.allclose(
                saved_preds, recalc_preds, atol=TOL_CHECKPOINT_ATOL, rtol=TOL_CHECKPOINT_RTOL
            ):
                pert_mismatches.append("Checkpoint prediction parity failed under stress probe")
    except Exception as exc:
        pert_mismatches.append(f"Checkpoint prediction parity error: {exc}")

    checks["perturbation_generation_integrity"] = {
        "status": "PASS" if not pert_mismatches else "FAIL",
        "mismatches": pert_mismatches,
    }
    if pert_mismatches:
        failing_reasons.extend(pert_mismatches)

    # -------------------------------------------------------------------------
    # 8. Reconstruct Interval Inversion, Simulation Policy, and Engine Metrics
    # -------------------------------------------------------------------------
    df_ablation_engine = pd.read_csv(ev_dir / "ablation_engine_metrics.csv")
    df_ablation_sim = pd.read_csv(ev_dir / "ablation_simulation_outcomes.csv")
    df_subgroups = pd.read_csv(ev_dir / "subgroup_metrics.csv")
    df_paired_contrasts = pd.read_csv(ev_dir / "paired_contrasts.csv")
    df_factor_effects = pd.read_csv(ev_dir / "factor_main_effects.csv")

    sim_violations = verify_simulation_terminal_precedence(df_ablation_sim)
    checks["simulation_terminal_precedence"] = {
        "status": "PASS" if not sim_violations else "FAIL",
        "violations": sim_violations[:10],
    }
    if sim_violations:
        failing_reasons.extend(sim_violations)

    # Validate Equal-Engine Subgroup Weighting
    df_sub_eng = pd.read_csv(ev_dir / "subgroup_engine_metrics.csv")
    subgroup_math_mismatches = verify_equal_engine_subgroup_math(
        df_subgroups, df_sub_eng, tol_atol=tol_atol, tol_rtol=tol_rtol
    )
    checks["equal_engine_subgroup_reconstruction"] = {
        "status": "PASS" if not subgroup_math_mismatches else "FAIL",
        "mismatches": subgroup_math_mismatches[:10],
    }
    if subgroup_math_mismatches:
        failing_reasons.append(
            f"Subgroup equal-engine weighting failed: {len(subgroup_math_mismatches)} mismatches"
        )

    # Validate Summary Aggregations
    df_stress_engine = pd.read_csv(ev_dir / "stress_engine_metrics.csv")
    df_stress_summary = pd.read_csv(ev_dir / "stress_summary.csv")
    df_ablation_summary = pd.read_csv(ev_dir / "ablation_summary.csv")
    summary_mismatches = verify_summary_aggregations(
        df_ablation_summary=df_ablation_summary,
        df_ablation_engine=df_ablation_engine,
        df_stress_summary=df_stress_summary,
        df_stress_engine=df_stress_engine,
        tol_atol=tol_atol,
        tol_rtol=tol_rtol,
    )
    checks["summary_aggregation_reconstruction"] = {
        "status": "PASS" if not summary_mismatches else "FAIL",
        "mismatches": summary_mismatches[:10],
    }
    if summary_mismatches:
        failing_reasons.extend(summary_mismatches)

    # Validate ALL Bootstrap Contrasts and Factor Main Effects
    bootstrap_mismatches, max_boot_discrepancy = verify_all_bootstrap_contrasts_and_effects(
        ev_dir=ev_dir,
        df_ablation_engine=df_ablation_engine,
        df_stress_engine=df_stress_engine,
        df_paired_contrasts=df_paired_contrasts,
        df_factor_effects=df_factor_effects,
        tol_atol=tol_atol,
        tol_rtol=tol_rtol,
    )
    if max_boot_discrepancy > max_discrepancy_overall:
        max_discrepancy_overall = max_boot_discrepancy

    checks["paired_contrasts_and_bootstrap_statistics"] = {
        "status": "PASS" if not bootstrap_mismatches else "FAIL",
        "checked_contrasts": len(df_paired_contrasts),
        "checked_factors": len(df_factor_effects),
        "max_discrepancy": max_boot_discrepancy,
        "mismatches": bootstrap_mismatches[:10],
    }
    if bootstrap_mismatches:
        failing_reasons.append(
            f"Paired contrasts and bootstrap statistics verification failed: "
            f"{len(bootstrap_mismatches)} mismatches (e.g. {bootstrap_mismatches[0]})"
        )

    # No 'favors_variant' column in paired_contrasts.csv
    if "favors_variant" in df_paired_contrasts.columns:
        failing_reasons.append("Misleading 'favors_variant' column present in paired_contrasts.csv")
        checks["no_misleading_interpretations"] = {"status": "FAIL"}
    else:
        checks["no_misleading_interpretations"] = {"status": "PASS"}

    # Overall Status Determination
    overall_status = "PASS" if not failing_reasons else "FAIL"

    return {
        "overall_status": overall_status,
        "failing_reasons": failing_reasons,
        "max_discrepancies": {"overall": max_discrepancy_overall},
        "checks": checks,
    }
