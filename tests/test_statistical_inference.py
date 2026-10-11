"""Tests for statistical inference protocol and bootstrap missing-group bounds logic."""

from __future__ import annotations

import pytest


def compute_replicate_worst_group_bounds(
    available_errors: list[float] | dict[str, float],
    missing_group_count: int,
    nominal_coverage: float = 0.90,
) -> tuple[float, float]:
    """Compute conservative lower and upper bounds on worst-group coverage error for a replicate.

    Rule:
    If |G_available^(b)| > 0:
        WorstErr_lower^(b) = max over available groups of Err^(b)(g)
    else:
        WorstErr_lower^(b) = 0.0

    Then:
    If |G_missing^(b)| > 0:
        WorstErr_upper^(b) = max(WorstErr_lower^(b), 0.90)
    else:
        WorstErr_upper^(b) = WorstErr_lower^(b)
    """
    if isinstance(available_errors, dict):
        vals = list(available_errors.values())
    else:
        vals = list(available_errors)

    if len(vals) > 0:
        worst_err_lower = max(vals)
    else:
        worst_err_lower = 0.0

    if missing_group_count > 0:
        worst_err_upper = max(worst_err_lower, nominal_coverage)
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
    delta_lower = b_lower - p_upper
    delta_upper = b_upper - p_lower
    return (delta_lower, delta_upper)


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
    # Baseline has [0.05, 0.05], Proposed has [0.02, 0.90] (some group missing in proposed)
    b_bounds = (0.05, 0.05)
    p_bounds = (0.02, 0.90)
    d_lower, d_upper = propagate_delta_error_bounds(b_bounds, p_bounds)
    assert d_lower == pytest.approx(0.05 - 0.90)  # -0.85
    assert d_upper == pytest.approx(0.05 - 0.02)  # +0.03
