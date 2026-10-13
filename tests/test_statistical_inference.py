"""Tests for statistical inference protocol, decision logic, and bootstrap methods."""

from __future__ import annotations

import numpy as np
import pytest

from intellitwin.evaluation.bootstrap import (
    generate_stratified_bootstrap_draws,
    load_partition_quartile_strata,
)
from intellitwin.evaluation.decisions import (
    DecisionStatus,
    RQStatus,
    aggregate_rq_decision,
    evaluate_failure_safeguard,
    evaluate_improvement,
    evaluate_noninferiority,
)
from intellitwin.evaluation.metrics import (
    compute_interval_score,
    compute_replicate_worst_group_bounds,
    propagate_delta_error_bounds,
)


def test_no_groups_missing() -> None:
    """When all eligible groups are available, upper and lower bounds equal the exact max."""
    errors = {"group_1": 0.02, "group_2": 0.045, "group_3": 0.015}
    lower, upper = compute_replicate_worst_group_bounds(errors, missing_group_count=0)
    assert lower == pytest.approx(0.045)
    assert upper == pytest.approx(0.045)


def test_some_groups_missing() -> None:
    """When some groups are missing, lower bound is max available, upper is max(avail, 0.90)."""
    errors = {"group_1": 0.03, "group_2": 0.02}
    lower, upper = compute_replicate_worst_group_bounds(errors, missing_group_count=2)
    assert lower == pytest.approx(0.03)
    assert upper == pytest.approx(0.90)


def test_all_eligible_groups_missing() -> None:
    """When every eligible group is missing, bounds are [0.0, 0.90] with no max(empty) error."""
    errors: list[float] = []
    lower, upper = compute_replicate_worst_group_bounds(errors, missing_group_count=6)
    assert lower == 0.0
    assert upper == 0.90


def test_exactly_one_available_group() -> None:
    """When exactly one group is available and none missing, bounds equal that group's error."""
    errors = [0.032]
    lower, upper = compute_replicate_worst_group_bounds(errors, missing_group_count=0)
    assert lower == pytest.approx(0.032)
    assert upper == pytest.approx(0.032)


def test_exactly_one_available_group_with_missing() -> None:
    """When exactly one group is available and some missing, lower is that error, upper is 0.90."""
    errors = [0.032]
    lower, upper = compute_replicate_worst_group_bounds(errors, missing_group_count=3)
    assert lower == pytest.approx(0.032)
    assert upper == pytest.approx(0.90)


def test_deterministic_result_for_identical_inputs() -> None:
    """Identical inputs must yield identical results across repeated evaluations."""
    errors = {"regime_1": 0.04, "regime_2": 0.01, "regime_3": 0.025}
    res1 = compute_replicate_worst_group_bounds(errors, missing_group_count=1)
    res2 = compute_replicate_worst_group_bounds(errors, missing_group_count=1)
    assert res1 == res2
    assert res1 == (0.04, 0.90)


def test_delta_error_bound_propagation() -> None:
    """Verify conservative subtraction propagation for Delta_error."""
    b_bounds = (0.05, 0.05)
    p_bounds = (0.02, 0.90)
    d_lower, d_upper = propagate_delta_error_bounds(b_bounds, p_bounds)
    assert d_lower == pytest.approx(0.05 - 0.90)
    assert d_upper == pytest.approx(0.05 - 0.02)


def test_decision_improvement_rules() -> None:
    """Verify improvement hypothesis decisions."""
    # Pass: lower bound > margin
    assert evaluate_improvement(0.25, 0.50, margin=0.20) == DecisionStatus.PASS

    # Fail: upper bound < margin
    assert evaluate_improvement(0.05, 0.15, margin=0.20) == DecisionStatus.FAIL

    # Indeterminate: CI spans margin
    assert evaluate_improvement(0.15, 0.25, margin=0.20) == DecisionStatus.INDETERMINATE

    # Boundary equality is indeterminate
    assert evaluate_improvement(0.20, 0.30, margin=0.20) == DecisionStatus.INDETERMINATE
    assert evaluate_improvement(0.10, 0.20, margin=0.20) == DecisionStatus.INDETERMINATE

    # Degenerate zero-width interval is indeterminate
    assert evaluate_improvement(0.25, 0.25, margin=0.20) == DecisionStatus.INDETERMINATE


def test_decision_noninferiority_rules() -> None:
    """Verify noninferiority / ceiling hypothesis decisions."""
    # Pass: upper bound < margin
    assert evaluate_noninferiority(0.01, 0.04, margin=0.05) == DecisionStatus.PASS

    # Fail: lower bound > margin
    assert evaluate_noninferiority(0.06, 0.08, margin=0.05) == DecisionStatus.FAIL

    # Indeterminate: CI spans margin
    assert evaluate_noninferiority(0.03, 0.07, margin=0.05) == DecisionStatus.INDETERMINATE

    # Boundary equality is indeterminate
    assert evaluate_noninferiority(0.02, 0.05, margin=0.05) == DecisionStatus.INDETERMINATE
    assert evaluate_noninferiority(0.05, 0.08, margin=0.05) == DecisionStatus.INDETERMINATE

    # Degenerate zero-width interval is indeterminate
    assert evaluate_noninferiority(0.03, 0.03, margin=0.05) == DecisionStatus.INDETERMINATE


def test_failure_safeguard() -> None:
    """Verify observed failure safeguard logic."""
    # Strict improvement passes
    assert (
        evaluate_failure_safeguard(observed_proposed_failures=2, observed_baseline_failures=5)
        == DecisionStatus.PASS
    )
    # Equality passes
    assert (
        evaluate_failure_safeguard(observed_proposed_failures=5, observed_baseline_failures=5)
        == DecisionStatus.PASS
    )
    # Increase fails
    assert (
        evaluate_failure_safeguard(observed_proposed_failures=6, observed_baseline_failures=5)
        == DecisionStatus.FAIL
    )


def test_iut_rq_decision_aggregation() -> None:
    """Verify Intersection-Union Testing aggregation."""
    # All PASS -> SUPPORTED
    all_pass = [DecisionStatus.PASS, DecisionStatus.PASS, DecisionStatus.PASS]
    assert aggregate_rq_decision(all_pass) == RQStatus.SUPPORTED

    # Any FAIL -> UNSUPPORTED (even if some PASS)
    with_fail = [DecisionStatus.PASS, DecisionStatus.FAIL, DecisionStatus.PASS]
    assert aggregate_rq_decision(with_fail) == RQStatus.UNSUPPORTED

    # None FAIL, any INDETERMINATE -> INCONCLUSIVE
    with_indet = [DecisionStatus.PASS, DecisionStatus.INDETERMINATE, DecisionStatus.PASS]
    assert aggregate_rq_decision(with_indet) == RQStatus.INCONCLUSIVE

    # Empty list raises ValueError
    with pytest.raises(ValueError):
        aggregate_rq_decision([])


def test_stratified_bootstrap_draws_properties() -> None:
    """Verify deterministic draws, multiplicity retention, and stratum stratification."""
    # Use FD002 validation engines (26 engines)
    valid_engs = list(range(1, 27))
    strata = load_partition_quartile_strata("FD002", valid_engs)
    assert len(strata) == 4
    draws = generate_stratified_bootstrap_draws("FD002", valid_engs, n_replicates=50)

    assert draws.shape == (50, 26)

    # Multiplicity check: duplicate engines should appear in resampled rows
    has_duplicates = any(len(set(row)) < 26 for row in draws)
    assert has_duplicates, "Stratified bootstrap must retain duplicate multiplicity."

    # Repeat call produces bit-for-bit identical draws
    draws2 = generate_stratified_bootstrap_draws("FD002", valid_engs, n_replicates=50)
    assert np.array_equal(draws, draws2)


def test_winkler_interval_score_calculation() -> None:
    """Verify interval score calculation on known test vectors."""
    y = np.array([50.0, 10.0, 90.0])
    lower = np.array([20.0, 20.0, 20.0])
    upper = np.array([80.0, 80.0, 80.0])

    # alpha = 0.10 -> 2/alpha = 20
    # Point 0: 50 in [20, 80] -> score = 60
    # Point 1: 10 < 20 -> score = 60 + 20 * (20 - 10) = 60 + 200 = 260
    # Point 2: 90 > 80 -> score = 60 + 20 * (90 - 80) = 60 + 200 = 260
    scores = compute_interval_score(y, lower, upper, nominal_coverage=0.90)
    expected = np.array([60.0, 260.0, 260.0])
    assert np.allclose(scores, expected)
