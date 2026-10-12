"""Unit tests for engine-weighted empirical and hierarchical quantiles."""

from __future__ import annotations

import math

import numpy as np

from intellitwin.uncertainty.quantiles import (
    compute_engine_weighted_dev_quantile,
    compute_engine_weighted_hierarchical_quantile,
)


def test_unequal_trajectory_lengths_equal_engine_mass() -> None:
    """Verify that an engine with 100 endpoints has equal mass to an engine with 10 endpoints."""
    # Engine 1: 10 endpoints with large scores [10.0 .. 10.0]
    # Engine 2: 100 endpoints with small scores [1.0 .. 1.0]
    eids = np.array([1] * 10 + [2] * 100)
    cycles = np.array(list(range(1, 11)) + list(range(1, 101)))
    scores = np.array([10.0] * 10 + [1.0] * 100)

    # In development quantile at 50% (Fraction(1, 2) <= 0.80 -> test at 80% and 90%):
    # Engine 2 has mass 0.5 for scores <= 1.0.
    # At score 1.0, cumulative mass is 0.5. At 10.0, cumulative mass is 1.0.
    # For coverage 0.80: mass 0.5 < 0.80, so threshold must be 10.0!
    q_dev_80 = compute_engine_weighted_dev_quantile(eids, cycles, scores, 0.80)
    assert q_dev_80 == 10.0


def test_duplicating_endpoints_leaves_distribution_unchanged() -> None:
    """Verify that duplicating all endpoints of an engine does not change the threshold."""
    eids = np.array([1, 1, 2, 2, 3, 3])
    cycles = np.array([1, 2, 1, 2, 1, 2])
    scores = np.array([2.0, 4.0, 6.0, 8.0, 10.0, 12.0])

    q_orig = compute_engine_weighted_dev_quantile(eids, cycles, scores, 0.80)

    # Duplicate engine 1's endpoints: (e.g. simulate double frequency with new dummy cycle indices)
    eids_dup = np.array([1, 1, 1, 1, 2, 2, 3, 3])
    cycles_dup = np.array([1, 2, 3, 4, 1, 2, 1, 2])
    scores_dup = np.array([2.0, 4.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0])

    q_dup = compute_engine_weighted_dev_quantile(eids_dup, cycles_dup, scores_dup, 0.80)
    assert q_orig == q_dup


def test_hand_calculated_development_and_final_quantiles() -> None:
    """Verify exact hand-calculated threshold values on a small controlled fixture."""
    # 3 engines, 1 endpoint each: scores 1.0, 2.0, 3.0
    eids = np.array([1, 2, 3])
    cycles = np.array([1, 1, 1])
    scores = np.array([1.0, 2.0, 3.0])

    # Dev at 80% (4/5): m=3. Required sum = 3 * 4/5 = 12/5 = 2.4.
    # At q=1: count sum = 1 < 2.4
    # At q=2: count sum = 2 < 2.4
    # At q=3: count sum = 3 >= 2.4 -> threshold = 3.0
    q_dev_80 = compute_engine_weighted_dev_quantile(eids, cycles, scores, 0.80)
    assert q_dev_80 == 3.0

    # Hierarchical at 80% (4/5): m=3. (m+1)*4/5 = 4 * 4/5 = 16/5 = 3.2 > 3.
    # Maximum possible sum is 3. Since 3 < 3.2, threshold is INFINITY!
    q_hier_80 = compute_engine_weighted_hierarchical_quantile(eids, cycles, scores, 0.80)
    assert math.isinf(q_hier_80)


def test_one_observation_per_engine_reduction_to_conformal_ranks() -> None:
    """When each engine has 1 observation, matches standard split-conformal rank."""
    # m = 9 engines, scores 10, 20, 30, 40, 50, 60, 70, 80, 90
    m = 9
    eids = np.arange(1, m + 1)
    cycles = np.ones(m, dtype=int)
    scores = np.arange(10, 100, 10, dtype=float)

    # Hierarchical at 90% (9/10): (m+1) * 9/10 = 10 * 9/10 = 9.
    # At score 90: count sum = 9 >= 9. Preceding score 80: count sum = 8 < 9.
    # Threshold must be exactly 90.0!
    q_hier_90 = compute_engine_weighted_hierarchical_quantile(eids, cycles, scores, 0.90)
    assert q_hier_90 == 90.0


def test_finite_infinite_boundary_19_engines_at_95_percent() -> None:
    """Verify rational boundary: 18 engines gives inf at 95%, 19 engines gives finite threshold."""
    # 18 engines:
    eids_18 = np.arange(1, 19)
    cycles_18 = np.ones(18, dtype=int)
    scores_18 = np.arange(1.0, 19.0)

    q_18 = compute_engine_weighted_hierarchical_quantile(eids_18, cycles_18, scores_18, 0.95)
    assert math.isinf(q_18)

    # 19 engines:
    eids_19 = np.arange(1, 20)
    cycles_19 = np.ones(19, dtype=int)
    scores_19 = np.arange(1.0, 20.0)

    q_19 = compute_engine_weighted_hierarchical_quantile(eids_19, cycles_19, scores_19, 0.95)
    assert math.isfinite(q_19)
    assert q_19 == 19.0


def test_tied_scores_handling_no_interpolation() -> None:
    """Verify tied scores form a single boundary without interpolation."""
    eids = np.array([1, 2, 3, 4, 5])
    cycles = np.array([1, 1, 1, 1, 1])
    # Scores have ties: 5.0, 5.0, 5.0, 10.0, 10.0
    scores = np.array([5.0, 5.0, 5.0, 10.0, 10.0])

    q_dev_80 = compute_engine_weighted_dev_quantile(eids, cycles, scores, 0.80)
    # At q=5: mass is 3/5 = 0.60 < 0.80.
    # At q=10: mass is 5/5 = 1.0 >= 0.80.
    assert q_dev_80 == 10.0
    assert q_dev_80 in scores  # exact non-interpolated observed score
