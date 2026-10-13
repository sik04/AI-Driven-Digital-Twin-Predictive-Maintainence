"""Nonconformity score functions and interval inversion for conformal calibration."""

from __future__ import annotations

from typing import Any

import numpy as np

from intellitwin.uncertainty.schema import (
    SIGMA_SCALE,
    Z_SCALE,
    CandidateConfig,
)


def compute_absolute_residual_score(
    predictions: np.ndarray[Any, Any],
    labels: np.ndarray[Any, Any],
) -> np.ndarray[Any, Any]:
    """Compute standard absolute residual score s = |y - p|.

    Parameters
    ----------
    predictions : np.ndarray
        Array of point predictions p >= 0.
    labels : np.ndarray
        Array of true RUL targets y >= 0.

    Returns
    -------
    np.ndarray
        Array of scores s >= 0 with dtype float64.
    """
    p = np.asarray(predictions, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)

    if p.shape != y.shape:
        raise ValueError(f"Shape mismatch: predictions {p.shape} != labels {y.shape}")
    if not np.all(np.isfinite(p)):
        raise ValueError("Non-finite predictions encountered in score calculation.")
    if not np.all(np.isfinite(y)):
        raise ValueError("Non-finite labels encountered in score calculation.")
    if np.any(p < 0.0):
        raise ValueError("Negative predictions encountered in score calculation.")
    if np.any(y < 0.0):
        raise ValueError("Negative labels encountered in score calculation.")

    return np.abs(y - p)


def compute_shape_factors(
    predictions: np.ndarray[Any, Any],
    gamma: int,
    beta: float,
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Compute asymmetric scale and asymmetry factors a(p) and b(p).

    Equations:
        sigma(p) = (1 + p / 125.0)^gamma
        z(p) = exp(-p / 20.0)
        a(p) = sigma(p) * exp(beta * z(p))
        b(p) = sigma(p) * exp(-beta * z(p))

    Parameters
    ----------
    predictions : np.ndarray
        Array of point predictions p >= 0.
    gamma : int
        Scaling exponent (0, 1, or 2).
    beta : float
        Asymmetry coefficient.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (a(p), b(p)) factors, both strictly positive float64 arrays.
    """
    p = np.asarray(predictions, dtype=np.float64)
    if not np.all(np.isfinite(p)):
        raise ValueError("Non-finite predictions encountered in compute_shape_factors.")
    if np.any(p < 0.0):
        raise ValueError("Negative predictions encountered in compute_shape_factors.")

    # sigma(p) = (1 + p / 125)^gamma
    if gamma == 0:
        sigma_p = np.ones_like(p)
    elif gamma == 1:
        sigma_p = 1.0 + (p / SIGMA_SCALE)
    elif gamma == 2:
        base = 1.0 + (p / SIGMA_SCALE)
        sigma_p = base * base
    else:
        sigma_p = (1.0 + (p / SIGMA_SCALE)) ** gamma

    z_p = np.exp(-p / Z_SCALE)
    exp_pos = np.exp(beta * z_p)
    exp_neg = np.exp(-beta * z_p)

    a_p = sigma_p * exp_pos
    b_p = sigma_p * exp_neg

    return a_p, b_p


def compute_decision_aware_score(
    predictions: np.ndarray[Any, Any],
    labels: np.ndarray[Any, Any],
    candidate: CandidateConfig,
) -> np.ndarray[Any, Any]:
    """Compute proposed decision-aware asymmetric nonconformity score.

    Score Equation:
        score(p, y) = max((p - y) / a(p), (y - p) / b(p), 0)

    When gamma=0, beta=0, a(p)=1, b(p)=1:
        score(p, y) == |y - p| (numerically matches absolute residual).

    Parameters
    ----------
    predictions : np.ndarray
        Array of point predictions p >= 0.
    labels : np.ndarray
        Array of true RUL targets y >= 0.
    candidate : CandidateConfig
        Candidate parameter configuration.

    Returns
    -------
    np.ndarray
        Array of nonconformity scores >= 0 with dtype float64.
    """
    p = np.asarray(predictions, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)

    if p.shape != y.shape:
        raise ValueError(f"Shape mismatch: predictions {p.shape} != labels {y.shape}")
    if not np.all(np.isfinite(p)):
        raise ValueError("Non-finite predictions encountered in decision-aware score calculation.")
    if not np.all(np.isfinite(y)):
        raise ValueError("Non-finite labels encountered in decision-aware score calculation.")
    if np.any(p < 0.0):
        raise ValueError("Negative predictions encountered in decision-aware score calculation.")
    if np.any(y < 0.0):
        raise ValueError("Negative labels encountered in decision-aware score calculation.")

    a_p, b_p = compute_shape_factors(p, gamma=candidate.gamma, beta=candidate.beta)

    score_lower = (p - y) / a_p
    score_upper = (y - p) / b_p

    scores = np.maximum(np.maximum(score_lower, score_upper), 0.0)
    return np.asarray(scores, dtype=np.float64)


def invert_score_to_interval(
    predictions: np.ndarray[Any, Any],
    threshold: float | np.ndarray[Any, Any],
    candidate: CandidateConfig | None = None,
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Invert nonconformity score threshold to prediction interval bounds [L, U].

    For standard residual score (candidate is None or identity):
        L = max(0, p - q)
        U = p + q

    For decision-aware score:
        L = max(0, p - q * a(p))
        U = p + q * b(p)

    Parameters
    ----------
    predictions : np.ndarray
        Point predictions p >= 0.
    threshold : float or np.ndarray
        Fitted quantile threshold(s) q >= 0.
    candidate : CandidateConfig, optional
        Candidate configuration. If None, uses a(p)=1, b(p)=1.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (lower_bounds, upper_bounds) with 0 <= L <= p <= U.
    """
    p = np.asarray(predictions, dtype=np.float64)
    q = np.asarray(threshold, dtype=np.float64)

    if not np.all(np.isfinite(p)):
        raise ValueError("Non-finite predictions encountered in interval inversion.")
    if np.any(p < 0.0):
        raise ValueError("Negative predictions encountered in interval inversion.")
    if not np.all(np.isfinite(q)):
        raise ValueError("Non-finite threshold encountered in interval inversion.")
    if np.any(q < 0.0):
        raise ValueError("Negative threshold encountered in interval inversion.")

    if candidate is None or (candidate.gamma == 0 and candidate.beta_code == 0):
        a_p = np.ones_like(p)
        b_p = np.ones_like(p)
    else:
        a_p, b_p = compute_shape_factors(p, gamma=candidate.gamma, beta=candidate.beta)

    lower = np.maximum(0.0, p - q * a_p)
    upper = p + q * b_p

    return np.asarray(lower, dtype=np.float64), np.asarray(upper, dtype=np.float64)
