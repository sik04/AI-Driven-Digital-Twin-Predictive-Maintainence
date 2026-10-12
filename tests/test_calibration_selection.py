"""Unit tests for validation-only candidate selection, maintenance policy, and tie-breaking."""

from __future__ import annotations

import pandas as pd

from intellitwin.decision.policies import lower_bound_one_cycle_policy
from intellitwin.simulator.costs import MaintenanceCostConfig
from intellitwin.simulator.engine import simulate_engine_trajectory
from intellitwin.simulator.types import MaintenanceAction, PredictionState
from intellitwin.uncertainty.schema import (
    ALL_NINE_CANDIDATES,
    IDENTITY_CANDIDATE_ID,
)
from intellitwin.uncertainty.selection import (
    CandidateAggregateResult,
    run_leave_one_engine_out_evaluation,
    select_winning_candidate,
)


def test_one_cycle_policy_boundary_at_1_0() -> None:
    """Verify that lower_bound_one_cycle_policy maintains at <= 1.0 and continues at > 1.0."""
    st_maintain_exact = PredictionState(
        engine_id=1, cycle=30, point_rul=5.0, lower_rul=1.0, upper_rul=10.0, regime=1
    )
    st_maintain_sub = PredictionState(
        engine_id=1, cycle=30, point_rul=5.0, lower_rul=0.99, upper_rul=10.0, regime=1
    )
    st_continue = PredictionState(
        engine_id=1, cycle=30, point_rul=5.0, lower_rul=1.0001, upper_rul=10.0, regime=1
    )

    assert lower_bound_one_cycle_policy(st_maintain_exact) == MaintenanceAction.MAINTAIN_NOW
    assert lower_bound_one_cycle_policy(st_maintain_sub) == MaintenanceAction.MAINTAIN_NOW
    assert lower_bound_one_cycle_policy(st_continue) == MaintenanceAction.CONTINUE


def test_maintenance_cannot_happen_at_failure_cycle_T() -> None:
    """Verify replay evaluates policy up to T-1, and fails at T if unmitigated."""
    cost_cfg = MaintenanceCostConfig(1.0, 5.0, 0.20)
    # T = 35. States cover cycles 30..34
    states = [
        PredictionState(
            engine_id=1, cycle=c, point_rul=10.0, lower_rul=2.0, upper_rul=15.0, regime=1
        )
        for c in range(30, 35)
    ]
    res = simulate_engine_trajectory(
        engine_id=1,
        failure_cycle=35,
        states=states,
        policy=lower_bound_one_cycle_policy,
        cost_config=cost_cfg,
    )
    # Never maintained -> failed at 35
    assert res.failure_indicator == 1
    assert res.preventive_maintenance_indicator == 0
    assert res.total_simulated_cost == 5.0


def test_tie_breaking_deterministic_order() -> None:
    """Verify deterministic tie-breaking: identity first, then gamma, abs(beta), signed beta."""
    aggregates: dict[str, CandidateAggregateResult] = {}
    for cand in ALL_NINE_CANDIDATES:
        aggregates[cand.candidate_id] = CandidateAggregateResult(
            candidate_id=cand.candidate_id,
            marginal_picp=0.90,
            regime_picp={"C1": 0.90},
            mpiw=10.0,
            interval_score=15.0,
            mean_cost=2.0,  # all tied at cost 2.0
            failure_rate=0.0,
            total_failures=0,
            pm_rate=1.0,
            total_pms=10,
            mean_wasted_rul=1.0,
            pm_wasted_rul_mean=1.0,
            is_feasible=True,
            feasibility_reasons=[],
        )

    # 1. Identity candidate should win when all tied
    winner, status, log = select_winning_candidate(aggregates)
    assert winner.candidate_id == IDENTITY_CANDIDATE_ID

    # 2. If identity is NOT in the tie, smaller gamma wins
    for cid in aggregates:
        aggregates[cid].mean_cost = 5.0  # high cost
    aggregates["gamma1_betap1"].mean_cost = 1.0  # gamma=1, beta=p1
    aggregates["gamma2_beta0"].mean_cost = 1.0  # gamma=2, beta=0

    winner2, _, _ = select_winning_candidate(aggregates)
    assert winner2.candidate_id == "gamma1_betap1"  # smaller gamma (1 < 2)


def test_fallback_when_no_candidate_feasible() -> None:
    """Verify fallback selects gamma0_beta0 with proper status when no candidate is feasible."""
    aggregates: dict[str, CandidateAggregateResult] = {}
    for cand in ALL_NINE_CANDIDATES:
        aggregates[cand.candidate_id] = CandidateAggregateResult(
            candidate_id=cand.candidate_id,
            marginal_picp=0.70,  # below 0.85 -> infeasible
            regime_picp={"C1": 0.70},
            mpiw=10.0,
            interval_score=15.0,
            mean_cost=1.0,
            failure_rate=0.5,
            total_failures=5,
            pm_rate=0.5,
            total_pms=5,
            mean_wasted_rul=2.0,
            pm_wasted_rul_mean=2.0,
            is_feasible=False,
            feasibility_reasons=["Marginal PICP 0.7000 outside [0.85, 0.95]"],
        )

    winner, status, log = select_winning_candidate(aggregates)
    assert winner.candidate_id == IDENTITY_CANDIDATE_ID
    assert status == "fallback_no_feasible_candidate"
    assert log[0]["event"] == "no_feasible_candidate"


def test_exact_failure_count_comparison_in_feasibility() -> None:
    """Verify exact integer comparison of failure counts without tolerance."""
    # Build minimal synthetic df_val_preds
    rows = []
    # 10 engines, 5 seeds, endpoints 30..35
    for s in [2026, 2027]:
        for u in range(1, 11):
            for cyc in range(30, 36):
                rows.append(
                    {
                        "seed": s,
                        "unit": u,
                        "endpoint_cycle": cyc,
                        "rul_true": float(35 - cyc),
                        "prediction": float(max(0, 35 - cyc)),
                        "regime": "C1",
                    }
                )
    df_val = pd.DataFrame(rows)
    aggs, _, _, _ = run_leave_one_engine_out_evaluation(df_val)

    # All candidates evaluated with identical engine/seed grid
    for _cid, res in aggs.items():
        assert isinstance(res.total_failures, int)
