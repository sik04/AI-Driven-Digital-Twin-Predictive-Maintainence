"""Inference, sequential simulation, and repricing machinery for confirmatory evaluation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from intellitwin.evaluation.schema import (
    CostScenario,
)
from intellitwin.evaluation.validation import normalize_regime_id
from intellitwin.simulator.types import MaintenanceAction, PredictionState


@dataclass(frozen=True)
class SimulationTraceOutcome:
    """Outcome and complete trace of sequential policy execution on an engine trajectory."""

    unit: int
    seed: int
    configuration_id: str
    method_or_control_id: str
    failure_cycle: int
    terminal_event: str  # "PM" or "FAILURE"
    intervention_cycle: int | None
    failed: bool
    pm_occurred: bool
    wasted_rul: float
    is_cost_inefficient_early_pm: bool
    total_cost: float
    decision_trace: list[tuple[int, str]]  # (cycle, action_value)


def simulate_engine_policy(
    unit: int,
    seed: int,
    configuration_id: str,
    method_or_control_id: str,
    cycles: np.ndarray[Any, Any],
    predictions: np.ndarray[Any, Any],
    lower_bounds: np.ndarray[Any, Any] | None,
    upper_bounds: np.ndarray[Any, Any] | None,
    regimes: np.ndarray[Any, Any],
    failure_cycle: int,
    policy_fn: Callable[[PredictionState], MaintenanceAction],
    scenario: CostScenario,
) -> SimulationTraceOutcome:
    """Execute sequential policy on an engine trajectory adhering to observability contracts.

    Contract:
    - Endpoints run 30..T.
    - Decisions occur strictly on cycles 30..T-1.
    - No action occurs at cycle T (failure occurs if not maintained by T-1).
    - Policy receives observable state only (no true RUL, failure cycle, or oracle data).
    - First MAINTAIN_NOW terminates the episode.
    """
    n_pts = len(cycles)
    trace: list[tuple[int, str]] = []
    intervention_cycle: int | None = None
    terminal_event = "FAILURE"
    pm_occurred = False
    failed = True
    wasted_rul = 0.0

    for i in range(n_pts):
        cyc = int(cycles[i])
        if cyc >= failure_cycle:
            break

        low_val = float(lower_bounds[i]) if lower_bounds is not None else float("nan")
        upp_val = float(upper_bounds[i]) if upper_bounds is not None else float("nan")

        state = PredictionState(
            engine_id=unit,
            cycle=cyc,
            point_rul=float(predictions[i]),
            lower_rul=low_val,
            upper_rul=upp_val,
            regime=normalize_regime_id(regimes[i]),
        )

        action = policy_fn(state)
        trace.append((cyc, action.value))

        if action == MaintenanceAction.MAINTAIN_NOW:
            intervention_cycle = cyc
            terminal_event = "PM"
            pm_occurred = True
            failed = False
            wasted_rul = float(failure_cycle - cyc)
            break

    if pm_occurred:
        cost = scenario.c_pm + scenario.c_waste * wasted_rul
    else:
        cost = scenario.c_fail
        wasted_rul = 0.0

    early_pm = pm_occurred and (wasted_rul > scenario.r_equal)

    return SimulationTraceOutcome(
        unit=unit,
        seed=seed,
        configuration_id=configuration_id,
        method_or_control_id=method_or_control_id,
        failure_cycle=failure_cycle,
        terminal_event=terminal_event,
        intervention_cycle=intervention_cycle,
        failed=failed,
        pm_occurred=pm_occurred,
        wasted_rul=wasted_rul,
        is_cost_inefficient_early_pm=early_pm,
        total_cost=cost,
        decision_trace=trace,
    )


def reprice_simulation_outcome(
    base_outcome: SimulationTraceOutcome,
    new_scenario: CostScenario,
) -> SimulationTraceOutcome:
    """Reprice an existing simulation outcome under a different cost scenario.

    Crucial invariant: The physical intervention decision and cycle remain identical;
    only the monetary cost evaluation changes.
    """
    if base_outcome.pm_occurred:
        new_cost = new_scenario.c_pm + new_scenario.c_waste * base_outcome.wasted_rul
    else:
        new_cost = new_scenario.c_fail

    early_pm = base_outcome.pm_occurred and (base_outcome.wasted_rul > new_scenario.r_equal)

    return SimulationTraceOutcome(
        unit=base_outcome.unit,
        seed=base_outcome.seed,
        configuration_id=base_outcome.configuration_id,
        method_or_control_id=base_outcome.method_or_control_id,
        failure_cycle=base_outcome.failure_cycle,
        terminal_event=base_outcome.terminal_event,
        intervention_cycle=base_outcome.intervention_cycle,
        failed=base_outcome.failed,
        pm_occurred=base_outcome.pm_occurred,
        wasted_rul=base_outcome.wasted_rul,
        is_cost_inefficient_early_pm=early_pm,
        total_cost=new_cost,
        decision_trace=base_outcome.decision_trace,
    )
