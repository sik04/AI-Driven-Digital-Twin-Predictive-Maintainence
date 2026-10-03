"""
Evaluation and Uncertainty Quantification Metrics for IntelliTwin.
Computes PICP, NMPIW, Winkler Score, NASA C-MAPSS Score, RMSE, and MAE.
"""

import numpy as np


def nasa_scoring_function(y_true, y_pred):
    """NASA C-MAPSS asymmetric evaluation metric.
    Penalizes late predictions (over-estimation) more severely than early predictions.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    diff = y_pred - y_true
    score = np.where(diff < 0, np.exp(-diff / 13.0) - 1.0, np.exp(diff / 10.0) - 1.0)
    return float(np.sum(score))


def compute_regression_metrics(y_true, y_pred):
    """Compute standard RUL regression metrics."""
    diff = np.asarray(y_pred) - np.asarray(y_true)
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    nasa_score = nasa_scoring_function(y_true, y_pred)

    return {
        "mae": mae,
        "rmse": rmse,
        "nasa_score": nasa_score
    }


def compute_uq_metrics(y_true, lower_bounds, upper_bounds, alpha=0.10):
    """Compute formal uncertainty quantification metrics:
    - PICP: Prediction Interval Coverage Probability (target >= 1 - alpha)
    - NMPIW: Normalized Mean Prediction Interval Width
    - Winkler Score: Penalized interval score (lower is better)
    - Coverage Gap: max(0, (1 - alpha) - PICP)
    """
    y_true = np.asarray(y_true).ravel()
    lower = np.asarray(lower_bounds).ravel()
    upper = np.asarray(upper_bounds).ravel()
    n = len(y_true)

    # 1. PICP
    covered = (y_true >= lower) & (y_true <= upper)
    picp = float(np.mean(covered))

    # 2. NMPIW
    widths = upper - lower
    y_range = max(1e-4, float(np.max(y_true) - np.min(y_true)))
    mpiw = float(np.mean(widths))
    nmpiw = float(mpiw / y_range)

    # 3. Winkler Score
    # For target coverage 1 - alpha:
    # If in interval: width
    # If below lower: width + 2/alpha * (lower - y)
    # If above upper: width + 2/alpha * (y - upper)
    penalty_lower = (2.0 / alpha) * np.maximum(0.0, lower - y_true)
    penalty_upper = (2.0 / alpha) * np.maximum(0.0, y_true - upper)
    winkler_scores = widths + penalty_lower + penalty_upper
    winkler_mean = float(np.mean(winkler_scores))

    # 4. Coverage Width Criterion (CWC)
    # CWC = NMPIW * (1 + gamma * exp(-eta * (PICP - (1 - alpha))))
    target_coverage = 1.0 - alpha
    gamma = 1 if picp < target_coverage else 0
    eta = 50.0
    cwc = float(nmpiw * (1.0 + gamma * np.exp(-eta * (picp - target_coverage))))

    return {
        "target_coverage": float(target_coverage),
        "picp": picp,
        "mpiw": mpiw,
        "nmpiw": nmpiw,
        "winkler_score": winkler_mean,
        "cwc": cwc,
        "coverage_met": bool(picp >= target_coverage)
    }
