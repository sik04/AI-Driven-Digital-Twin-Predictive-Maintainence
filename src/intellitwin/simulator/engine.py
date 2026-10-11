"""Chronological engine replay engine for maintenance simulation."""

import math
import numbers
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


def _validate_positive_integer_scalar(val: Any, name: str) -> int:
    """Validate that a value is a positive integral scalar type.

    Accepts Python integers and compatible integral scalar types.
    Rejects booleans, strings, floats, NaN, infinity, nonpositive values.
    """
    if isinstance(val, bool):
        raise ValueError(f"{name} must be a positive integral scalar, got boolean: {val}")
    if not isinstance(val, numbers.Integral):
        raise ValueError(
            f"{name} must be a positive integral scalar, got {type(val).__name__}: {val}"
        )
    int_val = int(val)
    if int_val <= 0:
        raise ValueError(f"{name} must be positive, got {int_val}")
    return int_val


def _validate_prediction_state(state: PredictionState, expected_engine_id: int) -> None:
    """Validate prediction state values and engine ownership."""
    state_engine_id = _validate_positive_integer_scalar(state.engine_id, "state.engine_id")
    _validate_positive_integer_scalar(state.cycle, "state.cycle")
    if state_engine_id != expected_engine_id:
        msg = f"State engine_id {state.engine_id} does not match expected {expected_engine_id}"
        raise ValueError(msg)
    if (
        isinstance(state.point_rul, bool)
        or not isinstance(state.point_rul, (int, float, numbers.Real))
        or math.isnan(state.point_rul)
        or math.isinf(state.point_rul)
    ):
        raise ValueError(f"Invalid point_rul value: {state.point_rul}")
    if (
        isinstance(state.lower_rul, bool)
        or not isinstance(state.lower_rul, (int, float, numbers.Real))
        or math.isnan(state.lower_rul)
        or math.isinf(state.lower_rul)
    ):
        raise ValueError(f"Invalid lower_rul value: {state.lower_rul}")
    if (
        isinstance(state.upper_rul, bool)
        or not isinstance(state.upper_rul, (int, float, numbers.Real))
        or math.isnan(state.upper_rul)
        or math.isinf(state.upper_rul)
    ):
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
    val_engine_id = _validate_positive_integer_scalar(engine_id, "engine_id")
    val_failure_cycle = _validate_positive_integer_scalar(failure_cycle, "failure_cycle")

    if not states:
        raise ValueError(f"Empty prediction state sequence for engine {val_engine_id}")

    # Validate all states before constructing ranges or calling policy
    for state in states:
        _validate_prediction_state(state, val_engine_id)

    first_cycle = states[0].cycle
    if first_cycle >= val_failure_cycle:
        raise ValueError(
            f"first_cycle ({first_cycle}) must be strictly less than "
            f"failure_cycle ({val_failure_cycle})"
        )

    expected_cycles = list(range(first_cycle, val_failure_cycle))
    actual_cycles = [s.cycle for s in states]

    if actual_cycles != expected_cycles:
        raise ValueError(
            f"Prediction states for engine {val_engine_id} must cover every cycle from "
            f"{first_cycle} to failure_cycle - 1 ({val_failure_cycle - 1}). "
            f"Got cycles {actual_cycles[0]}..{actual_cycles[-1]} (len {len(actual_cycles)}), "
            f"expected {first_cycle}..{val_failure_cycle - 1} (len {len(expected_cycles)})."
        )

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
            engine_id=val_engine_id,
            cycle=t,
            point_rul=state.point_rul,
            lower_rul=state.lower_rul,
            upper_rul=state.upper_rul,
            regime=state.regime,
            action=action,
        )
        decision_history.append(record)

        if action == MaintenanceAction.MAINTAIN_NOW:
            wasted_rul = float(val_failure_cycle - t)
            cost = preventive_maintenance_cost(cost_config, wasted_rul)
            return EngineSimulationResult(
                engine_id=val_engine_id,
                terminal_event=TerminalEvent.PREVENTIVE_MAINTENANCE,
                intervention_cycle=t,
                failure_indicator=0,
                preventive_maintenance_indicator=1,
                wasted_rul=wasted_rul,
                total_simulated_cost=cost,
                decision_history=decision_history,
            )

        if action == MaintenanceAction.CONTINUE:
            if t == val_failure_cycle - 1:
                # Continuing past final pre-failure opportunity leads to unmitigated failure
                cost = failure_maintenance_cost(cost_config)
                return EngineSimulationResult(
                    engine_id=val_engine_id,
                    terminal_event=TerminalEvent.FAILURE,
                    intervention_cycle=None,
                    failure_indicator=1,
                    preventive_maintenance_indicator=0,
                    wasted_rul=0.0,
                    total_simulated_cost=cost,
                    decision_history=decision_history,
                )

    raise ValueError(
        f"Trajectory for engine {val_engine_id} reached end of states without terminal resolution."
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
    seen_engine_ids: set[int] = set()
    for item in engine_trajectories:
        if not isinstance(item, tuple) or len(item) != 3:
            raise ValueError(
                f"Each fleet trajectory must be a 3-tuple (engine_id, failure_cycle, states), "
                f"got {item}"
            )

        eid = _validate_positive_integer_scalar(item[0], "engine_id")
        if eid in seen_engine_ids:
            raise ValueError(f"Duplicate engine_id {eid} detected in fleet trajectories")
        seen_engine_ids.add(eid)

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
    intervention_cycles_pm = [
        r.intervention_cycle
        for r in results
        if r.preventive_maintenance_indicator == 1 and r.intervention_cycle is not None
    ]

    if wasted_ruls_pm:
        sorted_pm_wasted = sorted(wasted_ruls_pm)
        n = len(sorted_pm_wasted)
        mean_wasted_rul_pm = sum(sorted_pm_wasted) / n
        if n % 2 == 1:
            median_wasted_rul_pm = float(sorted_pm_wasted[n // 2])
        else:
            median_wasted_rul_pm = float(
                (sorted_pm_wasted[n // 2 - 1] + sorted_pm_wasted[n // 2]) / 2.0
            )
    else:
        mean_wasted_rul_pm = None
        median_wasted_rul_pm = None

    if intervention_cycles_pm:
        sorted_cycles = sorted(intervention_cycles_pm)
        n = len(sorted_cycles)
        mean_intervention = float(sum(sorted_cycles) / n)
        if n % 2 == 1:
            median_intervention = float(sorted_cycles[n // 2])
        else:
            median_intervention = float((sorted_cycles[n // 2 - 1] + sorted_cycles[n // 2]) / 2.0)
    else:
        mean_intervention = None
        median_intervention = None

    return {
        "n_engines": n_engines,
        "mean_simulated_cost": float(mean_cost),
        "failure_rate": float(failure_rate),
        "preventive_maintenance_rate": float(pm_rate),
        "mean_wasted_rul_all_engines": float(mean_wasted_rul_all),
        "mean_wasted_rul_preventive_only": (
            float(mean_wasted_rul_pm) if mean_wasted_rul_pm is not None else None
        ),
        "median_wasted_rul_preventive_only": (
            float(median_wasted_rul_pm) if median_wasted_rul_pm is not None else None
        ),
        "mean_intervention_cycle": mean_intervention,
        "median_intervention_cycle": median_intervention,
    }
