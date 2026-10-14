"""Confirmatory decision rules, hypothesis testing logic, and IUT aggregators."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any


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


@dataclass(frozen=True)
class HypothesisComponent:
    """Specification of an authoritative, immutable hypothesis test component."""

    component_id: str
    rq_id: str
    model_family: str | None
    dataset: str | None
    comparator: str
    metric: str
    rule_type: str  # "improvement", "noninferiority", "failure_safeguard"
    margin: float
    description: str


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
    - Degenerate zero-width intervals (lower == upper) are indeterminate.
    - Inverted intervals (lower > upper) raise ValueError.
    """
    if not math.isfinite(ci_lower) or not math.isfinite(ci_upper) or not math.isfinite(margin):
        raise ValueError(
            f"Non-finite input in evaluate_improvement: "
            f"lower={ci_lower}, upper={ci_upper}, margin={margin}"
        )
    if ci_lower > ci_upper:
        raise ValueError(f"Inverted confidence interval: lower ({ci_lower}) > upper ({ci_upper})")
    if ci_lower == ci_upper:
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
    - Degenerate zero-width intervals (lower == upper) are indeterminate.
    - Inverted intervals (lower > upper) raise ValueError.
    """
    if not math.isfinite(ci_lower) or not math.isfinite(ci_upper) or not math.isfinite(margin):
        raise ValueError(
            f"Non-finite input in evaluate_noninferiority: "
            f"lower={ci_lower}, upper={ci_upper}, margin={margin}"
        )
    if ci_lower > ci_upper:
        raise ValueError(f"Inverted confidence interval: lower ({ci_lower}) > upper ({ci_upper})")
    if ci_lower == ci_upper:
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
    Rejects negative failure counts and boolean types.
    """
    if isinstance(observed_proposed_failures, bool) or isinstance(observed_baseline_failures, bool):
        raise ValueError("Failure counts must not be boolean.")
    if observed_proposed_failures < 0 or observed_baseline_failures < 0:
        raise ValueError("Failure counts must be non-negative integers.")

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


def get_rq_component_manifest() -> dict[str, list[HypothesisComponent]]:
    """Return machine-readable manifest of all required hypothesis test components."""
    manifest: dict[str, list[HypothesisComponent]] = {
        "RQ1": [],
        "RQ2": [],
        "RQ3": [],
        "RQ4": [],
    }

    # RQ1: FD002, both models (GBR, LSTM), both baselines (global_hcp, regime_hcp)
    for fam in ("GBR", "LSTM"):
        for base in ("global_hcp", "regime_hcp"):
            manifest["RQ1"].append(
                HypothesisComponent(
                    component_id=f"RQ1_{fam}_{base}_cost_improvement",
                    rq_id="RQ1",
                    model_family=fam,
                    dataset="FD002",
                    comparator=base,
                    metric="delta_cost",
                    rule_type="improvement",
                    margin=0.20,
                    description=f"{fam} maintenance cost improvement over {base} > 0.20 SCU",
                )
            )
            manifest["RQ1"].append(
                HypothesisComponent(
                    component_id=f"RQ1_{fam}_{base}_failure_safeguard",
                    rq_id="RQ1",
                    model_family=fam,
                    dataset="FD002",
                    comparator=base,
                    metric="failure_count",
                    rule_type="failure_safeguard",
                    margin=0.0,
                    description=(
                        f"{fam} failure safeguard vs {base} "
                        f"(proposed failures <= baseline failures)"
                    ),
                )
            )
        # Proposed coverage ceilings
        manifest["RQ1"].append(
            HypothesisComponent(
                component_id=f"RQ1_{fam}_marginal_coverage_ceiling",
                rq_id="RQ1",
                model_family=fam,
                dataset="FD002",
                comparator="nominal_90",
                metric="marginal_coverage_abs_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{fam} proposed marginal coverage error < 0.05",
            )
        )
        manifest["RQ1"].append(
            HypothesisComponent(
                component_id=f"RQ1_{fam}_worst_regime_coverage_ceiling",
                rq_id="RQ1",
                model_family=fam,
                dataset="FD002",
                comparator="nominal_90",
                metric="worst_regime_coverage_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{fam} proposed worst-regime coverage error < 0.05",
            )
        )
        manifest["RQ1"].append(
            HypothesisComponent(
                component_id=f"RQ1_{fam}_worst_stage_coverage_ceiling",
                rq_id="RQ1",
                model_family=fam,
                dataset="FD002",
                comparator="nominal_90",
                metric="worst_stage_coverage_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{fam} proposed worst-stage coverage error < 0.05",
            )
        )

    # RQ2: FD002, both models, both baselines, both subgroup families (regime, stage)
    for fam in ("GBR", "LSTM"):
        for base in ("global_hcp", "regime_hcp"):
            manifest["RQ2"].append(
                HypothesisComponent(
                    component_id=f"RQ2_{fam}_{base}_regime_error_improvement",
                    rq_id="RQ2",
                    model_family=fam,
                    dataset="FD002",
                    comparator=base,
                    metric="delta_regime_error",
                    rule_type="improvement",
                    margin=0.01,
                    description=f"{fam} worst-regime coverage error improvement over {base} > 0.01",
                )
            )
            manifest["RQ2"].append(
                HypothesisComponent(
                    component_id=f"RQ2_{fam}_{base}_stage_error_improvement",
                    rq_id="RQ2",
                    model_family=fam,
                    dataset="FD002",
                    comparator=base,
                    metric="delta_stage_error",
                    rule_type="improvement",
                    margin=0.01,
                    description=f"{fam} worst-stage coverage error improvement over {base} > 0.01",
                )
            )
            manifest["RQ2"].append(
                HypothesisComponent(
                    component_id=f"RQ2_{fam}_{base}_mpiw_safeguard",
                    rq_id="RQ2",
                    model_family=fam,
                    dataset="FD002",
                    comparator=base,
                    metric="mpiw_deterioration",
                    rule_type="noninferiority",
                    margin=1.0,
                    description=f"{fam} MPIW deterioration vs {base} < 1.0 cycle",
                )
            )
            manifest["RQ2"].append(
                HypothesisComponent(
                    component_id=f"RQ2_{fam}_{base}_interval_score_safeguard",
                    rq_id="RQ2",
                    model_family=fam,
                    dataset="FD002",
                    comparator=base,
                    metric="interval_score_deterioration",
                    rule_type="noninferiority",
                    margin=1.0,
                    description=f"{fam} interval score deterioration vs {base} < 1.0 cycle",
                )
            )
        # Proposed subgroup error ceilings
        manifest["RQ2"].append(
            HypothesisComponent(
                component_id=f"RQ2_{fam}_worst_regime_ceiling",
                rq_id="RQ2",
                model_family=fam,
                dataset="FD002",
                comparator="nominal_90",
                metric="worst_regime_coverage_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{fam} proposed worst-regime coverage error < 0.05",
            )
        )
        manifest["RQ2"].append(
            HypothesisComponent(
                component_id=f"RQ2_{fam}_worst_stage_ceiling",
                rq_id="RQ2",
                model_family=fam,
                dataset="FD002",
                comparator="nominal_90",
                metric="worst_stage_coverage_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{fam} proposed worst-stage coverage error < 0.05",
            )
        )

    # RQ3: FD002, both models, all 4 controls
    ctrl_names = [
        "matched_width_interval",
        "widened_interval",
        "point_safety_margin",
        "earlier_intervention",
    ]
    for fam in ("GBR", "LSTM"):
        for ctrl in ctrl_names:
            manifest["RQ3"].append(
                HypothesisComponent(
                    component_id=f"RQ3_{fam}_{ctrl}_cost_improvement",
                    rq_id="RQ3",
                    model_family=fam,
                    dataset="FD002",
                    comparator=ctrl,
                    metric="delta_cost",
                    rule_type="improvement",
                    margin=0.20,
                    description=(
                        f"{fam} maintenance cost improvement over control {ctrl} > 0.20 SCU"
                    ),
                )
            )
            manifest["RQ3"].append(
                HypothesisComponent(
                    component_id=f"RQ3_{fam}_{ctrl}_failure_safeguard",
                    rq_id="RQ3",
                    model_family=fam,
                    dataset="FD002",
                    comparator=ctrl,
                    metric="failure_count",
                    rule_type="failure_safeguard",
                    margin=0.0,
                    description=(
                        f"{fam} failure safeguard vs control {ctrl} "
                        f"(proposed failures <= control failures)"
                    ),
                )
            )
        # Proposed coverage ceilings
        manifest["RQ3"].append(
            HypothesisComponent(
                component_id=f"RQ3_{fam}_marginal_coverage_ceiling",
                rq_id="RQ3",
                model_family=fam,
                dataset="FD002",
                comparator="nominal_90",
                metric="marginal_coverage_abs_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{fam} proposed marginal coverage error < 0.05",
            )
        )
        manifest["RQ3"].append(
            HypothesisComponent(
                component_id=f"RQ3_{fam}_worst_regime_coverage_ceiling",
                rq_id="RQ3",
                model_family=fam,
                dataset="FD002",
                comparator="nominal_90",
                metric="worst_regime_coverage_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{fam} proposed worst-regime coverage error < 0.05",
            )
        )
        manifest["RQ3"].append(
            HypothesisComponent(
                component_id=f"RQ3_{fam}_worst_stage_coverage_ceiling",
                rq_id="RQ3",
                model_family=fam,
                dataset="FD002",
                comparator="nominal_90",
                metric="worst_stage_coverage_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{fam} proposed worst-stage coverage error < 0.05",
            )
        )

    # RQ4: 6 cells (FD001/GBR, FD001/LSTM, FD002/GBR, FD002/LSTM, FD004/GBR, FD004/LSTM), weight 1/6
    cells = [
        ("FD001", "GBR"),
        ("FD001", "LSTM"),
        ("FD002", "GBR"),
        ("FD002", "LSTM"),
        ("FD004", "GBR"),
        ("FD004", "LSTM"),
    ]
    for base in ("global_hcp", "regime_hcp"):
        # Aggregate benefits
        manifest["RQ4"].append(
            HypothesisComponent(
                component_id=f"RQ4_aggregate_{base}_cost_improvement",
                rq_id="RQ4",
                model_family=None,
                dataset=None,
                comparator=base,
                metric="aggregate_delta_cost",
                rule_type="improvement",
                margin=0.20,
                description=f"Equal-cell aggregate cost improvement over {base} > 0.20 SCU",
            )
        )
        manifest["RQ4"].append(
            HypothesisComponent(
                component_id=f"RQ4_aggregate_{base}_regime_error_improvement",
                rq_id="RQ4",
                model_family=None,
                dataset=None,
                comparator=base,
                metric="aggregate_delta_regime_error",
                rule_type="improvement",
                margin=0.01,
                description=(
                    f"Equal-cell aggregate worst-regime error improvement over {base} > 0.01"
                ),
            )
        )
        manifest["RQ4"].append(
            HypothesisComponent(
                component_id=f"RQ4_aggregate_{base}_stage_error_improvement",
                rq_id="RQ4",
                model_family=None,
                dataset=None,
                comparator=base,
                metric="aggregate_delta_stage_error",
                rule_type="improvement",
                margin=0.01,
                description=(
                    f"Equal-cell aggregate worst-stage error improvement over {base} > 0.01"
                ),
            )
        )

    # Cell-level non-harm conditions and safeguards
    for ds, fam in cells:
        for base in ("global_hcp", "regime_hcp"):
            manifest["RQ4"].append(
                HypothesisComponent(
                    component_id=f"RQ4_cell_{ds}_{fam}_{base}_non_harm_cost",
                    rq_id="RQ4",
                    model_family=fam,
                    dataset=ds,
                    comparator=base,
                    metric="cell_delta_cost",
                    rule_type="improvement",
                    margin=-0.20,
                    description=f"{ds}/{fam} cost contrast vs {base} > -0.20 SCU (non-harm)",
                )
            )
            manifest["RQ4"].append(
                HypothesisComponent(
                    component_id=f"RQ4_cell_{ds}_{fam}_{base}_non_harm_regime_error",
                    rq_id="RQ4",
                    model_family=fam,
                    dataset=ds,
                    comparator=base,
                    metric="cell_delta_regime_error",
                    rule_type="improvement",
                    margin=-0.01,
                    description=f"{ds}/{fam} regime error contrast vs {base} > -0.01 (non-harm)",
                )
            )
            manifest["RQ4"].append(
                HypothesisComponent(
                    component_id=f"RQ4_cell_{ds}_{fam}_{base}_non_harm_stage_error",
                    rq_id="RQ4",
                    model_family=fam,
                    dataset=ds,
                    comparator=base,
                    metric="cell_delta_stage_error",
                    rule_type="improvement",
                    margin=-0.01,
                    description=f"{ds}/{fam} stage error contrast vs {base} > -0.01 (non-harm)",
                )
            )
            manifest["RQ4"].append(
                HypothesisComponent(
                    component_id=f"RQ4_cell_{ds}_{fam}_{base}_mpiw_safeguard",
                    rq_id="RQ4",
                    model_family=fam,
                    dataset=ds,
                    comparator=base,
                    metric="mpiw_deterioration",
                    rule_type="noninferiority",
                    margin=1.0,
                    description=f"{ds}/{fam} MPIW deterioration vs {base} < 1.0 cycle",
                )
            )
            manifest["RQ4"].append(
                HypothesisComponent(
                    component_id=f"RQ4_cell_{ds}_{fam}_{base}_interval_score_safeguard",
                    rq_id="RQ4",
                    model_family=fam,
                    dataset=ds,
                    comparator=base,
                    metric="interval_score_deterioration",
                    rule_type="noninferiority",
                    margin=1.0,
                    description=f"{ds}/{fam} interval score deterioration vs {base} < 1.0 cycle",
                )
            )
            manifest["RQ4"].append(
                HypothesisComponent(
                    component_id=f"RQ4_cell_{ds}_{fam}_{base}_failure_safeguard",
                    rq_id="RQ4",
                    model_family=fam,
                    dataset=ds,
                    comparator=base,
                    metric="failure_count",
                    rule_type="failure_safeguard",
                    margin=0.0,
                    description=(
                        f"{ds}/{fam} failure safeguard vs {base} "
                        f"(proposed failures <= baseline failures)"
                    ),
                )
            )
        manifest["RQ4"].append(
            HypothesisComponent(
                component_id=f"RQ4_cell_{ds}_{fam}_marginal_coverage_ceiling",
                rq_id="RQ4",
                model_family=fam,
                dataset=ds,
                comparator="nominal_90",
                metric="marginal_coverage_abs_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{ds}/{fam} proposed marginal coverage error < 0.05",
            )
        )
        manifest["RQ4"].append(
            HypothesisComponent(
                component_id=f"RQ4_cell_{ds}_{fam}_worst_regime_ceiling",
                rq_id="RQ4",
                model_family=fam,
                dataset=ds,
                comparator="nominal_90",
                metric="worst_regime_coverage_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{ds}/{fam} proposed worst-regime coverage error < 0.05",
            )
        )
        manifest["RQ4"].append(
            HypothesisComponent(
                component_id=f"RQ4_cell_{ds}_{fam}_worst_stage_ceiling",
                rq_id="RQ4",
                model_family=fam,
                dataset=ds,
                comparator="nominal_90",
                metric="worst_stage_coverage_error",
                rule_type="noninferiority",
                margin=0.05,
                description=f"{ds}/{fam} proposed worst-stage coverage error < 0.05",
            )
        )

    return manifest


def validate_component_manifest_completeness(
    evaluated_component_ids: Sequence[str] | set[str] | None = None,
    rq_id: str | None = None,
) -> dict[str, Any]:
    """Validate that every required hypothesis component is present in evaluated results.

    Raises ValueError if any required component is missing or duplicated.
    Returns completeness summary report.
    """
    manifest = get_rq_component_manifest()
    counts = {rq: len(comps) for rq, comps in manifest.items()}
    total = sum(counts.values())

    if evaluated_component_ids is not None:
        eval_list = list(evaluated_component_ids)
        eval_set = set(eval_list)
        if len(eval_list) != len(eval_set):
            seen = set()
            dups = set()
            for c_id in eval_list:
                if c_id in seen:
                    dups.add(c_id)
                seen.add(c_id)
            raise ValueError(
                f"Duplicate component IDs detected in evaluation results: {sorted(dups)}"
            )

        target_rqs = [rq_id] if rq_id is not None else ["RQ1", "RQ2", "RQ3", "RQ4"]
        all_expected_ids = set()
        for rq in target_rqs:
            required_ids = {c.component_id for c in manifest[rq]}
            all_expected_ids |= required_ids
            missing = required_ids - eval_set
            if missing:
                raise ValueError(
                    f"Missing required hypothesis components for {rq}: {sorted(missing)}"
                )

        unexpected = eval_set - all_expected_ids
        if unexpected:
            raise ValueError(
                f"Unexpected component IDs detected in evaluation results: {sorted(unexpected)}"
            )

    return {
        "all_valid": True,
        "rq1_components_count": counts.get("RQ1", 0),
        "rq2_components_count": counts.get("RQ2", 0),
        "rq3_components_count": counts.get("RQ3", 0),
        "rq4_components_count": counts.get("RQ4", 0),
        "total_components_count": total,
    }
