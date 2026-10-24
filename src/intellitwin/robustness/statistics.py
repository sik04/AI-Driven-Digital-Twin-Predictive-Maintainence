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
    # 1. Per endpoint indicators
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


def compute_paired_bootstrap_contrast(
    metric_a_per_engine: dict[int, float],
    metric_b_per_engine: dict[int, float],
    bootstrap_draws: np.ndarray[Any, Any],
) -> tuple[float, float, float]:
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
    tuple[float, float, float]
        (point_estimate, ci_low, ci_high) where intervals are 95% percentile [0.025, 0.975].
    """
    units = sorted(metric_a_per_engine.keys())
    assert set(units) == set(metric_b_per_engine.keys()), (
        "Engine sets must match for paired contrast"
    )

    # Point estimate
    vals_a = np.array([metric_a_per_engine[u] for u in units])
    vals_b = np.array([metric_b_per_engine[u] for u in units])
    point_est = float(np.mean(vals_a) - np.mean(vals_b))

    # Bootstrap replicates
    # Map draw matrix of engine IDs to array of contrast differences
    diff_map = {u: metric_a_per_engine[u] - metric_b_per_engine[u] for u in units}
    # vectorize lookup
    draws_diffs = np.vectorize(diff_map.get)(bootstrap_draws)
    # mean over engines (axis=1) for each replicate
    replicate_contrasts = np.mean(draws_diffs, axis=1)

    ci_low, ci_high = np.quantile(replicate_contrasts, [0.025, 0.975], method="linear")
    return point_est, float(ci_low), float(ci_high)
