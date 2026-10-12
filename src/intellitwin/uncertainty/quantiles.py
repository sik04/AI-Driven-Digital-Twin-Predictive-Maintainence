"""Engine-weighted empirical and hierarchical quantile computation.

Implements exact rational boundary arithmetic.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction

import numpy as np

from intellitwin.uncertainty.schema import COVERAGE_FRACTIONS


def _validate_inputs(
    engine_ids: np.ndarray,
    endpoint_cycles: np.ndarray,
    scores: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
    engine_ids: np.ndarray,
    endpoint_cycles: np.ndarray,
    scores: np.ndarray,
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

    # Group scores by engine
    engine_scores: dict[int, list[float]] = defaultdict(list)
    for eid, score_val in zip(eids, sc, strict=True):
        engine_scores[int(eid)].append(float(score_val))

    m = len(engine_scores)
    if m == 0:
        raise ValueError("Zero contributing engines.")

    n_i: dict[int, int] = {eid: len(vals) for eid, vals in engine_scores.items()}

    # Unique sorted scores
    unique_scores = np.sort(np.unique(sc))

    # Pre-sort each engine's scores for fast binary search count
    sorted_engine_scores = {
        eid: np.sort(np.asarray(vals, dtype=np.float64)) for eid, vals in engine_scores.items()
    }

    # Exact rational verification
    # Required: sum_i [ count(s_it <= q) / n_i ] >= m * target_frac
    required_sum = Fraction(m) * target_frac

    chosen_threshold: float | None = None
    for idx, q_val in enumerate(unique_scores):
        # Compute exact rational mass sum
        mass_sum = Fraction(0, 1)
        for eid, vals in sorted_engine_scores.items():
            count_le = int(np.searchsorted(vals, q_val, side="right"))
            mass_sum += Fraction(count_le, n_i[eid])

        if mass_sum >= required_sum:
            # Verify boundary property: preceding distinct score strictly below target
            if idx > 0:
                prev_q = unique_scores[idx - 1]
                prev_mass_sum = Fraction(0, 1)
                for eid, vals in sorted_engine_scores.items():
                    count_le = int(np.searchsorted(vals, prev_q, side="right"))
                    prev_mass_sum += Fraction(count_le, n_i[eid])
                if prev_mass_sum >= required_sum:
                    raise RuntimeError(
                        f"Boundary verification failed: prev score {prev_q} already reaches target."
                    )
            chosen_threshold = float(q_val)
            break

    if chosen_threshold is None:
        # Development empirical CDF at max observed score is exactly 1.0 >= target_frac
        chosen_threshold = float(unique_scores[-1])

    return chosen_threshold


def compute_engine_weighted_hierarchical_quantile(
    engine_ids: np.ndarray,
    endpoint_cycles: np.ndarray,
    scores: np.ndarray,
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

    unique_scores = np.sort(np.unique(sc))
    sorted_engine_scores = {
        eid: np.sort(np.asarray(vals, dtype=np.float64)) for eid, vals in engine_scores.items()
    }

    chosen_threshold: float | None = None
    for idx, q_val in enumerate(unique_scores):
        mass_sum = Fraction(0, 1)
        for eid, vals in sorted_engine_scores.items():
            count_le = int(np.searchsorted(vals, q_val, side="right"))
            mass_sum += Fraction(count_le, n_i[eid])

        if mass_sum >= required_sum:
            # Verify boundary property
            if idx > 0:
                prev_q = unique_scores[idx - 1]
                prev_mass_sum = Fraction(0, 1)
                for eid, vals in sorted_engine_scores.items():
                    count_le = int(np.searchsorted(vals, prev_q, side="right"))
                    prev_mass_sum += Fraction(count_le, n_i[eid])
                if prev_mass_sum >= required_sum:
                    raise RuntimeError(
                        f"Boundary verification failed: prev score {prev_q} already reaches target."
                    )
            chosen_threshold = float(q_val)
            break

    if chosen_threshold is None:
        return float("inf")

    return chosen_threshold
