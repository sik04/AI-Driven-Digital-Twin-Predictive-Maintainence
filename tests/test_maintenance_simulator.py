"""Automated unit tests for the sequential maintenance simulator."""

# ruff: noqa: E402
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is on sys.path for direct execution
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    import pytest
except ImportError:
    pytest = None  # type: ignore[assignment]


from intellitwin.simulator.costs import (
    MaintenanceCostConfig,
    failure_maintenance_cost,
    preventive_maintenance_cost,
)
from intellitwin.simulator.engine import (
    compute_fleet_metrics,
    simulate_engine_trajectory,
    simulate_fleet,
)
from intellitwin.simulator.types import (
    MaintenanceAction,
    PredictionState,
    TerminalEvent,
)

# Test-only cost configuration fixture (NOT a research cost scenario)
# NOTE: These numerical values are synthetic test fixtures used strictly
# to verify simulator arithmetic correctness in unit tests.
TEST_COST_CONFIG = MaintenanceCostConfig(
    preventive_cost=2.0,
    failure_cost=10.0,
    wasted_rul_cost_per_cycle=0.5,
)


def _assert_raises_value_error(func: Any) -> None:
    """Helper to verify ValueError is raised when pytest is not installed."""
    raised = False
    try:
        func()
    except ValueError:
        raised = True
    assert raised, "Expected ValueError was not raised"


def test_case_1_perfect_timing_path() -> None:
    """Case 1: Policy maintains at cycle 9 when failure_cycle = 10."""
    failure_cycle = 10
    states = [
        PredictionState(
            engine_id=1,
            cycle=t,
            point_rul=float(10 - t),
            lower_rul=float(8 - t),
            upper_rul=float(12 - t),
        )
        for t in range(1, 10)
    ]

    def policy(state: PredictionState) -> MaintenanceAction:
        return MaintenanceAction.MAINTAIN_NOW if state.cycle == 9 else MaintenanceAction.CONTINUE

    result = simulate_engine_trajectory(
        engine_id=1,
        failure_cycle=failure_cycle,
        states=states,
        policy=policy,
        cost_config=TEST_COST_CONFIG,
    )

    assert result.terminal_event == TerminalEvent.PREVENTIVE_MAINTENANCE
    assert result.intervention_cycle == 9
    assert result.wasted_rul == 1.0
    assert result.failure_indicator == 0
    assert result.preventive_maintenance_indicator == 1
    assert len(result.decision_history) == 9
    assert result.total_simulated_cost == 2.0 + 0.5 * 1.0  # PM cost: 2.5


def test_case_2_never_maintain() -> None:
    """Case 2: Policy always continues; episode ends in FAILURE after cycle 9."""
    failure_cycle = 10
    states = [
        PredictionState(
            engine_id=1,
            cycle=t,
            point_rul=float(10 - t),
            lower_rul=float(8 - t),
            upper_rul=float(12 - t),
        )
        for t in range(1, 10)
    ]

    def policy(state: PredictionState) -> MaintenanceAction:
        return MaintenanceAction.CONTINUE

    result = simulate_engine_trajectory(
        engine_id=1,
        failure_cycle=failure_cycle,
        states=states,
        policy=policy,
        cost_config=TEST_COST_CONFIG,
    )

    assert result.terminal_event == TerminalEvent.FAILURE
    assert result.intervention_cycle is None
    assert result.wasted_rul == 0.0
    assert result.failure_indicator == 1
    assert result.preventive_maintenance_indicator == 0
    assert len(result.decision_history) == 9
    assert result.decision_history[-1].cycle == 9
    assert result.total_simulated_cost == 10.0


def test_case_3_early_maintenance() -> None:
    """Case 3: Policy maintains early at cycle 4; episode terminates immediately."""
    failure_cycle = 10
    states = [
        PredictionState(
            engine_id=1,
            cycle=t,
            point_rul=float(10 - t),
            lower_rul=float(8 - t),
            upper_rul=float(12 - t),
        )
        for t in range(1, 10)
    ]

    def policy(state: PredictionState) -> MaintenanceAction:
        return MaintenanceAction.MAINTAIN_NOW if state.cycle == 4 else MaintenanceAction.CONTINUE

    result = simulate_engine_trajectory(
        engine_id=1,
        failure_cycle=failure_cycle,
        states=states,
        policy=policy,
        cost_config=TEST_COST_CONFIG,
    )

    assert result.terminal_event == TerminalEvent.PREVENTIVE_MAINTENANCE
    assert result.intervention_cycle == 4
    assert result.wasted_rul == 6.0
    assert len(result.decision_history) == 4  # Cycles 1..4 only
    assert result.total_simulated_cost == 2.0 + 0.5 * 6.0  # PM cost: 5.0


def test_case_4_final_opportunity_maintenance() -> None:
    """Case 4: Maintain at final opportunity t = failure_cycle - 1 (cycle 19)."""
    failure_cycle = 20
    states = [
        PredictionState(
            engine_id=2,
            cycle=t,
            point_rul=float(20 - t),
            lower_rul=float(18 - t),
            upper_rul=float(22 - t),
        )
        for t in range(1, 20)
    ]

    def policy(state: PredictionState) -> MaintenanceAction:
        return MaintenanceAction.MAINTAIN_NOW if state.cycle == 19 else MaintenanceAction.CONTINUE

    result = simulate_engine_trajectory(
        engine_id=2,
        failure_cycle=failure_cycle,
        states=states,
        policy=policy,
        cost_config=TEST_COST_CONFIG,
    )

    assert result.terminal_event == TerminalEvent.PREVENTIVE_MAINTENANCE
    assert result.intervention_cycle == 19
    assert result.wasted_rul == 1.0
    assert result.preventive_maintenance_indicator == 1


def test_case_5_continue_at_final_opportunity() -> None:
    """Case 5: Continue at final opportunity t = failure_cycle - 1 leads to FAILURE."""
    failure_cycle = 20
    states = [
        PredictionState(
            engine_id=2,
            cycle=t,
            point_rul=float(20 - t),
            lower_rul=float(18 - t),
            upper_rul=float(22 - t),
        )
        for t in range(1, 20)
    ]

    def policy(state: PredictionState) -> MaintenanceAction:
        return MaintenanceAction.CONTINUE

    result = simulate_engine_trajectory(
        engine_id=2,
        failure_cycle=failure_cycle,
        states=states,
        policy=policy,
        cost_config=TEST_COST_CONFIG,
    )

    assert result.terminal_event == TerminalEvent.FAILURE
    assert result.failure_indicator == 1
    assert result.total_simulated_cost == 10.0


def test_case_6_optimistic_prediction_stream() -> None:
    """Case 6: Optimistic prediction stream causes policy to continue into FAILURE."""
    failure_cycle = 15
    # Predictions overestimate true remaining life
    states = [
        PredictionState(engine_id=3, cycle=t, point_rul=50.0, lower_rul=40.0, upper_rul=60.0)
        for t in range(1, 15)
    ]

    # Simple threshold policy: maintain if lower_rul <= 5
    def threshold_policy(state: PredictionState) -> MaintenanceAction:
        return (
            MaintenanceAction.MAINTAIN_NOW if state.lower_rul <= 5.0 else MaintenanceAction.CONTINUE
        )

    result = simulate_engine_trajectory(
        engine_id=3,
        failure_cycle=failure_cycle,
        states=states,
        policy=threshold_policy,
        cost_config=TEST_COST_CONFIG,
    )

    assert result.terminal_event == TerminalEvent.FAILURE
    assert result.failure_indicator == 1


def test_case_7_pessimistic_prediction_stream() -> None:
    """Case 7: Pessimistic prediction stream causes policy to maintain very early."""
    failure_cycle = 25
    # Predictions underestimate true remaining life
    states = [
        PredictionState(
            engine_id=4,
            cycle=t,
            point_rul=1.0 if t >= 3 else 20.0,
            lower_rul=0.0 if t >= 3 else 15.0,
            upper_rul=2.0 if t >= 3 else 25.0,
        )
        for t in range(1, 25)
    ]

    def threshold_policy(state: PredictionState) -> MaintenanceAction:
        return (
            MaintenanceAction.MAINTAIN_NOW if state.lower_rul <= 5.0 else MaintenanceAction.CONTINUE
        )

    result = simulate_engine_trajectory(
        engine_id=4,
        failure_cycle=failure_cycle,
        states=states,
        policy=threshold_policy,
        cost_config=TEST_COST_CONFIG,
    )

    assert result.terminal_event == TerminalEvent.PREVENTIVE_MAINTENANCE
    assert result.intervention_cycle == 3
    assert result.wasted_rul == 22.0  # 25 - 3


def test_case_8_cost_arithmetic() -> None:
    """Case 8: Explicit verification of cost equations under test fixtures."""
    # Test fixture cost parameters: C_PM = 2.0, C_FAIL = 10.0, C_WASTE = 0.5
    cost_cfg = MaintenanceCostConfig(
        preventive_cost=2.0,
        failure_cost=10.0,
        wasted_rul_cost_per_cycle=0.5,
    )

    # For wasted_rul = 4.0: cost = 2.0 + 0.5 * 4.0 = 4.0
    pm_cost = preventive_maintenance_cost(cost_cfg, wasted_rul=4.0)
    assert pm_cost == 4.0

    # Failure cost = 10.0
    fail_cost = failure_maintenance_cost(cost_cfg)
    assert fail_cost == 10.0


def test_case_9_policy_information_isolation() -> None:
    """Case 9: Verify policy interface receives PredictionState only.

    Ensures ground-truth variables (e.g. failure_cycle) cannot be accessed via policy.
    """
    received_attributes: set[str] = set()

    def audit_policy(state: PredictionState) -> MaintenanceAction:
        nonlocal received_attributes
        received_attributes = set(dir(state))
        return MaintenanceAction.CONTINUE

    state = PredictionState(engine_id=10, cycle=5, point_rul=20.0, lower_rul=15.0, upper_rul=25.0)
    audit_policy(state)

    assert "engine_id" in received_attributes
    assert "cycle" in received_attributes
    assert "point_rul" in received_attributes
    assert "lower_rul" in received_attributes
    assert "upper_rul" in received_attributes
    assert "regime" in received_attributes

    # Hidden ground truth fields MUST NOT exist in PredictionState
    assert "true_rul" not in received_attributes
    assert "failure_cycle" not in received_attributes
    assert "future_data" not in received_attributes


def test_case_10_invalid_input_validation() -> None:
    """Case 10: Verify explicit failures for invalid prediction states and trajectory structures."""
    cost_cfg = TEST_COST_CONFIG

    # Invalid cost config (preventive_cost <= 0)
    _assert_raises_value_error(
        lambda: MaintenanceCostConfig(
            preventive_cost=0.0, failure_cost=10.0, wasted_rul_cost_per_cycle=0.5
        )
    )

    # Invalid cost config (failure_cost <= preventive_cost)
    _assert_raises_value_error(
        lambda: MaintenanceCostConfig(
            preventive_cost=10.0, failure_cost=5.0, wasted_rul_cost_per_cycle=0.5
        )
    )

    # Empty states
    _assert_raises_value_error(
        lambda: simulate_engine_trajectory(
            1, 10, [], lambda s: MaintenanceAction.CONTINUE, cost_cfg
        )
    )

    # Duplicate cycles
    dup_states = [
        PredictionState(1, 1, 10.0, 5.0, 15.0),
        PredictionState(1, 1, 10.0, 5.0, 15.0),
    ]
    _assert_raises_value_error(
        lambda: simulate_engine_trajectory(
            1, 10, dup_states, lambda s: MaintenanceAction.CONTINUE, cost_cfg
        )
    )

    # Non-monotonic cycles
    non_mono = [
        PredictionState(1, 5, 10.0, 5.0, 15.0),
        PredictionState(1, 3, 10.0, 5.0, 15.0),
    ]
    _assert_raises_value_error(
        lambda: simulate_engine_trajectory(
            1, 10, non_mono, lambda s: MaintenanceAction.CONTINUE, cost_cfg
        )
    )

    # Cycle >= failure_cycle
    exceed_cycle = [PredictionState(1, 10, 10.0, 5.0, 15.0)]
    _assert_raises_value_error(
        lambda: simulate_engine_trajectory(
            1, 10, exceed_cycle, lambda s: MaintenanceAction.CONTINUE, cost_cfg
        )
    )

    # Lower bound > upper bound
    bad_bounds = [PredictionState(1, 1, 10.0, 20.0, 5.0)]
    _assert_raises_value_error(
        lambda: simulate_engine_trajectory(
            1, 10, bad_bounds, lambda s: MaintenanceAction.CONTINUE, cost_cfg
        )
    )


def test_fleet_simulation_and_metrics() -> None:
    """Verify simulate_fleet and compute_fleet_metrics aggregation."""
    # Engine 1: PM at cycle 8 (failure_cycle = 10, wasted = 2)
    # Engine 2: Failure (failure_cycle = 10)
    traj1 = (
        1,
        10,
        [PredictionState(1, t, float(10 - t), float(8 - t), float(12 - t)) for t in range(1, 10)],
    )
    traj2 = (
        2,
        10,
        [PredictionState(2, t, float(10 - t), float(8 - t), float(12 - t)) for t in range(1, 10)],
    )

    def policy(state: PredictionState) -> MaintenanceAction:
        if state.engine_id == 1 and state.cycle == 8:
            return MaintenanceAction.MAINTAIN_NOW
        return MaintenanceAction.CONTINUE

    results = simulate_fleet([traj1, traj2], policy, TEST_COST_CONFIG)
    assert len(results) == 2

    metrics = compute_fleet_metrics(results)
    assert metrics["n_engines"] == 2
    # PM cost: 2.0 + 0.5 * 2 = 3.0. Failure cost: 10.0. Mean cost = (3.0 + 10.0) / 2 = 6.5
    assert metrics["mean_simulated_cost"] == 6.5
    assert metrics["failure_rate"] == 0.5
    assert metrics["preventive_maintenance_rate"] == 0.5
    assert metrics["mean_wasted_rul_all_engines"] == 1.0  # (2.0 + 0.0) / 2
    assert metrics["mean_wasted_rul_preventive_only"] == 2.0


if __name__ == "__main__":
    test_funcs = [
        test_case_1_perfect_timing_path,
        test_case_2_never_maintain,
        test_case_3_early_maintenance,
        test_case_4_final_opportunity_maintenance,
        test_case_5_continue_at_final_opportunity,
        test_case_6_optimistic_prediction_stream,
        test_case_7_pessimistic_prediction_stream,
        test_case_8_cost_arithmetic,
        test_case_9_policy_information_isolation,
        test_case_10_invalid_input_validation,
        test_fleet_simulation_and_metrics,
    ]
    for func in test_funcs:
        print(f"Running {func.__name__}...", end=" ")
        func()
        print("PASS")
    print(f"\nAll {len(test_funcs)} simulator unit tests PASSED successfully!")
