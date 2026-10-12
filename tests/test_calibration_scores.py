"""Unit tests for calibration scores, asymmetry factors, and interval inversion."""

from __future__ import annotations

import numpy as np
import pytest

from intellitwin.uncertainty.schema import (
    ALL_NINE_CANDIDATES,
    CandidateConfig,
)
from intellitwin.uncertainty.scores import (
    compute_absolute_residual_score,
    compute_decision_aware_score,
    invert_score_to_interval,
)


def test_identity_proposed_score_equals_absolute_residual() -> None:
    """Verify that candidate gamma0_beta0 produces scores identical to |y - p|."""
    p = np.array([0.0, 10.0, 25.5, 50.0, 100.0, 125.0, 150.0], dtype=np.float64)
    y = np.array([5.0, 12.0, 20.0, 50.0, 95.0, 130.0, 120.0], dtype=np.float64)

    identity_cand = CandidateConfig.from_id("gamma0_beta0")
    da_scores = compute_decision_aware_score(p, y, identity_cand)
    abs_scores = compute_absolute_residual_score(p, y)

    np.testing.assert_allclose(da_scores, abs_scores, rtol=1e-12, atol=1e-12)


def test_exact_lower_upper_score_inversion() -> None:
    """Verify that score(p, y) <= q is exactly equivalent to L <= y <= U."""
    p = np.array([10.0, 25.0, 50.0, 100.0], dtype=np.float64)
    threshold = 5.0

    for cand in ALL_NINE_CANDIDATES:
        lower, upper = invert_score_to_interval(p, threshold, cand)

        # Invariant 0 <= lower <= p <= upper
        assert np.all(lower >= 0.0)
        assert np.all(lower <= p + 1e-9)
        assert np.all(upper >= p - 1e-9)

        # Verify boundary scores: at y = upper, score should equal threshold
        score_at_upper = compute_decision_aware_score(p, upper, cand)
        np.testing.assert_allclose(score_at_upper, threshold, rtol=1e-10, atol=1e-10)

        # At y = lower (when lower > 0), score should equal threshold
        pos_mask = lower > 0.0
        if np.any(pos_mask):
            score_at_lower = compute_decision_aware_score(p[pos_mask], lower[pos_mask], cand)
            np.testing.assert_allclose(score_at_lower, threshold, rtol=1e-10, atol=1e-10)


def test_no_upper_cap_at_125() -> None:
    """Verify that upper bounds are never artificially capped at 125."""
    p = np.array([120.0, 130.0], dtype=np.float64)
    threshold = 20.0
    cand = CandidateConfig.from_id("gamma1_betap1")
    lower, upper = invert_score_to_interval(p, threshold, cand)

    assert np.all(upper > 125.0)


def test_input_validation_and_rejections() -> None:
    """Verify negative, non-finite, or mismatched inputs are rejected."""
    p = np.array([10.0, 20.0])
    y_neg = np.array([10.0, -5.0])
    y_nan = np.array([10.0, np.nan])
    y_inf = np.array([10.0, np.inf])

    with pytest.raises(ValueError, match="Negative labels"):
        compute_absolute_residual_score(p, y_neg)

    with pytest.raises(ValueError, match="Non-finite labels"):
        compute_absolute_residual_score(p, y_nan)

    with pytest.raises(ValueError, match="Non-finite labels"):
        compute_absolute_residual_score(p, y_inf)

    with pytest.raises(ValueError, match="Negative predictions"):
        compute_absolute_residual_score(np.array([-1.0, 10.0]), p)
