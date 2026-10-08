"""Core data structures and types for the sequential maintenance simulator."""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class MaintenanceAction(str, Enum):
    """Approved action space for decision policies."""

    CONTINUE = "CONTINUE"
    MAINTAIN_NOW = "MAINTAIN_NOW"


class TerminalEvent(str, Enum):
    """Allowed terminal events for engine simulation replay."""

    PREVENTIVE_MAINTENANCE = "PREVENTIVE_MAINTENANCE"
    FAILURE = "FAILURE"


@dataclass(frozen=True)
class PredictionState:
    """Observable state available to a maintenance decision policy at cycle t.

    Must NEVER contain true RUL, failure cycle, or future observations.
    """

    engine_id: int
    cycle: int
    point_rul: float
    lower_rul: float
    upper_rul: float
    regime: int | None = None


@dataclass(frozen=True)
class MaintenanceDecision:
    """Decision selected by a policy at cycle t."""

    engine_id: int
    cycle: int
    action: MaintenanceAction


@dataclass(frozen=True)
class DecisionRecord:
    """Auditable provenance record of a single cycle decision."""

    engine_id: int
    cycle: int
    point_rul: float
    lower_rul: float
    upper_rul: float
    regime: int | None
    action: MaintenanceAction


@dataclass(frozen=True)
class EngineSimulationResult:
    """Terminal outcome record for an individual engine simulation episode."""

    engine_id: int
    terminal_event: TerminalEvent
    intervention_cycle: int | None
    failure_indicator: int
    preventive_maintenance_indicator: int
    wasted_rul: float
    total_simulated_cost: float
    decision_history: list[DecisionRecord] = field(default_factory=list)


# Protocol/Callable signature for maintenance policies.
# Input: PredictionState (observable state through cycle t).
# Output: MaintenanceAction (CONTINUE or MAINTAIN_NOW).
MaintenancePolicy = Callable[[PredictionState], MaintenanceAction]
