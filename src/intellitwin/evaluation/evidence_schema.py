"""Authoritative evidence schema and configuration definitions for pre-test verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_METHODS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
    CONTROL_ALL_FOUR,
    COST_SCENARIOS,
)

CANONICAL_NOMINAL_COVERAGES: Final[tuple[int, ...]] = (80, 90, 95)
PRIMARY_CANONICAL_COVERAGE: Final[int] = 90
PRIMARY_COST_SCENARIO: Final[str] = "primary_reference"

EXPECTED_PRIMARY_CONFIGS_COUNT: Final[int] = 810
EXPECTED_CONTROL_CONFIGS_COUNT: Final[int] = 120
EXPECTED_TOTAL_CONFIGS_COUNT: Final[int] = 930

EXPECTED_PRIMARY_OUTCOMES_COUNT: Final[int] = 16470
EXPECTED_CONTROL_OUTCOMES_COUNT: Final[int] = 3120
EXPECTED_TOTAL_OUTCOMES_COUNT: Final[int] = 19590

EXPECTED_PRIMARY_CELL_SUMMARIES_COUNT: Final[int] = 162
EXPECTED_CONTROL_CELL_SUMMARIES_COUNT: Final[int] = 24
EXPECTED_TOTAL_CELL_SUMMARIES_COUNT: Final[int] = 186

EXPECTED_TOTAL_COMPONENTS_COUNT: Final[int] = 152


def canonicalize_coverage(cov: float | int | str) -> int:
    """Convert float or string coverage (e.g. 0.90, 90, '90') to canonical integer 80, 90, or 95.

    Rejects any value not matching 80, 90, or 95.
    """
    if isinstance(cov, str):
        cov = float(cov.strip())
    if isinstance(cov, float):
        if abs(cov - 0.80) < 1e-4 or abs(cov - 80.0) < 1e-4:
            return 80
        elif abs(cov - 0.90) < 1e-4 or abs(cov - 90.0) < 1e-4:
            return 90
        elif abs(cov - 0.95) < 1e-4 or abs(cov - 95.0) < 1e-4:
            return 95
        else:
            raise ValueError(f"Invalid nominal coverage: {cov}; must be 0.80, 0.90, or 0.95")
    elif isinstance(cov, int):
        if cov in (80, 90, 95):
            return cov
        raise ValueError(f"Invalid canonical coverage: {cov}; must be 80, 90, or 95")
    else:
        raise TypeError(f"Unsupported coverage type {type(cov)}: {cov}")


def coverage_to_float(cov: int) -> float:
    """Convert canonical integer coverage (80, 90, 95) to standard decimal float."""
    if cov == 80:
        return 0.80
    elif cov == 90:
        return 0.90
    elif cov == 95:
        return 0.95
    else:
        raise ValueError(f"Unsupported canonical coverage: {cov}")


def generate_expected_configurations() -> tuple[
    set[tuple[str, str, int, str, int, str]],
    set[tuple[str, str, int, str, int, str]],
]:
    """Generate expected Cartesian products for primary and control configurations.

    Tuple format: (dataset, model_family, seed, method_or_control_id, nominal_coverage, scenario_id)
    """
    primary_set: set[tuple[str, str, int, str, int, str]] = set()
    for ds in CONFIRMATORY_DATASETS:
        for fam in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                for meth in CONFIRMATORY_METHODS:
                    for cov in CANONICAL_NOMINAL_COVERAGES:
                        for scen in COST_SCENARIOS:
                            primary_set.add((ds, fam, seed, meth, cov, scen))

    control_set: set[tuple[str, str, int, str, int, str]] = set()
    for fam in CONFIRMATORY_MODELS:
        for seed in CONFIRMATORY_SEEDS:
            for ctrl in CONTROL_ALL_FOUR:
                for scen in COST_SCENARIOS:
                    control_set.add(("FD002", fam, seed, ctrl, PRIMARY_CANONICAL_COVERAGE, scen))

    return primary_set, control_set


def generate_expected_cell_summary_keys() -> tuple[
    set[tuple[str, str, str, int, str]],
    set[tuple[str, str, str, int, str]],
]:
    """Generate expected configuration keys for cell_summary.csv after removing seed and engine.

    Tuple format: (dataset, model_family, method_or_control_id, nominal_coverage, scenario_id)
    """
    prim_cfgs, ctrl_cfgs = generate_expected_configurations()
    prim_keys = {(ds, fam, meth, cov, scen) for (ds, fam, _, meth, cov, scen) in prim_cfgs}
    ctrl_keys = {(ds, fam, ctrl, cov, scen) for (ds, fam, _, ctrl, cov, scen) in ctrl_cfgs}
    return prim_keys, ctrl_keys


def generate_expected_engine_outcome_keys(
    validation_engines: dict[str, list[int]],
) -> set[tuple[str, str, int, str, int, str, int]]:
    """Generate exact set of:
    (dataset, model_family, seed, method_or_control_id, nominal_coverage, scenario_id, unit).
    """
    prim_cfgs, ctrl_cfgs = generate_expected_configurations()
    all_keys: set[tuple[str, str, int, str, int, str, int]] = set()

    for ds, fam, seed, meth, cov, scen in prim_cfgs:
        for u in validation_engines[ds]:
            all_keys.add((ds, fam, seed, meth, cov, scen, int(u)))

    for ds, fam, seed, ctrl, cov, scen in ctrl_cfgs:
        for u in validation_engines[ds]:
            all_keys.add((ds, fam, seed, ctrl, cov, scen, int(u)))

    return all_keys


@dataclass(frozen=True)
class StatisticArraySpec:
    """Specification of an expected bootstrap statistic array in NPZ storage."""

    stat_id: str
    dataset: str  # "FD001", "FD002", "FD004", or "ALL_6_CELLS"
    target_npz: str  # e.g. "bootstrap_statistics_FD001.npz"
    is_bounded: bool  # True if stored as lower/upper pair
    array_key: str | None  # If not bounded
    lower_array_key: str | None  # If bounded
    upper_array_key: str | None  # If bounded
    model_family: str | None
    comparator: str
    metric: str
    margin: float
    rule_type: str  # "improvement" or "noninferiority"


def get_expected_contrast_statistic_specs() -> dict[str, StatisticArraySpec]:
    """Return explicit mapping for every expected contrast statistic in contrast_intervals.csv."""
    specs: dict[str, StatisticArraySpec] = {}

    # 1. Primary cell contrasts vs baselines (3 datasets x 2 models x 2 baselines x 5 metrics = 60)
    for ds in CONFIRMATORY_DATASETS:
        target_npz = f"bootstrap_statistics_{ds}.npz"
        for fam in CONFIRMATORY_MODELS:
            for base in ("global_hcp", "regime_hcp"):
                # Cost improvement (scalar)
                c_cost = f"{ds}_{fam}_{base}_cost_improvement"
                specs[c_cost] = StatisticArraySpec(
                    stat_id=c_cost,
                    dataset=ds,
                    target_npz=target_npz,
                    is_bounded=False,
                    array_key=c_cost,
                    lower_array_key=None,
                    upper_array_key=None,
                    model_family=fam,
                    comparator=base,
                    metric="delta_cost",
                    margin=0.20,
                    rule_type="improvement",
                )
                # Regime error improvement (bounded)
                c_reg = f"{ds}_{fam}_{base}_regime_error_improvement"
                specs[c_reg] = StatisticArraySpec(
                    stat_id=c_reg,
                    dataset=ds,
                    target_npz=target_npz,
                    is_bounded=True,
                    array_key=None,
                    lower_array_key=f"{c_reg}_lower",
                    upper_array_key=f"{c_reg}_upper",
                    model_family=fam,
                    comparator=base,
                    metric="delta_regime_error",
                    margin=0.01,
                    rule_type="improvement",
                )
                # Stage error improvement (bounded)
                c_stg = f"{ds}_{fam}_{base}_stage_error_improvement"
                specs[c_stg] = StatisticArraySpec(
                    stat_id=c_stg,
                    dataset=ds,
                    target_npz=target_npz,
                    is_bounded=True,
                    array_key=None,
                    lower_array_key=f"{c_stg}_lower",
                    upper_array_key=f"{c_stg}_upper",
                    model_family=fam,
                    comparator=base,
                    metric="delta_stage_error",
                    margin=0.01,
                    rule_type="improvement",
                )
                # MPIW deterioration (scalar)
                c_mpiw = f"{ds}_{fam}_{base}_mpiw_deterioration"
                specs[c_mpiw] = StatisticArraySpec(
                    stat_id=c_mpiw,
                    dataset=ds,
                    target_npz=target_npz,
                    is_bounded=False,
                    array_key=c_mpiw,
                    lower_array_key=None,
                    upper_array_key=None,
                    model_family=fam,
                    comparator=base,
                    metric="mpiw_deterioration",
                    margin=1.0,
                    rule_type="noninferiority",
                )
                # Interval score deterioration (scalar)
                c_is = f"{ds}_{fam}_{base}_interval_score_deterioration"
                specs[c_is] = StatisticArraySpec(
                    stat_id=c_is,
                    dataset=ds,
                    target_npz=target_npz,
                    is_bounded=False,
                    array_key=c_is,
                    lower_array_key=None,
                    upper_array_key=None,
                    model_family=fam,
                    comparator=base,
                    metric="interval_score_deterioration",
                    margin=1.0,
                    rule_type="noninferiority",
                )

    # 2. FD002 Benchmark controls cost improvement (2 models x 4 controls = 8)
    for fam in CONFIRMATORY_MODELS:
        for ctrl in CONTROL_ALL_FOUR:
            c_ctrl = f"FD002_{fam}_{ctrl}_cost_improvement"
            specs[c_ctrl] = StatisticArraySpec(
                stat_id=c_ctrl,
                dataset="FD002",
                target_npz="bootstrap_statistics_FD002.npz",
                is_bounded=False,
                array_key=c_ctrl,
                lower_array_key=None,
                upper_array_key=None,
                model_family=fam,
                comparator=ctrl,
                metric="delta_cost",
                margin=0.20,
                rule_type="improvement",
            )

    # 3. RQ4 Aggregates (2 baselines x 3 metrics = 6)
    target_rq4_npz = "bootstrap_statistics_RQ4.npz"
    for base in ("global_hcp", "regime_hcp"):
        # Aggregate cost improvement (scalar)
        c_agg_cost = f"RQ4_aggregate_{base}_cost_improvement"
        specs[c_agg_cost] = StatisticArraySpec(
            stat_id=c_agg_cost,
            dataset="ALL_6_CELLS",
            target_npz=target_rq4_npz,
            is_bounded=False,
            array_key=f"agg_{base}_cost_improvement",
            lower_array_key=None,
            upper_array_key=None,
            model_family="BOTH",
            comparator=base,
            metric="aggregate_delta_cost",
            margin=0.20,
            rule_type="improvement",
        )
        # Aggregate regime error improvement (bounded)
        c_agg_reg = f"RQ4_aggregate_{base}_regime_error_improvement"
        specs[c_agg_reg] = StatisticArraySpec(
            stat_id=c_agg_reg,
            dataset="ALL_6_CELLS",
            target_npz=target_rq4_npz,
            is_bounded=True,
            array_key=None,
            lower_array_key=f"agg_{base}_regime_error_improvement_lower",
            upper_array_key=f"agg_{base}_regime_error_improvement_upper",
            model_family="BOTH",
            comparator=base,
            metric="aggregate_delta_regime_error",
            margin=0.01,
            rule_type="improvement",
        )
        # Aggregate stage error improvement (bounded)
        c_agg_stg = f"RQ4_aggregate_{base}_stage_error_improvement"
        specs[c_agg_stg] = StatisticArraySpec(
            stat_id=c_agg_stg,
            dataset="ALL_6_CELLS",
            target_npz=target_rq4_npz,
            is_bounded=True,
            array_key=None,
            lower_array_key=f"agg_{base}_stage_error_improvement_lower",
            upper_array_key=f"agg_{base}_stage_error_improvement_upper",
            model_family="BOTH",
            comparator=base,
            metric="aggregate_delta_stage_error",
            margin=0.01,
            rule_type="improvement",
        )

    return specs


COMPONENT_EVIDENCE_COLUMNS: Final[tuple[str, ...]] = (
    "component_id",
    "rq_id",
    "dataset",
    "model_family",
    "comparator",
    "metric",
    "rule_type",
    "margin",
    "evidence_kind",
    "statistic_id",
    "observed_lower",
    "observed_upper",
    "ci_95_low",
    "ci_95_high",
    "ci_decision_low",
    "ci_decision_high",
    "proposed_failure_count",
    "comparator_failure_count",
    "status",
)


def map_component_to_evidence_spec(
    component_id: str,
    rq_id: str,
    model_family: str | None,
    dataset: str | None,
    comparator: str,
    metric: str,
    rule_type: str,
) -> tuple[str, str]:
    """Map hypothesis component attributes to authoritative (evidence_kind, statistic_id).

    evidence_kind is one of: 'bootstrap_scalar', 'bootstrap_bounded', 'observed_failure'.
    """
    if rule_type == "failure_safeguard":
        return "observed_failure", f"{dataset}_{model_family}_{comparator}_failure_count"

    if comparator == "nominal_90":
        if metric == "marginal_coverage_abs_error":
            return (
                "bootstrap_scalar",
                f"{dataset}_{model_family}_decision_aware_hcp_marginal_coverage_error",
            )
        elif metric == "worst_regime_coverage_error":
            return (
                "bootstrap_bounded",
                f"{dataset}_{model_family}_decision_aware_hcp_regime_error",
            )
        elif metric == "worst_stage_coverage_error":
            return (
                "bootstrap_bounded",
                f"{dataset}_{model_family}_decision_aware_hcp_stage_error",
            )
        else:
            raise ValueError(f"Unknown ceiling metric: {metric} for component {component_id}")

    if rq_id == "RQ4" and dataset is None:
        if metric == "aggregate_delta_cost":
            return "bootstrap_scalar", f"RQ4_aggregate_{comparator}_cost_improvement"
        elif metric == "aggregate_delta_regime_error":
            return "bootstrap_bounded", f"RQ4_aggregate_{comparator}_regime_error_improvement"
        elif metric == "aggregate_delta_stage_error":
            return "bootstrap_bounded", f"RQ4_aggregate_{comparator}_stage_error_improvement"
        else:
            raise ValueError(f"Unknown RQ4 aggregate metric: {metric} for component {component_id}")

    if metric in ("delta_cost", "cell_delta_cost"):
        return "bootstrap_scalar", f"{dataset}_{model_family}_{comparator}_cost_improvement"
    elif metric in ("delta_regime_error", "cell_delta_regime_error"):
        return (
            "bootstrap_bounded",
            f"{dataset}_{model_family}_{comparator}_regime_error_improvement",
        )
    elif metric in ("delta_stage_error", "cell_delta_stage_error"):
        return (
            "bootstrap_bounded",
            f"{dataset}_{model_family}_{comparator}_stage_error_improvement",
        )
    elif metric == "mpiw_deterioration":
        return (
            "bootstrap_scalar",
            f"{dataset}_{model_family}_{comparator}_mpiw_deterioration",
        )
    elif metric == "interval_score_deterioration":
        return (
            "bootstrap_scalar",
            f"{dataset}_{model_family}_{comparator}_interval_score_deterioration",
        )

    raise ValueError(f"Unhandled component specification: {component_id} ({metric}, {rule_type})")
