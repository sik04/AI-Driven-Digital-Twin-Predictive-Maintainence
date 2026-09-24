"""
Uncertainty Quantification and Prognostic Performance Evaluation Metrics.

Implements standard benchmark criteria for probabilistic time-series forecasting:
- Prediction Interval Coverage Probability (PICP)
- Normalized Mean Prediction Interval Width (NMPIW)
- Coverage Width-based Criterion (CWC)
- Winkler Score (Interval Score)
- Continuous Ranked Probability Score (CRPS)
- Negative Log-Likelihood (NLL)
- Deterministic Baselines: RMSE, MAE, R^2
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Union


def compute_picp(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    """
    Computes Prediction Interval Coverage Probability (PICP).
    PICP = (1/N) * sum( 1{ lower_i <= y_i <= upper_i } )
    """
    y_true = np.asarray(y_true).ravel()
    lower = np.asarray(lower).ravel()
    upper = np.asarray(upper).ravel()
    
    covered = (y_true >= lower) & (y_true <= upper)
    return float(np.mean(covered))


def compute_nmpiw(
    y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray, y_range: Union[float, None] = None
) -> float:
    """
    Computes Normalized Mean Prediction Interval Width (NMPIW).
    NMPIW = (1 / (N * range(y))) * sum( upper_i - lower_i )
    """
    y_true = np.asarray(y_true).ravel()
    lower = np.asarray(lower).ravel()
    upper = np.asarray(upper).ravel()

    width = upper - lower
    if y_range is None or y_range <= 0:
        y_range = float(np.max(y_true) - np.min(y_true))
        if y_range == 0:
            y_range = 1.0

    return float(np.mean(width) / y_range)


def compute_cwc(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    nominal_coverage: float = 0.90,
    eta: float = 50.0,
    y_range: Union[float, None] = None,
) -> float:
    """
    Computes Coverage Width-based Criterion (CWC).
    Penalizes narrow intervals that fail to meet nominal coverage target (1 - alpha).
    CWC = NMPIW * (1 + gamma * exp(eta * (nominal_coverage - PICP)))
    where gamma = 1 if PICP < nominal_coverage else 0.
    """
    picp = compute_picp(y_true, lower, upper)
    nmpiw = compute_nmpiw(y_true, lower, upper, y_range)

    if picp < nominal_coverage:
        penalty = np.exp(eta * (nominal_coverage - picp))
        cwc = nmpiw * (1.0 + penalty)
    else:
        cwc = nmpiw

    return float(cwc)


def compute_winkler_score(
    y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray, alpha: float = 0.10
) -> float:
    """
    Computes the Winkler Score (Interval Score) at significance level alpha.
    W_alpha = (upper - lower) + (2 / alpha) * (lower - y) * 1{y < lower}
                              + (2 / alpha) * (y - upper) * 1{y > upper}
    Lower values indicate higher interval calibration and sharpness.
    """
    y_true = np.asarray(y_true).ravel()
    lower = np.asarray(lower).ravel()
    upper = np.asarray(upper).ravel()

    width = upper - lower
    below = np.maximum(0.0, lower - y_true)
    above = np.maximum(0.0, y_true - upper)

    scores = width + (2.0 / alpha) * below + (2.0 / alpha) * above
    return float(np.mean(scores))


def compute_crps_gaussian(y_true: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> float:
    """
    Computes the analytical Continuous Ranked Probability Score (CRPS)
    for Gaussian predictive distributions N(mu, sigma^2).
    """
    y_true = np.asarray(y_true).ravel()
    mu = np.asarray(mu).ravel()
    sigma = np.maximum(np.asarray(sigma).ravel(), 1e-6)

    z = (y_true - mu) / sigma
    pdf_z = norm.pdf(z)
    cdf_z = norm.cdf(z)

    crps = sigma * (z * (2.0 * cdf_z - 1.0) + 2.0 * pdf_z - 1.0 / np.sqrt(np.pi))
    return float(np.mean(crps))


def compute_nll(y_true: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> float:
    """
    Computes Gaussian Negative Log-Likelihood (NLL).
    NLL = 0.5 * mean( ln(2*pi*sigma^2) + (y - mu)^2 / sigma^2 )
    """
    y_true = np.asarray(y_true).ravel()
    mu = np.asarray(mu).ravel()
    sigma2 = np.maximum(np.asarray(sigma).ravel() ** 2, 1e-8)

    nll = 0.5 * (np.log(2 * np.pi * sigma2) + ((y_true - mu) ** 2) / sigma2)
    return float(np.mean(nll))


def compute_point_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes deterministic point evaluation metrics: RMSE, MAE, R^2.
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    ss_res = np.sum((y_true - y_pred) ** 2)
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    return {"rmse": rmse, "mae": mae, "r2": r2}


def evaluate_uq_benchmark(
    y_true: np.ndarray,
    mu: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    sigma: Union[np.ndarray, None] = None,
    nominal_coverage: float = 0.90,
    y_range: Union[float, None] = None,
) -> Dict[str, float]:
    """
    Runs full comprehensive evaluation returning both point and UQ metrics.
    """
    alpha = 1.0 - nominal_coverage
    point_res = compute_point_metrics(y_true, mu)
    picp = compute_picp(y_true, lower, upper)
    nmpiw = compute_nmpiw(y_true, lower, upper, y_range)
    cwc = compute_cwc(y_true, lower, upper, nominal_coverage, y_range=y_range)
    winkler = compute_winkler_score(y_true, lower, upper, alpha=alpha)

    results = {
        **point_res,
        "picp": picp,
        "nmpiw": nmpiw,
        "cwc": cwc,
        "winkler": winkler,
        "nominal_coverage": nominal_coverage,
    }

    if sigma is not None:
        results["crps"] = compute_crps_gaussian(y_true, mu, sigma)
        results["nll"] = compute_nll(y_true, mu, sigma)

    return results
