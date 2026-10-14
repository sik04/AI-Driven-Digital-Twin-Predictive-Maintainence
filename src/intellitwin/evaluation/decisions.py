"""Confirmatory decision rules, hypothesis testing logic, and IUT aggregators."""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum


class DecisionStatus(str, Enum):
    """Component-level statistical hypothesis test outcome."""

    PASS = "PASS"
    FAIL = "FAIL"
    INDETERMINATE = "INDETERMINATE"


class RQStatus(str, Enum):
    """Overall Research Question status from Intersection-Union Testing."""

    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    INCONCLUSIVE = "INCONCLUSIVE"


def evaluate_improvement(
    ci_lower: float,
    ci_upper: float,
    margin: float,
) -> DecisionStatus:
    """Evaluate an improvement hypothesis: Delta > margin.

    Rules:
    - Pass if lower bound > margin.
    - Fail if upper bound < margin.
    - Otherwise indeterminate (confidence interval spans margin, or boundary equality).
    - Degenerate zero-width intervals are indeterminate.
    """
    if ci_lower >= ci_upper:
        # Zero-width or inverted interval is indeterminate
        return DecisionStatus.INDETERMINATE

    if ci_lower > margin:
        return DecisionStatus.PASS
    elif ci_upper < margin:
        return DecisionStatus.FAIL
    else:
        return DecisionStatus.INDETERMINATE


def evaluate_noninferiority(
    ci_lower: float,
    ci_upper: float,
    margin: float,
) -> DecisionStatus:
    """Evaluate non-inferiority or upper bound ceiling: Metric < margin.

    Rules:
    - Pass if upper bound < margin.
    - Fail if lower bound > margin.
    - Otherwise indeterminate (confidence interval spans margin, or boundary equality).
    - Degenerate zero-width intervals are indeterminate.
    """
    if ci_lower >= ci_upper:
        return DecisionStatus.INDETERMINATE

    if ci_upper < margin:
        return DecisionStatus.PASS
    elif ci_lower > margin:
        return DecisionStatus.FAIL
    else:
        return DecisionStatus.INDETERMINATE


def evaluate_failure_safeguard(
    observed_proposed_failures: int,
    observed_baseline_failures: int,
) -> DecisionStatus:
    """Evaluate observed failure safeguard over identical evaluation grid.

    Equality passes: proposed failures <= baseline failures.
    """
    if observed_proposed_failures <= observed_baseline_failures:
        return DecisionStatus.PASS
    else:
        return DecisionStatus.FAIL


def aggregate_rq_decision(
    component_statuses: Sequence[DecisionStatus],
) -> RQStatus:
    """Aggregate required component decisions under Intersection-Union Testing (IUT).

    Rules:
    - Any failed required component makes the RQ Unsupported.
    - If none fail and any is indeterminate, the RQ is Inconclusive.
    - Only all-pass makes it Supported.
    - Empty component list is an execution error.
    """
    if len(component_statuses) == 0:
        raise ValueError("Cannot aggregate RQ decision from empty component statuses.")

    if any(s == DecisionStatus.FAIL for s in component_statuses):
        return RQStatus.UNSUPPORTED
    elif any(s == DecisionStatus.INDETERMINATE for s in component_statuses):
        return RQStatus.INCONCLUSIVE
    elif all(s == DecisionStatus.PASS for s in component_statuses):
        return RQStatus.SUPPORTED
    else:
        return RQStatus.INCONCLUSIVE
