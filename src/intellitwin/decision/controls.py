"""Prespecified benchmark control families and validation-only parameter selection.

Implements the four prespecified matched-conservatism controls for RQ3:
A. matched_width_interval (matched to proposed validation MPIW)
B. widened_interval (cost-optimal lambda >= 1.0)
C. point_safety_margin (cost-optimal m in 0..250 cycles)
D. earlier_intervention (cost-optimal h in 1..251 cycles)

Selection is performed strictly on FD002 validation engines across 5 seeds.
Calibration and test engines are strictly forbidden.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.splits import load_split_manifest
from intellitwin.evaluation.schema import (
    CONTROL_EARLIER_INTERVENTION,
    CONTROL_MATCHED_WIDTH,
    CONTROL_SAFETY_MARGIN,
    CONTROL_WIDENED,
    COST_SCENARIOS,
    INTERVENTION_THRESHOLD_CYCLES,
    PRIMARY_COST_SCENARIO,
    CostScenario,
)
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
)
from intellitwin.simulator.types import (
    MaintenanceAction,
    PredictionState,
)
from intellitwin.uncertainty.artifacts import (
    load_frozen_calibrator,
    resolve_repo_relative_path,
)

# Grids
SOURCES: Final[tuple[str, ...]] = ("global_hcp", "regime_hcp")

# A. Matched width: k/100 for k in 1..400 plus {5, 6, 8, 12, 16}
_MATCHED_LAMBDAS = [round(k / 100.0, 4) for k in range(1, 401)] + [5.0, 6.0, 8.0, 12.0, 16.0]
GRID_MATCHED_WIDTH_LAMBDA: Final[tuple[float, ...]] = tuple(sorted(set(_MATCHED_LAMBDAS)))

# B. Widened: k/100 for k in 100..400 plus {5, 6, 8, 12, 16} (lambda >= 1.0)
_WIDENED_LAMBDAS = [round(k / 100.0, 4) for k in range(100, 401)] + [5.0, 6.0, 8.0, 12.0, 16.0]
GRID_WIDENED_LAMBDA: Final[tuple[float, ...]] = tuple(sorted(set(_WIDENED_LAMBDAS)))

# C. Point safety margin: m in 0..250 cycles
GRID_SAFETY_MARGIN_M: Final[tuple[int, ...]] = tuple(range(0, 251))

# D. Earlier intervention: h in 1..251 cycles
GRID_EARLIER_INTERVENTION_H: Final[tuple[int, ...]] = tuple(range(1, 252))

TIE_TOLERANCE: Final[float] = 1e-8


@dataclass(frozen=True)
class SimulationOutcome:
    """Outcome of running an observable policy on a single engine trajectory."""

    unit: int
    seed: int
    control_id: str
    failure_cycle: int
    terminal_event: str  # "PM" or "FAILURE"
    intervention_cycle: int | None
    failed: bool
    pm_occurred: bool
    wasted_rul: float
    total_cost: float
    is_cost_inefficient_early_pm: bool
    decision_trace: list[tuple[int, str]]  # (cycle, action_str)


def simulate_observable_trajectory(
    unit: int,
    seed: int,
    control_id: str,
    cycles: np.ndarray[Any, Any],
    predictions: np.ndarray[Any, Any],
    lower_bounds: np.ndarray[Any, Any],
    upper_bounds: np.ndarray[Any, Any],
    regimes: np.ndarray[Any, Any],
    failure_cycle: int,
    policy_fn: Any,
    scenario: CostScenario,
) -> SimulationOutcome:
    """Simulate sequential maintenance on a single complete engine trajectory.

    Rules:
    - Endpoints run from cycle 30 through T.
    - Maintenance decisions occur on cycles 30 through T-1.
    - No action occurs at cycle T (failure occurs if not maintained by T-1).
    - Policy receives observable state only (no true RUL, failure cycle, or oracle data).
    - First MAINTAIN_NOW terminates the episode.
    """
    trace: list[tuple[int, str]] = []
    intervention_cycle: int | None = None
    terminal_event = "FAILURE"
    pm_occurred = False
    failed = True
    wasted_rul = 0.0

    n_pts = len(cycles)
    for i in range(n_pts):
        cyc = int(cycles[i])
        if cyc >= failure_cycle:
            break

        state = PredictionState(
            engine_id=unit,
            cycle=cyc,
            point_rul=float(predictions[i]),
            lower_rul=float(lower_bounds[i]),
            upper_rul=float(upper_bounds[i]),
            regime=int(str(regimes[i]).replace("C", "")),
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

    return SimulationOutcome(
        unit=unit,
        seed=seed,
        control_id=control_id,
        failure_cycle=failure_cycle,
        terminal_event=terminal_event,
        intervention_cycle=intervention_cycle,
        failed=failed,
        pm_occurred=pm_occurred,
        wasted_rul=wasted_rul,
        total_cost=cost,
        is_cost_inefficient_early_pm=early_pm,
        decision_trace=trace,
    )


def compute_fleet_outcomes(
    df_cell: pd.DataFrame,
    control_id: str,
    policy_fn: Any,
    lower_col: str,
    upper_col: str,
    scenario: CostScenario,
    engine_lifetimes: dict[int, int],
) -> tuple[dict[str, float], list[SimulationOutcome]]:
    """Simulate fleet of engines across 5 seeds and compute equal-engine metrics."""
    outcomes: list[SimulationOutcome] = []

    for (unit, seed), grp in df_cell.groupby(["unit", "seed"]):
        grp_sorted = grp.sort_values("endpoint_cycle")
        T = engine_lifetimes[int(unit)]
        out = simulate_observable_trajectory(
            unit=int(unit),
            seed=int(seed),
            control_id=control_id,
            cycles=grp_sorted["endpoint_cycle"].to_numpy(),
            predictions=grp_sorted["prediction"].to_numpy(),
            lower_bounds=grp_sorted[lower_col].to_numpy(),
            upper_bounds=grp_sorted[upper_col].to_numpy(),
            regimes=grp_sorted["regime"].to_numpy(),
            failure_cycle=T,
            policy_fn=policy_fn,
            scenario=scenario,
        )
        outcomes.append(out)

    df_out = pd.DataFrame(
        [
            {
                "unit": o.unit,
                "seed": o.seed,
                "cost": o.total_cost,
                "failed": 1.0 if o.failed else 0.0,
                "pm": 1.0 if o.pm_occurred else 0.0,
                "wasted_rul": o.wasted_rul,
                "early_pm": 1.0 if o.is_cost_inefficient_early_pm else 0.0,
            }
            for o in outcomes
        ]
    )

    engine_avgs = df_out.groupby("unit").mean()
    mean_cost = float(engine_avgs["cost"].mean())
    failure_rate = float(engine_avgs["failed"].mean())
    pm_rate = float(engine_avgs["pm"].mean())
    mean_wasted_rul = float(engine_avgs["wasted_rul"].mean())
    fleet_early_pm_rate = float(engine_avgs["early_pm"].mean())

    pm_rows = df_out[df_out["pm"] > 0]
    pm_early_rate = float(pm_rows["early_pm"].mean()) if len(pm_rows) > 0 else float("nan")
    pm_wasted_mean = float(pm_rows["wasted_rul"].mean()) if len(pm_rows) > 0 else float("nan")

    metrics = {
        "mean_cost": mean_cost,
        "failure_rate": failure_rate,
        "pm_rate": pm_rate,
        "mean_wasted_rul": mean_wasted_rul,
        "fleet_early_pm_rate": fleet_early_pm_rate,
        "pm_only_early_pm_rate": pm_early_rate,
        "pm_wasted_rul_mean": pm_wasted_mean,
        "total_failures": int(df_out["failed"].sum()),
        "total_pms": int(df_out["pm"].sum()),
    }
    return metrics, outcomes


def compute_engine_weighted_mpiw(
    df_cell: pd.DataFrame,
    lower_col: str,
    upper_col: str,
) -> float:
    """Compute engine-weighted 5-seed-averaged MPIW using clipped lower bounds."""
    widths = df_cell[upper_col].to_numpy() - df_cell[lower_col].to_numpy()
    df_w = pd.DataFrame(
        {
            "unit": df_cell["unit"],
            "seed": df_cell["seed"],
            "width": widths,
        }
    )
    # Mean width per unit-seed
    unit_seed_w = df_w.groupby(["unit", "seed"])["width"].mean().reset_index()
    # Mean across seeds for each engine
    engine_w = unit_seed_w.groupby("unit")["width"].mean()
    # Equal engine mean
    return float(engine_w.mean())


@dataclass(frozen=True)
class FastTrajectory:
    unit: int
    seed: int
    unit_idx: int
    seed_idx: int
    failure_cycle: int
    obs_cycles: np.ndarray
    obs_predictions: np.ndarray
    obs_q_global: np.ndarray
    obs_q_regime: np.ndarray
    obs_lower_global: np.ndarray
    obs_lower_regime: np.ndarray
    all_predictions: np.ndarray
    all_q_global: np.ndarray
    all_q_regime: np.ndarray


def _eval_candidate_sim(
    trajectories: list[FastTrajectory],
    n_units: int,
    n_seeds: int,
    scenario: CostScenario,
    get_cond: Callable[[FastTrajectory], np.ndarray],
) -> dict[str, float]:
    costs = np.zeros((n_units, n_seeds), dtype=float)
    failed_arr = np.zeros((n_units, n_seeds), dtype=float)
    pm_arr = np.zeros((n_units, n_seeds), dtype=float)
    wasted_arr = np.zeros((n_units, n_seeds), dtype=float)
    early_pm_arr = np.zeros((n_units, n_seeds), dtype=float)

    for t in trajectories:
        cond = get_cond(t)
        m_idxs = np.where(cond)[0]
        if len(m_idxs) > 0:
            idx = int(m_idxs[0])
            inter_cyc = int(t.obs_cycles[idx])
            wasted = float(t.failure_cycle - inter_cyc)
            cost = scenario.c_pm + scenario.c_waste * wasted
            failed = 0.0
            pm = 1.0
            early_pm = 1.0 if wasted > scenario.r_equal else 0.0
        else:
            cost = scenario.c_fail
            failed = 1.0
            pm = 0.0
            wasted = 0.0
            early_pm = 0.0

        costs[t.unit_idx, t.seed_idx] = cost
        failed_arr[t.unit_idx, t.seed_idx] = failed
        pm_arr[t.unit_idx, t.seed_idx] = pm
        wasted_arr[t.unit_idx, t.seed_idx] = wasted
        early_pm_arr[t.unit_idx, t.seed_idx] = early_pm

    mean_cost = float(np.mean(np.mean(costs, axis=1)))
    failure_rate = float(np.mean(np.mean(failed_arr, axis=1)))
    pm_rate = float(np.mean(np.mean(pm_arr, axis=1)))
    mean_wasted_rul = float(np.mean(np.mean(wasted_arr, axis=1)))
    fleet_early_pm_rate = float(np.mean(np.mean(early_pm_arr, axis=1)))

    pm_mask = pm_arr > 0
    pm_only_early_pm_rate = (
        float(np.mean(early_pm_arr[pm_mask])) if np.any(pm_mask) else float("nan")
    )
    pm_wasted_rul_mean = float(np.mean(wasted_arr[pm_mask])) if np.any(pm_mask) else float("nan")

    return {
        "mean_cost": mean_cost,
        "failure_rate": failure_rate,
        "pm_rate": pm_rate,
        "mean_wasted_rul": mean_wasted_rul,
        "fleet_early_pm_rate": fleet_early_pm_rate,
        "pm_only_early_pm_rate": pm_only_early_pm_rate,
        "pm_wasted_rul_mean": pm_wasted_rul_mean,
        "total_failures": int(np.sum(failed_arr)),
        "total_pms": int(np.sum(pm_arr)),
    }


def _eval_candidate_mpiw(
    trajectories: list[FastTrajectory],
    n_units: int,
    n_seeds: int,
    src: str,
    lam: float,
) -> float:
    widths = np.zeros((n_units, n_seeds), dtype=float)
    for t in trajectories:
        q_all = t.all_q_global if src == "global_hcp" else t.all_q_regime
        low = np.maximum(0.0, t.all_predictions - lam * q_all)
        upp = t.all_predictions + lam * q_all
        widths[t.unit_idx, t.seed_idx] = float(np.mean(upp - low))
    return float(np.mean(np.mean(widths, axis=1)))


def _make_matched_condition(src: str, lam: float) -> Callable[[FastTrajectory], np.ndarray]:
    def cond(t: FastTrajectory) -> np.ndarray:
        q = t.obs_q_global if src == "global_hcp" else t.obs_q_regime
        return np.maximum(0.0, t.obs_predictions - lam * q) <= INTERVENTION_THRESHOLD_CYCLES

    return cond


def _make_widened_condition(src: str, lam: float) -> Callable[[FastTrajectory], np.ndarray]:
    def cond(t: FastTrajectory) -> np.ndarray:
        q = t.obs_q_global if src == "global_hcp" else t.obs_q_regime
        return np.maximum(0.0, t.obs_predictions - lam * q) <= INTERVENTION_THRESHOLD_CYCLES

    return cond


def _make_safety_condition(m: float | int) -> Callable[[FastTrajectory], np.ndarray]:
    def cond(t: FastTrajectory) -> np.ndarray:
        return t.obs_predictions <= (1.0 + m)

    return cond


def _make_earlier_condition(src: str, h: float | int) -> Callable[[FastTrajectory], np.ndarray]:
    def cond(t: FastTrajectory) -> np.ndarray:
        low = t.obs_lower_global if src == "global_hcp" else t.obs_lower_regime
        return low <= float(h)

    return cond


def run_fd002_control_selection(
    model_family: str,
    base_dir: Path | str = ".",
    scenario_id: str = PRIMARY_COST_SCENARIO,
    allow_dirty: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Select prespecified benchmark controls for FD002 on validation engines only.

    Strict Requirements:
    - FD002 validation engines only (26 engines).
    - Training, calibration, and test partitions are strictly rejected.
    - Joint parameter selection over all 5 frozen seeds (never per seed/engine/regime/scenario).
    - Frozen calibrators at 90% nominal coverage.
    - primary_reference cost scenario for objective function.
    """
    base = Path(base_dir).resolve()
    scenario = COST_SCENARIOS[scenario_id]

    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty)
    env_meta = capture_environment_metadata()

    # 1. Load FD002 split manifest and verify validation engines
    split_p = resolve_repo_relative_path(base, "data/splits/fd002_engine_split_seed_2026.json")
    split_data = load_split_manifest(split_p)
    valid_engines = set(split_data.get_partition("validation"))
    train_engines = set(split_data.get_partition("train"))
    cal_engines = set(split_data.get_partition("calibration"))
    test_engines = set(split_data.get_partition("test"))

    # 2. Load validation prediction caches for all 5 seeds
    dfs: list[pd.DataFrame] = []
    input_file_hashes: dict[str, str] = {
        "split_manifest": compute_sha256(split_p),
    }

    for seed in (2026, 2027, 2028, 2029, 2030):
        cache_p = resolve_repo_relative_path(
            base,
            f"experiments/calibration/point_predictions/validation/FD002/{model_family}/seed_{seed}.csv",
        )
        input_file_hashes[f"pred_cache_seed_{seed}"] = compute_sha256(cache_p)
        df_s = pd.read_csv(cache_p)
        df_s["seed"] = seed

        # Anti-leakage assertions
        units = set(df_s["unit"].astype(int))
        if units != valid_engines:
            raise ValueError(f"Validation cache {cache_p} contains non-validation engines!")
        if units.intersection(train_engines):
            raise RuntimeError("Train engines detected in control selection input!")
        if units.intersection(cal_engines):
            raise RuntimeError("Calibration engines detected in control selection input!")
        if units.intersection(test_engines):
            raise RuntimeError("Test engines detected in control selection input!")

        # 3. Generate intervals using frozen 90% calibrators
        for method in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
            cal = load_frozen_calibrator(
                dataset="FD002",
                model_family=model_family,
                seed=seed,
                method_id=method,
                base_dir=base,
            )
            cal_rel = (
                f"experiments/calibration/fitted/FD002/{model_family}/"
                f"seed_{seed}/{method}/calibrator.json"
            )
            cal_path = base / cal_rel
            input_file_hashes[f"calibrator_{method}_seed_{seed}"] = compute_sha256(cal_path)
            low, upp, _ = cal.predict_intervals(
                predictions=df_s["prediction"].to_numpy(),
                regimes=df_s["regime"].to_numpy(),
                nominal_coverage=0.90,
            )
            df_s[f"lower_{method}"] = low
            df_s[f"upper_{method}"] = upp

        dfs.append(df_s)

    df_val = pd.concat(dfs, ignore_index=True)

    # Pre-compute true terminal lifetime T for each validation engine
    engine_lifetimes: dict[int, int] = {}
    for unit, grp in df_val.groupby("unit"):
        max_cyc = int(grp["endpoint_cycle"].max())
        rul_at_max = float(grp.loc[grp["endpoint_cycle"] == max_cyc, "rul_true"].iloc[0])
        engine_lifetimes[int(unit)] = max_cyc + int(round(rul_at_max))

    # Pre-extract fast trajectory representations
    sorted_units = sorted(valid_engines)
    unit_to_idx = {u: i for i, u in enumerate(sorted_units)}
    seed_to_idx = {s: i for i, s in enumerate((2026, 2027, 2028, 2029, 2030))}
    n_units = len(sorted_units)
    n_seeds = 5

    trajectories: list[FastTrajectory] = []
    for (unit, seed), grp in df_val.groupby(["unit", "seed"]):
        grp_sorted = grp.sort_values("endpoint_cycle")
        T = engine_lifetimes[int(unit)]
        cycs = grp_sorted["endpoint_cycle"].to_numpy().astype(int)
        preds = grp_sorted["prediction"].to_numpy().astype(float)
        q_g = (grp_sorted["upper_global_hcp"] - grp_sorted["prediction"]).to_numpy().astype(float)
        q_r = (grp_sorted["upper_regime_hcp"] - grp_sorted["prediction"]).to_numpy().astype(float)
        l_g = grp_sorted["lower_global_hcp"].to_numpy().astype(float)
        l_r = grp_sorted["lower_regime_hcp"].to_numpy().astype(float)

        obs_mask = cycs < T

        trajectories.append(
            FastTrajectory(
                unit=int(unit),
                seed=int(seed),
                unit_idx=unit_to_idx[int(unit)],
                seed_idx=seed_to_idx[int(seed)],
                failure_cycle=T,
                obs_cycles=cycs[obs_mask],
                obs_predictions=preds[obs_mask],
                obs_q_global=q_g[obs_mask],
                obs_q_regime=q_r[obs_mask],
                obs_lower_global=l_g[obs_mask],
                obs_lower_regime=l_r[obs_mask],
                all_predictions=preds,
                all_q_global=q_g,
                all_q_regime=q_r,
            )
        )

    # Compute proposed method's target MPIW
    proposed_target_mpiw = compute_engine_weighted_mpiw(
        df_val,
        lower_col="lower_decision_aware_hcp",
        upper_col="upper_decision_aware_hcp",
    )

    # Pre-compute baseline MPIWs for earlier intervention
    base_mpiws: dict[str, float] = {
        src: compute_engine_weighted_mpiw(
            df_val, lower_col=f"lower_{src}", upper_col=f"upper_{src}"
        )
        for src in SOURCES
    }

    candidate_records: list[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # A. matched_width_interval
    # -------------------------------------------------------------------------
    matched_candidates: list[dict[str, Any]] = []
    for src in SOURCES:
        for lam in GRID_MATCHED_WIDTH_LAMBDA:
            mpiw_val = _eval_candidate_mpiw(trajectories, n_units, n_seeds, src, lam)
            width_diff = abs(mpiw_val - proposed_target_mpiw)

            cond_matched = _make_matched_condition(src, lam)

            metrics = _eval_candidate_sim(
                trajectories,
                n_units,
                n_seeds,
                scenario,
                cond_matched,
            )

            rec = {
                "control_family": CONTROL_MATCHED_WIDTH,
                "interval_source": src,
                "parameter_name": "lambda",
                "parameter_value": lam,
                "achieved_mpiw": mpiw_val,
                "target_mpiw": proposed_target_mpiw,
                "width_diff": width_diff,
                **metrics,
            }
            matched_candidates.append(rec)
            candidate_records.append(rec)

    # Sort & Tie-break for matched_width_interval:
    # 1. Minimize width_diff
    # 2. Width diff within 1e-8 tied -> minimize mean_cost
    # 3. Smaller lambda
    # 4. global_hcp before regime_hcp
    def matched_sort_key(r: dict[str, Any]) -> tuple[Any, ...]:
        w_bucket = round(r["width_diff"] / TIE_TOLERANCE)
        c_bucket = round(r["mean_cost"] / TIE_TOLERANCE)
        src_rank = 0 if r["interval_source"] == "global_hcp" else 1
        return (w_bucket, c_bucket, r["parameter_value"], src_rank)

    matched_candidates.sort(key=matched_sort_key)
    selected_matched = matched_candidates[0]
    matched_boundary = selected_matched["parameter_value"] == min(
        GRID_MATCHED_WIDTH_LAMBDA
    ) or selected_matched["parameter_value"] == max(GRID_MATCHED_WIDTH_LAMBDA)
    matched_width_verified = selected_matched["width_diff"] <= 1.0

    # -------------------------------------------------------------------------
    # B. widened_interval
    # -------------------------------------------------------------------------
    widened_candidates: list[dict[str, Any]] = []
    for src in SOURCES:
        for lam in GRID_WIDENED_LAMBDA:
            mpiw_val = _eval_candidate_mpiw(trajectories, n_units, n_seeds, src, lam)

            cond_widened = _make_widened_condition(src, lam)

            metrics = _eval_candidate_sim(
                trajectories,
                n_units,
                n_seeds,
                scenario,
                cond_widened,
            )

            rec = {
                "control_family": CONTROL_WIDENED,
                "interval_source": src,
                "parameter_name": "lambda",
                "parameter_value": lam,
                "achieved_mpiw": mpiw_val,
                "target_mpiw": proposed_target_mpiw,
                "width_diff": abs(mpiw_val - proposed_target_mpiw),
                **metrics,
            }
            widened_candidates.append(rec)
            candidate_records.append(rec)

    def widened_sort_key(r: dict[str, Any]) -> tuple[Any, ...]:
        c_bucket = round(r["mean_cost"] / TIE_TOLERANCE)
        src_rank = 0 if r["interval_source"] == "global_hcp" else 1
        return (c_bucket, r["parameter_value"], src_rank)

    widened_candidates.sort(key=widened_sort_key)
    selected_widened = widened_candidates[0]
    widened_boundary = selected_widened["parameter_value"] == min(
        GRID_WIDENED_LAMBDA
    ) or selected_widened["parameter_value"] == max(GRID_WIDENED_LAMBDA)

    # -------------------------------------------------------------------------
    # C. point_safety_margin
    # -------------------------------------------------------------------------
    safety_margin_candidates: list[dict[str, Any]] = []
    for m in GRID_SAFETY_MARGIN_M:
        cond_safety = _make_safety_condition(m)

        metrics = _eval_candidate_sim(
            trajectories,
            n_units,
            n_seeds,
            scenario,
            cond_safety,
        )

        rec = {
            "control_family": CONTROL_SAFETY_MARGIN,
            "interval_source": "regime_hcp",  # logged for schema consistency
            "parameter_name": "m",
            "parameter_value": m,
            "achieved_mpiw": float("nan"),
            "target_mpiw": proposed_target_mpiw,
            "width_diff": float("nan"),
            **metrics,
        }
        safety_margin_candidates.append(rec)
        candidate_records.append(rec)

    def safety_sort_key(r: dict[str, Any]) -> tuple[Any, ...]:
        c_bucket = round(r["mean_cost"] / TIE_TOLERANCE)
        return (c_bucket, r["parameter_value"])

    safety_margin_candidates.sort(key=safety_sort_key)
    selected_safety = safety_margin_candidates[0]
    safety_boundary = selected_safety["parameter_value"] == min(
        GRID_SAFETY_MARGIN_M
    ) or selected_safety["parameter_value"] == max(GRID_SAFETY_MARGIN_M)

    # -------------------------------------------------------------------------
    # D. earlier_intervention
    # -------------------------------------------------------------------------
    earlier_candidates: list[dict[str, Any]] = []
    for src in SOURCES:
        base_w = base_mpiws[src]
        for h in GRID_EARLIER_INTERVENTION_H:
            cond_earlier = _make_earlier_condition(src, h)

            metrics = _eval_candidate_sim(
                trajectories,
                n_units,
                n_seeds,
                scenario,
                cond_earlier,
            )

            rec = {
                "control_family": CONTROL_EARLIER_INTERVENTION,
                "interval_source": src,
                "parameter_name": "h",
                "parameter_value": h,
                "achieved_mpiw": base_w,
                "target_mpiw": proposed_target_mpiw,
                "width_diff": float("nan"),
                **metrics,
            }
            earlier_candidates.append(rec)
            candidate_records.append(rec)

    def earlier_sort_key(r: dict[str, Any]) -> tuple[Any, ...]:
        c_bucket = round(r["mean_cost"] / TIE_TOLERANCE)
        src_rank = 0 if r["interval_source"] == "global_hcp" else 1
        return (c_bucket, r["parameter_value"], src_rank)

    earlier_candidates.sort(key=earlier_sort_key)
    selected_earlier = earlier_candidates[0]
    earlier_boundary = selected_earlier["parameter_value"] == min(
        GRID_EARLIER_INTERVENTION_H
    ) or selected_earlier["parameter_value"] == max(GRID_EARLIER_INTERVENTION_H)

    # -------------------------------------------------------------------------
    # Collect Engine-Seed Simulation Outcomes for the 4 Selected Controls
    # -------------------------------------------------------------------------
    selected_outcomes_list: list[dict[str, Any]] = []

    # 1. Matched width
    m_src = selected_matched["interval_source"]
    m_lam = selected_matched["parameter_value"]
    df_val["sel_lower_matched"] = np.maximum(
        0.0, df_val["prediction"] - m_lam * (df_val[f"upper_{m_src}"] - df_val["prediction"])
    )
    df_val["sel_upper_matched"] = df_val["prediction"] + m_lam * (
        df_val[f"upper_{m_src}"] - df_val["prediction"]
    )
    _, outs_m = compute_fleet_outcomes(
        df_cell=df_val,
        control_id=CONTROL_MATCHED_WIDTH,
        policy_fn=lambda s: (
            MaintenanceAction.MAINTAIN_NOW
            if s.lower_rul <= INTERVENTION_THRESHOLD_CYCLES
            else MaintenanceAction.CONTINUE
        ),
        lower_col="sel_lower_matched",
        upper_col="sel_upper_matched",
        scenario=scenario,
        engine_lifetimes=engine_lifetimes,
    )
    for o in outs_m:
        selected_outcomes_list.append(
            {
                "control_id": CONTROL_MATCHED_WIDTH,
                "unit": o.unit,
                "seed": o.seed,
                "terminal_event": o.terminal_event,
                "intervention_cycle": o.intervention_cycle,
                "failed": o.failed,
                "pm": o.pm_occurred,
                "wasted_rul": o.wasted_rul,
                "total_cost": o.total_cost,
                "is_cost_inefficient_early_pm": o.is_cost_inefficient_early_pm,
            }
        )

    # 2. Widened
    w_src = selected_widened["interval_source"]
    w_lam = selected_widened["parameter_value"]
    df_val["sel_lower_widened"] = np.maximum(
        0.0, df_val["prediction"] - w_lam * (df_val[f"upper_{w_src}"] - df_val["prediction"])
    )
    df_val["sel_upper_widened"] = df_val["prediction"] + w_lam * (
        df_val[f"upper_{w_src}"] - df_val["prediction"]
    )
    _, outs_w = compute_fleet_outcomes(
        df_cell=df_val,
        control_id=CONTROL_WIDENED,
        policy_fn=lambda s: (
            MaintenanceAction.MAINTAIN_NOW
            if s.lower_rul <= INTERVENTION_THRESHOLD_CYCLES
            else MaintenanceAction.CONTINUE
        ),
        lower_col="sel_lower_widened",
        upper_col="sel_upper_widened",
        scenario=scenario,
        engine_lifetimes=engine_lifetimes,
    )
    for o in outs_w:
        selected_outcomes_list.append(
            {
                "control_id": CONTROL_WIDENED,
                "unit": o.unit,
                "seed": o.seed,
                "terminal_event": o.terminal_event,
                "intervention_cycle": o.intervention_cycle,
                "failed": o.failed,
                "pm": o.pm_occurred,
                "wasted_rul": o.wasted_rul,
                "total_cost": o.total_cost,
                "is_cost_inefficient_early_pm": o.is_cost_inefficient_early_pm,
            }
        )

    # 3. Point safety margin
    sm_m = int(selected_safety["parameter_value"])
    _, outs_sm = compute_fleet_outcomes(
        df_cell=df_val,
        control_id=CONTROL_SAFETY_MARGIN,
        policy_fn=lambda s: (
            MaintenanceAction.MAINTAIN_NOW
            if s.point_rul <= (1.0 + sm_m)
            else MaintenanceAction.CONTINUE
        ),
        lower_col="lower_regime_hcp",
        upper_col="upper_regime_hcp",
        scenario=scenario,
        engine_lifetimes=engine_lifetimes,
    )
    for o in outs_sm:
        selected_outcomes_list.append(
            {
                "control_id": CONTROL_SAFETY_MARGIN,
                "unit": o.unit,
                "seed": o.seed,
                "terminal_event": o.terminal_event,
                "intervention_cycle": o.intervention_cycle,
                "failed": o.failed,
                "pm": o.pm_occurred,
                "wasted_rul": o.wasted_rul,
                "total_cost": o.total_cost,
                "is_cost_inefficient_early_pm": o.is_cost_inefficient_early_pm,
            }
        )

    # 4. Earlier intervention
    e_src = selected_earlier["interval_source"]
    e_h = float(selected_earlier["parameter_value"])
    _, outs_e = compute_fleet_outcomes(
        df_cell=df_val,
        control_id=CONTROL_EARLIER_INTERVENTION,
        policy_fn=lambda s: (
            MaintenanceAction.MAINTAIN_NOW if s.lower_rul <= e_h else MaintenanceAction.CONTINUE
        ),
        lower_col=f"lower_{e_src}",
        upper_col=f"upper_{e_src}",
        scenario=scenario,
        engine_lifetimes=engine_lifetimes,
    )
    for o in outs_e:
        selected_outcomes_list.append(
            {
                "control_id": CONTROL_EARLIER_INTERVENTION,
                "unit": o.unit,
                "seed": o.seed,
                "terminal_event": o.terminal_event,
                "intervention_cycle": o.intervention_cycle,
                "failed": o.failed,
                "pm": o.pm_occurred,
                "wasted_rul": o.wasted_rul,
                "total_cost": o.total_cost,
                "is_cost_inefficient_early_pm": o.is_cost_inefficient_early_pm,
            }
        )

    df_candidate_metrics = pd.DataFrame(candidate_records)
    df_engine_seed_outcomes = pd.DataFrame(selected_outcomes_list)

    selection_json = {
        "dataset": "FD002",
        "model_family": model_family,
        "status": "DEVELOPMENT_ONLY",
        "notice": (
            "Selected strictly on FD002 validation engines across 5 seeds. "
            "Unbiased test estimates will be obtained during confirmatory evaluation."
        ),
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "cost_scenario": scenario.to_dict(),
        "proposed_target_mpiw": proposed_target_mpiw,
        "validation_engine_count": len(valid_engines),
        "validation_engines": sorted(valid_engines),
        "seeds": [2026, 2027, 2028, 2029, 2030],
        "selected_controls": {
            CONTROL_MATCHED_WIDTH: {
                "control_family": CONTROL_MATCHED_WIDTH,
                "interval_source": selected_matched["interval_source"],
                "parameter_name": "lambda",
                "parameter_value": selected_matched["parameter_value"],
                "achieved_mpiw": selected_matched["achieved_mpiw"],
                "target_mpiw": proposed_target_mpiw,
                "width_diff": selected_matched["width_diff"],
                "width_matched_verified": matched_width_verified,
                "boundary_selection": matched_boundary,
                "metrics": {
                    "mean_cost": selected_matched["mean_cost"],
                    "failure_rate": selected_matched["failure_rate"],
                    "pm_rate": selected_matched["pm_rate"],
                    "mean_wasted_rul": selected_matched["mean_wasted_rul"],
                    "fleet_early_pm_rate": selected_matched["fleet_early_pm_rate"],
                    "pm_only_early_pm_rate": selected_matched["pm_only_early_pm_rate"],
                    "pm_wasted_rul_mean": selected_matched["pm_wasted_rul_mean"],
                },
            },
            CONTROL_WIDENED: {
                "control_family": CONTROL_WIDENED,
                "interval_source": selected_widened["interval_source"],
                "parameter_name": "lambda",
                "parameter_value": selected_widened["parameter_value"],
                "achieved_mpiw": selected_widened["achieved_mpiw"],
                "boundary_selection": widened_boundary,
                "metrics": {
                    "mean_cost": selected_widened["mean_cost"],
                    "failure_rate": selected_widened["failure_rate"],
                    "pm_rate": selected_widened["pm_rate"],
                    "mean_wasted_rul": selected_widened["mean_wasted_rul"],
                    "fleet_early_pm_rate": selected_widened["fleet_early_pm_rate"],
                    "pm_only_early_pm_rate": selected_widened["pm_only_early_pm_rate"],
                    "pm_wasted_rul_mean": selected_widened["pm_wasted_rul_mean"],
                },
            },
            CONTROL_SAFETY_MARGIN: {
                "control_family": CONTROL_SAFETY_MARGIN,
                "interval_source": selected_safety["interval_source"],
                "parameter_name": "m",
                "parameter_value": selected_safety["parameter_value"],
                "boundary_selection": safety_boundary,
                "metrics": {
                    "mean_cost": selected_safety["mean_cost"],
                    "failure_rate": selected_safety["failure_rate"],
                    "pm_rate": selected_safety["pm_rate"],
                    "mean_wasted_rul": selected_safety["mean_wasted_rul"],
                    "fleet_early_pm_rate": selected_safety["fleet_early_pm_rate"],
                    "pm_only_early_pm_rate": selected_safety["pm_only_early_pm_rate"],
                    "pm_wasted_rul_mean": selected_safety["pm_wasted_rul_mean"],
                },
            },
            CONTROL_EARLIER_INTERVENTION: {
                "control_family": CONTROL_EARLIER_INTERVENTION,
                "interval_source": selected_earlier["interval_source"],
                "parameter_name": "h",
                "parameter_value": selected_earlier["parameter_value"],
                "achieved_mpiw": selected_earlier["achieved_mpiw"],
                "boundary_selection": earlier_boundary,
                "metrics": {
                    "mean_cost": selected_earlier["mean_cost"],
                    "failure_rate": selected_earlier["failure_rate"],
                    "pm_rate": selected_earlier["pm_rate"],
                    "mean_wasted_rul": selected_earlier["mean_wasted_rul"],
                    "fleet_early_pm_rate": selected_earlier["fleet_early_pm_rate"],
                    "pm_only_early_pm_rate": selected_earlier["pm_only_early_pm_rate"],
                    "pm_wasted_rul_mean": selected_earlier["pm_wasted_rul_mean"],
                },
            },
        },
        "input_hashes": input_file_hashes,
    }

    return df_candidate_metrics, df_engine_seed_outcomes, selection_json
