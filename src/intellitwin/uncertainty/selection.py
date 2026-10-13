"""Validation-only leave-one-engine-out development and candidate selection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.decision.policies import load_primary_reference_cost, lower_bound_one_cycle_policy
from intellitwin.simulator.costs import MaintenanceCostConfig
from intellitwin.simulator.engine import simulate_engine_trajectory
from intellitwin.simulator.types import PredictionState
from intellitwin.uncertainty.metrics import compute_engine_weighted_interval_metrics
from intellitwin.uncertainty.quantiles import compute_engine_weighted_dev_quantile
from intellitwin.uncertainty.schema import (
    ALL_NINE_CANDIDATES,
    IDENTITY_CANDIDATE_ID,
    METHOD_GLOBAL,
    METHOD_REGIME,
    CandidateConfig,
)
from intellitwin.uncertainty.scores import (
    compute_absolute_residual_score,
    compute_decision_aware_score,
    invert_score_to_interval,
)


@dataclass
class EngineReplayResult:
    """Simulation replay result for a single engine under a specific candidate and seed."""

    unit: int
    seed: int
    method_or_candidate: str
    total_cost: float
    failure: bool
    pm: bool
    wasted_rul: float
    picp: float
    mpiw: float
    interval_score: float
    regime_picp: dict[str, float]


@dataclass
class CandidateAggregateResult:
    """Aggregated development performance for a candidate or baseline."""

    candidate_id: str
    marginal_picp: float
    regime_picp: dict[str, float]
    mpiw: float
    interval_score: float
    mean_cost: float
    failure_rate: float
    total_failures: int
    pm_rate: float
    total_pms: int
    mean_wasted_rul: float
    pm_wasted_rul_mean: float | None
    is_feasible: bool
    feasibility_reasons: list[str]


def run_leave_one_engine_out_evaluation(
    df_val_preds: pd.DataFrame,
    cost_config: MaintenanceCostConfig | None = None,
) -> tuple[
    dict[str, CandidateAggregateResult],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Execute validation leave-one-engine-out evaluation across 5 seeds.

    Parameters
    ----------
    df_val_preds : pd.DataFrame
        DataFrame containing validation predictions across all 5 seeds with columns:
        ['seed', 'unit', 'endpoint_cycle', 'rul_true', 'prediction', 'regime']
    cost_config : MaintenanceCostConfig, optional
        Cost parameters. Defaults to primary_reference.

    Returns
    -------
    tuple
        (candidate_aggregates, engine_seed_records, regime_summary_records, fold_thresholds_record)
    """
    if cost_config is None:
        cost_config = load_primary_reference_cost()

    seeds = sorted(df_val_preds["seed"].unique())
    units = sorted(df_val_preds["unit"].unique())

    # 1. Determine eligible regimes from complete validation metadata (>= 10 engines)
    regime_engine_counts: dict[str, set[int]] = defaultdict(set)
    for _, row in df_val_preds.iterrows():
        regime_engine_counts[str(row["regime"])].add(int(row["unit"]))

    eligible_regimes = sorted(
        [reg for reg, eids in regime_engine_counts.items() if len(eids) >= 10]
    )

    methods_and_candidates: list[str] = [METHOD_GLOBAL, METHOD_REGIME] + [
        c.candidate_id for c in ALL_NINE_CANDIDATES
    ]

    engine_seed_records: list[dict[str, Any]] = []
    fold_thresholds_record: dict[str, Any] = defaultdict(dict)

    # Group predictions by (seed, unit) for fast trajectory access
    # Calculate true failure cycle T_i per unit from validation data
    true_T: dict[int, int] = {}
    for unit, grp in df_val_preds.groupby("unit"):
        max_cyc = int(grp["endpoint_cycle"].max())
        rul_at_max = float(grp.loc[grp["endpoint_cycle"] == max_cyc, "rul_true"].iloc[0])
        true_T[int(unit)] = max_cyc + int(round(rul_at_max))

    # Evaluate across all seeds and held-out validation engines
    for seed in seeds:
        df_seed = df_val_preds[df_val_preds["seed"] == seed]

        for held_out_unit in units:
            df_train = df_seed[df_seed["unit"] != held_out_unit]
            df_test = df_seed[df_seed["unit"] == held_out_unit].sort_values("endpoint_cycle")

            # Pre-compute thresholds for all candidates on other validation engines
            thresholds_by_target: dict[str, dict[str, float]] = {}

            # Global & Regime baselines (absolute residual)
            train_abs_scores = compute_absolute_residual_score(
                df_train["prediction"].to_numpy(), df_train["rul_true"].to_numpy()
            )
            global_q_abs = compute_engine_weighted_dev_quantile(
                engine_ids=df_train["unit"].to_numpy(),
                endpoint_cycles=df_train["endpoint_cycle"].to_numpy(),
                scores=train_abs_scores,
                nominal_coverage=0.90,
            )

            regime_q_abs: dict[str, float] = {}
            for reg in regime_engine_counts.keys():
                reg_mask = df_train["regime"] == reg
                train_reg_eids = df_train.loc[reg_mask, "unit"].to_numpy()
                other_engine_count = len(set(train_reg_eids))
                if other_engine_count >= 10:
                    reg_q = compute_engine_weighted_dev_quantile(
                        engine_ids=train_reg_eids,
                        endpoint_cycles=df_train.loc[reg_mask, "endpoint_cycle"].to_numpy(),
                        scores=train_abs_scores[reg_mask],
                        nominal_coverage=0.90,
                    )
                    regime_q_abs[reg] = reg_q
                else:
                    regime_q_abs[reg] = global_q_abs

            thresholds_by_target[METHOD_GLOBAL] = {"global": global_q_abs}
            thresholds_by_target[METHOD_REGIME] = {
                "global": global_q_abs,
                **{f"regime_{r}": q for r, q in regime_q_abs.items()},
            }

            # Evaluate each proposed candidate
            for cand in ALL_NINE_CANDIDATES:
                train_cand_scores = compute_decision_aware_score(
                    df_train["prediction"].to_numpy(),
                    df_train["rul_true"].to_numpy(),
                    cand,
                )
                cand_global_q = compute_engine_weighted_dev_quantile(
                    engine_ids=df_train["unit"].to_numpy(),
                    endpoint_cycles=df_train["endpoint_cycle"].to_numpy(),
                    scores=train_cand_scores,
                    nominal_coverage=0.90,
                )
                cand_reg_q: dict[str, float] = {}
                for reg in regime_engine_counts.keys():
                    reg_mask = df_train["regime"] == reg
                    train_reg_eids = df_train.loc[reg_mask, "unit"].to_numpy()
                    other_engine_count = len(set(train_reg_eids))
                    if other_engine_count >= 10:
                        rq = compute_engine_weighted_dev_quantile(
                            engine_ids=train_reg_eids,
                            endpoint_cycles=df_train.loc[reg_mask, "endpoint_cycle"].to_numpy(),
                            scores=train_cand_scores[reg_mask],
                            nominal_coverage=0.90,
                        )
                        cand_reg_q[reg] = rq
                    else:
                        cand_reg_q[reg] = cand_global_q

                thresholds_by_target[cand.candidate_id] = {
                    "global": cand_global_q,
                    **{f"regime_{r}": rq for r, rq in cand_reg_q.items()},
                }

            fold_thresholds_record[f"seed_{seed}"][f"held_out_{held_out_unit}"] = (
                thresholds_by_target
            )

            # Now generate intervals and run replay for held-out engine
            test_preds = df_test["prediction"].to_numpy()
            test_labels = df_test["rul_true"].to_numpy()
            test_regimes = df_test["regime"].to_numpy()
            test_cycles = df_test["endpoint_cycle"].to_numpy()
            t_failure = true_T[held_out_unit]

            for item_id in methods_and_candidates:
                # Determine threshold per endpoint
                th_dict = thresholds_by_target[item_id]
                cand_obj = (
                    CandidateConfig.from_id(item_id)
                    if item_id not in (METHOD_GLOBAL, METHOD_REGIME)
                    else None
                )

                ep_thresholds: np.ndarray[Any, Any]
                if item_id == METHOD_GLOBAL:
                    ep_thresholds = np.full(len(test_preds), th_dict["global"], dtype=np.float64)
                    cand_for_invert = None
                elif item_id == METHOD_REGIME:
                    ep_thresholds = np.array(
                        [th_dict.get(f"regime_{r}", th_dict["global"]) for r in test_regimes],
                        dtype=np.float64,
                    )
                    cand_for_invert = None
                else:
                    assert cand_obj is not None
                    ep_thresholds = np.array(
                        [th_dict.get(f"regime_{r}", th_dict["global"]) for r in test_regimes],
                        dtype=np.float64,
                    )
                    cand_for_invert = cand_obj

                lower, upper = invert_score_to_interval(
                    predictions=test_preds,
                    threshold=ep_thresholds,
                    candidate=cand_for_invert,
                )

                # Interval metrics over endpoints 30..T
                int_metrics = compute_engine_weighted_interval_metrics(
                    engine_ids=np.full(len(test_preds), held_out_unit),
                    endpoint_cycles=test_cycles,
                    labels=test_labels,
                    lower=lower,
                    upper=upper,
                    regimes=test_regimes,
                    alpha=0.10,
                )

                # Maintenance simulation over cycles 30..T-1
                # Prepare states for cycles < t_failure
                states: list[PredictionState] = []
                for cyc, p_val, l_val, u_val, reg_val in zip(
                    test_cycles, test_preds, lower, upper, test_regimes, strict=True
                ):
                    if cyc < t_failure:
                        reg_s = str(reg_val)
                        reg_int: int | None = (
                            int(reg_s[1:])
                            if reg_s.startswith("C") and reg_s[1:].isdigit()
                            else None
                        )
                        states.append(
                            PredictionState(
                                engine_id=held_out_unit,
                                cycle=int(cyc),
                                point_rul=float(p_val),
                                lower_rul=float(l_val),
                                upper_rul=float(u_val),
                                regime=reg_int,
                            )
                        )

                sim_res = simulate_engine_trajectory(
                    engine_id=held_out_unit,
                    failure_cycle=t_failure,
                    states=states,
                    policy=lower_bound_one_cycle_policy,
                    cost_config=cost_config,
                )

                rec: dict[str, Any] = {
                    "seed": seed,
                    "unit": held_out_unit,
                    "candidate_id": item_id,
                    "cost": float(sim_res.total_simulated_cost),
                    "failure": int(sim_res.failure_indicator),
                    "pm": int(sim_res.preventive_maintenance_indicator),
                    "wasted_rul": float(sim_res.wasted_rul),
                    "picp": float(int_metrics["marginal_picp"]),
                    "mpiw": float(int_metrics["mpiw"]),
                    "interval_score": float(int_metrics["interval_score"]),
                }
                for reg, cov in int_metrics.get("regime_picp", {}).items():
                    rec[f"picp_regime_{reg}"] = float(cov)

                engine_seed_records.append(rec)

    # 2. Aggregation: within engine across seeds, then equally across engines
    df_es = pd.DataFrame(engine_seed_records)

    candidate_aggregates: dict[str, CandidateAggregateResult] = {}
    regime_summary_records: list[dict[str, Any]] = []

    # First get regime baseline metrics for feasibility comparison
    regime_baseline_mpiw = 0.0
    regime_baseline_is = 0.0
    global_total_failures = 0
    regime_total_failures = 0

    for item_id in methods_and_candidates:
        df_item = df_es[df_es["candidate_id"] == item_id]

        # Engine level mean across 5 seeds
        df_eng = df_item.groupby("unit").mean(numeric_only=True).reset_index()

        mean_cost = float(df_eng["cost"].mean())
        marginal_picp = float(df_eng["picp"].mean())
        mpiw = float(df_eng["mpiw"].mean())
        interval_score = float(df_eng["interval_score"].mean())
        failure_rate = float(df_eng["failure"].mean())
        pm_rate = float(df_eng["pm"].mean())
        mean_wasted_rul = float(df_eng["wasted_rul"].mean())

        total_failures = int(df_item["failure"].sum())
        total_pms = int(df_item["pm"].sum())

        pm_only_wasted = df_item.loc[df_item["pm"] == 1, "wasted_rul"]
        pm_wasted_mean = float(pm_only_wasted.mean()) if len(pm_only_wasted) > 0 else None

        # Regime coverage: average per contributing engine across seeds, then average across engines
        regime_picp_agg: dict[str, float] = {}
        for reg in eligible_regimes:
            col = f"picp_regime_{reg}"
            if col in df_eng.columns:
                valid_eng_cov = df_eng[col].dropna()
                if len(valid_eng_cov) > 0:
                    reg_cov_mean = float(valid_eng_cov.mean())
                    regime_picp_agg[reg] = reg_cov_mean
                    regime_summary_records.append(
                        {
                            "candidate_id": item_id,
                            "regime": reg,
                            "contributing_engines": len(valid_eng_cov),
                            "regime_picp": reg_cov_mean,
                        }
                    )

        if item_id == METHOD_REGIME:
            regime_baseline_mpiw = mpiw
            regime_baseline_is = interval_score
            regime_total_failures = total_failures
        elif item_id == METHOD_GLOBAL:
            global_total_failures = total_failures

        candidate_aggregates[item_id] = CandidateAggregateResult(
            candidate_id=item_id,
            marginal_picp=marginal_picp,
            regime_picp=regime_picp_agg,
            mpiw=mpiw,
            interval_score=interval_score,
            mean_cost=mean_cost,
            failure_rate=failure_rate,
            total_failures=total_failures,
            pm_rate=pm_rate,
            total_pms=total_pms,
            mean_wasted_rul=mean_wasted_rul,
            pm_wasted_rul_mean=pm_wasted_mean,
            is_feasible=True,  # will check below
            feasibility_reasons=[],
        )

    # 3. Check feasibility for each candidate
    for cand in ALL_NINE_CANDIDATES:
        cid = cand.candidate_id
        res = candidate_aggregates[cid]
        reasons: list[str] = []

        # marginal PICP in [0.85, 0.95]
        if not (0.85 <= res.marginal_picp <= 0.95):
            reasons.append(f"Marginal PICP {res.marginal_picp:.4f} outside [0.85, 0.95]")

        # PICP(g) in [0.85, 0.95] for every eligible regime
        for reg in eligible_regimes:
            cov = res.regime_picp.get(reg)
            if cov is None or not (0.85 <= cov <= 0.95):
                cov_str = f"{cov:.4f}" if cov is not None else "None"
                reasons.append(f"Regime {reg} PICP {cov_str} outside [0.85, 0.95]")

        # MPIW_candidate - MPIW_regime <= 1.0 cycle
        mpiw_diff = res.mpiw - regime_baseline_mpiw
        if mpiw_diff > 1.0:
            reasons.append(f"MPIW inflation {mpiw_diff:.4f} > 1.0 cycle")

        # IS_candidate - IS_regime <= 1.0 cycle
        is_diff = res.interval_score - regime_baseline_is
        if is_diff > 1.0:
            reasons.append(f"Interval score inflation {is_diff:.4f} > 1.0 cycle")

        # Observed failure rate no greater than global_hcp and regime_hcp (exact count comparison)
        if res.total_failures > global_total_failures:
            reasons.append(
                f"Failures ({res.total_failures}) exceed global_hcp ({global_total_failures})"
            )
        if res.total_failures > regime_total_failures:
            reasons.append(
                f"Failures ({res.total_failures}) exceed regime_hcp ({regime_total_failures})"
            )

        res.is_feasible = len(reasons) == 0
        res.feasibility_reasons = reasons

    return (
        candidate_aggregates,
        engine_seed_records,
        regime_summary_records,
        dict(fold_thresholds_record),
    )


def select_winning_candidate(
    candidate_aggregates: dict[str, CandidateAggregateResult],
) -> tuple[CandidateConfig, str, list[dict[str, Any]]]:
    """Select winning candidate among feasible candidates with deterministic tie-breaking.

    Tie-breaking Order:
        1. Identity candidate (gamma0_beta0), if present in tie.
        2. Smaller gamma.
        3. Smaller absolute beta.
        4. Smaller signed beta.

    Fallback:
        If no candidate is feasible, select gamma0_beta0 with status
        "fallback_no_feasible_candidate".

    Parameters
    ----------
    candidate_aggregates : dict[str, CandidateAggregateResult]
        Dictionary of aggregated candidate results.

    Returns
    -------
    tuple
        (selected_candidate, selection_status, tie_breaking_log)
    """
    feasible_cands = [
        CandidateConfig.from_id(cid)
        for cid, res in candidate_aggregates.items()
        if cid in [c.candidate_id for c in ALL_NINE_CANDIDATES] and res.is_feasible
    ]

    tie_log: list[dict[str, Any]] = []

    if not feasible_cands:
        return (
            CandidateConfig.from_id(IDENTITY_CANDIDATE_ID),
            "fallback_no_feasible_candidate",
            [{"event": "no_feasible_candidate", "selected": IDENTITY_CANDIDATE_ID}],
        )

    # Find minimum cost
    min_cost = min(candidate_aggregates[c.candidate_id].mean_cost for c in feasible_cands)

    # Tied candidates within 1e-8 SCU
    tied_cands = [
        c
        for c in feasible_cands
        if abs(candidate_aggregates[c.candidate_id].mean_cost - min_cost) <= 1e-8
    ]

    tie_log.append(
        {
            "event": "evaluated_feasible",
            "feasible_count": len(feasible_cands),
            "min_cost": min_cost,
            "tied_count": len(tied_cands),
            "tied_candidates": [c.candidate_id for c in tied_cands],
        }
    )

    if len(tied_cands) == 1:
        return tied_cands[0], "feasible_optimal", tie_log

    # Tie-breaking rule 1: Identity candidate if present
    for c in tied_cands:
        if c.candidate_id == IDENTITY_CANDIDATE_ID:
            tie_log.append({"event": "tie_broken_identity", "selected": c.candidate_id})
            return c, "feasible_optimal_tied", tie_log

    # Tie-breaking rules 2, 3, 4:
    # Sort key: (gamma, abs(beta), beta)
    sorted_tied = sorted(tied_cands, key=lambda c: (c.gamma, abs(c.beta), c.beta))
    winner = sorted_tied[0]
    tie_log.append(
        {
            "event": "tie_broken_parameters",
            "selected": winner.candidate_id,
            "sort_key": (winner.gamma, abs(winner.beta), winner.beta),
        }
    )
    return winner, "feasible_optimal_tied", tie_log
