"""Engine-weighted empirical and hierarchical quantile computation.

Implements exact rational boundary arithmetic with fast cumulative score scanning.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Any

import numpy as np

from intellitwin.uncertainty.schema import COVERAGE_FRACTIONS


def _validate_inputs(
    engine_ids: np.ndarray[Any, Any],
    endpoint_cycles: np.ndarray[Any, Any],
    scores: np.ndarray[Any, Any],
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Validate engine IDs, endpoint cycles, and score arrays."""
    eids = np.asarray(engine_ids)
    cycles = np.asarray(endpoint_cycles)
    sc = np.asarray(scores, dtype=np.float64)

    if len(sc) == 0:
        raise ValueError("Cannot compute quantiles on empty input.")

    if not (len(eids) == len(cycles) == len(sc)):
        raise ValueError(
            f"Array length mismatch: engine_ids ({len(eids)}), "
            f"endpoint_cycles ({len(cycles)}), scores ({len(sc)})"
        )

    if not np.all(np.isfinite(sc)):
        raise ValueError("Non-finite score encountered in quantile calculation.")
    if np.any(sc < 0.0):
        raise ValueError("Negative score encountered in quantile calculation.")

    # Validate engine IDs are positive integers
    for eid in eids:
        if isinstance(eid, bool) or not isinstance(eid, (int, np.integer)):
            raise ValueError(f"Engine ID must be a positive integer, got: {eid}")
        if int(eid) <= 0:
            raise ValueError(f"Engine ID must be strictly positive, got: {eid}")

    # Validate endpoint cycles are positive integers
    for c in cycles:
        if isinstance(c, bool) or not isinstance(c, (int, np.integer)):
            raise ValueError(f"Endpoint cycle must be a positive integer, got: {c}")
        if int(c) <= 0:
            raise ValueError(f"Endpoint cycle must be strictly positive, got: {c}")

    # Check for duplicate (engine_id, endpoint_cycle) keys
    keys = list(zip(eids, cycles, strict=True))
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate (engine_id, endpoint_cycle) keys detected in quantile input.")

    return eids, cycles, sc


def compute_engine_weighted_dev_quantile(
    engine_ids: np.ndarray[Any, Any],
    endpoint_cycles: np.ndarray[Any, Any],
    scores: np.ndarray[Any, Any],
    nominal_coverage: float,
) -> float:
    """Compute engine-weighted development empirical quantile threshold.

    CDF:
        F_dev(q) = (1 / m) * sum_i [ count(s_it <= q) / n_i ]
    Target:
        Smallest observed score q satisfying F_dev(q) >= nominal_coverage.

    Parameters
    ----------
    engine_ids : np.ndarray
        Contributing engine IDs.
    endpoint_cycles : np.ndarray
        Endpoint cycles for each window.
    scores : np.ndarray
        Nonconformity scores >= 0.
    nominal_coverage : float
        Nominal coverage level (e.g. 0.80, 0.90, 0.95).

    Returns
    -------
    float
        Exact finite non-interpolated quantile threshold.
    """
    eids, cycles, sc = _validate_inputs(engine_ids, endpoint_cycles, scores)

    target_frac = COVERAGE_FRACTIONS.get(nominal_coverage)
    if target_frac is None:
        raise ValueError(
            f"Unsupported nominal coverage: {nominal_coverage}. "
            f"Expected one of {list(COVERAGE_FRACTIONS.keys())}"
        )

    engine_scores: dict[int, list[float]] = defaultdict(list)
    for eid, score_val in zip(eids, sc, strict=True):
        engine_scores[int(eid)].append(float(score_val))

    m = len(engine_scores)
    if m == 0:
        raise ValueError("Zero contributing engines.")

    n_i: dict[int, int] = {eid: len(vals) for eid, vals in engine_scores.items()}
    sorted_engine_scores = {
        eid: np.sort(np.asarray(vals, dtype=np.float64)) for eid, vals in engine_scores.items()
    }

    # Required rational mass: sum_i [ count / n_i ] >= m * target_frac
    required_sum = Fraction(m) * target_frac

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
        cand_idx = len(unique_scores) - 1

    # Verify boundary property
    assert exact_mass(float(unique_scores[cand_idx])) >= required_sum
    if cand_idx > 0:
        assert exact_mass(float(unique_scores[cand_idx - 1])) < required_sum

    return float(unique_scores[cand_idx])


def compute_engine_weighted_hierarchical_quantile(
    engine_ids: np.ndarray[Any, Any],
    endpoint_cycles: np.ndarray[Any, Any],
    scores: np.ndarray[Any, Any],
    nominal_coverage: float,
) -> float:
    """Compute engine-weighted final hierarchical conformal quantile threshold.

    Following Lee, Barber, & Willett (arXiv:2306.06342v4):
        Finite mass: F_final(q) = (1 / (m + 1)) * sum_i [ count(s_it <= q) / n_i ]
        Mass at +infinity: 1 / (m + 1)
    Target:
        Smallest score q satisfying F_final(q) >= nominal_coverage.
        If no finite score satisfies this condition, returns float('inf').

    Parameters
    ----------
    engine_ids : np.ndarray
        Contributing engine IDs.
    endpoint_cycles : np.ndarray
        Endpoint cycles for each window.
    scores : np.ndarray
        Nonconformity scores >= 0.
    nominal_coverage : float
        Nominal coverage level (e.g. 0.80, 0.90, 0.95).

    Returns
    -------
    float
        Exact non-interpolated quantile threshold, or float('inf') if unsupported.
    """
    eids, cycles, sc = _validate_inputs(engine_ids, endpoint_cycles, scores)

    target_frac = COVERAGE_FRACTIONS.get(nominal_coverage)
    if target_frac is None:
        raise ValueError(
            f"Unsupported nominal coverage: {nominal_coverage}. "
            f"Expected one of {list(COVERAGE_FRACTIONS.keys())}"
        )

    # Group scores by engine
    engine_scores: dict[int, list[float]] = defaultdict(list)
    for eid, score_val in zip(eids, sc, strict=True):
        engine_scores[int(eid)].append(float(score_val))

    m = len(engine_scores)
    if m == 0:
        raise ValueError("Zero contributing engines.")

    n_i: dict[int, int] = {eid: len(vals) for eid, vals in engine_scores.items()}

    # Required rational mass: sum_i [ count / n_i ] >= (m + 1) * target_frac
    required_sum = Fraction(m + 1) * target_frac

    # Maximum possible finite mass is m
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

    # Verify boundary property: preceding distinct score strictly below target
    assert exact_mass(float(unique_scores[cand_idx])) >= required_sum
    if cand_idx > 0:
        assert exact_mass(float(unique_scores[cand_idx - 1])) < required_sum

    return float(unique_scores[cand_idx])
