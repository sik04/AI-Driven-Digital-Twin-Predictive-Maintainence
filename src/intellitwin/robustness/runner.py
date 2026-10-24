"""Production runner orchestrating Experiment A (ablation) and Experiment B (stress tests)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.confirmatory.data import (
    generate_predictions_for_cell,
    verify_raw_data_hashes,
)
from intellitwin.data.artifacts import compute_sha256, load_preprocessor_artifact
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import (
    EXPECTED_ENGINE_COUNTS,
    LIFECYCLE_STAGES,
    SENSOR_COLUMNS,
)
from intellitwin.data.splits import load_split_manifest, select_partition
from intellitwin.data.windowing import construct_windows
from intellitwin.decision.policies import (
    load_primary_reference_cost,
    lower_bound_one_cycle_policy,
)
from intellitwin.evaluation.inference import simulate_engine_policy
from intellitwin.evaluation.schema import (
    CONFIRMATORY_DATASETS,
    CONFIRMATORY_MODELS,
    CONFIRMATORY_SEEDS,
    COST_SCENARIOS,
)
from intellitwin.provenance import write_immutable_csv, write_immutable_json
from intellitwin.robustness.ablation import (
    ALL_EIGHT_ABLATION_VARIANTS,
    VARIANT_BY_ID,
    fit_exploratory_ablation_calibrator,
    predict_ablation_intervals,
)
from intellitwin.robustness.perturbations import (
    ALL_STRESS_CONDITIONS,
    construct_perturbed_windows,
)
from intellitwin.robustness.statistics import (
    PHASE08_BOOTSTRAP_REPLICATES,
    compute_engine_summary_records,
    compute_paired_bootstrap_contrast,
    generate_phase08_bootstrap_draws,
)
from intellitwin.uncertainty.artifacts import (
    load_calibrator_from_artifact,
    resolve_repo_relative_path,
)
from intellitwin.uncertainty.calibration import Calibrator

logger = logging.getLogger(__name__)


def execute_phase08_evaluation(
    output_dir: Path | str,
    base_dir: Path | str = ".",
    raw_data_dir: Path | str = "data/raw/cmapss",
    confirmatory_dir: Path | str = "experiments/confirmatory_v1",
    calibration_cache_dir: Path | str = "experiments/calibration/point_predictions/calibration",
    overwrite: bool = False,
) -> dict[str, Any]:
    """Execute complete Phase 8 exploratory ablation and robustness evaluations.

    Produces all immutable output artifacts under output_dir.
    """
    base = Path(base_dir).resolve()
    out_dir = Path(output_dir).resolve()
    conf_dir = (base / confirmatory_dir).resolve()

    if (out_dir / "execution_manifest.json").exists() and not overwrite:
        raise FileExistsError(
            f"Execution manifest already exists at {out_dir / 'execution_manifest.json'}. "
            "Refusing to overwrite completed exploratory run."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    calibrators_out_dir = out_dir / "exploratory_calibrators"
    calibrators_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify frozen raw source hashes
    raw_hashes = verify_raw_data_hashes(raw_data_dir=raw_data_dir, base_dir=base)

    # Load frozen cost scenario
    _ = load_primary_reference_cost(
        base / "research/research_design/maintenance_cost_scenarios.yaml"
    )
    cost_scenario = COST_SCENARIOS["primary_reference"]

    # Load clean held-out point predictions from confirmatory_v1
    clean_point_preds_p = conf_dir / "point_predictions.csv"
    if not clean_point_preds_p.exists():
        raise FileNotFoundError(
            f"Confirmatory point predictions cache missing: {clean_point_preds_p}"
        )
    df_clean_preds = pd.read_csv(clean_point_preds_p)

    # Pre-generate bootstrap draws for each dataset
    bootstrap_draws_by_ds: dict[str, np.ndarray[Any, Any]] = {}
    partition_engines_by_ds: dict[str, list[int]] = {}
    for ds in CONFIRMATORY_DATASETS:
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        split_manifest = load_split_manifest(split_p)
        test_engines = sorted(split_manifest.get_partition("test"))
        partition_engines_by_ds[ds] = test_engines
        b_draws = generate_phase08_bootstrap_draws(ds, test_engines, base_dir=base)
        bootstrap_draws_by_ds[ds] = b_draws
        # Save bootstrap draws
        np.savez_compressed(out_dir / f"bootstrap_draws_{ds}.npz", draws=b_draws)

    # =========================================================================
    # EXPERIMENT A: FACTORIAL COMPONENT ABLATION
    # =========================================================================
    ablation_engine_rows: list[dict[str, Any]] = []
    # Key: (dataset, model_family, variant_id, metric_name) -> dict[unit, float]
    ablation_metric_store: dict[tuple[str, str, str, str], dict[int, float]] = {}

    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                # Sub-slice clean test predictions for cell
                mask_cell = (
                    (df_clean_preds["dataset"] == ds)
                    & (df_clean_preds["model_family"] == mf)
                    & (df_clean_preds["seed"] == seed)
                )
                df_cell_clean = df_clean_preds[mask_cell].copy()
                df_cell_clean = df_cell_clean.sort_values(["unit", "endpoint_cycle"]).reset_index(
                    drop=True
                )

                for variant in ALL_EIGHT_ABLATION_VARIANTS:
                    # Fit exploratory calibrator
                    cal = fit_exploratory_ablation_calibrator(
                        dataset=ds,
                        model_family=mf,
                        seed=seed,
                        variant=variant,
                        calibration_cache_dir=calibration_cache_dir,
                        base_dir=base,
                    )

                    # Save exploratory calibrator artifact (Phase 8 exploratory only)
                    bundles_data: dict[str, Any] = {}
                    for cov, b in cal.coverage_bundles.items():
                        bundles_data[f"coverage_{int(cov * 100)}"] = b.to_dict()
                    cal_art = {
                        "schema_version": "phase08-exploratory-calibrator-v1",
                        "status": "EXPLORATORY_POST_CONFIRMATORY",
                        "method_id": cal.method_id,
                        "variant_id": variant.variant_id,
                        "gamma": variant.gamma,
                        "beta_code": variant.beta_code,
                        "routing": variant.routing,
                        "dataset": cal.dataset_name,
                        "model_family": cal.model_family,
                        "model_seed": cal.model_seed,
                        "threshold_bundles": bundles_data,
                    }
                    cal_path = (
                        calibrators_out_dir / f"{ds}_{mf}_seed{seed}_{variant.variant_id}.json"
                    )
                    with open(cal_path, "w", encoding="utf-8") as f:
                        json.dump(cal_art, f, indent=2)

                    # Predict intervals on clean held-out predictions
                    low, upp, fallback = predict_ablation_intervals(
                        calibrator=cal,
                        variant=variant,
                        predictions=df_cell_clean["prediction"].to_numpy(),
                        regimes=df_cell_clean["regime"].to_numpy(),
                        nominal_coverage=0.90,
                    )

                    df_pred_var = df_cell_clean.copy()
                    df_pred_var["lower"] = low
                    df_pred_var["upper"] = upp
                    df_pred_var["fallback_used"] = fallback

                    # Simulate policy on each engine
                    sim_rows: list[dict[str, Any]] = []
                    for unit in partition_engines_by_ds[ds]:
                        df_eng = df_pred_var[df_pred_var["unit"] == unit].sort_values(
                            "endpoint_cycle"
                        )
                        cyc_arr = df_eng["endpoint_cycle"].to_numpy()
                        p_arr = df_eng["prediction"].to_numpy()
                        l_arr = df_eng["lower"].to_numpy()
                        u_arr = df_eng["upper"].to_numpy()
                        r_arr = df_eng["regime"].to_numpy()
                        # Terminal failure cycle T = max(endpoint_cycle) + 1
                        # More precisely: rul_true + endpoint_cycle = failure_cycle
                        # In confirmatory data, endpoint_cycle + rul_true = failure_cycle
                        fail_cycle = int(cyc_arr[0] + df_eng["rul_true"].to_numpy()[0])

                        sim_out = simulate_engine_policy(
                            unit=int(unit),
                            seed=int(seed),
                            configuration_id=f"{ds}_{mf}_{variant.variant_id}",
                            method_or_control_id=variant.variant_id,
                            cycles=cyc_arr,
                            predictions=p_arr,
                            lower_bounds=l_arr,
                            upper_bounds=u_arr,
                            regimes=r_arr,
                            failure_cycle=fail_cycle,
                            policy_fn=lower_bound_one_cycle_policy,
                            scenario=cost_scenario,
                        )
                        sim_rows.append(
                            {
                                "unit": int(unit),
                                "seed": int(seed),
                                "total_cost": sim_out.total_cost,
                                "pm_occurred": sim_out.pm_occurred,
                                "failed": sim_out.failed,
                                "wasted_rul": sim_out.wasted_rul,
                                "intervention_cycle": sim_out.intervention_cycle,
                            }
                        )

                    df_sim_var = pd.DataFrame(sim_rows)
                    eng_summary = compute_engine_summary_records(
                        df_pred_var, df_sim_var, nominal_coverage=0.90
                    )
                    eng_summary["dataset"] = ds
                    eng_summary["model_family"] = mf
                    eng_summary["seed"] = seed
                    eng_summary["variant_id"] = variant.variant_id
                    eng_summary["gamma"] = variant.gamma
                    eng_summary["beta_code"] = variant.beta_code
                    eng_summary["routing"] = variant.routing
                    eng_summary["is_full_method"] = variant.is_full_method

                    ablation_engine_rows.extend(eng_summary.to_dict(orient="records"))

    df_ablation_engine_raw = pd.DataFrame(ablation_engine_rows)
    # Average across model seeds within each engine
    # for each (dataset, model_family, variant_id, unit)
    metric_cols = [
        "rmse",
        "mae",
        "coverage",
        "coverage_abs_error",
        "width",
        "interval_score",
        "lower_tail_miss",
        "upper_tail_miss",
        "cost",
        "failure_rate",
        "pm_rate",
        "wasted_rul",
        "intervention_cycle",
        "fallback_freq",
    ]
    df_ablation_engine = (
        df_ablation_engine_raw.groupby(
            [
                "dataset",
                "model_family",
                "variant_id",
                "gamma",
                "beta_code",
                "routing",
                "is_full_method",
                "unit",
            ]
        )[metric_cols]
        .mean()
        .reset_index()
    )

    # Populate ablation_metric_store
    for (ds, mf, vid), grp in df_ablation_engine.groupby(["dataset", "model_family", "variant_id"]):
        for col in metric_cols:
            ablation_metric_store[(ds, mf, vid, col)] = dict(
                zip(grp["unit"], grp[col], strict=False)
            )

    # =========================================================================
    # EXPERIMENT B: FROZEN-METHOD STRESS TESTS
    # =========================================================================
    stress_engine_rows: list[dict[str, Any]] = []
    # Key: (dataset, model_family, method_id, condition_id, metric_name) -> dict[unit, float]
    stress_metric_store: dict[tuple[str, str, str, str, str], dict[int, float]] = {}

    # Load frozen calibrators for the 3 original methods
    frozen_calibrators: dict[tuple[str, str, int, str], Calibrator] = {}
    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                for m_id in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
                    cal_dir = base / "experiments/calibration/fitted" / ds / mf / f"seed_{seed}"
                    cal_p = cal_dir / m_id / "calibrator.json"
                    with open(cal_p, encoding="utf-8") as f:
                        art = json.load(f)
                    cal_obj = load_calibrator_from_artifact(art)
                    frozen_calibrators[(ds, mf, seed, m_id)] = cal_obj

    # Cache preprocessed clean test DataFrames per dataset
    preprocessed_clean_by_ds: dict[str, pd.DataFrame] = {}
    for ds in CONFIRMATORY_DATASETS:
        raw_p = base / raw_data_dir / f"train_{ds}.txt"
        df_raw = load_cmapss_run_to_failure(
            path=raw_p,
            dataset_name=ds,
            expected_engine_count=EXPECTED_ENGINE_COUNTS[ds],
        )
        split_p = resolve_repo_relative_path(
            base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        )
        split_manifest = load_split_manifest(split_p)
        df_part = select_partition(df_raw, split_manifest, partition_name="test")
        prep_p = resolve_repo_relative_path(
            base, f"experiments/preprocessing/{ds}/preprocessor.json"
        )
        preproc, _ = load_preprocessor_artifact(prep_p)
        df_trans = preproc.transform(df_part)
        preprocessed_clean_by_ds[ds] = df_trans

    for ds in CONFIRMATORY_DATASETS:
        df_trans = preprocessed_clean_by_ds[ds]
        for cond in ALL_STRESS_CONDITIONS:
            for rep_id in range(cond.replicates):
                # Construct perturbed windows
                if cond.condition_type == "clean":
                    windows = construct_windows(df_trans)
                else:
                    windows = construct_perturbed_windows(
                        df_preprocessed=df_trans,
                        dataset=ds,
                        condition=cond,
                        replicate_id=rep_id,
                    )

                for mf in CONFIRMATORY_MODELS:
                    for seed in CONFIRMATORY_SEEDS:
                        # Generate point predictions
                        df_pred_stressed = generate_predictions_for_cell(
                            windows=windows,
                            dataset=ds,
                            model_family=mf,
                            seed=seed,
                            base_dir=base,
                        )
                        # Re-attach clean true labels and regime
                        # generate_predictions_for_cell preserves unit, endpoint_cycle,
                        # rul_true, regime
                        for m_id in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
                            cal_obj = frozen_calibrators[(ds, mf, seed, m_id)]
                            low, upp, fallback = cal_obj.predict_intervals(
                                predictions=df_pred_stressed["prediction"].to_numpy(),
                                regimes=df_pred_stressed["regime"].to_numpy(),
                                nominal_coverage=0.90,
                            )
                            df_pred_method = df_pred_stressed.copy()
                            df_pred_method["lower"] = low
                            df_pred_method["upper"] = upp
                            df_pred_method["fallback_used"] = fallback

                            sim_rows: list[dict[str, Any]] = []
                            for unit in partition_engines_by_ds[ds]:
                                df_eng = df_pred_method[df_pred_method["unit"] == unit].sort_values(
                                    "endpoint_cycle"
                                )
                                cyc_arr = df_eng["endpoint_cycle"].to_numpy()
                                p_arr = df_eng["prediction"].to_numpy()
                                l_arr = df_eng["lower"].to_numpy()
                                u_arr = df_eng["upper"].to_numpy()
                                r_arr = df_eng["regime"].to_numpy()
                                fail_cycle = int(cyc_arr[0] + df_eng["rul_true"].to_numpy()[0])

                                sim_out = simulate_engine_policy(
                                    unit=int(unit),
                                    seed=int(seed),
                                    configuration_id=f"{ds}_{mf}_{cond.condition_id}_{m_id}",
                                    method_or_control_id=m_id,
                                    cycles=cyc_arr,
                                    predictions=p_arr,
                                    lower_bounds=l_arr,
                                    upper_bounds=u_arr,
                                    regimes=r_arr,
                                    failure_cycle=fail_cycle,
                                    policy_fn=lower_bound_one_cycle_policy,
                                    scenario=cost_scenario,
                                )
                                sim_rows.append(
                                    {
                                        "unit": int(unit),
                                        "seed": int(seed),
                                        "total_cost": sim_out.total_cost,
                                        "pm_occurred": sim_out.pm_occurred,
                                        "failed": sim_out.failed,
                                        "wasted_rul": sim_out.wasted_rul,
                                        "intervention_cycle": sim_out.intervention_cycle,
                                    }
                                )

                            df_sim_method = pd.DataFrame(sim_rows)
                            eng_summary = compute_engine_summary_records(
                                df_pred_method, df_sim_method, nominal_coverage=0.90
                            )
                            eng_summary["dataset"] = ds
                            eng_summary["model_family"] = mf
                            eng_summary["seed"] = seed
                            eng_summary["condition_id"] = cond.condition_id
                            eng_summary["condition_type"] = cond.condition_type
                            eng_summary["param_value"] = (
                                cond.param_value if cond.param_value is not None else 0.0
                            )
                            eng_summary["replicate_id"] = rep_id
                            eng_summary["method_id"] = m_id

                            stress_engine_rows.extend(eng_summary.to_dict(orient="records"))

    df_stress_engine_raw = pd.DataFrame(stress_engine_rows)
    # Average across model seeds and perturbation replicates within each engine
    df_stress_engine = (
        df_stress_engine_raw.groupby(
            [
                "dataset",
                "model_family",
                "method_id",
                "condition_id",
                "condition_type",
                "param_value",
                "unit",
            ]
        )[metric_cols]
        .mean()
        .reset_index()
    )

    for (ds, mf, mid, cid), grp in df_stress_engine.groupby(
        ["dataset", "model_family", "method_id", "condition_id"]
    ):
        for col in metric_cols:
            stress_metric_store[(ds, mf, mid, cid, col)] = dict(
                zip(grp["unit"], grp[col], strict=False)
            )

    # =========================================================================
    # SUMMARY AGGREGATION AND BOOTSTRAP CONTRASTS
    # =========================================================================
    # 1. Ablation Summary
    ablation_summary_rows: list[dict[str, Any]] = []
    for (ds, mf, vid, g, b, r, is_f), grp in df_ablation_engine.groupby(
        ["dataset", "model_family", "variant_id", "gamma", "beta_code", "routing", "is_full_method"]
    ):
        row = {
            "dataset": ds,
            "model_family": mf,
            "variant_id": vid,
            "gamma": g,
            "beta_code": b,
            "routing": r,
            "is_full_method": is_f,
        }
        for col in metric_cols:
            row[f"{col}_mean"] = float(grp[col].mean())
            row[f"{col}_std"] = float(grp[col].std())
        ablation_summary_rows.append(row)
    df_ablation_summary = pd.DataFrame(ablation_summary_rows)

    # 2. Stress Summary
    stress_summary_rows: list[dict[str, Any]] = []
    for (ds, mf, mid, cid, ctype, pval), grp in df_stress_engine.groupby(
        ["dataset", "model_family", "method_id", "condition_id", "condition_type", "param_value"]
    ):
        row = {
            "dataset": ds,
            "model_family": mf,
            "method_id": mid,
            "condition_id": cid,
            "condition_type": ctype,
            "param_value": pval,
        }
        for col in metric_cols:
            row[f"{col}_mean"] = float(grp[col].mean())
            row[f"{col}_std"] = float(grp[col].std())
        stress_summary_rows.append(row)
    df_stress_summary = pd.DataFrame(stress_summary_rows)

    # 3. Paired Contrasts
    paired_contrast_rows: list[dict[str, Any]] = []

    # Ablation contrasts: Variant minus Full Method (full = gamma2_betam1_regime)
    full_vid = "gamma2_betam1_regime"
    for ds in CONFIRMATORY_DATASETS:
        b_draws = bootstrap_draws_by_ds[ds]
        for mf in CONFIRMATORY_MODELS:
            for variant in ALL_EIGHT_ABLATION_VARIANTS:
                vid = variant.variant_id
                for col in ("cost", "coverage", "width", "interval_score", "rmse", "failure_rate"):
                    vals_var = ablation_metric_store[(ds, mf, vid, col)]
                    vals_full = ablation_metric_store[(ds, mf, full_vid, col)]
                    pt, lo, hi = compute_paired_bootstrap_contrast(vals_var, vals_full, b_draws)
                    paired_contrast_rows.append(
                        {
                            "comparison_type": "ablation_vs_full",
                            "dataset": ds,
                            "model_family": mf,
                            "variant_or_condition": vid,
                            "baseline_or_full": full_vid,
                            "metric": col,
                            "delta_point": pt,
                            "ci_95_low": lo,
                            "ci_95_high": hi,
                            "favors_variant": (pt < 0)
                            if col in ("cost", "width", "interval_score", "rmse", "failure_rate")
                            else (pt > 0),
                        }
                    )

    # Stress contrasts: Stressed minus Clean
    for ds in CONFIRMATORY_DATASETS:
        b_draws = bootstrap_draws_by_ds[ds]
        for mf in CONFIRMATORY_MODELS:
            for mid in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
                for cond in ALL_STRESS_CONDITIONS:
                    cid = cond.condition_id
                    if cid == "clean":
                        continue
                    for col in (
                        "cost",
                        "coverage",
                        "width",
                        "interval_score",
                        "rmse",
                        "failure_rate",
                    ):
                        vals_str = stress_metric_store[(ds, mf, mid, cid, col)]
                        vals_cln = stress_metric_store[(ds, mf, mid, "clean", col)]
                        pt, lo, hi = compute_paired_bootstrap_contrast(vals_str, vals_cln, b_draws)
                        paired_contrast_rows.append(
                            {
                                "comparison_type": "stress_vs_clean",
                                "dataset": ds,
                                "model_family": mf,
                                "variant_or_condition": f"{mid}:{cid}",
                                "baseline_or_full": f"{mid}:clean",
                                "metric": col,
                                "delta_point": pt,
                                "ci_95_low": lo,
                                "ci_95_high": hi,
                                "favors_variant": (pt < 0)
                                if col
                                in ("cost", "width", "interval_score", "rmse", "failure_rate")
                                else (pt > 0),
                            }
                        )

    df_paired_contrasts = pd.DataFrame(paired_contrast_rows)

    # 4. Factor Main Effects (On minus Off)
    # Average across the 4 matched settings of the other two factors
    factor_effect_rows: list[dict[str, Any]] = []
    # For gamma: gamma=2 (on) vs gamma=0 (off)
    # Pairs: (beta0, global), (beta0, regime), (betam1, global), (betam1, regime)
    for ds in CONFIRMATORY_DATASETS:
        b_draws = bootstrap_draws_by_ds[ds]
        for mf in CONFIRMATORY_MODELS:
            for factor_name, on_vids, off_vids in [
                (
                    "gamma_scale",
                    [
                        "gamma2_beta0_global",
                        "gamma2_beta0_regime",
                        "gamma2_betam1_global",
                        "gamma2_betam1_regime",
                    ],
                    [
                        "gamma0_beta0_global",
                        "gamma0_beta0_regime",
                        "gamma0_betam1_global",
                        "gamma0_betam1_regime",
                    ],
                ),
                (
                    "beta_asymmetry",
                    [
                        "gamma0_betam1_global",
                        "gamma0_betam1_regime",
                        "gamma2_betam1_global",
                        "gamma2_betam1_regime",
                    ],
                    [
                        "gamma0_beta0_global",
                        "gamma0_beta0_regime",
                        "gamma2_beta0_global",
                        "gamma2_beta0_regime",
                    ],
                ),
                (
                    "regime_routing",
                    [
                        "gamma0_beta0_regime",
                        "gamma0_betam1_regime",
                        "gamma2_beta0_regime",
                        "gamma2_betam1_regime",
                    ],
                    [
                        "gamma0_beta0_global",
                        "gamma0_betam1_global",
                        "gamma2_beta0_global",
                        "gamma2_betam1_global",
                    ],
                ),
            ]:
                for col in ("cost", "coverage", "width", "interval_score", "rmse", "failure_rate"):
                    units = partition_engines_by_ds[ds]
                    on_means = {
                        u: float(
                            np.mean(
                                [ablation_metric_store[(ds, mf, vid, col)][u] for vid in on_vids]
                            )
                        )
                        for u in units
                    }
                    off_means = {
                        u: float(
                            np.mean(
                                [ablation_metric_store[(ds, mf, vid, col)][u] for vid in off_vids]
                            )
                        )
                        for u in units
                    }
                    pt, lo, hi = compute_paired_bootstrap_contrast(on_means, off_means, b_draws)
                    factor_effect_rows.append(
                        {
                            "dataset": ds,
                            "model_family": mf,
                            "factor": factor_name,
                            "metric": col,
                            "effect_on_minus_off": pt,
                            "ci_95_low": lo,
                            "ci_95_high": hi,
                        }
                    )

    df_factor_effects = pd.DataFrame(factor_effect_rows)

    # 5. Subgroup Metrics (Regime and Lifecycle Stage coverage breakdown)
    # Compute clean subgroup breakdowns
    subgroup_rows: list[dict[str, Any]] = []
    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for seed in CONFIRMATORY_SEEDS:
                mask_cell = (
                    (df_clean_preds["dataset"] == ds)
                    & (df_clean_preds["model_family"] == mf)
                    & (df_clean_preds["seed"] == seed)
                )
                df_sub = df_clean_preds[mask_cell].copy()
                for vid in (full_vid, "gamma0_beta0_global", "gamma0_beta0_regime"):
                    variant = VARIANT_BY_ID[vid]
                    cal = fit_exploratory_ablation_calibrator(
                        ds,
                        mf,
                        seed,
                        variant,
                        calibration_cache_dir=calibration_cache_dir,
                        base_dir=base,
                    )
                    low, upp, _ = predict_ablation_intervals(
                        cal,
                        variant,
                        df_sub["prediction"].to_numpy(),
                        df_sub["regime"].to_numpy(),
                        0.90,
                    )
                    df_sub_eval = df_sub.copy()
                    df_sub_eval["covered"] = (
                        (low <= df_sub_eval["rul_true"]) & (df_sub_eval["rul_true"] <= upp)
                    ).astype(float)
                    df_sub_eval["lower_tail_miss"] = (df_sub_eval["rul_true"] < low).astype(float)
                    df_sub_eval["upper_tail_miss"] = (df_sub_eval["rul_true"] > upp).astype(float)

                    for reg in sorted(df_sub_eval["regime"].unique()):
                        df_reg = df_sub_eval[df_sub_eval["regime"] == reg]
                        subgroup_rows.append(
                            {
                                "dataset": ds,
                                "model_family": mf,
                                "seed": seed,
                                "variant_id": vid,
                                "subgroup_family": "regime",
                                "subgroup": reg,
                                "n_endpoints": len(df_reg),
                                "n_engines": df_reg["unit"].nunique(),
                                "coverage": float(df_reg["covered"].mean()),
                                "lower_tail_miss": float(df_reg["lower_tail_miss"].mean()),
                                "upper_tail_miss": float(df_reg["upper_tail_miss"].mean()),
                            }
                        )
                    for stg in LIFECYCLE_STAGES:
                        df_stg = df_sub_eval[df_sub_eval["lifecycle_stage"] == stg]
                        subgroup_rows.append(
                            {
                                "dataset": ds,
                                "model_family": mf,
                                "seed": seed,
                                "variant_id": vid,
                                "subgroup_family": "lifecycle_stage",
                                "subgroup": stg,
                                "n_endpoints": len(df_stg),
                                "n_engines": df_stg["unit"].nunique(),
                                "coverage": float(df_stg["covered"].mean()),
                                "lower_tail_miss": float(df_stg["lower_tail_miss"].mean()),
                                "upper_tail_miss": float(df_stg["upper_tail_miss"].mean()),
                            }
                        )

    df_subgroup = pd.DataFrame(subgroup_rows)
    # Average across seeds
    df_subgroup_summary = (
        df_subgroup.groupby(
            ["dataset", "model_family", "variant_id", "subgroup_family", "subgroup"]
        )
        .agg(
            n_endpoints=("n_endpoints", "mean"),
            n_engines=("n_engines", "max"),
            coverage=("coverage", "mean"),
            lower_tail_miss=("lower_tail_miss", "mean"),
            upper_tail_miss=("upper_tail_miss", "mean"),
        )
        .reset_index()
    )

    # Save output artifacts
    write_immutable_csv(out_dir / "ablation_engine_metrics.csv", df_ablation_engine)
    write_immutable_csv(out_dir / "stress_engine_metrics.csv", df_stress_engine)
    write_immutable_csv(out_dir / "ablation_summary.csv", df_ablation_summary)
    write_immutable_csv(out_dir / "stress_summary.csv", df_stress_summary)
    write_immutable_csv(out_dir / "paired_contrasts.csv", df_paired_contrasts)
    write_immutable_csv(out_dir / "subgroup_metrics.csv", df_subgroup_summary)

    # Save factor main effects
    write_immutable_csv(out_dir / "factor_main_effects.csv", df_factor_effects)

    # Save perturbation manifest
    perturbation_manifest = {
        "conditions": [c.__dict__ for c in ALL_STRESS_CONDITIONS],
        "sensor_columns": list(SENSOR_COLUMNS),
        "seed_sequence_formula": (
            "[2026, 8, dataset_number, engine_id, perturbation_family, replicate_id]"
        ),
        "total_stream_conditions": 18,
    }
    write_immutable_json(out_dir / "perturbation_manifest.json", perturbation_manifest)

    # Input manifest
    input_manifest = {
        "raw_source_hashes": raw_hashes,
        "clean_point_predictions_sha256": compute_sha256(clean_point_preds_p),
        "calibration_cache_dir": str(calibration_cache_dir),
    }
    write_immutable_json(out_dir / "input_manifest.json", input_manifest)

    # Execution manifest
    artifact_hashes = {
        "ablation_engine_metrics_csv": compute_sha256(out_dir / "ablation_engine_metrics.csv"),
        "stress_engine_metrics_csv": compute_sha256(out_dir / "stress_engine_metrics.csv"),
        "ablation_summary_csv": compute_sha256(out_dir / "ablation_summary.csv"),
        "stress_summary_csv": compute_sha256(out_dir / "stress_summary.csv"),
        "paired_contrasts_csv": compute_sha256(out_dir / "paired_contrasts.csv"),
        "subgroup_metrics_csv": compute_sha256(out_dir / "subgroup_metrics.csv"),
        "perturbation_manifest_json": compute_sha256(out_dir / "perturbation_manifest.json"),
        "input_manifest_json": compute_sha256(out_dir / "input_manifest.json"),
    }
    execution_manifest = {
        "protocol_version": "phase08-v1",
        "schema_version": "phase08-manifest-v1",
        "status": "EXPLORATORY_POST_CONFIRMATORY",
        "counts": {
            "ablation_configurations": 240,
            "stress_evaluations": 1620,
            "datasets": len(CONFIRMATORY_DATASETS),
            "models": len(CONFIRMATORY_MODELS),
            "seeds": len(CONFIRMATORY_SEEDS),
            "bootstrap_replicates": PHASE08_BOOTSTRAP_REPLICATES,
        },
        "artifact_hashes": artifact_hashes,
    }
    write_immutable_json(out_dir / "execution_manifest.json", execution_manifest)

    # Execution log
    log_content = (
        "Phase 8 Exploratory Ablation and Robustness Analysis Completed Successfully.\n"
        "Evaluated 240 ablation configurations and 1,620 stress evaluations "
        "across 122 held-out engines.\n"
        "All calculations performed under strict post-confirmatory exploratory protocol.\n"
    )
    (out_dir / "execution.log").write_text(log_content, encoding="utf-8")

    return {
        "status": "SUCCESS",
        "output_dir": str(out_dir),
        "execution_manifest": execution_manifest,
    }
