"""Chronological engine replay engine for maintenance simulation."""

import math
from typing import Any

from intellitwin.simulator.costs import (
    MaintenanceCostConfig,
    failure_maintenance_cost,
    preventive_maintenance_cost,
)
from intellitwin.simulator.types import (
    DecisionRecord,
    EngineSimulationResult,
    MaintenanceAction,
    MaintenancePolicy,
    PredictionState,
    TerminalEvent,
)


def _validate_prediction_state(state: PredictionState, expected_engine_id: int) -> None:
    """Validate prediction state values and engine ownership."""
    if state.engine_id != expected_engine_id:
        msg = f"State engine_id {state.engine_id} does not match expected {expected_engine_id}"
        raise ValueError(msg)
    if math.isnan(state.point_rul) or math.isinf(state.point_rul):
        raise ValueError(f"Invalid point_rul value: {state.point_rul}")
    if math.isnan(state.lower_rul) or math.isinf(state.lower_rul):
        raise ValueError(f"Invalid lower_rul value: {state.lower_rul}")
    if math.isnan(state.upper_rul) or math.isinf(state.upper_rul):
        raise ValueError(f"Invalid upper_rul value: {state.upper_rul}")
    if state.lower_rul > state.upper_rul:
        raise ValueError(
            f"lower_rul ({state.lower_rul}) cannot exceed upper_rul ({state.upper_rul})"
        )


def simulate_engine_trajectory(
    engine_id: int,
    failure_cycle: int,
    states: list[PredictionState],
    policy: MaintenancePolicy,
    cost_config: MaintenanceCostConfig,
) -> EngineSimulationResult:
    """Replay an individual engine trajectory chronologically under a maintenance policy.

    Parameters
    ----------
    engine_id : int
        Unique engine identifier.
    failure_cycle : int
        True final failure cycle of the engine (T_failure).
    states : list[PredictionState]
        Sequence of observable prediction states ordered by cycle t (< failure_cycle).
    policy : MaintenancePolicy
        Policy function/callable accepting PredictionState and returning MaintenanceAction.
    cost_config : MaintenanceCostConfig
        Maintenance cost parameters.

    Returns
    -------
    EngineSimulationResult
        Auditable simulation result record.
    """
    if not states:
        raise ValueError(f"Empty prediction state sequence for engine {engine_id}")

    # Verify chronological ordering and state validity
    cycles = [s.cycle for s in states]
    if len(cycles) != len(set(cycles)):
        raise ValueError(f"Duplicate decision cycles found for engine {engine_id}: {cycles}")
    if cycles != sorted(cycles):
        raise ValueError(
            f"Prediction states are not ordered chronologically for engine {engine_id}"
        )

    for idx, state in enumerate(states):
        _validate_prediction_state(state, engine_id)
        if idx > 0 and state.cycle <= states[idx - 1].cycle:
            msg = (
                f"Non-increasing cycles detected for engine {engine_id}: "
                f"{states[idx - 1].cycle} -> {state.cycle}"
            )
            raise ValueError(msg)
        if state.cycle >= failure_cycle:
            msg = (
                f"Decision cycle {state.cycle} is >= failure_cycle {failure_cycle} "
                f"for engine {engine_id}"
            )
            raise ValueError(msg)

    decision_history: list[DecisionRecord] = []

    for state in states:
        t = state.cycle
        action = policy(state)

        if not isinstance(action, MaintenanceAction):
            try:
                action = MaintenanceAction(action)
            except ValueError:
                raise ValueError(f"Unsupported maintenance action returned: {action}") from None

        record = DecisionRecord(
            engine_id=engine_id,
            cycle=t,
            point_rul=state.point_rul,
            lower_rul=state.lower_rul,
            upper_rul=state.upper_rul,
            regime=state.regime,
            action=action,
        )
        decision_history.append(record)

        if action == MaintenanceAction.MAINTAIN_NOW:
            wasted_rul = float(failure_cycle - t)
            cost = preventive_maintenance_cost(cost_config, wasted_rul)
            return EngineSimulationResult(
                engine_id=engine_id,
                terminal_event=TerminalEvent.PREVENTIVE_MAINTENANCE,
                intervention_cycle=t,
                failure_indicator=0,
                preventive_maintenance_indicator=1,
                wasted_rul=wasted_rul,
                total_simulated_cost=cost,
                decision_history=decision_history,
            )

        if action == MaintenanceAction.CONTINUE:
            if t == failure_cycle - 1:
                # Continuing past final pre-failure opportunity leads to unmitigated failure
                cost = failure_maintenance_cost(cost_config)
                return EngineSimulationResult(
                    engine_id=engine_id,
                    terminal_event=TerminalEvent.FAILURE,
                    intervention_cycle=None,
                    failure_indicator=1,
                    preventive_maintenance_indicator=0,
                    wasted_rul=0.0,
                    total_simulated_cost=cost,
                    decision_history=decision_history,
                )

    # If all provided states were CONTINUE and final state < failure_cycle - 1,
    # assume trajectory continued through failure_cycle - 1 to failure.
    cost = failure_maintenance_cost(cost_config)
    return EngineSimulationResult(
        engine_id=engine_id,
        terminal_event=TerminalEvent.FAILURE,
        intervention_cycle=None,
        failure_indicator=1,
        preventive_maintenance_indicator=0,
        wasted_rul=0.0,
        total_simulated_cost=cost,
        decision_history=decision_history,
    )


def simulate_fleet(
    engine_trajectories: list[tuple[int, int, list[PredictionState]]],
    policy: MaintenancePolicy,
    cost_config: MaintenanceCostConfig,
) -> list[EngineSimulationResult]:
    """Replay a fleet of engine trajectories chronologically.

    Parameters
    ----------
    engine_trajectories : list[tuple[int, int, list[PredictionState]]]
        List of tuples (engine_id, failure_cycle, states).
    policy : MaintenancePolicy
        Maintenance policy.
    cost_config : MaintenanceCostConfig
        Cost configuration.

    Returns
    -------
    list[EngineSimulationResult]
        List of per-engine simulation result records.
    """
    results: list[EngineSimulationResult] = []
    for engine_id, failure_cycle, states in engine_trajectories:
        res = simulate_engine_trajectory(
            engine_id=engine_id,
            failure_cycle=failure_cycle,
            states=states,
            policy=policy,
            cost_config=cost_config,
        )
        results.append(res)
    return results


def compute_fleet_metrics(results: list[EngineSimulationResult]) -> dict[str, Any]:
    """Compute aggregate summary metrics across a fleet of engine simulations.

    Denominator for primary cost metric is the total number of engines N.
    """
    if not results:
        raise ValueError("Cannot compute fleet metrics for empty results list")

    n_engines = len(results)
    total_cost = sum(r.total_simulated_cost for r in results)
    mean_cost = total_cost / n_engines

    n_failures = sum(r.failure_indicator for r in results)
    n_pm = sum(r.preventive_maintenance_indicator for r in results)

    failure_rate = n_failures / n_engines
    pm_rate = n_pm / n_engines

    wasted_ruls_all = [r.wasted_rul for r in results]
    mean_wasted_rul_all = sum(wasted_ruls_all) / n_engines

    wasted_ruls_pm = [r.wasted_rul for r in results if r.preventive_maintenance_indicator == 1]
    mean_wasted_rul_pm = (sum(wasted_ruls_pm) / len(wasted_ruls_pm)) if wasted_ruls_pm else 0.0

    return {
        "n_engines": n_engines,
        "mean_simulated_cost": float(mean_cost),
        "failure_rate": float(failure_rate),
        "preventive_maintenance_rate": float(pm_rate),
        "mean_wasted_rul_all_engines": float(mean_wasted_rul_all),
        "mean_wasted_rul_preventive_only": float(mean_wasted_rul_pm),
    }
