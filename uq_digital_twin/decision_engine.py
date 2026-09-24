"""
Uncertainty-Guided Maintenance Decision Support Engine.

Translates calibrated prognostic uncertainty distributions into risk-sensitive
maintenance scheduling policies, directly connecting Research Gap 3 (UQ)
with Research Gap 1 (Decision Support Systems) and quantifying economic benefits (Paper 7).
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, List, Tuple, Any


class RiskSensitiveMaintenanceScheduler:
    """
    Simulates operational maintenance policies:
    1. Deterministic Policy (Paper 14/Paper 6): Intervenes when point prediction RUL <= threshold.
    2. Conservative Policy (Fixed Safety Factor): Intervenes when point prediction RUL <= 2 * threshold.
    3. Uncertainty-Guided Policy (UQ-DT): Intervenes when lower confidence bound L_cqr <= threshold
       OR when Failure Probability P(RUL <= threshold) >= risk_tolerance.
    """

    def __init__(
        self,
        cost_preventive: float = 1200.0,
        cost_unplanned_failure: float = 12500.0,
        cost_per_wasted_cycle: float = 15.0,
        planning_horizon: int = 15,
        risk_tolerance_prob: float = 0.05,
    ):
        self.c_prev = cost_preventive
        self.c_fail = cost_unplanned_failure
        self.c_waste = cost_per_wasted_cycle
        self.horizon = planning_horizon
        self.risk_tol = risk_tolerance_prob

    def evaluate_fleet_policy(
        self,
        asset_trajectories: List[Dict[str, np.ndarray]],
        policy_type: str = "uq_dt",
    ) -> Dict[str, float]:
        """
        Runs maintenance simulation across an asset fleet.
        
        Args:
            asset_trajectories: List of dicts, each containing:
                - 'timesteps': array
                - 'true_rul': array
                - 'mu_pred': array
                - 'lower_bound': array
                - 'upper_bound': array
                - 'sigma': array
            policy_type: 'deterministic', 'conservative', or 'uq_dt'

        Returns:
            Dictionary with economic metrics: total_cost, failures_avoided, catastrophic_failures,
            wasted_cycles, mean_cost_per_asset.
        """
        total_cost = 0.0
        n_unplanned_failures = 0
        n_planned_preventive = 0
        total_wasted_cycles = 0

        for traj in asset_trajectories:
            timesteps = traj["timesteps"]
            true_rul = traj["true_rul"]
            mu_pred = traj["mu_pred"]
            lower_bound = traj["lower_bound"]
            sigma = traj.get("sigma", np.ones_like(mu_pred) * 5.0)

            intervened = False
            for t_idx in range(len(timesteps)):
                t = timesteps[t_idx]
                r_true = true_rul[t_idx]
                r_pred = mu_pred[t_idx]
                r_low = lower_bound[t_idx]
                s = max(sigma[t_idx], 1e-4)

                # Check if asset naturally suffered catastrophic failure before intervention
                if r_true <= 0:
                    total_cost += self.c_fail
                    n_unplanned_failures += 1
                    intervened = True
                    break

                # Decision rules:
                trigger_intervention = False
                if policy_type == "deterministic":
                    # Paper 14 / Paper 6 baseline: intervene only when mean point prediction <= horizon
                    if r_pred <= self.horizon:
                        trigger_intervention = True

                elif policy_type == "conservative":
                    # Naive ad-hoc heuristic: double the safety buffer
                    if r_pred <= 2.2 * self.horizon:
                        trigger_intervention = True

                elif policy_type == "uq_dt":
                    # UQ-DT: Intervene if lower calibrated bound touches horizon,
                    # OR if tail failure probability P(RUL <= horizon) exceeds risk tolerance
                    prob_failure = norm.cdf((self.horizon - r_pred) / s)
                    if (r_low <= self.horizon) or (prob_failure >= self.risk_tol):
                        trigger_intervention = True

                if trigger_intervention:
                    # Successful planned preventive intervention
                    wasted_life = max(0, r_true - self.horizon)
                    cost_event = self.c_prev + wasted_life * self.c_waste
                    total_cost += cost_event
                    n_planned_preventive += 1
                    total_wasted_cycles += wasted_life
                    intervened = True
                    break

            if not intervened:
                # Reached end of recorded trajectory without failure or intervention
                pass

        n_assets = len(asset_trajectories)
        return {
            "policy": policy_type,
            "total_cost": float(total_cost),
            "mean_cost_per_asset": float(total_cost / n_assets) if n_assets > 0 else 0.0,
            "catastrophic_failures": int(n_unplanned_failures),
            "planned_preventive": int(n_planned_preventive),
            "total_wasted_cycles": float(total_wasted_cycles),
        }


class MultiAssetConstrainedFleetScheduler:
    """
    Fleet-wide budget-constrained maintenance optimization solver.
    Solves the multi-asset knapsack dispatch problem:
        max sum_{i in A} P_fail(i) * C_fail(i)
        subject to sum_{i in A} C_prev(i) <= Budget
    Comparing UQ-guided Expected Loss Reduction vs Deterministic Point Ranking.
    """

    def __init__(
        self,
        planning_horizon: int = 15,
        default_cost_preventive: float = 1200.0,
        default_cost_failure: float = 12500.0,
    ):
        self.horizon = planning_horizon
        self.c_prev = default_cost_preventive
        self.c_fail = default_cost_failure

    def optimize_fleet_dispatch(
        self,
        asset_states: List[Dict[str, float]],
        budget_envelope: float,
        strategy: str = "uq_risk",
    ) -> Dict[str, Any]:
        """
        Dispatches maintenance across a portfolio of assets under budget envelope.
        
        Args:
            asset_states: List of dicts, each with keys:
                - 'asset_id': int
                - 'mu_pred': float (mean RUL point estimate)
                - 'lower_cqr': float (calibrated lower bound)
                - 'sigma_total': float (predictive uncertainty)
                - 'cost_prev': optional float
                - 'cost_fail': optional float
            budget_envelope: Total available budget for the cycle
            strategy: 'uq_risk' (Benefit/Cost ratio using tail risk) or 'deterministic' (greedy by lowest point RUL)
        """
        from scipy.stats import norm
        ranked_items = []

        for asset in asset_states:
            aid = asset["asset_id"]
            r_pred = asset["mu_pred"]
            r_low = asset.get("lower_cqr", r_pred)
            sigma = max(asset.get("sigma_total", 5.0), 1e-4)
            c_p = asset.get("cost_prev", self.c_prev)
            c_f = asset.get("cost_fail", self.c_fail)

            # Tail failure probability within horizon
            p_fail = float(norm.cdf((self.horizon - r_pred) / sigma))
            expected_failure_loss = p_fail * c_f

            if strategy == "uq_risk":
                # Priority index: Expected Loss Mitigated per dollar of intervention
                priority_index = expected_failure_loss / max(c_p, 1.0)
            elif strategy == "deterministic":
                # Conventional heuristic: prioritize lowest point prediction RUL
                priority_index = 1.0 / max(r_pred, 0.1)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")

            ranked_items.append({
                "asset_id": aid,
                "r_pred": r_pred,
                "r_low": r_low,
                "p_fail": p_fail,
                "c_prev": c_p,
                "c_fail": c_f,
                "expected_loss": expected_failure_loss,
                "priority_index": priority_index,
            })

        # Sort descending by priority index
        ranked_items.sort(key=lambda x: x["priority_index"], reverse=True)

        dispatched_assets = []
        spent_budget = 0.0
        mitigated_risk = 0.0

        for item in ranked_items:
            if spent_budget + item["c_prev"] <= budget_envelope:
                dispatched_assets.append(item["asset_id"])
                spent_budget += item["c_prev"]
                mitigated_risk += item["expected_loss"]

        return {
            "strategy": strategy,
            "budget_envelope": budget_envelope,
            "spent_budget": spent_budget,
            "dispatched_count": len(dispatched_assets),
            "dispatched_asset_ids": dispatched_assets,
            "mitigated_expected_risk": mitigated_risk,
        }

