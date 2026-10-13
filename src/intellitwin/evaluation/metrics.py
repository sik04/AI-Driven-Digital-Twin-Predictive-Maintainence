"""Production statistical metrics, equal-engine weighting, and subgroup error calculators."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.evaluation.schema import (
    PRIMARY_NOMINAL_COVERAGE,
    SUBGROUP_MIN_ENGINES,
)


def compute_interval_score(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    nominal_coverage: float = PRIMARY_NOMINAL_COVERAGE,
) -> np.ndarray:
    """Compute per-endpoint Winkler interval score.

    Score = (U - L) + (2 / alpha) * (L - y) * I(y < L) + (2 / alpha) * (y - U) * I(y > U)
    where alpha = 1.0 - nominal_coverage.
    """
    alpha = 1.0 - nominal_coverage
    if alpha <= 0.0 or alpha >= 1.0:
        raise ValueError(f"nominal_coverage must be strictly in (0, 1), got {nominal_coverage}")

    width = upper - lower
    penalty_lower = np.maximum(0.0, lower - y_true) * (2.0 / alpha)
    penalty_upper = np.maximum(0.0, y_true - upper) * (2.0 / alpha)
    res = np.asarray(width + penalty_lower + penalty_upper, dtype=np.float64)
    return res


def compute_equal_engine_metric(
    df: pd.DataFrame,
    metric_col: str,
    unit_col: str = "unit",
    seed_col: str = "seed",
) -> float:
    """Compute equal-engine-weighted metric averaged across 5 seeds per engine.

    Order of aggregation:
    1. Average within (unit, seed)
    2. Average across 5 seeds for each engine
    3. Average equally across all engines
    """
    unit_seed = df.groupby([unit_col, seed_col])[metric_col].mean().reset_index()
    engine_avgs = unit_seed.groupby(unit_col)[metric_col].mean()
    return float(engine_avgs.mean())


def compute_equal_engine_rmse(
    df: pd.DataFrame,
    pred_col: str = "prediction",
    target_col: str = "rul_target",
    unit_col: str = "unit",
    seed_col: str = "seed",
) -> float:
    """Compute equal-engine RMSE by aggregating squared errors before taking the square root."""
    df_temp = df.copy()
    sq_col = "_sq_err"
    df_temp[sq_col] = (df_temp[pred_col] - df_temp[target_col]) ** 2
    mse = compute_equal_engine_metric(
        df_temp, metric_col=sq_col, unit_col=unit_col, seed_col=seed_col
    )
    return float(np.sqrt(mse))


def compute_subgroup_coverage_and_errors(
    df: pd.DataFrame,
    subgroup_col: str,
    covered_col: str = "covered",
    nominal_coverage: float = PRIMARY_NOMINAL_COVERAGE,
    unit_col: str = "unit",
    seed_col: str = "seed",
    min_engines: int = SUBGROUP_MIN_ENGINES,
) -> dict[str, dict[str, Any]]:
    """Compute subgroup coverage and absolute coverage error for eligible groups.

    Eligibility rule:
    Subgroup must contain >= min_engines distinct engines with evaluated endpoints.

    Returns dict mapping group_id -> {
        'coverage': float,
        'abs_error': float,
        'engine_count': int,
        'is_eligible': bool,
    }
    """
    results: dict[str, dict[str, Any]] = {}
    for group_val, grp in df.groupby(subgroup_col):
        group_id = str(group_val)
        n_engs = int(grp[unit_col].nunique())
        is_eligible = n_engs >= min_engines
        if is_eligible:
            cov = compute_equal_engine_metric(
                grp, metric_col=covered_col, unit_col=unit_col, seed_col=seed_col
            )
            err = abs(cov - nominal_coverage)
        else:
            cov = float("nan")
            err = float("nan")

        results[group_id] = {
            "coverage": cov,
            "abs_error": err,
            "engine_count": n_engs,
            "is_eligible": is_eligible,
        }
    return results


def compute_replicate_worst_group_bounds(
    available_errors: Sequence[float] | dict[str, float],
    missing_group_count: int,
    nominal_coverage: float = PRIMARY_NOMINAL_COVERAGE,
) -> tuple[float, float]:
    """Compute conservative lower and upper bounds on worst-group coverage error for a replicate.

    Rule:
    If |G_available^(b)| > 0:
        WorstErr_lower^(b) = max over available groups of Err^(b)(g)
    else:
        WorstErr_lower^(b) = 0.0

    Then:
    If |G_missing^(b)| > 0:
        WorstErr_upper^(b) = max(WorstErr_lower^(b), nominal_coverage)
    else:
        WorstErr_upper^(b) = WorstErr_lower^(b)
    """
    if isinstance(available_errors, dict):
        vals = [v for v in available_errors.values() if np.isfinite(v)]
    else:
        vals = [v for v in available_errors if np.isfinite(v)]

    if len(vals) > 0:
        worst_err_lower = float(max(vals))
    else:
        worst_err_lower = 0.0

    if missing_group_count > 0:
        worst_err_upper = float(max(worst_err_lower, nominal_coverage))
    else:
        worst_err_upper = worst_err_lower

    return (worst_err_lower, worst_err_upper)


def propagate_delta_error_bounds(
    baseline_bounds: tuple[float, float],
    proposed_bounds: tuple[float, float],
) -> tuple[float, float]:
    """Propagate worst-case bounds for Delta_error = WorstErr_baseline - WorstErr_proposed."""
    b_lower, b_upper = baseline_bounds
    p_lower, p_upper = proposed_bounds
    delta_lower = b_lower - p_upper
    delta_upper = b_upper - p_lower
    return (delta_lower, delta_upper)
