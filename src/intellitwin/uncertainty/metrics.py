"""Engine-weighted uncertainty and interval evaluation metrics."""

from __future__ import annotations

from typing import Any

import numpy as np


def compute_observation_interval_score(
    lower: np.ndarray[Any, Any],
    upper: np.ndarray[Any, Any],
    labels: np.ndarray[Any, Any],
    alpha: float = 0.10,
) -> np.ndarray[Any, Any]:
    """Compute central interval score for each observation.

    Formula:
        IS = (U - L)
             + (2 / alpha) * (L - y) * I(y < L)
             + (2 / alpha) * (y - U) * I(y > U)
    """
    l_arr = np.asarray(lower, dtype=np.float64)
    u_arr = np.asarray(upper, dtype=np.float64)
    y_arr = np.asarray(labels, dtype=np.float64)

    width = u_arr - l_arr
    under_miss = np.maximum(0.0, l_arr - y_arr)
    over_miss = np.maximum(0.0, y_arr - u_arr)

    score = width + (2.0 / alpha) * under_miss + (2.0 / alpha) * over_miss
    return np.asarray(score, dtype=np.float64)


def compute_engine_weighted_interval_metrics(
    engine_ids: np.ndarray[Any, Any],
    endpoint_cycles: np.ndarray[Any, Any],
    labels: np.ndarray[Any, Any],
    lower: np.ndarray[Any, Any],
    upper: np.ndarray[Any, Any],
    regimes: np.ndarray[Any, Any] | None = None,
    alpha: float = 0.10,
) -> dict[str, Any]:
    """Compute engine-weighted interval performance metrics.

    Parameters
    ----------
    engine_ids : np.ndarray
        Engine ID for each window.
    endpoint_cycles : np.ndarray
        Endpoint cycle for each window.
    labels : np.ndarray
        True RUL targets y >= 0.
    lower : np.ndarray
        Interval lower bounds L.
    upper : np.ndarray
        Interval upper bounds U.
    regimes : np.ndarray, optional
        Regime labels for regime-specific PICP computation.
    alpha : float, default 0.10
        Significance level for interval score (1 - coverage).

    Returns
    -------
    dict[str, Any]
        Dictionary containing marginal_picp, mpiw, interval_score,
        lower_miss_rate, upper_miss_rate, and regime_picp.
    """
    eids = np.asarray(engine_ids)
    y = np.asarray(labels, dtype=np.float64)
    l_arr = np.asarray(lower, dtype=np.float64)
    u_arr = np.asarray(upper, dtype=np.float64)

    obs_covered = (y >= l_arr) & (y <= u_arr)
    obs_lower_miss = y < l_arr
    obs_upper_miss = y > u_arr
    obs_width = u_arr - l_arr
    obs_is = compute_observation_interval_score(l_arr, u_arr, y, alpha=alpha)

    # Group by engine
    unique_eids = sorted(set(eids))
    m = len(unique_eids)

    engine_picp: list[float] = []
    engine_mpiw: list[float] = []
    engine_is: list[float] = []
    engine_lower_miss: list[float] = []
    engine_upper_miss: list[float] = []

    for eid in unique_eids:
        mask = eids == eid
        engine_picp.append(float(np.mean(obs_covered[mask])))
        engine_mpiw.append(float(np.mean(obs_width[mask])))
        engine_is.append(float(np.mean(obs_is[mask])))
        engine_lower_miss.append(float(np.mean(obs_lower_miss[mask])))
        engine_upper_miss.append(float(np.mean(obs_upper_miss[mask])))

    marginal_picp = float(np.mean(engine_picp))
    mean_mpiw = float(np.mean(engine_mpiw))
    mean_is = float(np.mean(engine_is))
    mean_lower_miss = float(np.mean(engine_lower_miss))
    mean_upper_miss = float(np.mean(engine_upper_miss))

    metrics: dict[str, Any] = {
        "marginal_picp": marginal_picp,
        "mpiw": mean_mpiw,
        "interval_score": mean_is,
        "lower_miss_rate": mean_lower_miss,
        "upper_miss_rate": mean_upper_miss,
        "m_engines": m,
        "n_endpoints": len(y),
    }

    # Regime coverage if regimes provided
    if regimes is not None:
        reg_arr = np.asarray(regimes, dtype=object)
        unique_regimes = sorted(set(reg_arr))
        regime_picp_dict: dict[str, float] = {}
        regime_engine_counts: dict[str, int] = {}

        for reg in unique_regimes:
            reg_mask = reg_arr == reg
            reg_eids = eids[reg_mask]
            reg_covered = obs_covered[reg_mask]
            unique_reg_eids = sorted(set(reg_eids))
            regime_engine_counts[str(reg)] = len(unique_reg_eids)

            if len(unique_reg_eids) == 0:
                continue

            eng_covs: list[float] = []
            for eid in unique_reg_eids:
                eid_mask = reg_eids == eid
                eng_covs.append(float(np.mean(reg_covered[eid_mask])))

            regime_picp_dict[str(reg)] = float(np.mean(eng_covs))

        metrics["regime_picp"] = regime_picp_dict
        metrics["regime_engine_counts"] = regime_engine_counts

    return metrics
