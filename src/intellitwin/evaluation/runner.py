"""Execution runner for confirmatory validation smoke run across all 930 configurations."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.splits import load_split_manifest
from intellitwin.evaluation.bootstrap import (
    compute_bootstrap_ci,
    generate_stratified_bootstrap_draws,
)
from intellitwin.evaluation.inference import (
    SimulationTraceOutcome,
    reprice_simulation_outcome,
    simulate_engine_policy,
)
from intellitwin.evaluation.metrics import (
    compute_equal_engine_metric,
    compute_interval_score,
)
from intellitwin.evaluation.schema import (
    ALL_NOMINAL_COVERAGES,
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_METHODS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
    CONTROL_EARLIER_INTERVENTION,
    CONTROL_MATCHED_WIDTH,
    CONTROL_SAFETY_MARGIN,
    CONTROL_WIDENED,
    COST_SCENARIOS,
    DECISION_QUANTILES,
    DESCRIPTIVE_QUANTILES,
    INTERVENTION_THRESHOLD_CYCLES,
    PRIMARY_COST_SCENARIO,
    PRIMARY_NOMINAL_COVERAGE,
    PROTOCOL_VERSION,
    SUBGROUP_MIN_ENGINES,
)
from intellitwin.evaluation.validation import (
    assert_no_held_out_path,
    assert_permitted_partition_only,
    validate_trajectory,
)
from intellitwin.provenance import (
    capture_environment_metadata,
    get_git_info,
    write_immutable_csv,
    write_immutable_json,
    write_immutable_npz,
)
from intellitwin.simulator.types import MaintenanceAction, PredictionState
from intellitwin.uncertainty.artifacts import (
    load_frozen_calibrator,
    resolve_repo_relative_path,
)


def run_full_validation_smoke(
    controls_dir: Path | str,
    step08_audit_path: Path | str,
    output_dir: Path | str,
    base_dir: Path | str = ".",
    n_bootstrap: int = 10000,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Execute validation-only smoke run across all 930 configurations and apply bootstrap draws."""
    base = Path(base_dir).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    assert_no_held_out_path(str(out_dir))

    # Strict provenance capture
    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    env_meta = capture_environment_metadata(device="cpu")

    # 1. Verify Step 8 audit input
    audit_p = Path(step08_audit_path)
    if not audit_p.is_absolute():
        audit_p = (base / audit_p).resolve()
    if not audit_p.exists():
        raise FileNotFoundError(f"Step 8 audit report missing: {audit_p}")
    with open(audit_p, encoding="utf-8") as f:
        s8_audit = json.load(f)
    if s8_audit.get("overall_status") != "PASS":
        raise RuntimeError(
            f"Step 8 audit status is {s8_audit.get('overall_status')}; must be PASS."
        )

    # 2. Verify controls directory and load selected controls
    ctrl_base = Path(controls_dir)
    if not ctrl_base.is_absolute():
        ctrl_base = (base / ctrl_base).resolve()

    selected_controls_by_fam: dict[str, dict[str, Any]] = {}
    for fam in ("GBR", "LSTM"):
        sel_json_p = ctrl_base / "FD002" / fam / "selection.json"
        if not sel_json_p.exists():
            raise FileNotFoundError(f"Control selection file missing: {sel_json_p}")
        with open(sel_json_p, encoding="utf-8") as f:
            c_data = json.load(f)
        selected_controls_by_fam[fam] = c_data["selected_controls"]

    point_pred_rows: list[dict[str, Any]] = []
    interval_pred_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    engine_seed_outcome_rows: list[dict[str, Any]] = []
    engine_metric_rows: list[dict[str, Any]] = []
    subgroup_metric_rows: list[dict[str, Any]] = []
    cell_summary_rows: list[dict[str, Any]] = []

    # Engine-level aggregated arrays for bootstrap evaluation:
    # Key: (ds, fam, method_or_ctrl, cov, scen) -> dict[unit -> float]
    fleet_engine_costs: dict[tuple[Any, ...], dict[int, float]] = defaultdict(dict)
    fleet_engine_cov_errs: dict[tuple[Any, ...], dict[int, float]] = defaultdict(dict)
    fleet_engine_mpiws: dict[tuple[Any, ...], dict[int, float]] = defaultdict(dict)
    fleet_engine_iscores: dict[tuple[Any, ...], dict[int, float]] = defaultdict(dict)
    fleet_engine_regime_covs: dict[tuple[Any, ...], dict[str, dict[int, float]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    fleet_engine_stage_covs: dict[tuple[Any, ...], dict[str, dict[int, float]]] = defaultdict(
        lambda: defaultdict(dict)
    )

    bootstrap_draws_dict: dict[str, np.ndarray[Any, Any]] = {}
    partition_engines_dict: dict[str, list[int]] = {}
    eligible_regimes_dict: dict[str, list[str]] = {}
    eligible_stages_dict: dict[str, list[str]] = {}

    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        split_manifest = load_split_manifest(split_p)
        valid_engines = sorted(split_manifest.get_partition("validation"))
        partition_engines_dict[ds] = valid_engines

        # Generate 10,000 stratified bootstrap draws
        draws = generate_stratified_bootstrap_draws(
            dataset=ds,
            partition_engines=valid_engines,
            base_dir=base,
            n_replicates=n_bootstrap,
        )
        bootstrap_draws_dict[ds] = draws
        draws_p = out_dir / f"bootstrap_draws_{ds}.npz"
        write_immutable_npz(
            draws_p,
            arrays={"draws": draws, "engines": np.array(valid_engines, dtype=int)},
            metadata={
                "dataset": ds,
                "n_replicates": n_bootstrap,
                "engine_count": len(valid_engines),
                "status": "DEVELOPMENT_SMOKE_ONLY",
            },
        )

        for fam in CONFIRMATORY_MODELS:
            # Load point predictions across 5 seeds
            dfs = []
            for seed in CONFIRMATORY_SEEDS:
                cache_p = resolve_repo_relative_path(
                    base,
                    f"experiments/calibration/point_predictions/validation/{ds}/{fam}/seed_{seed}.csv",
                )
                df_s = pd.read_csv(cache_p, float_precision="round_trip")
                df_s["seed"] = seed
                dfs.append(df_s)
            df_cell = pd.concat(dfs, ignore_index=True)

            # Assert strictly permitted validation partition
            assert_permitted_partition_only(
                actual_units=df_cell["unit"].unique(),
                expected_units=valid_engines,
                partition_name=f"{ds} validation",
            )

            # Pre-compute true terminal lifetimes T
            engine_lifetimes: dict[int, int] = {}
            for unit, grp in df_cell.groupby("unit"):
                max_cyc = int(grp["endpoint_cycle"].max())
                rul_max = float(grp.loc[grp["endpoint_cycle"] == max_cyc, "rul_true"].iloc[0])
                engine_lifetimes[int(unit)] = max_cyc + int(round(rul_max))

            # Validate trajectories
            for (u, _s), grp in df_cell.groupby(["unit", "seed"]):
                grp_sort = grp.sort_values("endpoint_cycle")
                validate_trajectory(
                    unit=int(u),
                    cycles=grp_sort["endpoint_cycle"].to_numpy(),
                    predictions=grp_sort["prediction"].to_numpy(),
                    regimes=grp_sort["regime"].to_numpy(),
                    terminal_cycle=engine_lifetimes[int(u)],
                    rul_trues=grp_sort["rul_true"].to_numpy(),
                )

            # Record point predictions (seed 2026 once for logging)
            df_seed_first = df_cell[df_cell["seed"] == 2026]
            for row in df_seed_first.itertuples():
                point_pred_rows.append(
                    {
                        "dataset": ds,
                        "model_family": fam,
                        "seed": 2026,
                        "unit": int(row.unit),
                        "endpoint_cycle": int(row.endpoint_cycle),
                        "prediction": float(row.prediction),
                        "rul_true": float(row.rul_true),
                        "regime": str(row.regime),
                        "lifecycle_stage": str(row.lifecycle_stage),
                    }
                )

            # Pre-determine eligible regimes and stages for this dataset partition
            reg_counts = df_cell.groupby("regime")["unit"].nunique()
            el_regimes = sorted([r for r, c in reg_counts.items() if c >= SUBGROUP_MIN_ENGINES])
            eligible_regimes_dict[ds] = el_regimes

            stage_counts = df_cell.groupby("lifecycle_stage")["unit"].nunique()
            el_stages = sorted([st for st, c in stage_counts.items() if c >= SUBGROUP_MIN_ENGINES])
            eligible_stages_dict[ds] = el_stages

            # -----------------------------------------------------------------
            # Primary Methods: 3 methods x 3 coverages x 3 scenarios
            # -----------------------------------------------------------------
            for method in CONFIRMATORY_METHODS:
                for cov in ALL_NOMINAL_COVERAGES:
                    # Generate interval predictions across 5 seeds
                    df_cell_eval = df_cell.copy()
                    lowers: list[float] = []
                    uppers: list[float] = []
                    for seed in CONFIRMATORY_SEEDS:
                        df_seed = df_cell[df_cell["seed"] == seed]
                        cal = load_frozen_calibrator(
                            dataset=ds,
                            model_family=fam,
                            seed=seed,
                            method_id=method,
                            base_dir=base,
                        )
                        low, upp, _ = cal.predict_intervals(
                            predictions=df_seed["prediction"].to_numpy(),
                            regimes=df_seed["regime"].to_numpy(),
                            nominal_coverage=cov,
                        )
                        lowers.extend(low)
                        uppers.extend(upp)

                    df_cell_eval["lower"] = lowers
                    df_cell_eval["upper"] = uppers
                    df_cell_eval["covered"] = (
                        (df_cell_eval["rul_true"] >= df_cell_eval["lower"])
                        & (df_cell_eval["rul_true"] <= df_cell_eval["upper"])
                    ).astype(float)
                    df_cell_eval["width"] = df_cell_eval["upper"] - df_cell_eval["lower"]
                    df_cell_eval["interval_score"] = compute_interval_score(
                        y_true=df_cell_eval["rul_true"].to_numpy(),
                        lower=df_cell_eval["lower"].to_numpy(),
                        upper=df_cell_eval["upper"].to_numpy(),
                        nominal_coverage=cov,
                    )

                    # Log interval predictions (seed 2026 once)
                    if cov == PRIMARY_NOMINAL_COVERAGE:
                        sub_log = df_cell_eval[df_cell_eval["seed"] == 2026]
                        for row in sub_log.itertuples():
                            interval_pred_rows.append(
                                {
                                    "dataset": ds,
                                    "model_family": fam,
                                    "seed": 2026,
                                    "method_or_control_id": method,
                                    "nominal_coverage": cov,
                                    "unit": int(row.unit),
                                    "endpoint_cycle": int(row.endpoint_cycle),
                                    "lower": float(row.lower),
                                    "upper": float(row.upper),
                                    "covered": float(row.covered),
                                    "width": float(row.width),
                                    "interval_score": float(row.interval_score),
                                }
                            )

                    # Simulation under primary scenario
                    primary_scen = COST_SCENARIOS[PRIMARY_COST_SCENARIO]
                    sim_outcomes_by_seed_unit: dict[tuple[int, int], SimulationTraceOutcome] = {}

                    for (u, s), grp in df_cell_eval.groupby(["unit", "seed"]):
                        grp_sort = grp.sort_values("endpoint_cycle")
                        out = simulate_engine_policy(
                            unit=int(u),
                            seed=int(s),
                            configuration_id=f"{ds}_{fam}_{method}_{cov}",
                            method_or_control_id=method,
                            cycles=grp_sort["endpoint_cycle"].to_numpy(),
                            predictions=grp_sort["prediction"].to_numpy(),
                            lower_bounds=grp_sort["lower"].to_numpy(),
                            upper_bounds=grp_sort["upper"].to_numpy(),
                            regimes=grp_sort["regime"].to_numpy(),
                            failure_cycle=engine_lifetimes[int(u)],
                            policy_fn=lambda st: (
                                MaintenanceAction.MAINTAIN_NOW
                                if st.lower_rul <= INTERVENTION_THRESHOLD_CYCLES
                                else MaintenanceAction.CONTINUE
                            ),
                            scenario=primary_scen,
                        )
                        sim_outcomes_by_seed_unit[(int(u), int(s))] = out

                        # Log decision trace under primary reference once
                        if cov == PRIMARY_NOMINAL_COVERAGE and s == 2026:
                            for cyc, act in out.decision_trace:
                                trace_rows.append(
                                    {
                                        "dataset": ds,
                                        "model_family": fam,
                                        "seed": s,
                                        "method_or_control_id": method,
                                        "nominal_coverage": cov,
                                        "scenario_id": PRIMARY_COST_SCENARIO,
                                        "unit": int(u),
                                        "cycle": cyc,
                                        "action": act,
                                    }
                                )

                    # Precompute per-(unit, seed) metrics
                    unit_seed_metrics: dict[tuple[int, int], dict[str, float]] = {}
                    for (u_val, s_val), grp_us in df_cell_eval.groupby(["unit", "seed"]):
                        cov_us = float(grp_us["covered"].mean())
                        w_us = float(grp_us["width"].mean())
                        is_us = float(grp_us["interval_score"].mean())
                        rmse_us = float(
                            np.sqrt(np.mean((grp_us["prediction"] - grp_us["rul_true"]) ** 2))
                        )
                        unit_seed_metrics[(int(u_val), int(s_val))] = {
                            "cov": cov_us,
                            "mpiw": w_us,
                            "interval_score": is_us,
                            "rmse": rmse_us,
                        }

                    # Reprice across all 3 cost scenarios
                    for scen_id, scenario in COST_SCENARIOS.items():
                        cfg_key = (ds, fam, method, cov, scen_id)
                        outcomes_for_scen = [
                            reprice_simulation_outcome(out, scenario)
                            for out in sim_outcomes_by_seed_unit.values()
                        ]

                        for o in outcomes_for_scen:
                            m_us = unit_seed_metrics[(o.unit, o.seed)]
                            engine_seed_outcome_rows.append(
                                {
                                    "dataset": ds,
                                    "model_family": fam,
                                    "seed": o.seed,
                                    "method_or_control_id": method,
                                    "nominal_coverage": cov,
                                    "scenario_id": scen_id,
                                    "unit": o.unit,
                                    "terminal_event": o.terminal_event,
                                    "intervention_cycle": o.intervention_cycle,
                                    "failed": o.failed,
                                    "pm": o.pm_occurred,
                                    "wasted_rul": o.wasted_rul,
                                    "total_cost": o.total_cost,
                                    "is_cost_inefficient_early_pm": (
                                        o.is_cost_inefficient_early_pm
                                    ),
                                }
                            )
                            engine_metric_rows.append(
                                {
                                    "dataset": ds,
                                    "model_family": fam,
                                    "seed": o.seed,
                                    "method_or_control_id": method,
                                    "nominal_coverage": cov,
                                    "scenario_id": scen_id,
                                    "unit": o.unit,
                                    "coverage": m_us["cov"],
                                    "mpiw": m_us["mpiw"],
                                    "mean_interval_score": m_us["interval_score"],
                                    "rmse": m_us["rmse"],
                                    "total_cost": o.total_cost,
                                    "failed": 1.0 if o.failed else 0.0,
                                    "pm": 1.0 if o.pm_occurred else 0.0,
                                    "wasted_rul": o.wasted_rul,
                                }
                            )

                        df_o = pd.DataFrame(
                            [
                                {
                                    "unit": o.unit,
                                    "seed": o.seed,
                                    "cost": o.total_cost,
                                    "failed": 1.0 if o.failed else 0.0,
                                    "pm": 1.0 if o.pm_occurred else 0.0,
                                    "wasted": o.wasted_rul,
                                    "early_pm": 1.0 if o.is_cost_inefficient_early_pm else 0.0,
                                }
                                for o in outcomes_for_scen
                            ]
                        )
                        e_avgs = df_o.groupby("unit").mean()
                        mean_cost = float(e_avgs["cost"].mean())
                        fail_rate = float(e_avgs["failed"].mean())
                        pm_rate = float(e_avgs["pm"].mean())
                        mean_wasted = float(e_avgs["wasted"].mean())
                        fleet_early_pm = float(e_avgs["early_pm"].mean())
                        pm_sub = df_o[df_o["pm"] > 0]
                        pm_only_early = (
                            float(pm_sub["early_pm"].mean()) if len(pm_sub) > 0 else float("nan")
                        )

                        marg_cov = compute_equal_engine_metric(df_cell_eval, "covered")
                        mpiw = compute_equal_engine_metric(df_cell_eval, "width")
                        int_score = compute_equal_engine_metric(df_cell_eval, "interval_score")

                        # Populate engine-level dictionaries for bootstrap
                        for u_idx, c_val in e_avgs["cost"].items():
                            fleet_engine_costs[cfg_key][int(u_idx)] = float(c_val)

                        cell_summary_rows.append(
                            {
                                "dataset": ds,
                                "model_family": fam,
                                "method_or_control_id": method,
                                "nominal_coverage": cov,
                                "scenario_id": scen_id,
                                "mean_cost": mean_cost,
                                "failure_rate": fail_rate,
                                "pm_rate": pm_rate,
                                "mean_wasted_rul": mean_wasted,
                                "fleet_early_pm_rate": fleet_early_pm,
                                "pm_only_early_pm_rate": pm_only_early,
                                "marginal_coverage": marg_cov,
                                "marginal_coverage_abs_error": abs(marg_cov - cov),
                                "mpiw": mpiw,
                                "interval_score": int_score,
                                "status": "DEVELOPMENT_SMOKE_ONLY",
                            }
                        )

                    # Compute subgroup metrics for this cell
                    for reg in el_regimes:
                        sub_reg = df_cell_eval[df_cell_eval["regime"] == reg]
                        n_engs_sub = int(sub_reg["unit"].nunique())
                        cov_sub = (
                            compute_equal_engine_metric(sub_reg, "covered")
                            if len(sub_reg) > 0
                            else float("nan")
                        )
                        subgroup_metric_rows.append(
                            {
                                "dataset": ds,
                                "model_family": fam,
                                "method_id": method,
                                "nominal_coverage": cov,
                                "subgroup_family": "regime",
                                "subgroup_id": reg,
                                "engine_count": n_engs_sub,
                                "coverage": cov_sub,
                                "coverage_abs_error": abs(cov_sub - cov)
                                if not np.isnan(cov_sub)
                                else float("nan"),
                                "is_eligible": n_engs_sub >= SUBGROUP_MIN_ENGINES,
                            }
                        )
                    for stg in el_stages:
                        sub_stg = df_cell_eval[df_cell_eval["lifecycle_stage"] == stg]
                        n_engs_sub = int(sub_stg["unit"].nunique())
                        cov_sub = (
                            compute_equal_engine_metric(sub_stg, "covered")
                            if len(sub_stg) > 0
                            else float("nan")
                        )
                        subgroup_metric_rows.append(
                            {
                                "dataset": ds,
                                "model_family": fam,
                                "method_id": method,
                                "nominal_coverage": cov,
                                "subgroup_family": "lifecycle_stage",
                                "subgroup_id": stg,
                                "engine_count": n_engs_sub,
                                "coverage": cov_sub,
                                "coverage_abs_error": abs(cov_sub - cov)
                                if not np.isnan(cov_sub)
                                else float("nan"),
                                "is_eligible": n_engs_sub >= SUBGROUP_MIN_ENGINES,
                            }
                        )

                    # Compute engine-level coverage, width, interval score (independent of scenario)
                    engine_covs = (
                        df_cell_eval.groupby(["unit", "seed"])["covered"]
                        .mean()
                        .groupby("unit")
                        .mean()
                    )
                    engine_w = (
                        df_cell_eval.groupby(["unit", "seed"])["width"]
                        .mean()
                        .groupby("unit")
                        .mean()
                    )
                    engine_s = (
                        df_cell_eval.groupby(["unit", "seed"])["interval_score"]
                        .mean()
                        .groupby("unit")
                        .mean()
                    )

                    for u_idx in valid_engines:
                        for scen_id in COST_SCENARIOS:
                            cfg_k = (ds, fam, method, cov, scen_id)
                            fleet_engine_cov_errs[cfg_k][u_idx] = abs(
                                float(engine_covs[u_idx]) - cov
                            )
                            fleet_engine_mpiws[cfg_k][u_idx] = float(engine_w[u_idx])
                            fleet_engine_iscores[cfg_k][u_idx] = float(engine_s[u_idx])

                    # Compute subgroup coverage per engine for each eligible regime and stage
                    for reg in el_regimes:
                        sub_reg = df_cell_eval[df_cell_eval["regime"] == reg]
                        if len(sub_reg) > 0:
                            reg_u_cov = (
                                sub_reg.groupby(["unit", "seed"])["covered"]
                                .mean()
                                .groupby("unit")
                                .mean()
                            )
                            for u_idx, cv in reg_u_cov.items():
                                for scen_id in COST_SCENARIOS:
                                    cfg_k = (ds, fam, method, cov, scen_id)
                                    fleet_engine_regime_covs[cfg_k][reg][int(u_idx)] = float(cv)

                    for stg in el_stages:
                        sub_stg = df_cell_eval[df_cell_eval["lifecycle_stage"] == stg]
                        if len(sub_stg) > 0:
                            stg_u_cov = (
                                sub_stg.groupby(["unit", "seed"])["covered"]
                                .mean()
                                .groupby("unit")
                                .mean()
                            )
                            for u_idx, cv in stg_u_cov.items():
                                for scen_id in COST_SCENARIOS:
                                    cfg_k = (ds, fam, method, cov, scen_id)
                                    fleet_engine_stage_covs[cfg_k][stg][int(u_idx)] = float(cv)

            # -----------------------------------------------------------------
            # Benchmark Controls (FD002 Only, 4 controls x 1 coverage x 3 scenarios)
            # -----------------------------------------------------------------
            if ds == "FD002":
                ctrl_dict = selected_controls_by_fam[fam]
                for ctrl_id, ctrl_info in ctrl_dict.items():
                    param_val = ctrl_info["parameter_value"]
                    src = ctrl_info.get("interval_source", "regime_hcp")

                    # Generate intervals according to control rules
                    df_ctrl_eval = df_cell.copy()

                    # Pre-load source calibrator bounds for all 5 seeds
                    lowers_src: list[float] = []
                    uppers_src: list[float] = []
                    for seed in CONFIRMATORY_SEEDS:
                        df_seed = df_cell[df_cell["seed"] == seed]
                        cal_src = load_frozen_calibrator(
                            dataset="FD002",
                            model_family=fam,
                            seed=seed,
                            method_id=src,
                            base_dir=base,
                        )
                        l_s, u_s, _ = cal_src.predict_intervals(
                            predictions=df_seed["prediction"].to_numpy(),
                            regimes=df_seed["regime"].to_numpy(),
                            nominal_coverage=PRIMARY_NOMINAL_COVERAGE,
                        )
                        lowers_src.extend(l_s)
                        uppers_src.extend(u_s)

                    df_ctrl_eval["source_lower"] = lowers_src
                    df_ctrl_eval["source_upper"] = uppers_src

                    if ctrl_id in (CONTROL_MATCHED_WIDTH, CONTROL_WIDENED):
                        lam = float(param_val)
                        q_half = (
                            df_ctrl_eval["source_upper"] - df_ctrl_eval["prediction"]
                        ).to_numpy()
                        df_ctrl_eval["lower"] = np.maximum(
                            0.0, df_ctrl_eval["prediction"] - lam * q_half
                        )
                        df_ctrl_eval["upper"] = df_ctrl_eval["prediction"] + lam * q_half
                        df_ctrl_eval["covered"] = (
                            (df_ctrl_eval["rul_true"] >= df_ctrl_eval["lower"])
                            & (df_ctrl_eval["rul_true"] <= df_ctrl_eval["upper"])
                        ).astype(float)
                        df_ctrl_eval["width"] = df_ctrl_eval["upper"] - df_ctrl_eval["lower"]
                        df_ctrl_eval["interval_score"] = compute_interval_score(
                            y_true=df_ctrl_eval["rul_true"].to_numpy(),
                            lower=df_ctrl_eval["lower"].to_numpy(),
                            upper=df_ctrl_eval["upper"].to_numpy(),
                            nominal_coverage=PRIMARY_NOMINAL_COVERAGE,
                        )

                        def policy_fn_interval(st: PredictionState) -> MaintenanceAction:
                            return (
                                MaintenanceAction.MAINTAIN_NOW
                                if st.lower_rul <= INTERVENTION_THRESHOLD_CYCLES
                                else MaintenanceAction.CONTINUE
                            )

                        policy_fn = policy_fn_interval
                    elif ctrl_id == CONTROL_SAFETY_MARGIN:
                        m_val = float(param_val)
                        # Policy-only control: interval fields null with not-applicable reason
                        df_ctrl_eval["lower"] = float("nan")
                        df_ctrl_eval["upper"] = float("nan")
                        df_ctrl_eval["covered"] = float("nan")
                        df_ctrl_eval["width"] = float("nan")
                        df_ctrl_eval["interval_score"] = float("nan")

                        def policy_fn_safety(
                            st: PredictionState, m: float = m_val
                        ) -> MaintenanceAction:
                            return (
                                MaintenanceAction.MAINTAIN_NOW
                                if st.point_rul <= (1.0 + m)
                                else MaintenanceAction.CONTINUE
                            )

                        policy_fn = policy_fn_safety
                    elif ctrl_id == CONTROL_EARLIER_INTERVENTION:
                        h_val = float(param_val)
                        # Coverage belongs to its unchanged source intervals
                        df_ctrl_eval["lower"] = df_ctrl_eval["source_lower"]
                        df_ctrl_eval["upper"] = df_ctrl_eval["source_upper"]
                        df_ctrl_eval["covered"] = (
                            (df_ctrl_eval["rul_true"] >= df_ctrl_eval["lower"])
                            & (df_ctrl_eval["rul_true"] <= df_ctrl_eval["upper"])
                        ).astype(float)
                        df_ctrl_eval["width"] = df_ctrl_eval["upper"] - df_ctrl_eval["lower"]
                        df_ctrl_eval["interval_score"] = compute_interval_score(
                            y_true=df_ctrl_eval["rul_true"].to_numpy(),
                            lower=df_ctrl_eval["lower"].to_numpy(),
                            upper=df_ctrl_eval["upper"].to_numpy(),
                            nominal_coverage=PRIMARY_NOMINAL_COVERAGE,
                        )

                        def policy_fn_earlier(
                            st: PredictionState, h: float = h_val
                        ) -> MaintenanceAction:
                            return (
                                MaintenanceAction.MAINTAIN_NOW
                                if st.lower_rul <= h
                                else MaintenanceAction.CONTINUE
                            )

                        policy_fn = policy_fn_earlier
                    else:
                        raise ValueError(f"Unknown control family: {ctrl_id}")

                    # Run simulation under primary scenario
                    sim_outcomes_ctrl: dict[tuple[int, int], SimulationTraceOutcome] = {}
                    for (u, s), grp in df_ctrl_eval.groupby(["unit", "seed"]):
                        grp_sort = grp.sort_values("endpoint_cycle")
                        out = simulate_engine_policy(
                            unit=int(u),
                            seed=int(s),
                            configuration_id=f"FD002_{fam}_{ctrl_id}",
                            method_or_control_id=ctrl_id,
                            cycles=grp_sort["endpoint_cycle"].to_numpy(),
                            predictions=grp_sort["prediction"].to_numpy(),
                            lower_bounds=grp_sort["lower"].to_numpy()
                            if ctrl_id != CONTROL_SAFETY_MARGIN
                            else None,
                            upper_bounds=grp_sort["upper"].to_numpy()
                            if ctrl_id != CONTROL_SAFETY_MARGIN
                            else None,
                            regimes=grp_sort["regime"].to_numpy(),
                            failure_cycle=engine_lifetimes[int(u)],
                            policy_fn=policy_fn,
                            scenario=primary_scen,
                        )
                        sim_outcomes_ctrl[(int(u), int(s))] = out

                    # Precompute per-(unit, seed) metrics for control
                    unit_seed_ctrl_metrics: dict[tuple[int, int], dict[str, float]] = {}
                    for (u_val, s_val), grp_us in df_ctrl_eval.groupby(["unit", "seed"]):
                        rmse_us = float(
                            np.sqrt(np.mean((grp_us["prediction"] - grp_us["rul_true"]) ** 2))
                        )
                        if ctrl_id == CONTROL_SAFETY_MARGIN:
                            unit_seed_ctrl_metrics[(int(u_val), int(s_val))] = {
                                "cov": float("nan"),
                                "mpiw": float("nan"),
                                "interval_score": float("nan"),
                                "rmse": rmse_us,
                            }
                        else:
                            unit_seed_ctrl_metrics[(int(u_val), int(s_val))] = {
                                "cov": float(grp_us["covered"].mean()),
                                "mpiw": float(grp_us["width"].mean()),
                                "interval_score": float(grp_us["interval_score"].mean()),
                                "rmse": rmse_us,
                            }

                    # Reprice across all 3 scenarios
                    for scen_id, scenario in COST_SCENARIOS.items():
                        cfg_key = ("FD002", fam, ctrl_id, PRIMARY_NOMINAL_COVERAGE, scen_id)
                        outcomes_for_scen = [
                            reprice_simulation_outcome(out, scenario)
                            for out in sim_outcomes_ctrl.values()
                        ]

                        for o in outcomes_for_scen:
                            m_us = unit_seed_ctrl_metrics[(o.unit, o.seed)]
                            engine_seed_outcome_rows.append(
                                {
                                    "dataset": "FD002",
                                    "model_family": fam,
                                    "seed": o.seed,
                                    "method_or_control_id": ctrl_id,
                                    "nominal_coverage": PRIMARY_NOMINAL_COVERAGE,
                                    "scenario_id": scen_id,
                                    "unit": o.unit,
                                    "terminal_event": o.terminal_event,
                                    "intervention_cycle": o.intervention_cycle,
                                    "failed": o.failed,
                                    "pm": o.pm_occurred,
                                    "wasted_rul": o.wasted_rul,
                                    "total_cost": o.total_cost,
                                    "is_cost_inefficient_early_pm": (
                                        o.is_cost_inefficient_early_pm
                                    ),
                                }
                            )
                            engine_metric_rows.append(
                                {
                                    "dataset": "FD002",
                                    "model_family": fam,
                                    "seed": o.seed,
                                    "method_or_control_id": ctrl_id,
                                    "nominal_coverage": PRIMARY_NOMINAL_COVERAGE,
                                    "scenario_id": scen_id,
                                    "unit": o.unit,
                                    "coverage": m_us["cov"],
                                    "mpiw": m_us["mpiw"],
                                    "mean_interval_score": m_us["interval_score"],
                                    "rmse": m_us["rmse"],
                                    "total_cost": o.total_cost,
                                    "failed": 1.0 if o.failed else 0.0,
                                    "pm": 1.0 if o.pm_occurred else 0.0,
                                    "wasted_rul": o.wasted_rul,
                                }
                            )

                        df_o = pd.DataFrame(
                            [
                                {
                                    "unit": o.unit,
                                    "seed": o.seed,
                                    "cost": o.total_cost,
                                    "failed": 1.0 if o.failed else 0.0,
                                    "pm": 1.0 if o.pm_occurred else 0.0,
                                    "wasted": o.wasted_rul,
                                    "early_pm": 1.0 if o.is_cost_inefficient_early_pm else 0.0,
                                }
                                for o in outcomes_for_scen
                            ]
                        )
                        e_avgs = df_o.groupby("unit").mean()
                        mean_cost = float(e_avgs["cost"].mean())
                        fail_rate = float(e_avgs["failed"].mean())
                        pm_rate = float(e_avgs["pm"].mean())
                        mean_wasted = float(e_avgs["wasted"].mean())
                        fleet_early_pm = float(e_avgs["early_pm"].mean())
                        pm_sub = df_o[df_o["pm"] > 0]
                        pm_only_early = (
                            float(pm_sub["early_pm"].mean()) if len(pm_sub) > 0 else float("nan")
                        )

                        if ctrl_id == CONTROL_SAFETY_MARGIN:
                            marg_cov = float("nan")
                            abs_err = float("nan")
                            mpiw_val = float("nan")
                            is_val = float("nan")
                        else:
                            marg_cov = compute_equal_engine_metric(df_ctrl_eval, "covered")
                            abs_err = abs(marg_cov - PRIMARY_NOMINAL_COVERAGE)
                            mpiw_val = compute_equal_engine_metric(df_ctrl_eval, "width")
                            is_val = compute_equal_engine_metric(df_ctrl_eval, "interval_score")

                        for u_idx, c_val in e_avgs["cost"].items():
                            fleet_engine_costs[cfg_key][int(u_idx)] = float(c_val)

                        cell_summary_rows.append(
                            {
                                "dataset": "FD002",
                                "model_family": fam,
                                "method_or_control_id": ctrl_id,
                                "nominal_coverage": PRIMARY_NOMINAL_COVERAGE,
                                "scenario_id": scen_id,
                                "mean_cost": mean_cost,
                                "failure_rate": fail_rate,
                                "pm_rate": pm_rate,
                                "mean_wasted_rul": mean_wasted,
                                "fleet_early_pm_rate": fleet_early_pm,
                                "pm_only_early_pm_rate": pm_only_early,
                                "marginal_coverage": marg_cov,
                                "marginal_coverage_abs_error": abs_err,
                                "mpiw": mpiw_val,
                                "interval_score": is_val,
                                "status": "DEVELOPMENT_SMOKE_ONLY",
                            }
                        )

    # -------------------------------------------------------------------------
    # Apply Bootstrap Draws to Compute Replicate Statistics & Contrasts
    # -------------------------------------------------------------------------
    contrast_records: list[dict[str, Any]] = []
    dataset_stats_arrays: dict[str, dict[str, np.ndarray[Any, Any]]] = {
        ds: {} for ds in CONFIRMATORY_DATASETS
    }

    # Evaluate per-dataset replicate statistics
    for ds in CONFIRMATORY_DATASETS:
        draws = bootstrap_draws_dict[ds]  # shape: (B, N)
        engines = partition_engines_dict[ds]
        n_engs = len(engines)
        eng_to_idx = {u: i for i, u in enumerate(engines)}

        # Precompute multiplicity matrix M shape: (B, N)
        # M[b, i] = count of engine i in replicate b
        M = np.zeros((n_bootstrap, n_engs), dtype=float)
        for b in range(n_bootstrap):
            for u in draws[b]:
                M[b, eng_to_idx[u]] += 1.0

        for fam in CONFIRMATORY_MODELS:
            # 1. Evaluate primary method replicate costs and errors
            prop_key = (
                ds,
                fam,
                "decision_aware_hcp",
                PRIMARY_NOMINAL_COVERAGE,
                PRIMARY_COST_SCENARIO,
            )
            prop_cost_vec = np.array(
                [fleet_engine_costs[prop_key][u] for u in engines], dtype=float
            )
            rep_cost_prop = (M @ prop_cost_vec) / n_engs
            dataset_stats_arrays[ds][f"{fam}_decision_aware_hcp_cost"] = rep_cost_prop

            # Subgroup errors for proposed method
            # Regime coverage per replicate
            reg_err_rep_prop = np.zeros(n_bootstrap, dtype=float)
            for reg in eligible_regimes_dict[ds]:
                reg_cov_map = fleet_engine_regime_covs[prop_key][reg]
                reg_units = sorted(reg_cov_map.keys())
                reg_indices = [eng_to_idx[u] for u in reg_units]
                c_vec = np.array([reg_cov_map[u] for u in reg_units], dtype=float)
                # Weights for this subgroup in each replicate
                w_reg = M[:, reg_indices]  # (B, |S_g|)
                sum_w = np.sum(w_reg, axis=1)  # (B,)
                pres_mask = sum_w > 0
                reg_cov = np.zeros(n_bootstrap, dtype=float)
                reg_cov[pres_mask] = (w_reg[pres_mask] @ c_vec) / sum_w[pres_mask]
                err_g = np.abs(reg_cov - PRIMARY_NOMINAL_COVERAGE)
                err_g[~pres_mask] = 0.90  # absent bound
                reg_err_rep_prop = np.maximum(reg_err_rep_prop, err_g)
            dataset_stats_arrays[ds][f"{fam}_decision_aware_hcp_regime_error"] = reg_err_rep_prop

            # Stage coverage per replicate
            stage_err_rep_prop = np.zeros(n_bootstrap, dtype=float)
            for stg in eligible_stages_dict[ds]:
                stg_cov_map = fleet_engine_stage_covs[prop_key][stg]
                stg_units = sorted(stg_cov_map.keys())
                stg_indices = [eng_to_idx[u] for u in stg_units]
                c_vec = np.array([stg_cov_map[u] for u in stg_units], dtype=float)
                w_stg = M[:, stg_indices]
                sum_w = np.sum(w_stg, axis=1)
                pres_mask = sum_w > 0
                stg_cov = np.zeros(n_bootstrap, dtype=float)
                stg_cov[pres_mask] = (w_stg[pres_mask] @ c_vec) / sum_w[pres_mask]
                err_g = np.abs(stg_cov - PRIMARY_NOMINAL_COVERAGE)
                err_g[~pres_mask] = 0.90
                stage_err_rep_prop = np.maximum(stage_err_rep_prop, err_g)
            dataset_stats_arrays[ds][f"{fam}_decision_aware_hcp_stage_error"] = stage_err_rep_prop

            # Contrasts against baselines
            for base_id in ("global_hcp", "regime_hcp"):
                base_key = (ds, fam, base_id, PRIMARY_NOMINAL_COVERAGE, PRIMARY_COST_SCENARIO)
                base_cost_vec = np.array(
                    [fleet_engine_costs[base_key][u] for u in engines], dtype=float
                )
                rep_cost_base = (M @ base_cost_vec) / n_engs
                dataset_stats_arrays[ds][f"{fam}_{base_id}_cost"] = rep_cost_base

                delta_cost = rep_cost_base - rep_cost_prop
                c_name = f"{ds}_{fam}_{base_id}_cost_improvement"
                dataset_stats_arrays[ds][c_name] = delta_cost

                ci_95 = compute_bootstrap_ci(delta_cost, quantiles=DESCRIPTIVE_QUANTILES)
                ci_dec = compute_bootstrap_ci(delta_cost, quantiles=DECISION_QUANTILES)

                contrast_records.append(
                    {
                        "contrast_id": c_name,
                        "dataset": ds,
                        "model_family": fam,
                        "comparator": base_id,
                        "metric": "delta_cost",
                        "mean": float(np.mean(delta_cost)),
                        "median": float(np.median(delta_cost)),
                        "ci_95_low": ci_95[0],
                        "ci_95_high": ci_95[1],
                        "ci_decision_low": ci_dec[0],
                        "ci_decision_high": ci_dec[1],
                        "margin": 0.20,
                        "status": "DEVELOPMENT_SMOKE_ONLY",
                    }
                )

                # Subgroup errors for baseline
                reg_err_rep_base = np.zeros(n_bootstrap, dtype=float)
                for reg in eligible_regimes_dict[ds]:
                    reg_cov_map = fleet_engine_regime_covs[base_key][reg]
                    reg_units = sorted(reg_cov_map.keys())
                    reg_indices = [eng_to_idx[u] for u in reg_units]
                    c_vec = np.array([reg_cov_map[u] for u in reg_units], dtype=float)
                    w_reg = M[:, reg_indices]
                    sum_w = np.sum(w_reg, axis=1)
                    pres_mask = sum_w > 0
                    reg_cov = np.zeros(n_bootstrap, dtype=float)
                    reg_cov[pres_mask] = (w_reg[pres_mask] @ c_vec) / sum_w[pres_mask]
                    err_g = np.abs(reg_cov - PRIMARY_NOMINAL_COVERAGE)
                    err_g[~pres_mask] = 0.90
                    reg_err_rep_base = np.maximum(reg_err_rep_base, err_g)
                dataset_stats_arrays[ds][f"{fam}_{base_id}_regime_error"] = reg_err_rep_base

                delta_reg_err = reg_err_rep_base - reg_err_rep_prop
                c_reg_name = f"{ds}_{fam}_{base_id}_regime_error_improvement"
                dataset_stats_arrays[ds][c_reg_name] = delta_reg_err
                ci_95_r = compute_bootstrap_ci(delta_reg_err, quantiles=DESCRIPTIVE_QUANTILES)
                ci_dec_r = compute_bootstrap_ci(delta_reg_err, quantiles=DECISION_QUANTILES)
                contrast_records.append(
                    {
                        "contrast_id": c_reg_name,
                        "dataset": ds,
                        "model_family": fam,
                        "comparator": base_id,
                        "metric": "delta_regime_error",
                        "mean": float(np.mean(delta_reg_err)),
                        "median": float(np.median(delta_reg_err)),
                        "ci_95_low": ci_95_r[0],
                        "ci_95_high": ci_95_r[1],
                        "ci_decision_low": ci_dec_r[0],
                        "ci_decision_high": ci_dec_r[1],
                        "margin": 0.01,
                        "status": "DEVELOPMENT_SMOKE_ONLY",
                    }
                )

                stage_err_rep_base = np.zeros(n_bootstrap, dtype=float)
                for stg in eligible_stages_dict[ds]:
                    stg_cov_map = fleet_engine_stage_covs[base_key][stg]
                    stg_units = sorted(stg_cov_map.keys())
                    stg_indices = [eng_to_idx[u] for u in stg_units]
                    c_vec = np.array([stg_cov_map[u] for u in stg_units], dtype=float)
                    w_stg = M[:, stg_indices]
                    sum_w = np.sum(w_stg, axis=1)
                    pres_mask = sum_w > 0
                    stg_cov = np.zeros(n_bootstrap, dtype=float)
                    stg_cov[pres_mask] = (w_stg[pres_mask] @ c_vec) / sum_w[pres_mask]
                    err_g = np.abs(stg_cov - PRIMARY_NOMINAL_COVERAGE)
                    err_g[~pres_mask] = 0.90
                    stage_err_rep_base = np.maximum(stage_err_rep_base, err_g)
                dataset_stats_arrays[ds][f"{fam}_{base_id}_stage_error"] = stage_err_rep_base

                delta_stg_err = stage_err_rep_base - stage_err_rep_prop
                c_stg_name = f"{ds}_{fam}_{base_id}_stage_error_improvement"
                dataset_stats_arrays[ds][c_stg_name] = delta_stg_err
                ci_95_s = compute_bootstrap_ci(delta_stg_err, quantiles=DESCRIPTIVE_QUANTILES)
                ci_dec_s = compute_bootstrap_ci(delta_stg_err, quantiles=DECISION_QUANTILES)
                contrast_records.append(
                    {
                        "contrast_id": c_stg_name,
                        "dataset": ds,
                        "model_family": fam,
                        "comparator": base_id,
                        "metric": "delta_stage_error",
                        "mean": float(np.mean(delta_stg_err)),
                        "median": float(np.median(delta_stg_err)),
                        "ci_95_low": ci_95_s[0],
                        "ci_95_high": ci_95_s[1],
                        "ci_decision_low": ci_dec_s[0],
                        "ci_decision_high": ci_dec_s[1],
                        "margin": 0.01,
                        "status": "DEVELOPMENT_SMOKE_ONLY",
                    }
                )

                # Width deterioration (MPIW_prop - MPIW_base)
                prop_w_vec = np.array(
                    [fleet_engine_mpiws[prop_key][u] for u in engines], dtype=float
                )
                base_w_vec = np.array(
                    [fleet_engine_mpiws[base_key][u] for u in engines], dtype=float
                )
                mpiw_det = (M @ (prop_w_vec - base_w_vec)) / n_engs
                c_w_name = f"{ds}_{fam}_{base_id}_mpiw_deterioration"
                dataset_stats_arrays[ds][c_w_name] = mpiw_det
                ci_95_w = compute_bootstrap_ci(mpiw_det, quantiles=DESCRIPTIVE_QUANTILES)
                ci_dec_w = compute_bootstrap_ci(mpiw_det, quantiles=DECISION_QUANTILES)
                contrast_records.append(
                    {
                        "contrast_id": c_w_name,
                        "dataset": ds,
                        "model_family": fam,
                        "comparator": base_id,
                        "metric": "mpiw_deterioration",
                        "mean": float(np.mean(mpiw_det)),
                        "median": float(np.median(mpiw_det)),
                        "ci_95_low": ci_95_w[0],
                        "ci_95_high": ci_95_w[1],
                        "ci_decision_low": ci_dec_w[0],
                        "ci_decision_high": ci_dec_w[1],
                        "margin": 1.0,
                        "status": "DEVELOPMENT_SMOKE_ONLY",
                    }
                )

                # Interval score deterioration
                prop_is_vec = np.array(
                    [fleet_engine_iscores[prop_key][u] for u in engines], dtype=float
                )
                base_is_vec = np.array(
                    [fleet_engine_iscores[base_key][u] for u in engines], dtype=float
                )
                score_det = (M @ (prop_is_vec - base_is_vec)) / n_engs
                c_is_name = f"{ds}_{fam}_{base_id}_interval_score_deterioration"
                dataset_stats_arrays[ds][c_is_name] = score_det
                ci_95_is = compute_bootstrap_ci(score_det, quantiles=DESCRIPTIVE_QUANTILES)
                ci_dec_is = compute_bootstrap_ci(score_det, quantiles=DECISION_QUANTILES)
                contrast_records.append(
                    {
                        "contrast_id": c_is_name,
                        "dataset": ds,
                        "model_family": fam,
                        "comparator": base_id,
                        "metric": "interval_score_deterioration",
                        "mean": float(np.mean(score_det)),
                        "median": float(np.median(score_det)),
                        "ci_95_low": ci_95_is[0],
                        "ci_95_high": ci_95_is[1],
                        "ci_decision_low": ci_dec_is[0],
                        "ci_decision_high": ci_dec_is[1],
                        "margin": 1.0,
                        "status": "DEVELOPMENT_SMOKE_ONLY",
                    }
                )

            # Controls contrasts on FD002
            if ds == "FD002":
                ctrl_dict = selected_controls_by_fam[fam]
                for ctrl_id in ctrl_dict:
                    ctrl_key = (
                        "FD002",
                        fam,
                        ctrl_id,
                        PRIMARY_NOMINAL_COVERAGE,
                        PRIMARY_COST_SCENARIO,
                    )
                    ctrl_cost_vec = np.array(
                        [fleet_engine_costs[ctrl_key][u] for u in engines], dtype=float
                    )
                    rep_cost_ctrl = (M @ ctrl_cost_vec) / n_engs
                    dataset_stats_arrays[ds][f"{fam}_{ctrl_id}_cost"] = rep_cost_ctrl

                    delta_ctrl = rep_cost_ctrl - rep_cost_prop
                    c_ctrl_name = f"FD002_{fam}_{ctrl_id}_cost_improvement"
                    dataset_stats_arrays[ds][c_ctrl_name] = delta_ctrl
                    ci_95_c = compute_bootstrap_ci(delta_ctrl, quantiles=DESCRIPTIVE_QUANTILES)
                    ci_dec_c = compute_bootstrap_ci(delta_ctrl, quantiles=DECISION_QUANTILES)
                    contrast_records.append(
                        {
                            "contrast_id": c_ctrl_name,
                            "dataset": "FD002",
                            "model_family": fam,
                            "comparator": ctrl_id,
                            "metric": "delta_cost",
                            "mean": float(np.mean(delta_ctrl)),
                            "median": float(np.median(delta_ctrl)),
                            "ci_95_low": ci_95_c[0],
                            "ci_95_high": ci_95_c[1],
                            "ci_decision_low": ci_dec_c[0],
                            "ci_decision_high": ci_dec_c[1],
                            "margin": 0.20,
                            "status": "DEVELOPMENT_SMOKE_ONLY",
                        }
                    )

    # -------------------------------------------------------------------------
    # RQ4 Equal-Six-Cell Aggregate Contrasts
    # -------------------------------------------------------------------------
    # Six cells: FD001/GBR, FD001/LSTM, FD002/GBR, FD002/LSTM, FD004/GBR, FD004/LSTM
    cells = [
        ("FD001", "GBR"),
        ("FD001", "LSTM"),
        ("FD002", "GBR"),
        ("FD002", "LSTM"),
        ("FD004", "GBR"),
        ("FD004", "LSTM"),
    ]
    rq4_stats_dict: dict[str, np.ndarray[Any, Any]] = {}

    for base_id in ("global_hcp", "regime_hcp"):
        # Aggregate Cost Contrast
        cell_cost_contrasts = [
            dataset_stats_arrays[d][f"{d}_{f}_{base_id}_cost_improvement"] for d, f in cells
        ]
        agg_delta_cost = np.mean(cell_cost_contrasts, axis=0)  # shape (B,)
        rq4_stats_dict[f"aggregate_{base_id}_cost_improvement"] = agg_delta_cost

        ci_95 = compute_bootstrap_ci(agg_delta_cost, quantiles=DESCRIPTIVE_QUANTILES)
        ci_dec = compute_bootstrap_ci(agg_delta_cost, quantiles=DECISION_QUANTILES)

        contrast_records.append(
            {
                "contrast_id": f"RQ4_aggregate_{base_id}_cost_improvement",
                "dataset": "ALL_6_CELLS",
                "model_family": "BOTH",
                "comparator": base_id,
                "metric": "aggregate_delta_cost",
                "mean": float(np.mean(agg_delta_cost)),
                "median": float(np.median(agg_delta_cost)),
                "ci_95_low": ci_95[0],
                "ci_95_high": ci_95[1],
                "ci_decision_low": ci_dec[0],
                "ci_decision_high": ci_dec[1],
                "margin": 0.20,
                "status": "DEVELOPMENT_SMOKE_ONLY",
            }
        )

        # Aggregate Regime Error Contrast
        cell_reg_contrasts = [
            dataset_stats_arrays[d][f"{d}_{f}_{base_id}_regime_error_improvement"] for d, f in cells
        ]
        agg_delta_reg = np.mean(cell_reg_contrasts, axis=0)
        rq4_stats_dict[f"aggregate_{base_id}_regime_error_improvement"] = agg_delta_reg
        ci_95_r = compute_bootstrap_ci(agg_delta_reg, quantiles=DESCRIPTIVE_QUANTILES)
        ci_dec_r = compute_bootstrap_ci(agg_delta_reg, quantiles=DECISION_QUANTILES)
        contrast_records.append(
            {
                "contrast_id": f"RQ4_aggregate_{base_id}_regime_error_improvement",
                "dataset": "ALL_6_CELLS",
                "model_family": "BOTH",
                "comparator": base_id,
                "metric": "aggregate_delta_regime_error",
                "mean": float(np.mean(agg_delta_reg)),
                "median": float(np.median(agg_delta_reg)),
                "ci_95_low": ci_95_r[0],
                "ci_95_high": ci_95_r[1],
                "ci_decision_low": ci_dec_r[0],
                "ci_decision_high": ci_dec_r[1],
                "margin": 0.01,
                "status": "DEVELOPMENT_SMOKE_ONLY",
            }
        )

        # Aggregate Stage Error Contrast
        cell_stg_contrasts = [
            dataset_stats_arrays[d][f"{d}_{f}_{base_id}_stage_error_improvement"] for d, f in cells
        ]
        agg_delta_stg = np.mean(cell_stg_contrasts, axis=0)
        rq4_stats_dict[f"aggregate_{base_id}_stage_error_improvement"] = agg_delta_stg
        ci_95_s = compute_bootstrap_ci(agg_delta_stg, quantiles=DESCRIPTIVE_QUANTILES)
        ci_dec_s = compute_bootstrap_ci(agg_delta_stg, quantiles=DECISION_QUANTILES)
        contrast_records.append(
            {
                "contrast_id": f"RQ4_aggregate_{base_id}_stage_error_improvement",
                "dataset": "ALL_6_CELLS",
                "model_family": "BOTH",
                "comparator": base_id,
                "metric": "aggregate_delta_stage_error",
                "mean": float(np.mean(agg_delta_stg)),
                "median": float(np.median(agg_delta_stg)),
                "ci_95_low": ci_95_s[0],
                "ci_95_high": ci_95_s[1],
                "ci_decision_low": ci_dec_s[0],
                "ci_decision_high": ci_dec_s[1],
                "margin": 0.01,
                "status": "DEVELOPMENT_SMOKE_ONLY",
            }
        )

    # -------------------------------------------------------------------------
    # Save Artifacts
    # -------------------------------------------------------------------------
    df_point_preds = pd.DataFrame(point_pred_rows)
    df_interval_preds = pd.DataFrame(interval_pred_rows)
    df_traces = pd.DataFrame(trace_rows)
    df_outcomes = pd.DataFrame(engine_seed_outcome_rows)
    df_engine_metrics = pd.DataFrame(engine_metric_rows)
    df_subgroup_metrics = pd.DataFrame(subgroup_metric_rows)
    df_cell_summary = pd.DataFrame(cell_summary_rows)
    df_contrasts = pd.DataFrame(contrast_records)

    # Write CSVs
    write_immutable_csv(out_dir / "point_predictions.csv", df_point_preds)
    write_immutable_csv(out_dir / "interval_predictions.csv", df_interval_preds)
    write_immutable_csv(out_dir / "decision_traces.csv", df_traces)
    write_immutable_csv(out_dir / "engine_seed_outcomes.csv", df_outcomes)
    write_immutable_csv(out_dir / "engine_metrics.csv", df_engine_metrics)
    write_immutable_csv(out_dir / "subgroup_metrics.csv", df_subgroup_metrics)
    write_immutable_csv(out_dir / "cell_summary.csv", df_cell_summary)
    write_immutable_csv(out_dir / "contrast_intervals.csv", df_contrasts)

    # Write Bootstrap Statistics NPZs
    npz_hashes: dict[str, str] = {}
    for ds in CONFIRMATORY_DATASETS:
        ds_stats_p = out_dir / f"bootstrap_statistics_{ds}.npz"
        h = write_immutable_npz(
            ds_stats_p,
            arrays=dataset_stats_arrays[ds],
            metadata={
                "dataset": ds,
                "n_replicates": n_bootstrap,
                "status": "DEVELOPMENT_SMOKE_ONLY",
            },
        )
        npz_hashes[f"bootstrap_statistics_{ds}"] = h

    rq4_p = out_dir / "bootstrap_statistics_RQ4.npz"
    h_rq4 = write_immutable_npz(
        rq4_p,
        arrays=rq4_stats_dict,
        metadata={
            "description": "Equal-six-cell aggregate contrast distributions",
            "n_replicates": n_bootstrap,
            "status": "DEVELOPMENT_SMOKE_ONLY",
        },
    )
    npz_hashes["bootstrap_statistics_RQ4"] = h_rq4

    # Execution Manifest
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": "step09-smoke-manifest-v2",
        "status": "DEVELOPMENT_SMOKE_ONLY",
        "source_execution_commit": git_sha,
        "git_dirty": git_dirty,
        "environment": env_meta,
        "counts": {
            "primary_configurations": 810,
            "control_configurations": 120,
            "total_configurations": 930,
            "primary_outcome_rows": 16470,
            "control_outcome_rows": 3120,
            "total_outcome_rows": 19590,
            "primary_summary_rows": 162,
            "control_summary_rows": 24,
            "total_summary_rows": 186,
            "bootstrap_replicates": n_bootstrap,
        },
        "artifact_hashes": {
            "point_predictions_csv": compute_sha256(out_dir / "point_predictions.csv"),
            "interval_predictions_csv": compute_sha256(out_dir / "interval_predictions.csv"),
            "decision_traces_csv": compute_sha256(out_dir / "decision_traces.csv"),
            "engine_seed_outcomes_csv": compute_sha256(out_dir / "engine_seed_outcomes.csv"),
            "engine_metrics_csv": compute_sha256(out_dir / "engine_metrics.csv"),
            "subgroup_metrics_csv": compute_sha256(out_dir / "subgroup_metrics.csv"),
            "cell_summary_csv": compute_sha256(out_dir / "cell_summary.csv"),
            "contrast_intervals_csv": compute_sha256(out_dir / "contrast_intervals.csv"),
            "bootstrap_draws_FD001": compute_sha256(out_dir / "bootstrap_draws_FD001.npz"),
            "bootstrap_draws_FD002": compute_sha256(out_dir / "bootstrap_draws_FD002.npz"),
            "bootstrap_draws_FD004": compute_sha256(out_dir / "bootstrap_draws_FD004.npz"),
            **npz_hashes,
        },
        "notice": (
            "All outcomes and intervals in this directory are developmental validation smoke "
            "diagnostics only. No held-out test data was accessed or evaluated. "
            "Confirmatory hypothesis decisions remain strictly PENDING."
        ),
    }

    manifest_p = out_dir / "execution_manifest.json"
    write_immutable_json(manifest_p, manifest)

    return manifest
