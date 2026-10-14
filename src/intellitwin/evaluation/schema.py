"""Step 9 / Phase 7 confirmatory evaluation schemas, constants, and matrix configurations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

PROTOCOL_VERSION: Final[str] = "step09-v1"
EVALUATION_SCHEMA_VERSION: Final[str] = "step09-eval-v1"
FREEZE_SCHEMA_VERSION: Final[str] = "step09-freeze-v1"
SMOKE_SCHEMA_VERSION: Final[str] = "step09-smoke-v1"

# Primary & Secondary Datasets
CONFIRMATORY_DATASETS: Final[tuple[str, ...]] = ("FD001", "FD002", "FD004")
CONFIRMATORY_MODELS: Final[tuple[str, ...]] = ("GBR", "LSTM")
CONFIRMATORY_SEEDS: Final[tuple[int, ...]] = (2026, 2027, 2028, 2029, 2030)

# Methods
METHOD_GLOBAL: Final[str] = "global_hcp"
METHOD_REGIME: Final[str] = "regime_hcp"
METHOD_DECISION_AWARE: Final[str] = "decision_aware_hcp"
CONFIRMATORY_METHODS: Final[tuple[str, ...]] = (
    METHOD_GLOBAL,
    METHOD_REGIME,
    METHOD_DECISION_AWARE,
)

# Nominal Coverage Levels
PRIMARY_NOMINAL_COVERAGE: Final[float] = 0.90
SECONDARY_NOMINAL_COVERAGES: Final[tuple[float, ...]] = (0.80, 0.95)
ALL_NOMINAL_COVERAGES: Final[tuple[float, ...]] = (0.80, 0.90, 0.95)

# Primary Intervention Policy
INTERVENTION_THRESHOLD_CYCLES: Final[float] = 1.0


@dataclass(frozen=True)
class CostScenario:
    """Maintenance cost scenario specification."""

    scenario_id: str
    c_pm: float
    c_fail: float
    c_waste: float
    r_equal: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "c_pm": self.c_pm,
            "c_fail": self.c_fail,
            "c_waste": self.c_waste,
            "r_equal": self.r_equal,
        }


COST_SCENARIOS: Final[dict[str, CostScenario]] = {
    "primary_reference": CostScenario(
        scenario_id="primary_reference",
        c_pm=1.0,
        c_fail=5.0,
        c_waste=0.20,
        r_equal=20.0,
    ),
    "failure_sensitive": CostScenario(
        scenario_id="failure_sensitive",
        c_pm=1.0,
        c_fail=10.0,
        c_waste=0.20,
        r_equal=45.0,
    ),
    "waste_sensitive": CostScenario(
        scenario_id="waste_sensitive",
        c_pm=1.0,
        c_fail=5.0,
        c_waste=0.40,
        r_equal=10.0,
    ),
}
PRIMARY_COST_SCENARIO: Final[str] = "primary_reference"

# Control IDs
CONTROL_MATCHED_WIDTH: Final[str] = "matched_width_interval"
CONTROL_WIDENED: Final[str] = "widened_interval"
CONTROL_SAFETY_MARGIN: Final[str] = "point_safety_margin"
CONTROL_EARLIER_INTERVENTION: Final[str] = "earlier_intervention"
ALL_RQ3_CONTROLS: Final[tuple[str, ...]] = (
    CONTROL_MATCHED_WIDTH,
    CONTROL_WIDENED,
    CONTROL_SAFETY_MARGIN,
    CONTROL_EARLIER_INTERVENTION,
)

# Confirmatory Thresholds & Margins (Frozen under ADR-018 / Step 6 Contract)
DELTA_COST_MARGIN_SCU: Final[float] = 0.20
DELTA_ERROR_MARGIN: Final[float] = 0.01
MAX_ABSOLUTE_COVERAGE_ERROR: Final[float] = 0.05
MPIW_NONINFERIORITY_MARGIN_CYCLES: Final[float] = 1.0
INTERVAL_SCORE_NONINFERIORITY_MARGIN_CYCLES: Final[float] = 1.0
ROBUSTNESS_COST_HARM_MARGIN_SCU: Final[float] = -0.20
ROBUSTNESS_ERROR_HARM_MARGIN: Final[float] = -0.01
OBSERVED_FAILURE_RATE_INCREASE_ALLOWED: Final[float] = 0.0

# Bootstrap Specifications
BOOTSTRAP_REPLICATES: Final[int] = 10000
DESCRIPTIVE_QUANTILES: Final[tuple[float, float]] = (0.025, 0.975)
DECISION_QUANTILES: Final[tuple[float, float]] = (0.00625, 0.99375)

# Subgroup eligibility threshold
SUBGROUP_MIN_ENGINES: Final[int] = 10

# Subgroups and Regimes
VALID_REGIMES: Final[tuple[int, ...]] = (1, 2, 3, 4, 5, 6)
VALID_REGIME_STRS: Final[tuple[str, ...]] = ("C1", "C2", "C3", "C4", "C5", "C6")
LIFECYCLE_STAGES: Final[tuple[str, ...]] = ("Early", "Mid", "Late", "Terminal")
