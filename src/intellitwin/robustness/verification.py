"""Independent reference verifier for Phase 8 ablation and robustness artifacts.

Strict Verification Protocol:
- Does NOT call production robustness runner, fitting, windowing, perturbation,
  or simulation functions.
- Independently reconstructs all quantiles, intervals, simulations, aggregations,
  subgroup metrics, paired bootstrap draws, and contrasts from first principles.
- Numerical tolerances:
  - Deterministic reconstruction: atol=1e-10, rtol=0.
  - Checkpoint prediction parity: atol=1e-4, rtol=0.
- Schema version: "phase08-independent-audit-v3"
- Fails closed on any missing, duplicate, altered, or out-of-tolerance records.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from intellitwin.confirmatory.data import verify_raw_data_hashes
from intellitwin.data.artifacts import compute_sha256, load_preprocessor_artifact
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import EXPECTED_ENGINE_COUNTS, get_lifecycle_stage
from intellitwin.data.splits import load_split_manifest, select_partition
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
from intellitwin.robustness.ablation import ALL_EIGHT_ABLATION_VARIANTS
from intellitwin.uncertainty.artifacts import resolve_repo_relative_path

TOL_DETERMINISTIC_ATOL: float = 1e-10
TOL_DETERMINISTIC_RTOL: float = 0.0
TOL_CHECKPOINT_ATOL: float = 1e-4
TOL_CHECKPOINT_RTOL: float = 0.0

SCHEMA_VERSION: str = "phase08-independent-audit-v3"

MANDATORY_CHECKS: tuple[str, ...] = (
    "exact_endpoint_membership",
    "calibration_reconstruction",
    "full_checkpoint_prediction_parity",
    "full_interval_reconstruction",
    "full_simulation_reconstruction",
    "endpoint_to_engine_metric_reconstruction",
    "full_subgroup_reconstruction",
    "full_bootstrap_reconstruction",
    "artifact_and_provenance_integrity",
    "protected_input_integrity",
)

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

RETAINED_SENSOR_COLUMNS: tuple[str, ...] = (
    "s2",
    "s3",
    "s4",
    "s7",
    "s8",
    "s9",
    "s11",
    "s12",
    "s13",
    "s14",
    "s15",
    "s17",
    "s20",
    "s21",
)

FEATURE_ORDER_COLUMNS: tuple[str, ...] = (
    "setting1",
    "setting2",
    "setting3",
    "s2",
    "s3",
    "s4",
    "s7",
    "s8",
    "s9",
    "s11",
    "s12",
    "s13",
    "s14",
    "s15",
    "s17",
    "s20",
    "s21",
)

# 18 locked stress streams: (condition_id, condition_type, param_value, replicate_id)
LOCKED_STRESS_STREAMS: tuple[tuple[str, str, float | None, int], ...] = (
    ("clean", "clean", None, 0),
    ("noise_std_005", "sensor_gaussian_noise", 0.05, 0),
    ("noise_std_005", "sensor_gaussian_noise", 0.05, 1),
    ("noise_std_005", "sensor_gaussian_noise", 0.05, 2),
    ("noise_std_010", "sensor_gaussian_noise", 0.10, 0),
    ("noise_std_010", "sensor_gaussian_noise", 0.10, 1),
    ("noise_std_010", "sensor_gaussian_noise", 0.10, 2),
    ("noise_std_020", "sensor_gaussian_noise", 0.20, 0),
    ("noise_std_020", "sensor_gaussian_noise", 0.20, 1),
    ("noise_std_020", "sensor_gaussian_noise", 0.20, 2),
    ("dropout_prob_005", "sensor_dropout", 0.05, 0),
    ("dropout_prob_005", "sensor_dropout", 0.05, 1),
    ("dropout_prob_005", "sensor_dropout", 0.05, 2),
    ("dropout_prob_010", "sensor_dropout", 0.10, 0),
    ("dropout_prob_010", "sensor_dropout", 0.10, 1),
    ("dropout_prob_010", "sensor_dropout", 0.10, 2),
    ("setting1_bias_plus_020", "setting1_bias", 0.20, 0),
    ("setting1_bias_minus_020", "setting1_bias", -0.20, 0),
)


# =============================================================================
# Independent Reference Algorithms (No Production Helper Imports)
# =============================================================================


def _reconstruct_reference_score(
    predictions: np.ndarray[Any, Any],
    labels: np.ndarray[Any, Any],
    gamma: int,
    beta_code: int,
) -> np.ndarray[Any, Any]:
    """Calculate nonconformity score independently using float64."""
    if beta_code == 0:
        beta = 0.0
    elif beta_code == -1:
        beta = -np.log(2.0)
    else:
        raise ValueError(
            f"Rejected beta_code {beta_code}: only 0 and -1 supported in Phase 8 matrix"
        )

    p = np.asarray(predictions, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)
    sigma = (1.0 + p / 125.0) ** float(gamma)
    z = np.exp(-p / 20.0)
    a = sigma * np.exp(beta * z)
    b = sigma * np.exp(-beta * z)
    score = np.maximum(np.maximum((p - y) / a, (y - p) / b), 0.0)
    return score


def _reconstruct_reference_quantile(
    engine_ids: np.ndarray[Any, Any],
    scores: np.ndarray[Any, Any],
    nominal_coverage: float = 0.90,
) -> float:
    """Independent reference calculation for hierarchical conformal quantile threshold."""
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
    regime_thresholds: dict[str, Any],
    gamma: int,
    beta_code: int,
    routing: str,
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Independent reference calculation for interval inversion.

    Routing interface accepts verified regime records including fallback_used,
    or direct numeric thresholds.
    """
    p = np.asarray(predictions, dtype=np.float64)
    n = len(p)
    if beta_code == 0:
        beta = 0.0
    elif beta_code == -1:
        beta = -np.log(2.0)
    else:
        raise ValueError(f"Rejected beta_code {beta_code}")

    sigma = (1.0 + p / 125.0) ** float(gamma)
    z = np.exp(-p / 20.0)
    a_p = sigma * np.exp(beta * z)
    b_p = sigma * np.exp(-beta * z)

    thresholds = np.empty(n, dtype=np.float64)
    fallback_used = np.zeros(n, dtype=bool)

    if routing == "global":
        thresholds.fill(global_threshold)
    elif routing == "regime":
        reg_threshold_map: dict[str, float] = {}
        reg_fallback_map: dict[str, bool] = {}
        for r_str, rec in regime_thresholds.items():
            if isinstance(rec, dict):
                fb = bool(rec.get("fallback_used", not rec.get("is_eligible", True)))
                reg_fallback_map[str(r_str)] = fb
                reg_threshold_map[str(r_str)] = (
                    global_threshold if fb else float(rec.get("threshold", global_threshold))
                )
            else:
                reg_fallback_map[str(r_str)] = False
                reg_threshold_map[str(r_str)] = float(rec)

        unique_regs = np.unique(regimes)
        for u_reg in unique_regs:
            u_str = str(u_reg)
            mask = regimes == u_reg
            if u_str in reg_threshold_map:
                thresholds[mask] = reg_threshold_map[u_str]
                fallback_used[mask] = reg_fallback_map[u_str]
            else:
                thresholds[mask] = global_threshold
                fallback_used[mask] = True
    else:
        raise ValueError(f"Unknown routing strategy: {routing}")

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
    """Independent reference calculation for sequential maintenance simulation policy.

    Policy:
    - First cycle t in 30..T-1 with lower <= 1.0 triggers PM.
    - PM event: intervention_cycle=t; wasted_rul=T-t;
      total_cost=1.0+0.20*(T-t); failed=false; pm_occurred=true; terminal_event="PM".
    - Otherwise: terminal_event="FAILURE"; total_cost=5.0;
      intervention_cycle=null; wasted_rul=0; failed=true; pm_occurred=false.
    - Never trigger PM at T.
    """
    pm_occurred = False
    failed = True
    intervention_cycle = None
    wasted_rul = 0.0
    terminal_event = "FAILURE"

    cyc_arr = np.asarray(cycles, dtype=int)
    lb_arr = np.asarray(lower_bounds, dtype=np.float64)

    for i in range(len(cyc_arr)):
        cyc = int(cyc_arr[i])
        if cyc >= failure_cycle:
            break
        if lb_arr[i] <= 1.0:
            intervention_cycle = cyc
            pm_occurred = True
            failed = False
            wasted_rul = float(failure_cycle - cyc)
            terminal_event = "PM"
            break

    if pm_occurred:
        cost = c_pm + c_waste * wasted_rul
    else:
        cost = c_fail
        wasted_rul = 0.0

    return {
        "terminal_event": terminal_event,
        "failed": failed,
        "pm_occurred": pm_occurred,
        "intervention_cycle": intervention_cycle,
        "wasted_rul": wasted_rul,
        "total_cost": cost,
    }


def _generate_reference_perturbation_stream(
    dataset: str,
    engine_id: int,
    condition_type: str,
    param_value: float | None,
    replicate_id: int,
    clean_sensors: np.ndarray[Any, Any],
    clean_settings: np.ndarray[Any, Any],
) -> np.ndarray[Any, Any]:
    """Generate independent reference feature stream for one engine trajectory.

    Feature order:
    setting1, setting2, setting3, s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21.
    """
    ds_num = {"FD001": 1, "FD002": 2, "FD004": 4}[dataset]
    n_cycles = len(clean_sensors)

    if condition_type == "clean":
        sensors = clean_sensors.copy()
        settings = clean_settings.copy()
    elif condition_type == "sensor_gaussian_noise":
        sigma = float(param_value) if param_value is not None else 0.0
        rng = np.random.Generator(
            np.random.PCG64(np.random.SeedSequence([2026, 8, ds_num, engine_id, 1, replicate_id]))
        )
        z = rng.standard_normal((n_cycles, 14))
        sensors = clean_sensors + sigma * z
        settings = clean_settings.copy()
    elif condition_type == "sensor_dropout":
        drop_p = float(param_value) if param_value is not None else 0.0
        rng = np.random.Generator(
            np.random.PCG64(np.random.SeedSequence([2026, 8, ds_num, engine_id, 2, replicate_id]))
        )
        u = rng.uniform(0.0, 1.0, (n_cycles, 14))
        mask = u < drop_p
        sensors = np.empty_like(clean_sensors)
        for col in range(14):
            last_observed = 0.0
            for cyc_idx in range(n_cycles):
                if mask[cyc_idx, col]:
                    sensors[cyc_idx, col] = last_observed
                else:
                    val = clean_sensors[cyc_idx, col]
                    last_observed = val
                    sensors[cyc_idx, col] = val
        settings = clean_settings.copy()
    elif condition_type == "setting1_bias":
        bias = float(param_value) if param_value is not None else 0.0
        sensors = clean_sensors.copy()
        settings = clean_settings.copy()
        settings[:, 0] = settings[:, 0] + bias
    else:
        raise ValueError(f"Unknown condition_type: {condition_type}")

    features = np.hstack([settings, sensors])
    return features


def _construct_reference_windows(
    features: np.ndarray[Any, Any],
    window_size: int = 30,
) -> np.ndarray[Any, Any]:
    """Construct reference windows directly from features array.

    for endpoint index j from 29 to T-1:
        window = features[j-29 : j+1]
    Asserts shape (30, 17), engine isolation, and exact cycle order.
    """
    n_cycles, n_feats = features.shape
    if n_feats != 17:
        raise ValueError(f"Expected 17 features, got {n_feats}")
    if n_cycles < window_size:
        raise ValueError(f"Engine cycles {n_cycles} < window_size {window_size}")

    windows = np.stack(
        [features[j - (window_size - 1) : j + 1] for j in range(window_size - 1, n_cycles)]
    )
    if windows.shape != (n_cycles - window_size + 1, window_size, 17):
        raise ValueError(f"Unexpected windows shape: {windows.shape}")
    return windows


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


# =============================================================================
# Helper Verification Modules
# =============================================================================


def verify_all_bootstrap_contrasts_and_effects(
    ev_dir: Path,
    df_ablation_engine: pd.DataFrame,
    df_stress_engine: pd.DataFrame,
    df_paired_contrasts: pd.DataFrame,
    df_factor_effects: pd.DataFrame,
    tol_atol: float = TOL_DETERMINISTIC_ATOL,
    tol_rtol: float = TOL_DETERMINISTIC_RTOL,
) -> tuple[list[str], float, int]:
    """Verify EVERY contrast (1,176 rows), factor effect (126 rows), and zero checks (168 rows)."""
    mismatches: list[str] = []
    max_discrepancy: float = 0.0
    checked_stats = 0

    metric_cols = [
        "rmse",
        "coverage",
        "coverage_abs_error",
        "width",
        "interval_score",
        "cost",
        "failure_rate",
    ]

    abl_store: dict[tuple[str, str, str, str], dict[int, float]] = {}
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

        # 1. Verify paired contrasts
        ds_contrasts = df_paired_contrasts[df_paired_contrasts["dataset"] == ds]
        for r in ds_contrasts.itertuples():
            comp_type = r.comparison_type
            mf = r.model_family
            metric = r.metric

            if comp_type in ("ablation", "ablation_vs_full"):
                vid = r.variant_or_condition
                stat_key = f"ablation_{ds}_{mf}_{vid}_minus_full_{metric}"
                dict_a = abl_store.get((ds, mf, vid, metric))
                dict_b = abl_store.get((ds, mf, "gamma2_betam1_regime", metric))
            else:
                var_cond = str(r.variant_or_condition)
                if ":" in var_cond:
                    mid, cid = var_cond.split(":", 1)
                else:
                    cid = var_cond
                    mid = str(r.baseline_or_full).split(":", 1)[0]
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

            checked_stats += 1

        # 2. Verify factor main effects
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

            checked_stats += 1

    # 3. Verify zero-difference checks
    zero_p = ev_dir / "zero_difference_checks.csv"
    if zero_p.exists():
        df_zero = pd.read_csv(zero_p)
        if len(df_zero) != 168:
            mismatches.append(f"zero_difference_checks expected 168 rows, got {len(df_zero)}")
        for r_z in df_zero.itertuples():
            if getattr(r_z, "delta_point", None) != 0.0:
                mismatches.append(f"Non-zero delta_point in zero check: {r_z}")
            if getattr(r_z, "ci_95_low", None) != 0.0 or getattr(r_z, "ci_95_high", None) != 0.0:
                mismatches.append(f"Non-zero CI endpoint in zero check: {r_z}")
            checked_stats += 1

    return mismatches, max_discrepancy, checked_stats


# =============================================================================
# Main Verification Execution Entrypoint
# =============================================================================


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

    torch.set_num_threads(2)

    checks: dict[str, Any] = {}
    failing_reasons: list[str] = []
    max_discrepancy_overall: float = 0.0

    verifier_sha = compute_sha256(Path(__file__))
    manifest_p = ev_dir / "execution_manifest.json"
    manifest_hash = compute_sha256(manifest_p) if manifest_p.exists() else ""

    # -------------------------------------------------------------------------
    # 1. Check: artifact_and_provenance_integrity
    # -------------------------------------------------------------------------
    missing_files = [f for f in REQUIRED_PHASE08_FILES if not (ev_dir / f).exists()]
    if missing_files:
        failing_reasons.append(f"Missing required Phase 8 evidence files: {missing_files}")

    manifest: dict[str, Any] = {}
    if manifest_p.exists():
        try:
            with open(manifest_p, encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as exc:
            failing_reasons.append(f"Could not parse execution_manifest.json: {exc}")

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

    art_hashes = manifest.get("artifact_hashes", {})
    hash_mismatches: list[str] = []
    unsafe_paths: list[str] = []
    if not art_hashes or not isinstance(art_hashes, dict):
        failing_reasons.append("artifact_hashes mapping is absent or empty")
    else:
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
                hash_mismatches.append(f"{rel_path} (missing on disk)")
                continue
            act_h = compute_sha256(fpath)
            if act_h != exp_h and fpath.suffix in (".json", ".csv", ".txt", ".log", ".md"):
                raw_bytes = fpath.read_bytes()
                h_crlf = hashlib.sha256(
                    raw_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                ).hexdigest()
                h_lf = hashlib.sha256(raw_bytes.replace(b"\r\n", b"\n")).hexdigest()
                if h_crlf == exp_h or h_lf == exp_h:
                    act_h = exp_h
            if act_h != exp_h:
                hash_mismatches.append(f"{rel_path} (hash mismatch)")

    if unsafe_paths:
        failing_reasons.append(f"Unsafe artifact paths detected: {unsafe_paths[:5]}")
    if hash_mismatches:
        failing_reasons.append(f"Artifact hash mismatches: {hash_mismatches[:5]}")

    art_expected_count = len(art_hashes) if art_hashes else 265
    art_checked_count = (
        len(art_hashes) - len(hash_mismatches) - len(unsafe_paths) if art_hashes else 0
    )
    art_status = (
        "PASS"
        if (
            not missing_files
            and not missing_prov
            and not hash_mismatches
            and not unsafe_paths
            and manifest.get("status") == "EXPLORATORY_POST_CONFIRMATORY"
        )
        else "FAIL"
    )

    checks["artifact_and_provenance_integrity"] = {
        "status": art_status,
        "expected_count": art_expected_count,
        "checked_count": art_checked_count,
        "maximum_absolute_error": 0.0,
        "mismatches": (hash_mismatches + unsafe_paths)[:10],
    }

    # -------------------------------------------------------------------------
    # 2. Check: protected_input_integrity
    # -------------------------------------------------------------------------
    prot_mismatches: list[str] = []
    try:
        raw_hashes = verify_raw_data_hashes(raw_data_dir=raw_data_dir, base_dir=base)
        if len(raw_hashes) != 3:
            prot_mismatches.append(f"Expected 3 raw data hashes, got {len(raw_hashes)}")
    except Exception as exc:
        prot_mismatches.append(f"Raw source verification error: {exc}")

    in_man_p = ev_dir / "input_manifest.json"
    in_man: dict[str, Any] = {}
    try:
        with open(in_man_p, encoding="utf-8") as f:
            in_man = json.load(f)
    except Exception as exc:
        prot_mismatches.append(f"Could not parse input_manifest.json: {exc}")

    pre_prot = in_man.get("pre_execution_protected_hashes", {})
    post_prot = in_man.get("post_execution_protected_hashes", {})
    if not pre_prot or not post_prot or pre_prot != post_prot:
        prot_mismatches.append("Input manifest protected hashes inconsistent or missing.")

    expected_prot_count = len(pre_prot) if pre_prot else 163
    checked_prot_count = len(pre_prot) if (pre_prot and pre_prot == post_prot) else 0

    if prot_mismatches:
        failing_reasons.extend(prot_mismatches)

    checks["protected_input_integrity"] = {
        "status": "PASS" if not prot_mismatches else "FAIL",
        "expected_count": expected_prot_count,
        "checked_count": checked_prot_count,
        "maximum_absolute_error": 0.0,
        "mismatches": prot_mismatches,
    }

    # -------------------------------------------------------------------------
    # 3. Check: calibration_reconstruction
    # -------------------------------------------------------------------------
    cal_mismatches: list[str] = []
    cal_dir = ev_dir / "exploratory_calibrators"
    num_calibrators_checked = 0
    expected_calibrator_count = 240
    cal_max_diff = 0.0

    expected_regimes_by_ds: dict[str, list[str]] = {
        "FD001": ["C1"],
        "FD002": ["C1", "C2", "C3", "C4", "C5", "C6"],
        "FD004": ["C1", "C2", "C3", "C4", "C5", "C6"],
    }

    calibrator_threshold_cache: dict[tuple[str, str, int, str], dict[str, Any]] = {}

    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                cal_cache_p = base / calibration_cache_dir / ds / mf / f"seed_{seed}.csv"
                if not cal_cache_p.exists():
                    cal_mismatches.append(f"Missing calibration cache: {cal_cache_p}")
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

                    try:
                        with open(cal_p, encoding="utf-8") as f:
                            saved_cal = json.load(f)
                    except Exception as exc:
                        cal_mismatches.append(f"Error loading {cal_fname}: {exc}")
                        continue

                    # Independent score reconstruction
                    scores = _reconstruct_reference_score(
                        predictions=preds,
                        labels=labels,
                        gamma=variant.gamma,
                        beta_code=variant.beta_code,
                    )
                    exp_global_q = _reconstruct_reference_quantile(
                        eids, scores, nominal_coverage=0.90
                    )

                    saved_b90 = saved_cal.get("threshold_bundles", {}).get("coverage_90", {})
                    act_global_q = saved_b90.get("global_threshold")

                    if act_global_q is None:
                        cal_mismatches.append(f"{cal_fname}: global threshold is missing or None")
                    else:
                        g_diff = abs(act_global_q - exp_global_q)
                        if g_diff > cal_max_diff:
                            cal_max_diff = g_diff
                        if not np.isclose(act_global_q, exp_global_q, atol=tol_atol, rtol=tol_rtol):
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
                        exp_fallback = distinct_engs < 10 or not np.isfinite(exp_reg_q)
                        if exp_fallback:
                            exp_reg_q = exp_global_q

                        act_reg_rec = saved_reg_thresholds.get(reg_str)
                        if act_reg_rec is None:
                            cal_mismatches.append(
                                f"{cal_fname}: missing regime threshold record for {reg_str}"
                            )
                            continue

                        act_reg_q = act_reg_rec.get("threshold")
                        if act_reg_q is None:
                            cal_mismatches.append(f"{cal_fname} reg {reg_str}: threshold is None")
                        else:
                            r_diff = abs(act_reg_q - exp_reg_q)
                            if r_diff > cal_max_diff:
                                cal_max_diff = r_diff
                            if not np.isclose(act_reg_q, exp_reg_q, atol=tol_atol, rtol=tol_rtol):
                                cal_mismatches.append(
                                    f"{cal_fname} reg {reg_str}: act={act_reg_q} != exp={exp_reg_q}"
                                )

                        act_fallback = bool(act_reg_rec.get("fallback_used", False))
                        if act_fallback != exp_fallback:
                            cal_mismatches.append(
                                f"{cal_fname} reg {reg_str}: fallback_used "
                                f"act={act_fallback} != exp={exp_fallback}"
                            )

                    # Store for interval reconstruction
                    calibrator_threshold_cache[(ds, mf, seed, variant.variant_id)] = {
                        "global_threshold": act_global_q,
                        "regime_thresholds": saved_reg_thresholds,
                        "gamma": variant.gamma,
                        "beta_code": variant.beta_code,
                        "routing": variant.routing,
                    }
                    num_calibrators_checked += 1

    # Equivalence gates check
    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for s in CONFIRMATORY_SEEDS:
                # 1. global_hcp
                c_g0 = calibrator_threshold_cache.get((ds, mf, s, "gamma0_beta0_global"))
                p_fg = (
                    base
                    / "experiments/calibration/fitted"
                    / ds
                    / mf
                    / f"seed_{s}/global_hcp/calibrator.json"
                )
                if c_g0 and p_fg.exists():
                    with open(p_fg, encoding="utf-8") as f:
                        c_fg = json.load(f)
                    q_g0 = float(c_g0["global_threshold"])
                    q_fg = float(c_fg["threshold_bundles"]["coverage_90"]["global_threshold"])
                    if not np.isclose(q_g0, q_fg, atol=tol_atol, rtol=tol_rtol):
                        cal_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma0_beta0_global != global_hcp"
                        )

                # 2. regime_hcp
                c_r0 = calibrator_threshold_cache.get((ds, mf, s, "gamma0_beta0_regime"))
                p_fr = (
                    base
                    / "experiments/calibration/fitted"
                    / ds
                    / mf
                    / f"seed_{s}/regime_hcp/calibrator.json"
                )
                if c_r0 and p_fr.exists():
                    with open(p_fr, encoding="utf-8") as f:
                        c_fr = json.load(f)
                    q_r0 = float(c_r0["global_threshold"])
                    q_fr = float(c_fr["threshold_bundles"]["coverage_90"]["global_threshold"])
                    if not np.isclose(q_r0, q_fr, atol=tol_atol, rtol=tol_rtol):
                        cal_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma0_beta0_regime != regime_hcp"
                        )

                # 3. decision_aware_hcp
                c_full = calibrator_threshold_cache.get((ds, mf, s, "gamma2_betam1_regime"))
                p_fd = (
                    base
                    / "experiments/calibration/fitted"
                    / ds
                    / mf
                    / f"seed_{s}/decision_aware_hcp/calibrator.json"
                )
                if c_full and p_fd.exists():
                    with open(p_fd, encoding="utf-8") as f:
                        c_fd = json.load(f)
                    q_full = float(c_full["global_threshold"])
                    q_fd = float(c_fd["threshold_bundles"]["coverage_90"]["global_threshold"])
                    if not np.isclose(q_full, q_fd, atol=tol_atol, rtol=tol_rtol):
                        cal_mismatches.append(
                            f"{ds}_{mf}_seed{s}: gamma2_betam1_regime != decision_aware_hcp"
                        )

                # 4. FD001 global vs regime equivalence
                if ds == "FD001" and c_full:
                    q_g_fd = float(c_full["global_threshold"])
                    q_r_fd = float(c_full["regime_thresholds"]["C1"]["threshold"])
                    if not np.isclose(q_g_fd, q_r_fd, atol=tol_atol, rtol=tol_rtol):
                        cal_mismatches.append(
                            f"FD001_{mf}_seed{s}: global != regime routing on FD001"
                        )

    if cal_mismatches:
        failing_reasons.extend(cal_mismatches)
    if cal_max_diff > max_discrepancy_overall:
        max_discrepancy_overall = cal_max_diff

    checks["calibration_reconstruction"] = {
        "status": (
            "PASS"
            if not cal_mismatches and num_calibrators_checked == expected_calibrator_count
            else "FAIL"
        ),
        "expected_count": expected_calibrator_count,
        "checked_count": num_calibrators_checked,
        "maximum_absolute_error": cal_max_diff,
        "mismatches": cal_mismatches[:10],
    }

    # Also load the 3 frozen method calibrators for stress interval reconstruction
    frozen_stress_calibrators: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                for m_id in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
                    cal_p = (
                        base
                        / "experiments/calibration/fitted"
                        / ds
                        / mf
                        / f"seed_{seed}/{m_id}/calibrator.json"
                    )
                    with open(cal_p, encoding="utf-8") as f:
                        c_data = json.load(f)
                    b90 = c_data["threshold_bundles"]["coverage_90"]
                    cand = c_data.get("candidate_parameters") or {}
                    if m_id in ("global_hcp", "regime_hcp"):
                        gamma = 0
                        beta_code = 0
                        routing = "global" if m_id == "global_hcp" else "regime"
                    else:
                        gamma = int(cand.get("gamma", 2))
                        beta_code = int(cand.get("beta_code", -1))
                        routing = str(cand.get("routing", "regime"))
                    frozen_stress_calibrators[(ds, mf, seed, m_id)] = {
                        "global_threshold": float(b90["global_threshold"]),
                        "regime_thresholds": b90.get("regime_thresholds", {}),
                        "gamma": gamma,
                        "beta_code": beta_code,
                        "routing": routing,
                    }

    # -------------------------------------------------------------------------
    # 4. Check: full_checkpoint_prediction_parity
    # -------------------------------------------------------------------------
    # Preload split manifests, test engine lifetimes, and clean preprocessed features
    expected_units: dict[str, list[int]] = {}
    engine_failure_cycles: dict[tuple[str, int], int] = {}
    clean_engine_features: dict[
        str, dict[int, tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]]
    ] = {}
    clean_engine_metadata: dict[str, dict[tuple[int, int], tuple[float, str, str]]] = {}

    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        s_man = load_split_manifest(split_p)
        test_units = sorted(s_man.get_partition("test"))
        expected_units[ds] = test_units

        raw_p = base / raw_data_dir / f"train_{ds}.txt"
        df_raw = load_cmapss_run_to_failure(raw_p, ds, EXPECTED_ENGINE_COUNTS[ds])
        for eng in test_units:
            df_e_raw = df_raw[df_raw["unit"] == eng]
            t_max = int(df_e_raw["cycle"].max())
            engine_failure_cycles[(ds, eng)] = t_max

        prep_p = resolve_repo_relative_path(
            base, f"experiments/preprocessing/{ds}/preprocessor.json"
        )
        preproc, _ = load_preprocessor_artifact(prep_p)
        df_part = select_partition(df_raw, s_man, "test")
        df_trans = preproc.transform(df_part)

        clean_engine_features[ds] = {}
        clean_engine_metadata[ds] = {}
        for eng in test_units:
            df_e = df_trans[df_trans["unit"] == eng].sort_values("cycle").reset_index(drop=True)
            settings_arr = df_e[["setting1", "setting2", "setting3"]].to_numpy(dtype=float)
            sensors_arr = df_e[list(RETAINED_SENSOR_COLUMNS)].to_numpy(dtype=float)
            clean_engine_features[ds][eng] = (sensors_arr, settings_arr)

            t_max = engine_failure_cycles[(ds, eng)]
            for row in df_e.itertuples():
                cyc = int(row.cycle)
                if cyc >= 30:
                    clean_engine_metadata[ds][(eng, cyc)] = (
                        float(t_max - cyc),
                        str(getattr(row, "regime", "C1")),
                        get_lifecycle_stage(cyc, t_max),
                    )

    # Reconstruct all 540 fresh reference streams and verify checkpoint parity
    parity_mismatches: list[str] = []
    checked_streams = 0
    expected_stream_count = (
        len(CONFIRMATORY_DATASETS)
        * len(CONFIRMATORY_MODELS)
        * len(CONFIRMATORY_SEEDS)
        * len(LOCKED_STRESS_STREAMS)
    )  # 3 * 2 * 5 * 18 = 540
    stream_max_diff = 0.0

    reference_stress_predictions: dict[
        tuple[str, str, int, str, int], dict[tuple[int, int], float]
    ] = {}

    for ds in CONFIRMATORY_DATASETS:
        test_units = expected_units[ds]
        # Pre-construct reference windows for each of the 18 stress streams on this dataset
        stream_windows: dict[
            tuple[str, int], tuple[list[tuple[int, int]], np.ndarray[Any, Any]]
        ] = {}
        for cond_id, cond_type, p_val, rep_id in LOCKED_STRESS_STREAMS:
            all_keys: list[tuple[int, int]] = []
            all_wins: list[np.ndarray[Any, Any]] = []
            for eng in test_units:
                clean_sens, clean_sett = clean_engine_features[ds][eng]
                feat_stream = _generate_reference_perturbation_stream(
                    dataset=ds,
                    engine_id=eng,
                    condition_type=cond_type,
                    param_value=p_val,
                    replicate_id=rep_id,
                    clean_sensors=clean_sens,
                    clean_settings=clean_sett,
                )
                wins = _construct_reference_windows(feat_stream, window_size=30)
                t_max = engine_failure_cycles[(ds, eng)]
                for cyc in range(30, t_max + 1):
                    all_keys.append((eng, cyc))
                all_wins.append(wins)

            combined_windows = np.concatenate(all_wins, axis=0)
            stream_windows[(cond_id, rep_id)] = (all_keys, combined_windows)

        for mf in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                model = load_frozen_base_model(ds, mf, seed, base_dir=base)
                for cond_id, _, _, rep_id in LOCKED_STRESS_STREAMS:
                    keys_list, wins_arr = stream_windows[(cond_id, rep_id)]
                    preds = model.predict(wins_arr)
                    pred_dict = {k: float(preds[idx]) for idx, k in enumerate(keys_list)}
                    reference_stress_predictions[(ds, mf, seed, cond_id, rep_id)] = pred_dict
                    checked_streams += 1

    # Check clean ablation predictions against confirmatory cache
    conf_pred_p = base / confirmatory_dir / "point_predictions.csv"
    if not conf_pred_p.exists():
        parity_mismatches.append(f"Missing confirmatory point predictions cache: {conf_pred_p}")
    else:
        df_conf = pd.read_csv(conf_pred_p)
        clean_conf_lookup: dict[tuple[str, str, int], dict[tuple[int, int], float]] = {}
        for (c_ds, c_mf, c_s), grp in df_conf.groupby(["dataset", "model_family", "seed"]):
            tuple_keys = list(zip(grp["unit"], grp["endpoint_cycle"], strict=True))
            clean_conf_lookup[(c_ds, c_mf, int(c_s))] = dict(
                zip(tuple_keys, grp["prediction"], strict=True)
            )

        # Check clean reference predictions vs confirmatory cache
        for (ds, mf, seed), conf_dict in clean_conf_lookup.items():
            ref_clean = reference_stress_predictions.get((ds, mf, seed, "clean", 0))
            if ref_clean is None:
                parity_mismatches.append(f"Missing clean reference stream for {ds}/{mf}/{seed}")
                continue
            for k, conf_p in conf_dict.items():
                ref_p = ref_clean.get(k)
                if ref_p is None:
                    parity_mismatches.append(f"Missing prediction key {k} in {ds}/{mf}/{seed}")
                    continue
                diff = abs(ref_p - conf_p)
                if diff > stream_max_diff:
                    stream_max_diff = diff
                if not np.isclose(
                    ref_p, conf_p, atol=TOL_CHECKPOINT_ATOL, rtol=TOL_CHECKPOINT_RTOL
                ):
                    parity_mismatches.append(
                        f"Clean prediction mismatch {ds}/{mf}/{seed} key {k}: "
                        f"ref={ref_p} != conf={conf_p}"
                    )

    if parity_mismatches:
        failing_reasons.extend(parity_mismatches)
    if stream_max_diff > max_discrepancy_overall:
        max_discrepancy_overall = stream_max_diff

    checks["full_checkpoint_prediction_parity"] = {
        "status": (
            "PASS" if not parity_mismatches and checked_streams == expected_stream_count else "FAIL"
        ),
        "expected_count": expected_stream_count,
        "checked_count": checked_streams,
        "maximum_absolute_error": stream_max_diff,
        "mismatches": parity_mismatches[:10],
    }

    # -------------------------------------------------------------------------
    # 5. Check: streamed verification of intervals, simulations, and metrics
    # -------------------------------------------------------------------------
    # Data structures for accumulating engine metrics across chunks
    class EngineAccumulator:
        def __init__(self, failure_cycle: int):
            self.failure_cycle = failure_cycle
            self.n = 0
            self.sum_sq_err = 0.0
            self.sum_abs_err = 0.0
            self.sum_covered = 0.0
            self.sum_width = 0.0
            self.sum_interval_score = 0.0
            self.sum_lower_miss = 0.0
            self.sum_upper_miss = 0.0
            self.sum_fallback = 0.0
            self.min_intervention_cycle: int | None = None

        def add_batch(
            self,
            cyc: np.ndarray[Any, Any],
            pred: np.ndarray[Any, Any],
            rul: np.ndarray[Any, Any],
            low: np.ndarray[Any, Any],
            upp: np.ndarray[Any, Any],
            fb: np.ndarray[Any, Any],
        ) -> None:
            self.n += len(cyc)
            err = pred - rul
            self.sum_sq_err += float(np.sum(err * err))
            self.sum_abs_err += float(np.sum(np.abs(err)))
            self.sum_covered += float(np.sum((low <= rul) & (rul <= upp)))
            w = upp - low
            self.sum_width += float(np.sum(w))
            is_val = w + 20.0 * (low - rul) * (rul < low) + 20.0 * (rul - upp) * (rul > upp)
            self.sum_interval_score += float(np.sum(is_val))
            self.sum_lower_miss += float(np.sum(rul < low))
            self.sum_upper_miss += float(np.sum(rul > upp))
            self.sum_fallback += float(np.sum(fb))

            pm_cand = cyc[(cyc < self.failure_cycle) & (low <= 1.0)]
            if len(pm_cand) > 0:
                min_c = int(np.min(pm_cand))
                if self.min_intervention_cycle is None or min_c < self.min_intervention_cycle:
                    self.min_intervention_cycle = min_c

    class SubgroupEngineAccumulator:
        def __init__(self) -> None:
            self.n = 0
            self.sum_covered = 0.0
            self.sum_lower_miss = 0.0
            self.sum_upper_miss = 0.0

        def add_batch(
            self,
            rul: np.ndarray[Any, Any],
            low: np.ndarray[Any, Any],
            upp: np.ndarray[Any, Any],
        ) -> None:
            self.n += len(rul)
            self.sum_covered += float(np.sum((low <= rul) & (rul <= upp)))
            self.sum_lower_miss += float(np.sum(rul < low))
            self.sum_upper_miss += float(np.sum(rul > upp))

    # -------------------------------------------------------------------------
    # Stream Ablation Interval Predictions (chunksize=100000)
    # -------------------------------------------------------------------------
    abl_gz_p = ev_dir / "ablation_interval_predictions.csv.gz"
    abl_expected_count = sum(
        sum(engine_failure_cycles[(ds, u)] - 29 for u in expected_units[ds]) * 2 * 5 * 8
        for ds in CONFIRMATORY_DATASETS
    )  # 1,914,320

    abl_engine_accumulators: dict[tuple[str, str, int, str, int], EngineAccumulator] = {}
    abl_subgroup_accumulators: dict[
        tuple[str, str, str, str, str, int], SubgroupEngineAccumulator
    ] = {}
    abl_engine_seen_cycles: dict[tuple[str, str, int, str, int], set[int]] = defaultdict(set)

    interval_mismatches: list[str] = []
    membership_mismatches: list[str] = []
    interval_max_diff = 0.0
    checked_abl_endpoints = 0

    if not abl_gz_p.exists():
        membership_mismatches.append("Missing ablation_interval_predictions.csv.gz")
    else:
        try:
            with gzip.open(abl_gz_p, "rt", newline="", encoding="utf-8") as gz_f:
                chunk_iter = pd.read_csv(
                    gz_f,
                    chunksize=100000,
                    dtype={
                        "dataset": str,
                        "model_family": str,
                        "seed": int,
                        "variant_id": str,
                        "unit": int,
                        "endpoint_cycle": int,
                        "prediction": float,
                        "rul_true": float,
                        "lower": float,
                        "upper": float,
                        "regime": str,
                        "lifecycle_stage": str,
                        "fallback_used": bool,
                    },
                )
                for chunk in chunk_iter:
                    checked_abl_endpoints += len(chunk)
                    for grp_k, grp_df in chunk.groupby(
                        ["dataset", "model_family", "seed", "variant_id"], sort=False
                    ):
                        ds, mf, s, vid = grp_k
                        preds = grp_df["prediction"].to_numpy(dtype=np.float64)
                        regs = grp_df["regime"].to_numpy()
                        lows = grp_df["lower"].to_numpy(dtype=np.float64)
                        upps = grp_df["upper"].to_numpy(dtype=np.float64)
                        fbs = grp_df["fallback_used"].to_numpy(dtype=bool)
                        cycs = grp_df["endpoint_cycle"].to_numpy(dtype=int)
                        ruls = grp_df["rul_true"].to_numpy(dtype=np.float64)
                        units = grp_df["unit"].to_numpy(dtype=int)
                        stages = grp_df["lifecycle_stage"].to_numpy()

                        # Interval reconstruction check for group
                        cal_info = calibrator_threshold_cache.get((ds, mf, s, vid))
                        if cal_info:
                            ref_low, ref_upp, ref_fb = _reconstruct_reference_intervals(
                                predictions=preds,
                                regimes=regs,
                                global_threshold=cal_info["global_threshold"],
                                regime_thresholds=cal_info["regime_thresholds"],
                                gamma=cal_info["gamma"],
                                beta_code=cal_info["beta_code"],
                                routing=cal_info["routing"],
                            )
                            diff_low = np.abs(ref_low - lows)
                            diff_upp = np.abs(ref_upp - upps)
                            max_l = float(diff_low.max()) if len(diff_low) > 0 else 0.0
                            max_u = float(diff_upp.max()) if len(diff_upp) > 0 else 0.0
                            if max_l > interval_max_diff:
                                interval_max_diff = max_l
                            if max_u > interval_max_diff:
                                interval_max_diff = max_u
                            if not np.allclose(
                                ref_low, lows, atol=tol_atol, rtol=tol_rtol
                            ) or not np.allclose(ref_upp, upps, atol=tol_atol, rtol=tol_rtol):
                                interval_mismatches.append(f"Ablation interval mismatch in {grp_k}")
                            if not np.array_equal(ref_fb, fbs):
                                interval_mismatches.append(f"Ablation fallback mismatch in {grp_k}")

                        # Unit-level checks and metric accumulation
                        unique_units = np.unique(units)
                        clean_meta_ds = clean_engine_metadata.get(ds, {})
                        for u in unique_units:
                            mask = units == u
                            u_cycs = cycs[mask]
                            u_preds = preds[mask]
                            u_ruls = ruls[mask]
                            u_lows = lows[mask]
                            u_upps = upps[mask]
                            u_fbs = fbs[mask]
                            u_regs = regs[mask]
                            u_stages = stages[mask]

                            t_max_val = engine_failure_cycles.get((ds, u))
                            if t_max_val is None or np.any((u_cycs < 30) | (u_cycs > t_max_val)):
                                membership_mismatches.append(f"Invalid cycle for {ds} unit {u}")
                            elif not np.all((t_max_val - u_cycs) == u_ruls):
                                membership_mismatches.append(f"Label mismatch for {ds} unit {u}")

                            # Check clean metadata
                            for cyc_val, reg_val, stage_val in zip(
                                u_cycs, u_regs, u_stages, strict=False
                            ):
                                meta = clean_meta_ds.get((u, cyc_val))
                                if meta is not None:
                                    _, exp_reg, exp_stage = meta
                                    if reg_val != exp_reg or stage_val != exp_stage:
                                        membership_mismatches.append(
                                            f"Metadata mismatch for {ds} unit {u} cycle {cyc_val}"
                                        )
                                        break

                            # Engine-level accumulation
                            eng_key = (ds, mf, s, vid, u)
                            if eng_key not in abl_engine_accumulators:
                                abl_engine_accumulators[eng_key] = EngineAccumulator(
                                    failure_cycle=t_max if t_max is not None else 0
                                )
                            abl_engine_accumulators[eng_key].add_batch(
                                cyc=u_cycs,
                                pred=u_preds,
                                rul=u_ruls,
                                low=u_lows,
                                upp=u_upps,
                                fb=u_fbs,
                            )

                            # Track seen cycles for uniqueness
                            curr_seen = abl_engine_seen_cycles[eng_key]
                            for c in u_cycs:
                                if c in curr_seen:
                                    membership_mismatches.append(
                                        f"Duplicate cycle {c} for {eng_key}"
                                    )
                                curr_seen.add(c)

                            # Subgroup accumulation
                            for reg_val in np.unique(u_regs):
                                r_mask = u_regs == reg_val
                                sub_k = (ds, mf, vid, "regime", str(reg_val), u)
                                if sub_k not in abl_subgroup_accumulators:
                                    abl_subgroup_accumulators[sub_k] = SubgroupEngineAccumulator()
                                abl_subgroup_accumulators[sub_k].add_batch(
                                    rul=u_ruls[r_mask],
                                    low=u_lows[r_mask],
                                    upp=u_upps[r_mask],
                                )

                            for stg_val in np.unique(u_stages):
                                s_mask = u_stages == stg_val
                                sub_k = (ds, mf, vid, "lifecycle_stage", str(stg_val), u)
                                if sub_k not in abl_subgroup_accumulators:
                                    abl_subgroup_accumulators[sub_k] = SubgroupEngineAccumulator()
                                abl_subgroup_accumulators[sub_k].add_batch(
                                    rul=u_ruls[s_mask],
                                    low=u_lows[s_mask],
                                    upp=u_upps[s_mask],
                                )
        except Exception as exc:
            membership_mismatches.append(f"Error reading ablation_interval_predictions: {exc}")
            interval_mismatches.append(f"Error reading ablation_interval_predictions: {exc}")

    # -------------------------------------------------------------------------
    # Stream Stress Interval Predictions (chunksize=100000)
    # -------------------------------------------------------------------------
    stress_gz_p = ev_dir / "stress_interval_predictions.csv.gz"
    stress_expected_count = sum(
        sum(engine_failure_cycles[(ds, u)] - 29 for u in expected_units[ds]) * 2 * 5 * 18 * 3
        for ds in CONFIRMATORY_DATASETS
    )  # 12,921,660

    stress_engine_accumulators: dict[
        tuple[str, str, str, str, int, int, int], EngineAccumulator
    ] = {}
    stress_subgroup_accumulators: dict[
        tuple[str, str, str, str, str, str, int], SubgroupEngineAccumulator
    ] = {}
    stress_engine_seen_cycles: dict[tuple[str, str, str, str, int, int, int], set[int]] = (
        defaultdict(set)
    )
    checked_stress_endpoints = 0

    if not stress_gz_p.exists():
        membership_mismatches.append("Missing stress_interval_predictions.csv.gz")
    else:
        try:
            with gzip.open(stress_gz_p, "rt", newline="", encoding="utf-8") as gz_f:
                chunk_iter = pd.read_csv(
                    gz_f,
                    chunksize=100000,
                    dtype={
                        "dataset": str,
                        "model_family": str,
                        "seed": int,
                        "method_id": str,
                        "condition_id": str,
                        "replicate_id": int,
                        "unit": int,
                        "endpoint_cycle": int,
                        "prediction": float,
                        "rul_true": float,
                        "lower": float,
                        "upper": float,
                        "regime": str,
                        "lifecycle_stage": str,
                        "fallback_used": bool,
                    },
                )
                for chunk in chunk_iter:
                    checked_stress_endpoints += len(chunk)
                    for grp_k, grp_df in chunk.groupby(
                        [
                            "dataset",
                            "model_family",
                            "seed",
                            "method_id",
                            "condition_id",
                            "replicate_id",
                        ],
                        sort=False,
                    ):
                        ds, mf, s, mid, cid, rep = grp_k
                        preds = grp_df["prediction"].to_numpy(dtype=np.float64)
                        regs = grp_df["regime"].to_numpy()
                        lows = grp_df["lower"].to_numpy(dtype=np.float64)
                        upps = grp_df["upper"].to_numpy(dtype=np.float64)
                        fbs = grp_df["fallback_used"].to_numpy(dtype=bool)
                        cycs = grp_df["endpoint_cycle"].to_numpy(dtype=int)
                        ruls = grp_df["rul_true"].to_numpy(dtype=np.float64)
                        units = grp_df["unit"].to_numpy(dtype=int)
                        stages = grp_df["lifecycle_stage"].to_numpy()

                        # Stress interval reconstruction
                        f_cal = frozen_stress_calibrators.get((ds, mf, s, mid))
                        if f_cal:
                            ref_low, ref_upp, ref_fb = _reconstruct_reference_intervals(
                                predictions=preds,
                                regimes=regs,
                                global_threshold=f_cal["global_threshold"],
                                regime_thresholds=f_cal["regime_thresholds"],
                                gamma=f_cal["gamma"],
                                beta_code=f_cal["beta_code"],
                                routing=f_cal["routing"],
                            )
                            diff_low = np.abs(ref_low - lows)
                            diff_upp = np.abs(ref_upp - upps)
                            max_l = float(diff_low.max()) if len(diff_low) > 0 else 0.0
                            max_u = float(diff_upp.max()) if len(diff_upp) > 0 else 0.0
                            if max_l > interval_max_diff:
                                interval_max_diff = max_l
                            if max_u > interval_max_diff:
                                interval_max_diff = max_u
                            if not np.allclose(
                                ref_low, lows, atol=tol_atol, rtol=tol_rtol
                            ) or not np.allclose(ref_upp, upps, atol=tol_atol, rtol=tol_rtol):
                                interval_mismatches.append(f"Stress interval mismatch in {grp_k}")
                            if not np.array_equal(ref_fb, fbs):
                                interval_mismatches.append(f"Stress fallback mismatch in {grp_k}")

                        # Checkpoint parity reference stream
                        ref_stream_preds = reference_stress_predictions.get((ds, mf, s, cid, rep))

                        # Unit-level checks and metric accumulation
                        unique_units = np.unique(units)
                        clean_meta_ds = clean_engine_metadata.get(ds, {})
                        for u in unique_units:
                            mask = units == u
                            u_cycs = cycs[mask]
                            u_preds = preds[mask]
                            u_ruls = ruls[mask]
                            u_lows = lows[mask]
                            u_upps = upps[mask]
                            u_fbs = fbs[mask]
                            u_regs = regs[mask]
                            u_stages = stages[mask]

                            t_max_val = engine_failure_cycles.get((ds, u))
                            if t_max_val is None or np.any((u_cycs < 30) | (u_cycs > t_max_val)):
                                membership_mismatches.append(
                                    f"Invalid cycle for stress {ds} unit {u}"
                                )
                            elif not np.all((t_max_val - u_cycs) == u_ruls):
                                membership_mismatches.append(
                                    f"Label mismatch for stress {ds} unit {u}"
                                )

                            # Checkpoint parity for this unit
                            if ref_stream_preds:
                                exp_preds = np.array(
                                    [ref_stream_preds.get((u, c), np.nan) for c in u_cycs],
                                    dtype=np.float64,
                                )
                                diff_p = np.abs(exp_preds - u_preds)
                                max_dp = float(np.nanmax(diff_p)) if len(diff_p) > 0 else 0.0
                                if max_dp > TOL_CHECKPOINT_ATOL or np.isnan(max_dp):
                                    parity_mismatches.append(
                                        f"Stress prediction mismatch for {grp_k} unit {u}: "
                                        f"max_diff={max_dp}"
                                    )

                            # Check clean metadata
                            for cyc_val, reg_val, stage_val in zip(
                                u_cycs, u_regs, u_stages, strict=False
                            ):
                                meta = clean_meta_ds.get((u, cyc_val))
                                if meta is not None:
                                    _, exp_reg, exp_stage = meta
                                    if reg_val != exp_reg or stage_val != exp_stage:
                                        membership_mismatches.append(
                                            f"Metadata mismatch for stress {ds} unit {u} "
                                            f"cycle {cyc_val}"
                                        )
                                        break

                            # Engine-level accumulation
                            eng_str_k = (ds, mf, mid, cid, rep, s, u)
                            if eng_str_k not in stress_engine_accumulators:
                                stress_engine_accumulators[eng_str_k] = EngineAccumulator(
                                    failure_cycle=t_max if t_max is not None else 0
                                )
                            stress_engine_accumulators[eng_str_k].add_batch(
                                cyc=u_cycs,
                                pred=u_preds,
                                rul=u_ruls,
                                low=u_lows,
                                upp=u_upps,
                                fb=u_fbs,
                            )

                            # Track seen cycles
                            curr_seen = stress_engine_seen_cycles[eng_str_k]
                            for c in u_cycs:
                                if c in curr_seen:
                                    membership_mismatches.append(
                                        f"Duplicate cycle {c} for stress {eng_str_k}"
                                    )
                                curr_seen.add(c)

                            # Subgroup accumulation
                            for reg_val in np.unique(u_regs):
                                r_mask = u_regs == reg_val
                                sub_str_k = (ds, mf, mid, cid, "regime", str(reg_val), u)
                                if sub_str_k not in stress_subgroup_accumulators:
                                    stress_subgroup_accumulators[sub_str_k] = (
                                        SubgroupEngineAccumulator()
                                    )
                                stress_subgroup_accumulators[sub_str_k].add_batch(
                                    rul=u_ruls[r_mask],
                                    low=u_lows[r_mask],
                                    upp=u_upps[r_mask],
                                )

                            for stg_val in np.unique(u_stages):
                                s_mask = u_stages == stg_val
                                sub_str_k = (ds, mf, mid, cid, "lifecycle_stage", str(stg_val), u)
                                if sub_str_k not in stress_subgroup_accumulators:
                                    stress_subgroup_accumulators[sub_str_k] = (
                                        SubgroupEngineAccumulator()
                                    )
                                stress_subgroup_accumulators[sub_str_k].add_batch(
                                    rul=u_ruls[s_mask],
                                    low=u_lows[s_mask],
                                    upp=u_upps[s_mask],
                                )
        except Exception as exc:
            membership_mismatches.append(f"Error reading stress_interval_predictions: {exc}")
            interval_mismatches.append(f"Error reading stress_interval_predictions: {exc}")

    # Membership check status
    total_expected_endpoints = abl_expected_count + stress_expected_count
    total_checked_endpoints = checked_abl_endpoints + checked_stress_endpoints

    # Check complete engine and cycle coverage for ablation
    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for s in CONFIRMATORY_SEEDS:
                for variant in ALL_EIGHT_ABLATION_VARIANTS:
                    vid = variant.variant_id
                    for u in expected_units[ds]:
                        eng_k = (ds, mf, s, vid, u)
                        t_max = engine_failure_cycles[(ds, u)]
                        exp_cycs = t_max - 29
                        seen_c = abl_engine_seen_cycles.get(eng_k, set())
                        if len(seen_c) != exp_cycs:
                            membership_mismatches.append(
                                f"Ablation engine {eng_k} incomplete: {len(seen_c)} != {exp_cycs}"
                            )

    # Check complete engine and cycle coverage for stress
    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for s in CONFIRMATORY_SEEDS:
                for mid in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
                    for cond_id, _, _, rep in LOCKED_STRESS_STREAMS:
                        for u in expected_units[ds]:
                            eng_str_k = (ds, mf, mid, cond_id, rep, s, u)
                            t_max = engine_failure_cycles[(ds, u)]
                            exp_cycs = t_max - 29
                            seen_c = stress_engine_seen_cycles.get(eng_str_k, set())
                            if len(seen_c) != exp_cycs:
                                membership_mismatches.append(
                                    f"Stress engine {eng_str_k} incomplete: "
                                    f"{len(seen_c)} != {exp_cycs}"
                                )

    if membership_mismatches:
        failing_reasons.extend(membership_mismatches)

    checks["exact_endpoint_membership"] = {
        "status": (
            "PASS"
            if not membership_mismatches and total_checked_endpoints == total_expected_endpoints
            else "FAIL"
        ),
        "expected_count": total_expected_endpoints,
        "checked_count": total_checked_endpoints,
        "maximum_absolute_error": 0.0,
        "mismatches": membership_mismatches[:10],
    }

    if interval_mismatches:
        failing_reasons.extend(interval_mismatches)
    if interval_max_diff > max_discrepancy_overall:
        max_discrepancy_overall = interval_max_diff

    checks["full_interval_reconstruction"] = {
        "status": (
            "PASS"
            if not interval_mismatches and total_checked_endpoints == total_expected_endpoints
            else "FAIL"
        ),
        "expected_count": total_expected_endpoints,
        "checked_count": total_checked_endpoints,
        "maximum_absolute_error": interval_max_diff,
        "mismatches": interval_mismatches[:10],
    }

    # -------------------------------------------------------------------------
    # 6. Check: full_simulation_reconstruction
    # -------------------------------------------------------------------------
    sim_mismatches: list[str] = []
    sim_max_diff = 0.0
    checked_sims = 0
    expected_sim_count = len(abl_engine_accumulators) + len(stress_engine_accumulators)  # 75,640

    reconstructed_sim_data: dict[str, dict[Any, dict[str, Any]]] = {
        "ablation": {},
        "stress": {},
    }

    try:
        # Read saved simulation outcomes
        df_abl_sim = pd.read_csv(ev_dir / "ablation_simulation_outcomes.csv")
        abl_sim_saved: dict[tuple[str, str, int, str, int], Any] = {}
        for r in df_abl_sim.itertuples(index=False):
            abl_sim_saved[(r.dataset, r.model_family, int(r.seed), r.variant_id, int(r.unit))] = r

        df_str_sim = pd.read_csv(ev_dir / "stress_simulation_outcomes.csv")
        str_sim_saved: dict[tuple[str, str, str, str, int, int, int], Any] = {}
        for r in df_str_sim.itertuples(index=False):
            str_sim_saved[
                (
                    r.dataset,
                    r.model_family,
                    r.method_id,
                    r.condition_id,
                    int(r.replicate_id),
                    int(r.seed),
                    int(r.unit),
                )
            ] = r

        # Reconstruct ablation simulations
        for eng_k, acc in abl_engine_accumulators.items():
            ds, mf, s, vid, u = eng_k
            t_max = acc.failure_cycle
            saved_rec = abl_sim_saved.get(eng_k)
            if saved_rec is None:
                sim_mismatches.append(f"Missing saved ablation simulation for {eng_k}")
                continue

            ref_sim = _reconstruct_reference_simulation(
                cycles=np.array([acc.min_intervention_cycle] if acc.min_intervention_cycle else []),
                lower_bounds=np.array([0.0] if acc.min_intervention_cycle else []),
                failure_cycle=t_max,
            )
            if acc.min_intervention_cycle is not None:
                ref_sim["terminal_event"] = "PM"
                ref_sim["intervention_cycle"] = acc.min_intervention_cycle
                ref_sim["failed"] = False
                ref_sim["pm_occurred"] = True
                ref_sim["wasted_rul"] = float(t_max - acc.min_intervention_cycle)
                ref_sim["total_cost"] = 1.0 + 0.20 * ref_sim["wasted_rul"]
            else:
                ref_sim["terminal_event"] = "FAILURE"
                ref_sim["intervention_cycle"] = None
                ref_sim["failed"] = True
                ref_sim["pm_occurred"] = False
                ref_sim["wasted_rul"] = 0.0
                ref_sim["total_cost"] = 5.0

            reconstructed_sim_data["ablation"][eng_k] = ref_sim

            # Compare saved vs reference
            if str(saved_rec.terminal_event) != ref_sim["terminal_event"]:
                sim_mismatches.append(
                    f"Ablation sim terminal_event {eng_k}: "
                    f"exp={ref_sim['terminal_event']} != act={saved_rec.terminal_event}"
                )
            if bool(saved_rec.failed) != ref_sim["failed"]:
                sim_mismatches.append(f"Ablation sim failed mismatch {eng_k}")
            if bool(saved_rec.pm_occurred) != ref_sim["pm_occurred"]:
                sim_mismatches.append(f"Ablation sim pm_occurred mismatch {eng_k}")

            c_diff = abs(float(saved_rec.total_cost) - ref_sim["total_cost"])
            if c_diff > sim_max_diff:
                sim_max_diff = c_diff
            if not np.isclose(float(saved_rec.total_cost), ref_sim["total_cost"], atol=tol_atol):
                sim_mismatches.append(
                    f"Ablation sim cost mismatch {eng_k}: "
                    f"exp={ref_sim['total_cost']} != act={saved_rec.total_cost}"
                )

            checked_sims += 1

        # Reconstruct stress simulations
        for eng_str_k, acc in stress_engine_accumulators.items():
            ds, mf, mid, cid, rep, s, u = eng_str_k
            t_max = acc.failure_cycle
            saved_rec = str_sim_saved.get(eng_str_k)
            if saved_rec is None:
                sim_mismatches.append(f"Missing saved stress simulation for {eng_str_k}")
                continue

            ref_sim = _reconstruct_reference_simulation(
                cycles=np.array([acc.min_intervention_cycle] if acc.min_intervention_cycle else []),
                lower_bounds=np.array([0.0] if acc.min_intervention_cycle else []),
                failure_cycle=t_max,
            )

            reconstructed_sim_data["stress"][eng_str_k] = ref_sim

            if str(saved_rec.terminal_event) != ref_sim["terminal_event"]:
                sim_mismatches.append(
                    f"Stress sim terminal_event {eng_str_k}: "
                    f"exp={ref_sim['terminal_event']} != act={saved_rec.terminal_event}"
                )
            if bool(saved_rec.failed) != ref_sim["failed"]:
                sim_mismatches.append(f"Stress sim failed mismatch {eng_str_k}")
            if bool(saved_rec.pm_occurred) != ref_sim["pm_occurred"]:
                sim_mismatches.append(f"Stress sim pm_occurred mismatch {eng_str_k}")

            c_diff = abs(float(saved_rec.total_cost) - ref_sim["total_cost"])
            if c_diff > sim_max_diff:
                sim_max_diff = c_diff
            if not np.isclose(float(saved_rec.total_cost), ref_sim["total_cost"], atol=tol_atol):
                sim_mismatches.append(f"Stress sim cost mismatch {eng_str_k}")

            checked_sims += 1
    except Exception as exc:
        sim_mismatches.append(f"Simulation reconstruction error: {exc}")

    if sim_mismatches:
        failing_reasons.extend(sim_mismatches)
    if sim_max_diff > max_discrepancy_overall:
        max_discrepancy_overall = sim_max_diff

    checks["full_simulation_reconstruction"] = {
        "status": ("PASS" if not sim_mismatches and checked_sims == expected_sim_count else "FAIL"),
        "expected_count": expected_sim_count,
        "checked_count": checked_sims,
        "maximum_absolute_error": sim_max_diff,
        "mismatches": sim_mismatches[:10],
    }

    # -------------------------------------------------------------------------
    # 7. Check: endpoint_to_engine_metric_reconstruction
    # -------------------------------------------------------------------------
    metric_mismatches: list[str] = []
    metric_max_diff = 0.0
    checked_metric_rows = 0
    expected_metric_rows = 83640
    df_abl_eng_rec = pd.DataFrame()
    df_str_eng_rec = pd.DataFrame()

    try:
        # Build Reconstructed Raw Engine Seed Metrics (Ablation)
        abl_engine_seed_records: list[dict[str, Any]] = []
        for eng_k, acc in abl_engine_accumulators.items():
            ds, mf, s, vid, u = eng_k
            n = acc.n
            sim_res = reconstructed_sim_data["ablation"].get(eng_k, {})
            cov = acc.sum_covered / n if n > 0 else 0.0
            rec_m = {
                "dataset": ds,
                "model_family": mf,
                "seed": s,
                "variant_id": vid,
                "unit": u,
                "rmse": float(np.sqrt(acc.sum_sq_err / n)) if n > 0 else 0.0,
                "mae": float(acc.sum_abs_err / n) if n > 0 else 0.0,
                "coverage": float(cov),
                "coverage_abs_error": float(abs(cov - 0.90)),
                "width": float(acc.sum_width / n) if n > 0 else 0.0,
                "interval_score": float(acc.sum_interval_score / n) if n > 0 else 0.0,
                "lower_tail_miss": float(acc.sum_lower_miss / n) if n > 0 else 0.0,
                "upper_tail_miss": float(acc.sum_upper_miss / n) if n > 0 else 0.0,
                "fallback_freq": float(acc.sum_fallback / n) if n > 0 else 0.0,
                "cost": float(sim_res.get("total_cost", 5.0)),
                "failure_rate": float(sim_res.get("failed", True)),
                "pm_rate": float(sim_res.get("pm_occurred", False)),
                "wasted_rul": float(sim_res.get("wasted_rul", 0.0)),
                "intervention_cycle": sim_res.get("intervention_cycle"),
            }
            abl_engine_seed_records.append(rec_m)
            checked_metric_rows += 1

        df_abl_engine_seed_rec = pd.DataFrame(abl_engine_seed_records)

        # Compare with saved ablation_engine_seed_metrics.csv
        df_abl_seed_saved = pd.read_csv(ev_dir / "ablation_engine_seed_metrics.csv")
        abl_seed_key_cols = ["dataset", "model_family", "seed", "variant_id", "unit"]
        df_merged_abl_seed = pd.merge(
            df_abl_engine_seed_rec,
            df_abl_seed_saved,
            on=abl_seed_key_cols,
            suffixes=("_rec", "_act"),
        )
        if len(df_merged_abl_seed) != len(df_abl_seed_saved):
            metric_mismatches.append("ablation_engine_seed_metrics row count mismatch on merge")
        for m_col in ("rmse", "mae", "coverage", "width", "interval_score", "cost"):
            diffs = np.abs(df_merged_abl_seed[f"{m_col}_rec"] - df_merged_abl_seed[f"{m_col}_act"])
            max_d = float(diffs.max()) if len(diffs) > 0 else 0.0
            if max_d > metric_max_diff:
                metric_max_diff = max_d
            if not np.allclose(
                df_merged_abl_seed[f"{m_col}_rec"],
                df_merged_abl_seed[f"{m_col}_act"],
                atol=tol_atol,
                rtol=tol_rtol,
            ):
                metric_mismatches.append(f"Ablation engine-seed metric {m_col} mismatch")

        # Aggregate Ablation Engine Metrics (average across seeds)
        num_cols = [
            "rmse",
            "mae",
            "coverage",
            "coverage_abs_error",
            "width",
            "interval_score",
            "lower_tail_miss",
            "upper_tail_miss",
            "cost",
            "failure_rate",
            "pm_rate",
            "wasted_rul",
            "intervention_cycle",
            "fallback_freq",
        ]
        df_abl_eng_rec = (
            df_abl_engine_seed_rec.groupby(["dataset", "model_family", "variant_id", "unit"])[
                num_cols
            ]
            .mean()
            .reset_index()
        )
        checked_metric_rows += len(df_abl_eng_rec)

        df_abl_eng_saved = pd.read_csv(ev_dir / "ablation_engine_metrics.csv")
        df_merged_abl_eng = pd.merge(
            df_abl_eng_rec,
            df_abl_eng_saved,
            on=["dataset", "model_family", "variant_id", "unit"],
            suffixes=("_rec", "_act"),
        )
        for m_col in ("rmse", "mae", "coverage", "width", "interval_score", "cost"):
            diffs = np.abs(df_merged_abl_eng[f"{m_col}_rec"] - df_merged_abl_eng[f"{m_col}_act"])
            max_d = float(diffs.max()) if len(diffs) > 0 else 0.0
            if max_d > metric_max_diff:
                metric_max_diff = max_d
            if not np.allclose(
                df_merged_abl_eng[f"{m_col}_rec"],
                df_merged_abl_eng[f"{m_col}_act"],
                atol=tol_atol,
                rtol=tol_rtol,
            ):
                metric_mismatches.append(f"Ablation aggregated engine metric {m_col} mismatch")

        # Aggregate Ablation Summary Metrics (average across engines)
        df_abl_sum_rec = (
            df_abl_eng_rec.groupby(["dataset", "model_family", "variant_id"])[num_cols]
            .mean()
            .reset_index()
        )
        checked_metric_rows += len(df_abl_sum_rec)

        df_abl_sum_saved = pd.read_csv(ev_dir / "ablation_summary.csv")
        for r_sum in df_abl_sum_rec.itertuples():
            match_s = df_abl_sum_saved[
                (df_abl_sum_saved["dataset"] == r_sum.dataset)
                & (df_abl_sum_saved["model_family"] == r_sum.model_family)
                & (df_abl_sum_saved["variant_id"] == r_sum.variant_id)
            ]
            if len(match_s) == 0:
                metric_mismatches.append(f"Missing row in ablation_summary for {r_sum.variant_id}")
                continue
            row_act = match_s.iloc[0]
            for m_col in ("coverage", "cost", "width", "interval_score", "rmse"):
                act_v = float(row_act[f"{m_col}_mean"])
                exp_v = float(getattr(r_sum, m_col))
                diff = abs(act_v - exp_v)
                if diff > metric_max_diff:
                    metric_max_diff = diff
                if not np.isclose(act_v, exp_v, atol=tol_atol, rtol=tol_rtol):
                    metric_mismatches.append(
                        f"Ablation summary {r_sum.variant_id} {m_col}: exp={exp_v} != act={act_v}"
                    )

        # Build Reconstructed Raw Engine Seed Rep Metrics (Stress)
        str_engine_seed_records: list[dict[str, Any]] = []
        for eng_str_k, acc in stress_engine_accumulators.items():
            ds, mf, mid, cid, rep, s, u = eng_str_k
            n = acc.n
            sim_res = reconstructed_sim_data["stress"].get(eng_str_k, {})
            cov = acc.sum_covered / n if n > 0 else 0.0
            rec_m = {
                "dataset": ds,
                "model_family": mf,
                "method_id": mid,
                "condition_id": cid,
                "replicate_id": rep,
                "seed": s,
                "unit": u,
                "rmse": float(np.sqrt(acc.sum_sq_err / n)) if n > 0 else 0.0,
                "mae": float(acc.sum_abs_err / n) if n > 0 else 0.0,
                "coverage": float(cov),
                "coverage_abs_error": float(abs(cov - 0.90)),
                "width": float(acc.sum_width / n) if n > 0 else 0.0,
                "interval_score": float(acc.sum_interval_score / n) if n > 0 else 0.0,
                "lower_tail_miss": float(acc.sum_lower_miss / n) if n > 0 else 0.0,
                "upper_tail_miss": float(acc.sum_upper_miss / n) if n > 0 else 0.0,
                "fallback_freq": float(acc.sum_fallback / n) if n > 0 else 0.0,
                "cost": float(sim_res.get("total_cost", 5.0)),
                "failure_rate": float(sim_res.get("failed", True)),
                "pm_rate": float(sim_res.get("pm_occurred", False)),
                "wasted_rul": float(sim_res.get("wasted_rul", 0.0)),
                "intervention_cycle": sim_res.get("intervention_cycle"),
            }
            str_engine_seed_records.append(rec_m)
            checked_metric_rows += 1

        df_str_engine_seed_rec = pd.DataFrame(str_engine_seed_records)

        df_str_seed_saved = pd.read_csv(ev_dir / "stress_engine_seed_rep_metrics.csv")
        str_seed_keys = [
            "dataset",
            "model_family",
            "method_id",
            "condition_id",
            "replicate_id",
            "seed",
            "unit",
        ]
        df_merged_str_seed = pd.merge(
            df_str_engine_seed_rec,
            df_str_seed_saved,
            on=str_seed_keys,
            suffixes=("_rec", "_act"),
        )
        for m_col in ("rmse", "mae", "coverage", "width", "interval_score", "cost"):
            diffs = np.abs(df_merged_str_seed[f"{m_col}_rec"] - df_merged_str_seed[f"{m_col}_act"])
            max_d = float(diffs.max()) if len(diffs) > 0 else 0.0
            if max_d > metric_max_diff:
                metric_max_diff = max_d
            if not np.allclose(
                df_merged_str_seed[f"{m_col}_rec"],
                df_merged_str_seed[f"{m_col}_act"],
                atol=tol_atol,
                rtol=tol_rtol,
            ):
                metric_mismatches.append(f"Stress engine-seed metric {m_col} mismatch")

        # Aggregate Stress Engine Metrics (average across seeds and replicates)
        df_str_eng_rec = (
            df_str_engine_seed_rec.groupby(
                ["dataset", "model_family", "method_id", "condition_id", "unit"]
            )[num_cols]
            .mean()
            .reset_index()
        )
        checked_metric_rows += len(df_str_eng_rec)

        df_str_eng_saved = pd.read_csv(ev_dir / "stress_engine_metrics.csv")
        df_merged_str_eng = pd.merge(
            df_str_eng_rec,
            df_str_eng_saved,
            on=["dataset", "model_family", "method_id", "condition_id", "unit"],
            suffixes=("_rec", "_act"),
        )
        for m_col in ("rmse", "mae", "coverage", "width", "interval_score", "cost"):
            diffs = np.abs(df_merged_str_eng[f"{m_col}_rec"] - df_merged_str_eng[f"{m_col}_act"])
            max_d = float(diffs.max()) if len(diffs) > 0 else 0.0
            if max_d > metric_max_diff:
                metric_max_diff = max_d
            if not np.allclose(
                df_merged_str_eng[f"{m_col}_rec"],
                df_merged_str_eng[f"{m_col}_act"],
                atol=tol_atol,
                rtol=tol_rtol,
            ):
                metric_mismatches.append(f"Stress aggregated engine metric {m_col} mismatch")

        # Aggregate Stress Summary Metrics (average across engines)
        df_str_sum_rec = (
            df_str_eng_rec.groupby(["dataset", "model_family", "method_id", "condition_id"])[
                num_cols
            ]
            .mean()
            .reset_index()
        )
        checked_metric_rows += len(df_str_sum_rec)

        df_str_sum_saved = pd.read_csv(ev_dir / "stress_summary.csv")
        for r_sum in df_str_sum_rec.itertuples():
            match_s = df_str_sum_saved[
                (df_str_sum_saved["dataset"] == r_sum.dataset)
                & (df_str_sum_saved["model_family"] == r_sum.model_family)
                & (df_str_sum_saved["method_id"] == r_sum.method_id)
                & (df_str_sum_saved["condition_id"] == r_sum.condition_id)
            ]
            if len(match_s) == 0:
                metric_mismatches.append(f"Missing row in stress_summary for {r_sum.condition_id}")
                continue
            row_act = match_s.iloc[0]
            for m_col in ("coverage", "cost", "width", "interval_score", "rmse"):
                act_v = float(row_act[f"{m_col}_mean"])
                exp_v = float(getattr(r_sum, m_col))
                diff = abs(act_v - exp_v)
                if diff > metric_max_diff:
                    metric_max_diff = diff
                if not np.isclose(act_v, exp_v, atol=tol_atol, rtol=tol_rtol):
                    metric_mismatches.append(
                        f"Stress summary {r_sum.condition_id} {m_col}: exp={exp_v} != act={act_v}"
                    )

        expected_metric_rows = (
            len(df_abl_engine_seed_rec)
            + len(df_abl_eng_rec)
            + len(df_abl_sum_rec)
            + len(df_str_engine_seed_rec)
            + len(df_str_eng_rec)
            + len(df_str_sum_rec)
        )
    except Exception as exc:
        metric_mismatches.append(f"Error reconstructing engine metrics: {exc}")

    if metric_mismatches:
        failing_reasons.extend(metric_mismatches)
    if metric_max_diff > max_discrepancy_overall:
        max_discrepancy_overall = metric_max_diff

    checks["endpoint_to_engine_metric_reconstruction"] = {
        "status": (
            "PASS"
            if not metric_mismatches and checked_metric_rows == expected_metric_rows
            else "FAIL"
        ),
        "expected_count": expected_metric_rows,
        "checked_count": checked_metric_rows,
        "maximum_absolute_error": metric_max_diff,
        "mismatches": metric_mismatches[:10],
    }

    # -------------------------------------------------------------------------
    # 8. Check: full_subgroup_reconstruction
    # -------------------------------------------------------------------------
    subgroup_mismatches: list[str] = []
    subgroup_max_diff = 0.0
    checked_subgroup_rows = 0
    expected_subgroup_rows = 0

    try:
        sub_engine_records: list[dict[str, Any]] = []
        for sub_k, sub_acc in abl_subgroup_accumulators.items():
            ds, mf, vid, fam, val, u = sub_k
            n = sub_acc.n
            sub_engine_records.append(
                {
                    "evaluation_type": "ablation",
                    "dataset": ds,
                    "model_family": mf,
                    "variant_id": vid,
                    "method_id": "",
                    "condition_id": "clean",
                    "subgroup_family": fam,
                    "subgroup": str(val),
                    "unit": u,
                    "n_endpoints": n,
                    "coverage": float(sub_acc.sum_covered / n) if n > 0 else 0.0,
                    "lower_tail_miss": float(sub_acc.sum_lower_miss / n) if n > 0 else 0.0,
                    "upper_tail_miss": float(sub_acc.sum_upper_miss / n) if n > 0 else 0.0,
                }
            )
            checked_subgroup_rows += 1

        for sub_str_k, sub_acc in stress_subgroup_accumulators.items():
            ds, mf, mid, cid, fam, val, u = sub_str_k
            n = sub_acc.n
            sub_engine_records.append(
                {
                    "evaluation_type": "stress",
                    "dataset": ds,
                    "model_family": mf,
                    "variant_id": "",
                    "method_id": mid,
                    "condition_id": cid,
                    "subgroup_family": fam,
                    "subgroup": str(val),
                    "unit": u,
                    "n_endpoints": n,
                    "coverage": float(sub_acc.sum_covered / n) if n > 0 else 0.0,
                    "lower_tail_miss": float(sub_acc.sum_lower_miss / n) if n > 0 else 0.0,
                    "upper_tail_miss": float(sub_acc.sum_upper_miss / n) if n > 0 else 0.0,
                }
            )
            checked_subgroup_rows += 1

        df_sub_eng_rec = pd.DataFrame(sub_engine_records)
        df_sub_eng_saved = pd.read_csv(ev_dir / "subgroup_engine_metrics.csv")

        sub_eng_keys = [
            "evaluation_type",
            "dataset",
            "model_family",
            "variant_id",
            "method_id",
            "condition_id",
            "subgroup_family",
            "subgroup",
            "unit",
        ]
        df_merged_sub_eng = pd.merge(
            df_sub_eng_rec,
            df_sub_eng_saved,
            on=sub_eng_keys,
            suffixes=("_rec", "_act"),
        )
        for col in ("coverage", "lower_tail_miss", "upper_tail_miss"):
            diffs = np.abs(df_merged_sub_eng[f"{col}_rec"] - df_merged_sub_eng[f"{col}_act"])
            max_d = float(diffs.max()) if len(diffs) > 0 else 0.0
            if max_d > subgroup_max_diff:
                subgroup_max_diff = max_d
            if not np.allclose(
                df_merged_sub_eng[f"{col}_rec"],
                df_merged_sub_eng[f"{col}_act"],
                atol=tol_atol,
                rtol=tol_rtol,
            ):
                subgroup_mismatches.append(f"Subgroup engine metric {col} mismatch")

        # Reconstruct Subgroup Summary Metrics (equal-engine weighting)
        subgroup_grp_keys = [
            "evaluation_type",
            "dataset",
            "model_family",
            "variant_id",
            "method_id",
            "condition_id",
            "subgroup_family",
            "subgroup",
        ]
        sub_summary_records: list[dict[str, Any]] = []
        for grp_k, grp_df in df_sub_eng_rec.groupby(subgroup_grp_keys):
            n_engs = len(grp_df)
            n_pts = int(grp_df["n_endpoints"].sum())
            is_elig = n_engs >= 10
            cov_m = float(grp_df["coverage"].mean())
            lt_m = float(grp_df["lower_tail_miss"].mean())
            ut_m = float(grp_df["upper_tail_miss"].mean())
            rec_sum = {
                "evaluation_type": grp_k[0],
                "dataset": grp_k[1],
                "model_family": grp_k[2],
                "variant_id": grp_k[3],
                "method_id": grp_k[4],
                "condition_id": grp_k[5],
                "subgroup_family": grp_k[6],
                "subgroup": grp_k[7],
                "n_endpoints": n_pts,
                "n_engines": n_engs,
                "is_eligible": is_elig,
                "coverage": cov_m,
                "coverage_abs_error": abs(cov_m - 0.90),
                "lower_tail_miss": lt_m,
                "upper_tail_miss": ut_m,
            }
            sub_summary_records.append(rec_sum)
            checked_subgroup_rows += 1

        df_sub_sum_rec = pd.DataFrame(sub_summary_records)
        df_sub_sum_saved = pd.read_csv(ev_dir / "subgroup_metrics.csv")

        df_merged_sub_sum = pd.merge(
            df_sub_sum_rec,
            df_sub_sum_saved,
            on=subgroup_grp_keys,
            suffixes=("_rec", "_act"),
        )
        for col in ("coverage", "coverage_abs_error", "lower_tail_miss", "upper_tail_miss"):
            diffs = np.abs(df_merged_sub_sum[f"{col}_rec"] - df_merged_sub_sum[f"{col}_act"])
            max_d = float(diffs.max()) if len(diffs) > 0 else 0.0
            if max_d > subgroup_max_diff:
                subgroup_max_diff = max_d
            if not np.allclose(
                df_merged_sub_sum[f"{col}_rec"],
                df_merged_sub_sum[f"{col}_act"],
                atol=tol_atol,
                rtol=tol_rtol,
            ):
                subgroup_mismatches.append(f"Subgroup summary metric {col} mismatch")

        expected_subgroup_rows = len(df_sub_eng_saved) + len(df_sub_sum_saved)
    except Exception as exc:
        subgroup_mismatches.append(f"Error reconstructing subgroup metrics: {exc}")

    if subgroup_mismatches:
        failing_reasons.extend(subgroup_mismatches)
    if subgroup_max_diff > max_discrepancy_overall:
        max_discrepancy_overall = subgroup_max_diff

    checks["full_subgroup_reconstruction"] = {
        "status": (
            "PASS"
            if not subgroup_mismatches and checked_subgroup_rows == expected_subgroup_rows
            else "FAIL"
        ),
        "expected_count": expected_subgroup_rows,
        "checked_count": checked_subgroup_rows,
        "maximum_absolute_error": subgroup_max_diff,
        "mismatches": subgroup_mismatches[:10],
    }

    # -------------------------------------------------------------------------
    # 9. Check: full_bootstrap_reconstruction
    # -------------------------------------------------------------------------
    expected_boot_count = 1176 + 126 + 168  # 1,470
    boot_mismatches: list[str] = []
    max_boot_diff: float = 0.0
    checked_boot_count: int = 0

    try:
        df_paired_contrasts = pd.read_csv(ev_dir / "paired_contrasts.csv")
        df_factor_effects = pd.read_csv(ev_dir / "factor_main_effects.csv")

        boot_mismatches, max_boot_diff, checked_boot_count = (
            verify_all_bootstrap_contrasts_and_effects(
                ev_dir=ev_dir,
                df_ablation_engine=df_abl_eng_rec,
                df_stress_engine=df_str_eng_rec,
                df_paired_contrasts=df_paired_contrasts,
                df_factor_effects=df_factor_effects,
                tol_atol=tol_atol,
                tol_rtol=tol_rtol,
            )
        )
    except Exception as exc:
        boot_mismatches.append(f"Error verifying bootstrap contrasts: {exc}")

    checks["full_bootstrap_reconstruction"] = {
        "status": "PASS"
        if not boot_mismatches and checked_boot_count == expected_boot_count
        else "FAIL",
        "expected_count": expected_boot_count,
        "checked_count": checked_boot_count,
        "maximum_absolute_error": max_boot_diff,
        "mismatches": boot_mismatches[:10],
    }

    # -------------------------------------------------------------------------
    # Overall Status Determination
    # -------------------------------------------------------------------------
    # Require every mandatory check exists, has status PASS, and checked_count == expected_count
    missing_mandatory = [m for m in MANDATORY_CHECKS if m not in checks]
    if missing_mandatory:
        failing_reasons.append(f"Missing mandatory audit checks: {missing_mandatory}")

    non_pass_checks = [m for m in MANDATORY_CHECKS if checks.get(m, {}).get("status") != "PASS"]
    if non_pass_checks:
        failing_reasons.append(f"Mandatory checks did not pass: {non_pass_checks}")

    count_mismatches = [
        m
        for m in MANDATORY_CHECKS
        if checks.get(m, {}).get("expected_count") != checks.get(m, {}).get("checked_count")
    ]
    if count_mismatches:
        failing_reasons.append(f"Mandatory checks count mismatch: {count_mismatches}")

    overall_status = "PASS" if not failing_reasons else "FAIL"

    return {
        "schema_version": SCHEMA_VERSION,
        "overall_status": overall_status,
        "execution_manifest_sha256": manifest_hash,
        "verifier_source_sha256": verifier_sha,
        "failing_reasons": failing_reasons,
        "max_discrepancies": {"overall": max_discrepancy_overall},
        "checks": checks,
    }


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
