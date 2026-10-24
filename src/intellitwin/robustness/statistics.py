"""Statistical aggregation, paired stratified cluster-bootstrap, and exploratory contrasts."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.evaluation.bootstrap import (
    DATASET_NUMBERS,
    load_partition_quartile_strata,
)
from intellitwin.evaluation.metrics import (
    compute_interval_score,
)
from intellitwin.evaluation.schema import (
    PRIMARY_NOMINAL_COVERAGE,
)

PHASE08_BOOTSTRAP_REPLICATES: int = 10000
SUBGROUP_MIN_ENGINES: int = 10


def generate_phase08_bootstrap_draws(
    dataset: str,
    partition_engines: Collection[int],
    base_dir: Path | str = ".",
    n_replicates: int = PHASE08_BOOTSTRAP_REPLICATES,
) -> np.ndarray[Any, Any]:
    """Generate deterministic stratified engine-cluster bootstrap draws for Phase 8.

    PRNG: np.random.Generator(PCG64(SeedSequence([2026, 8, dataset_number]))).
    Draws stratum-by-stratum (Q1, Q2, Q3, Q4) with replacement.
    Retains duplicate engine multiplicity.
    Returns array of shape (n_replicates, n_total_engines).
    """
    if dataset not in DATASET_NUMBERS:
        raise ValueError(f"Unknown dataset {dataset}")

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


def compute_engine_summary_records(
    df_pred: pd.DataFrame,
    df_sim: pd.DataFrame,
    nominal_coverage: float = PRIMARY_NOMINAL_COVERAGE,
) -> pd.DataFrame:
    """Compute engine-level summary metrics averaged across seeds.

    Input DataFrames must contain:
    - df_pred: ['unit', 'seed', 'endpoint_cycle', 'prediction', 'rul_true',
      'lower', 'upper', 'regime', 'lifecycle_stage', 'fallback_used']
    - df_sim: ['unit', 'seed', 'total_cost', 'pm_occurred', 'failed',
      'wasted_rul', 'intervention_cycle']

    Returns a DataFrame with one row per unit containing seed-averaged engine metrics.
    """
    df_p = df_pred.copy()
    y = df_p["rul_true"].to_numpy(dtype=float)
    p = df_p["prediction"].to_numpy(dtype=float)
    low = df_p["lower"].to_numpy(dtype=float)
    upp = df_p["upper"].to_numpy(dtype=float)

    df_p["sq_err"] = (p - y) ** 2
    df_p["abs_err"] = np.abs(p - y)
    df_p["covered"] = ((low <= y) & (y <= upp)).astype(float)
    df_p["width"] = upp - low
    df_p["interval_score"] = compute_interval_score(y, low, upp, nominal_coverage=nominal_coverage)
    df_p["lower_tail_miss"] = (y < low).astype(float)
    df_p["upper_tail_miss"] = (y > upp).astype(float)

    # Aggregate by unit and seed first
    grouped_ps = (
        df_p.groupby(["unit", "seed"])
        .agg(
            mse=("sq_err", "mean"),
            mae=("abs_err", "mean"),
            coverage=("covered", "mean"),
            width=("width", "mean"),
            interval_score=("interval_score", "mean"),
            lower_tail_miss=("lower_tail_miss", "mean"),
            upper_tail_miss=("upper_tail_miss", "mean"),
            fallback_freq=("fallback_used", "mean"),
        )
        .reset_index()
    )

    # Merge with simulation outcomes (one row per unit and seed)
    merged_us = pd.merge(grouped_ps, df_sim, on=["unit", "seed"], how="inner")

    # Now average across seeds for each unit
    engine_level = (
        merged_us.groupby("unit")
        .agg(
            rmse=("mse", lambda s: float(np.sqrt(np.mean(s)))),
            mae=("mae", "mean"),
            coverage=("coverage", "mean"),
            coverage_abs_error=("coverage", lambda s: float(np.abs(np.mean(s) - nominal_coverage))),
            width=("width", "mean"),
            interval_score=("interval_score", "mean"),
            lower_tail_miss=("lower_tail_miss", "mean"),
            upper_tail_miss=("upper_tail_miss", "mean"),
            cost=("total_cost", "mean"),
            failure_rate=("failed", "mean"),
            pm_rate=("pm_occurred", "mean"),
            wasted_rul=("wasted_rul", "mean"),
            intervention_cycle=("intervention_cycle", "mean"),
            fallback_freq=("fallback_freq", "mean"),
        )
        .reset_index()
    )

    return engine_level


def compute_subgroup_metrics_equal_engine(
    df_eval: pd.DataFrame,
    clean_subgroup_df: pd.DataFrame,
    subgroup_family: str,
    nominal_coverage: float = PRIMARY_NOMINAL_COVERAGE,
    min_engines: int = SUBGROUP_MIN_ENGINES,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute per-engine subgroup metrics and equal-engine-weighted subgroup summary.

    Aggregation Hierarchy (Protocol Requirement 2.A):
    1. Determine subgroup membership/eligibility from clean original trajectories.
    2. Calculate coverage and lower/upper-tail miss rates within each engine/group.
    3. Average seeds and perturbation replicates within each engine.
    4. Equally average the resulting engine-level values across distinct engines.
    5. Record endpoint counts, distinct-engine counts, and eligibility explicitly.

    Parameters
    ----------
    df_eval : pd.DataFrame
        Evaluated endpoint predictions/intervals containing 'unit', 'endpoint_cycle',
        'lower', 'upper', 'rul_true', 'seed', and optionally 'replicate_id'.
    clean_subgroup_df : pd.DataFrame
        Clean original trajectory mapping with 'unit', 'endpoint_cycle', and the
        group column ('regime' or 'lifecycle_stage').
    subgroup_family : str
        'regime' or 'lifecycle_stage'.
    nominal_coverage : float
        Target nominal coverage (default 0.90).
    min_engines : int
        Minimum distinct engines required for eligibility (default 10).

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        (df_engine_subgroup, df_subgroup_summary)
        - df_engine_subgroup has columns: ['unit', 'subgroup_family', 'subgroup',
          'n_endpoints', 'coverage', 'lower_tail_miss', 'upper_tail_miss']
        - df_subgroup_summary has columns: ['subgroup_family', 'subgroup',
          'n_endpoints', 'n_engines', 'is_eligible', 'coverage', 'coverage_abs_error',
          'lower_tail_miss', 'upper_tail_miss']
    """
    col_name = "regime" if subgroup_family == "regime" else "lifecycle_stage"
    if col_name not in clean_subgroup_df.columns:
        raise KeyError(f"Column '{col_name}' missing from clean subgroup mapping.")

    # Attach clean subgroup labels strictly via (unit, endpoint_cycle)
    clean_map = (
        clean_subgroup_df[["unit", "endpoint_cycle", col_name]]
        .drop_duplicates(subset=["unit", "endpoint_cycle"])
        .rename(columns={col_name: "clean_group"})
    )

    df_merged = pd.merge(df_eval, clean_map, on=["unit", "endpoint_cycle"], how="inner")

    y = df_merged["rul_true"].to_numpy(dtype=float)
    low = df_merged["lower"].to_numpy(dtype=float)
    upp = df_merged["upper"].to_numpy(dtype=float)

    df_merged["covered"] = ((low <= y) & (y <= upp)).astype(float)
    df_merged["lower_tail_miss"] = (y < low).astype(float)
    df_merged["upper_tail_miss"] = (y > upp).astype(float)

    group_keys = ["unit", "clean_group", "seed"]
    if "replicate_id" in df_merged.columns:
        group_keys.append("replicate_id")

    # Step 2: Calculate within each engine/group/seed(/replicate)
    per_realization = (
        df_merged.groupby(group_keys)
        .agg(
            n_endpoints=("covered", "count"),
            coverage=("covered", "mean"),
            lower_tail_miss=("lower_tail_miss", "mean"),
            upper_tail_miss=("upper_tail_miss", "mean"),
        )
        .reset_index()
    )

    # Step 3: Average seeds and perturbation replicates within each engine
    per_engine = (
        per_realization.groupby(["unit", "clean_group"])
        .agg(
            n_endpoints=("n_endpoints", "mean"),  # endpoint count per engine is invariant
            coverage=("coverage", "mean"),
            lower_tail_miss=("lower_tail_miss", "mean"),
            upper_tail_miss=("upper_tail_miss", "mean"),
        )
        .reset_index()
    )

    per_engine["subgroup_family"] = subgroup_family
    per_engine = per_engine.rename(columns={"clean_group": "subgroup"})
    engine_cols = [
        "unit",
        "subgroup_family",
        "subgroup",
        "n_endpoints",
        "coverage",
        "lower_tail_miss",
        "upper_tail_miss",
    ]
    df_engine_subgroup = (
        per_engine[engine_cols].sort_values(["subgroup", "unit"]).reset_index(drop=True)
    )

    # Step 4: Equally average the resulting engine-level values across distinct engines
    # Identify all possible groups observed in the clean trajectory
    all_observed_groups = sorted(clean_subgroup_df[col_name].unique())
    summary_rows: list[dict[str, Any]] = []

    for grp in all_observed_groups:
        sub_df = df_engine_subgroup[df_engine_subgroup["subgroup"] == grp]
        n_engs = int(len(sub_df))
        if n_engs > 0:
            tot_endpoints = int(sub_df["n_endpoints"].sum())
            cov_val = float(sub_df["coverage"].mean())
            cov_abs_err = float(abs(cov_val - nominal_coverage))
            low_miss_val = float(sub_df["lower_tail_miss"].mean())
            upp_miss_val = float(sub_df["upper_tail_miss"].mean())
            eligible = n_engs >= min_engines
        else:
            tot_endpoints = 0
            cov_val = float("nan")
            cov_abs_err = float("nan")
            low_miss_val = float("nan")
            upp_miss_val = float("nan")
            eligible = False

        summary_rows.append(
            {
                "subgroup_family": subgroup_family,
                "subgroup": grp,
                "n_endpoints": tot_endpoints,
                "n_engines": n_engs,
                "is_eligible": eligible,
                "coverage": cov_val,
                "coverage_abs_error": cov_abs_err,
                "lower_tail_miss": low_miss_val,
                "upper_tail_miss": upp_miss_val,
            }
        )

    df_subgroup_summary = pd.DataFrame(summary_rows)
    return df_engine_subgroup, df_subgroup_summary


def compute_paired_bootstrap_contrast(
    metric_a_per_engine: dict[int, float],
    metric_b_per_engine: dict[int, float],
    bootstrap_draws: np.ndarray[Any, Any],
) -> tuple[float, float, float, np.ndarray[Any, Any]]:
    """Compute paired contrast Delta = A - B over stratified bootstrap draws.

    Parameters
    ----------
    metric_a_per_engine : dict[int, float]
        Mapping engine_id -> metric value for candidate / stressed variant.
    metric_b_per_engine : dict[int, float]
        Mapping engine_id -> metric value for baseline / clean variant.
    bootstrap_draws : np.ndarray
        Array of shape (B, N) containing engine IDs sampled with replacement.

    Returns
    -------
    tuple[float, float, float, np.ndarray]
        (point_estimate, ci_low, ci_high, replicate_contrasts)
        where intervals are 95% empirical percentile [0.025, 0.975], and
        replicate_contrasts is an array of shape (B,).
    """
    units = sorted(metric_a_per_engine.keys())
    if set(units) != set(metric_b_per_engine.keys()):
        raise ValueError(
            f"Engine sets must match for paired contrast: "
            f"A={set(units)} != B={set(metric_b_per_engine.keys())}"
        )

    # Point estimate
    vals_a = np.array([metric_a_per_engine[u] for u in units], dtype=np.float64)
    vals_b = np.array([metric_b_per_engine[u] for u in units], dtype=np.float64)
    point_est = float(np.mean(vals_a) - np.mean(vals_b))

    # Bootstrap replicates
    diff_map = {u: float(metric_a_per_engine[u] - metric_b_per_engine[u]) for u in units}
    draws_diffs = np.vectorize(diff_map.get, otypes=[np.float64])(bootstrap_draws)
    replicate_contrasts = np.mean(draws_diffs, axis=1)

    ci_low, ci_high = np.quantile(replicate_contrasts, [0.025, 0.975], method="linear")
    return point_est, float(ci_low), float(ci_high), replicate_contrasts
