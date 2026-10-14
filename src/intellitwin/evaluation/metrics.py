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
    y_true: np.ndarray[Any, Any],
    lower: np.ndarray[Any, Any],
    upper: np.ndarray[Any, Any],
    nominal_coverage: float = PRIMARY_NOMINAL_COVERAGE,
) -> np.ndarray[Any, Any]:
    """Compute per-endpoint Winkler interval score.

    Score = (U - L) + (2 / alpha) * (L - y) * I(y < L) + (2 / alpha) * (y - U) * I(y > U)
    where alpha = 1.0 - nominal_coverage.
    """
    alpha = 1.0 - nominal_coverage
    if alpha <= 0.0 or alpha >= 1.0:
        raise ValueError(f"nominal_coverage must be strictly in (0, 1), got {nominal_coverage}")

    y_arr = np.asarray(y_true, dtype=np.float64)
    low_arr = np.asarray(lower, dtype=np.float64)
    upp_arr = np.asarray(upper, dtype=np.float64)

    if not (len(y_arr) == len(low_arr) == len(upp_arr)):
        raise ValueError("Length mismatch in compute_interval_score inputs.")
    if (
        not np.all(np.isfinite(y_arr))
        or not np.all(np.isfinite(low_arr))
        or not np.all(np.isfinite(upp_arr))
    ):
        raise ValueError("Non-finite values encountered in compute_interval_score.")
    if np.any(low_arr > upp_arr):
        raise ValueError("Inverted interval bounds detected: lower > upper.")

    width = upp_arr - low_arr
    penalty_lower = np.maximum(0.0, low_arr - y_arr) * (2.0 / alpha)
    penalty_upper = np.maximum(0.0, y_arr - upp_arr) * (2.0 / alpha)
    res = np.asarray(width + penalty_lower + penalty_upper, dtype=np.float64)
    return res


def compute_equal_engine_metric(
    df: pd.DataFrame,
    metric_col: str,
    unit_col: str = "unit",
    seed_col: str = "seed",
) -> float:
    """Compute equal-engine-weighted metric averaged across seeds per engine.

    Order of aggregation:
    1. Verify completeness of seeds across all engines (no silent dropping)
    2. Average within (unit, seed)
    3. Average across seeds for each engine
    4. Average equally across all engines
    """
    if metric_col not in df.columns:
        raise KeyError(f"Metric column '{metric_col}' not found in DataFrame.")

    vals = df[metric_col].to_numpy(dtype=float)
    if not np.all(np.isfinite(vals)):
        raise ValueError(f"Non-finite values encountered in metric column '{metric_col}'.")

    if seed_col in df.columns:
        counts_per_unit = df.groupby(unit_col)[seed_col].nunique()
        expected_seed_count = int(counts_per_unit.max())
        if not (counts_per_unit == expected_seed_count).all():
            bad_units = counts_per_unit[counts_per_unit != expected_seed_count].index.tolist()
            raise ValueError(
                f"Incomplete seed observations detected for engines: {bad_units}; "
                f"all engines must have {expected_seed_count} seeds."
            )

    unit_seed = df.groupby([unit_col, seed_col])[metric_col].mean().reset_index()
    engine_avgs = unit_seed.groupby(unit_col)[metric_col].mean()
    return float(engine_avgs.mean())


def compute_equal_engine_rmse(
    df: pd.DataFrame,
    pred_col: str = "prediction",
    target_col: str = "rul_true",
    unit_col: str = "unit",
    seed_col: str = "seed",
) -> float:
    """Compute equal-engine RMSE by aggregating squared errors before taking the square root.

    Default target_col is 'rul_true'. Capped-target RMSE ('rul_target') is secondary.
    """
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
        'is_missing': bool,
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
            missing = False
        else:
            cov = float("nan")
            err = float("nan")
            missing = True

        results[group_id] = {
            "coverage": cov,
            "abs_error": err,
            "engine_count": n_engs,
            "is_eligible": is_eligible,
            "is_missing": missing,
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
        for k, v in available_errors.items():
            if not np.isfinite(v):
                raise ValueError(f"Non-finite subgroup error encountered for group '{k}': {v}")
        vals = list(available_errors.values())
    else:
        for i, v in enumerate(available_errors):
            if not np.isfinite(v):
                raise ValueError(f"Non-finite subgroup error encountered at index {i}: {v}")
        vals = list(available_errors)

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
    if b_lower > b_upper or p_lower > p_upper:
        raise ValueError("Inverted bounds detected in propagate_delta_error_bounds.")
    delta_lower = float(b_lower - p_upper)
    delta_upper = float(b_upper - p_lower)
    return (delta_lower, delta_upper)
