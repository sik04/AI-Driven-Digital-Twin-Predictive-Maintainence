"""Production runner orchestrating Experiment A (ablation) and Experiment B (stress tests)."""

from __future__ import annotations

import gzip
import io
import json
import logging
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from intellitwin.confirmatory.data import (
    generate_predictions_for_cell,
    verify_raw_data_hashes,
)
from intellitwin.data.artifacts import compute_sha256, load_preprocessor_artifact
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import (
    EXPECTED_ENGINE_COUNTS,
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
from intellitwin.provenance import (
    get_git_info,
    write_immutable_csv,
    write_immutable_json,
)
from intellitwin.robustness.ablation import (
    ALL_EIGHT_ABLATION_VARIANTS,
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
    compute_subgroup_metrics_equal_engine,
    generate_phase08_bootstrap_draws,
)
from intellitwin.uncertainty.artifacts import (
    load_calibrator_from_artifact,
    resolve_repo_relative_path,
)
from intellitwin.uncertainty.calibration import Calibrator

logger = logging.getLogger(__name__)


def _gather_protected_input_paths(
    base: Path,
    raw_data_dir: Path | str = "data/raw/cmapss",
    confirmatory_dir: Path | str = "experiments/confirmatory_v1",
    calibration_cache_dir: Path | str = "experiments/calibration/point_predictions/calibration",
) -> list[Path]:
    """Collect all immutable input artifact paths required for Phase 8."""
    paths: list[Path] = []
    # 1. Raw text files
    for ds in CONFIRMATORY_DATASETS:
        paths.append(base / raw_data_dir / f"train_{ds}.txt")

    # 2. Split manifests
    for ds in CONFIRMATORY_DATASETS:
        paths.append(
            resolve_repo_relative_path(
                base, f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
            )
        )

    # 3. Preprocessors
    for ds in CONFIRMATORY_DATASETS:
        paths.append(
            resolve_repo_relative_path(base, f"experiments/preprocessing/{ds}/preprocessor.json")
        )

    # 4. Base model registry and checkpoints
    reg_p = base / "experiments/base_models/model_registry.json"
    if reg_p.exists():
        paths.append(reg_p)
        with open(reg_p, encoding="utf-8") as f:
            reg_data = json.load(f)
        for entry in reg_data.get("entries", {}).values():
            paths.append(resolve_repo_relative_path(base, entry["checkpoint_path"]))

    # 5. Clean point predictions cache from confirmatory
    paths.append(base / confirmatory_dir / "point_predictions.csv")

    # 6. Calibration prediction caches
    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for s in CONFIRMATORY_SEEDS:
                paths.append(base / calibration_cache_dir / ds / mf / f"seed_{s}.csv")

    # 7. Frozen calibrators
    for ds in CONFIRMATORY_DATASETS:
        for mf in CONFIRMATORY_MODELS:
            for s in CONFIRMATORY_SEEDS:
                for mid in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
                    paths.append(
                        base
                        / "experiments/calibration/fitted"
                        / ds
                        / mf
                        / f"seed_{s}"
                        / mid
                        / "calibrator.json"
                    )

    # 8. Cost scenario and config files
    paths.append(base / "research/research_design/maintenance_cost_scenarios.yaml")
    paths.append(base / "research/research_design/phase08_exploratory_config.json")

    return [p.resolve() for p in paths if p.exists()]


def execute_phase08_evaluation(
    output_dir: Path | str,
    base_dir: Path | str = ".",
    raw_data_dir: Path | str = "data/raw/cmapss",
    confirmatory_dir: Path | str = "experiments/confirmatory_v1",
    calibration_cache_dir: Path | str = "experiments/calibration/point_predictions/calibration",
    overwrite: bool = False,
    allow_dirty: bool = False,
) -> dict[str, Any]:
    """Execute complete Phase 8 exploratory ablation and robustness evaluations.

    Produces all immutable output artifacts under output_dir with complete
    cryptographic provenance, independent reference compatibility, and
    equal-engine subgroup weighting.
    """
    start_time_utc = datetime.now(timezone.utc).isoformat()
    execution_start_perf = time.perf_counter()
    log_lines: list[str] = []

    def log(msg: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        line = f"[{ts}] {msg}"
        print(line)
        log_lines.append(line)

    log("Starting Phase 8 Exploratory Ablation & Robustness Analysis")

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

    # CPU inference batching and thread pinning
    torch.set_num_threads(2)

    # 1. Environment and Git provenance
    git_sha, git_dirty = get_git_info(allow_dirty=allow_dirty, repo_root=base)
    log(f"Git commit: {git_sha} (dirty: {git_dirty})")

    # Capture pip freeze & pip check
    pip_freeze_proc = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )
    pip_check_proc = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        check=True,
    )
    (out_dir / "pip_freeze.txt").write_text(pip_freeze_proc.stdout, encoding="utf-8")
    (out_dir / "pip_check.txt").write_text(pip_check_proc.stdout, encoding="utf-8")

    # 2. Hash protected inputs pre-execution
    log("Hashing protected inputs pre-execution...")
    protected_paths = _gather_protected_input_paths(
        base=base,
        raw_data_dir=raw_data_dir,
        confirmatory_dir=confirmatory_dir,
        calibration_cache_dir=calibration_cache_dir,
    )
    pre_protected_hashes: dict[str, str] = {}
    for p in protected_paths:
        rel_posix = p.relative_to(base).as_posix()
        pre_protected_hashes[rel_posix] = compute_sha256(p)

    raw_hashes = verify_raw_data_hashes(raw_data_dir=raw_data_dir, base_dir=base)
    log("Protected inputs verified.")

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

    # Build clean subgroup mapping DataFrame for strict eligibility determination
    clean_subgroup_map = (
        df_clean_preds[
            ["dataset", "unit", "endpoint_cycle", "rul_true", "regime", "lifecycle_stage"]
        ]
        .drop_duplicates(subset=["dataset", "unit", "endpoint_cycle"])
        .reset_index(drop=True)
    )

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
        np.savez_compressed(out_dir / f"bootstrap_draws_{ds}.npz", draws=b_draws)

    # =========================================================================
    # EXPERIMENT A: FACTORIAL COMPONENT ABLATION (240 Cells)
    # =========================================================================
    log("Executing Experiment A: Component Factorial Ablation (240 cells)...")
    ablation_engine_seed_rows: list[dict[str, Any]] = []
    ablation_sim_rows: list[dict[str, Any]] = []
    ablation_interval_rows: list[dict[str, Any]] = []

    # Per-engine subgroup metric accumulator:
    # rows of (evaluation_type, dataset, model_family, variant_id, method_id, condition_id,
    #          subgroup_family, subgroup, unit, n_endpoints, cov, lower_miss, upper_miss)
    subgroup_engine_records: list[dict[str, Any]] = []
    # Subgroup summary accumulator
    subgroup_summary_records: list[dict[str, Any]] = []

    # Metrics store for paired contrasts: (ds, mf, variant_id, metric_col) -> dict[unit, float]
    ablation_metric_store: dict[tuple[str, str, str, str], dict[int, float]] = {}

    for ds in CONFIRMATORY_DATASETS:
        clean_ds_subgroups = clean_subgroup_map[clean_subgroup_map["dataset"] == ds]
        for mf in CONFIRMATORY_MODELS:
            for variant in ALL_EIGHT_ABLATION_VARIANTS:
                variant_eval_frames: list[pd.DataFrame] = []

                for seed in CONFIRMATORY_SEEDS:
                    # Slice clean test predictions for cell
                    mask_cell = (
                        (df_clean_preds["dataset"] == ds)
                        & (df_clean_preds["model_family"] == mf)
                        & (df_clean_preds["seed"] == seed)
                    )
                    df_cell_clean = df_clean_preds[mask_cell].copy()
                    df_cell_clean = df_cell_clean.sort_values(
                        ["unit", "endpoint_cycle"]
                    ).reset_index(drop=True)

                    # Fit exploratory calibrator strictly on calibration cache
                    cal = fit_exploratory_ablation_calibrator(
                        dataset=ds,
                        model_family=mf,
                        seed=seed,
                        variant=variant,
                        calibration_cache_dir=calibration_cache_dir,
                        base_dir=base,
                    )

                    # Save exploratory calibrator artifact
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

                    # Predict intervals on clean held-out test predictions
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
                    df_pred_var["seed"] = seed
                    variant_eval_frames.append(df_pred_var)

                    # Collect per-cycle interval predictions
                    for r in df_pred_var.itertuples():
                        ablation_interval_rows.append(
                            {
                                "dataset": ds,
                                "model_family": mf,
                                "seed": seed,
                                "variant_id": variant.variant_id,
                                "unit": int(r.unit),
                                "endpoint_cycle": int(r.endpoint_cycle),
                                "prediction": float(r.prediction),
                                "rul_true": float(r.rul_true),
                                "lower": float(r.lower),
                                "upper": float(r.upper),
                                "regime": str(r.regime),
                                "lifecycle_stage": str(r.lifecycle_stage),
                                "fallback_used": bool(r.fallback_used),
                            }
                        )

                    # Simulate policy on each engine
                    cell_sim_rows: list[dict[str, Any]] = []
                    for unit in partition_engines_by_ds[ds]:
                        df_eng = df_pred_var[df_pred_var["unit"] == unit].sort_values(
                            "endpoint_cycle"
                        )
                        cyc_arr = df_eng["endpoint_cycle"].to_numpy(dtype=int)
                        p_arr = df_eng["prediction"].to_numpy(dtype=float)
                        l_arr = df_eng["lower"].to_numpy(dtype=float)
                        u_arr = df_eng["upper"].to_numpy(dtype=float)
                        r_arr = df_eng["regime"].to_numpy()
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
                        sim_record = {
                            "dataset": ds,
                            "model_family": mf,
                            "seed": int(seed),
                            "variant_id": variant.variant_id,
                            "unit": int(unit),
                            "terminal_event": sim_out.terminal_event,
                            "intervention_cycle": sim_out.intervention_cycle,
                            "failed": sim_out.failed,
                            "pm_occurred": sim_out.pm_occurred,
                            "wasted_rul": sim_out.wasted_rul,
                            "total_cost": sim_out.total_cost,
                        }
                        ablation_sim_rows.append(sim_record)
                        cell_sim_rows.append(sim_record)

                    df_cell_sim = pd.DataFrame(cell_sim_rows)
                    eng_summary = compute_engine_summary_records(
                        df_pred_var, df_cell_sim, nominal_coverage=0.90
                    )
                    eng_summary["dataset"] = ds
                    eng_summary["model_family"] = mf
                    eng_summary["seed"] = seed
                    eng_summary["variant_id"] = variant.variant_id
                    eng_summary["gamma"] = variant.gamma
                    eng_summary["beta_code"] = variant.beta_code
                    eng_summary["routing"] = variant.routing
                    eng_summary["is_full_method"] = variant.is_full_method
                    ablation_engine_seed_rows.extend(eng_summary.to_dict(orient="records"))

                # Evaluate Subgroups for this ablation variant across all seeds
                df_variant_all_seeds = pd.concat(variant_eval_frames, ignore_index=True)
                for fam_name in ("regime", "lifecycle_stage"):
                    df_eng_sub, df_sub_sum = compute_subgroup_metrics_equal_engine(
                        df_eval=df_variant_all_seeds,
                        clean_subgroup_df=clean_ds_subgroups,
                        subgroup_family=fam_name,
                        nominal_coverage=0.90,
                    )
                    for r_sub in df_eng_sub.itertuples():
                        subgroup_engine_records.append(
                            {
                                "evaluation_type": "ablation",
                                "dataset": ds,
                                "model_family": mf,
                                "variant_id": variant.variant_id,
                                "method_id": "",
                                "condition_id": "clean",
                                "subgroup_family": fam_name,
                                "subgroup": str(r_sub.subgroup),
                                "unit": int(r_sub.unit),
                                "n_endpoints": int(r_sub.n_endpoints),
                                "coverage": float(r_sub.coverage),
                                "lower_tail_miss": float(r_sub.lower_tail_miss),
                                "upper_tail_miss": float(r_sub.upper_tail_miss),
                            }
                        )
                    for r_sum in df_sub_sum.itertuples():
                        subgroup_summary_records.append(
                            {
                                "evaluation_type": "ablation",
                                "dataset": ds,
                                "model_family": mf,
                                "variant_id": variant.variant_id,
                                "method_id": "",
                                "condition_id": "clean",
                                "subgroup_family": fam_name,
                                "subgroup": str(r_sum.subgroup),
                                "n_endpoints": int(r_sum.n_endpoints),
                                "n_engines": int(r_sum.n_engines),
                                "is_eligible": bool(r_sum.is_eligible),
                                "coverage": float(r_sum.coverage),
                                "coverage_abs_error": float(r_sum.coverage_abs_error),
                                "lower_tail_miss": float(r_sum.lower_tail_miss),
                                "upper_tail_miss": float(r_sum.upper_tail_miss),
                            }
                        )

    df_ablation_engine_raw = pd.DataFrame(ablation_engine_seed_rows)
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

    for (ds, mf, vid), grp in df_ablation_engine.groupby(["dataset", "model_family", "variant_id"]):
        for col in metric_cols:
            ablation_metric_store[(ds, mf, vid, col)] = dict(
                zip(grp["unit"], grp[col], strict=False)
            )

    # =========================================================================
    # EXPERIMENT B: FROZEN-METHOD STRESS TESTS (1,620 Evaluations)
    # =========================================================================
    log("Executing Experiment B: Stress Tests (1,620 evaluations)...")
    stress_engine_seed_rows: list[dict[str, Any]] = []
    stress_sim_rows: list[dict[str, Any]] = []
    stress_interval_rows: list[dict[str, Any]] = []

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

    # Preprocessed clean test DataFrames per dataset
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

    stress_metric_store: dict[tuple[str, str, str, str, str], dict[int, float]] = {}

    for ds in CONFIRMATORY_DATASETS:
        df_trans = preprocessed_clean_by_ds[ds]
        clean_ds_subgroups = clean_subgroup_map[clean_subgroup_map["dataset"] == ds]

        for cond in ALL_STRESS_CONDITIONS:
            # We collect all evaluations for this (ds, cond) to compute subgroup metrics per method
            for rep_id in range(cond.replicates):
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
                        # Generate single point-prediction stream from checkpoint
                        df_pred_stressed = generate_predictions_for_cell(
                            windows=windows,
                            dataset=ds,
                            model_family=mf,
                            seed=seed,
                            base_dir=base,
                        )

                        # Reused point-prediction stream across all three methods
                        for m_id in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
                            cal_obj = frozen_calibrators[(ds, mf, seed, m_id)]
                            low, upp, fallback = cal_obj.predict_intervals(
                                predictions=df_pred_stressed["prediction"].to_numpy(),
                                regimes=df_pred_stressed["regime"].to_numpy(),
                                nominal_coverage=0.90,
                            )
                            df_pred_method = df_pred_stressed.copy()
                            df_pred_method["seed"] = seed
                            df_pred_method["replicate_id"] = rep_id
                            df_pred_method["lower"] = low
                            df_pred_method["upper"] = upp
                            df_pred_method["fallback_used"] = fallback

                            # Collect interval predictions
                            for r in df_pred_method.itertuples():
                                stress_interval_rows.append(
                                    {
                                        "dataset": ds,
                                        "model_family": mf,
                                        "method_id": m_id,
                                        "condition_id": cond.condition_id,
                                        "replicate_id": rep_id,
                                        "seed": seed,
                                        "unit": int(r.unit),
                                        "endpoint_cycle": int(r.endpoint_cycle),
                                        "prediction": float(r.prediction),
                                        "rul_true": float(r.rul_true),
                                        "lower": float(r.lower),
                                        "upper": float(r.upper),
                                        "regime": str(r.regime),
                                        "lifecycle_stage": str(r.lifecycle_stage),
                                        "fallback_used": bool(r.fallback_used),
                                    }
                                )

                            stress_cell_sim_rows: list[dict[str, Any]] = []
                            for unit in partition_engines_by_ds[ds]:
                                df_eng = df_pred_method[df_pred_method["unit"] == unit].sort_values(
                                    "endpoint_cycle"
                                )
                                cyc_arr = df_eng["endpoint_cycle"].to_numpy(dtype=int)
                                p_arr = df_eng["prediction"].to_numpy(dtype=float)
                                l_arr = df_eng["lower"].to_numpy(dtype=float)
                                u_arr = df_eng["upper"].to_numpy(dtype=float)
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
                                sim_rec = {
                                    "dataset": ds,
                                    "model_family": mf,
                                    "method_id": m_id,
                                    "condition_id": cond.condition_id,
                                    "replicate_id": rep_id,
                                    "seed": int(seed),
                                    "unit": int(unit),
                                    "terminal_event": sim_out.terminal_event,
                                    "intervention_cycle": sim_out.intervention_cycle,
                                    "failed": sim_out.failed,
                                    "pm_occurred": sim_out.pm_occurred,
                                    "wasted_rul": sim_out.wasted_rul,
                                    "total_cost": sim_out.total_cost,
                                }
                                stress_sim_rows.append(sim_rec)
                                stress_cell_sim_rows.append(sim_rec)

                            df_sim_method = pd.DataFrame(stress_cell_sim_rows)
                            eng_summary = compute_engine_summary_records(
                                df_pred_method, df_sim_method, nominal_coverage=0.90
                            )
                            eng_summary["dataset"] = ds
                            eng_summary["model_family"] = mf
                            eng_summary["seed"] = seed
                            eng_summary["replicate_id"] = rep_id
                            eng_summary["condition_id"] = cond.condition_id
                            eng_summary["condition_type"] = cond.condition_type
                            eng_summary["param_value"] = (
                                cond.param_value if cond.param_value is not None else 0.0
                            )
                            eng_summary["method_id"] = m_id
                            stress_engine_seed_rows.extend(eng_summary.to_dict(orient="records"))

    df_stress_engine_raw = pd.DataFrame(stress_engine_seed_rows)
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

    # Subgroup metrics for Experiment B (stress tests)
    log("Computing equal-engine subgroup metrics for stress tests...")
    df_stress_intervals = pd.DataFrame(stress_interval_rows)
    for (ds, mf, mid, cid), grp_eval in df_stress_intervals.groupby(
        ["dataset", "model_family", "method_id", "condition_id"]
    ):
        clean_ds_subgroups = clean_subgroup_map[clean_subgroup_map["dataset"] == ds]
        for fam_name in ("regime", "lifecycle_stage"):
            df_eng_sub, df_sub_sum = compute_subgroup_metrics_equal_engine(
                df_eval=grp_eval,
                clean_subgroup_df=clean_ds_subgroups,
                subgroup_family=fam_name,
                nominal_coverage=0.90,
            )
            for r_sub in df_eng_sub.itertuples():
                subgroup_engine_records.append(
                    {
                        "evaluation_type": "stress",
                        "dataset": ds,
                        "model_family": mf,
                        "variant_id": "",
                        "method_id": mid,
                        "condition_id": cid,
                        "subgroup_family": fam_name,
                        "subgroup": str(r_sub.subgroup),
                        "unit": int(r_sub.unit),
                        "n_endpoints": int(r_sub.n_endpoints),
                        "coverage": float(r_sub.coverage),
                        "lower_tail_miss": float(r_sub.lower_tail_miss),
                        "upper_tail_miss": float(r_sub.upper_tail_miss),
                    }
                )
            for r_sum in df_sub_sum.itertuples():
                subgroup_summary_records.append(
                    {
                        "evaluation_type": "stress",
                        "dataset": ds,
                        "model_family": mf,
                        "variant_id": "",
                        "method_id": mid,
                        "condition_id": cid,
                        "subgroup_family": fam_name,
                        "subgroup": str(r_sum.subgroup),
                        "n_endpoints": int(r_sum.n_endpoints),
                        "n_engines": int(r_sum.n_engines),
                        "is_eligible": bool(r_sum.is_eligible),
                        "coverage": float(r_sum.coverage),
                        "coverage_abs_error": float(r_sum.coverage_abs_error),
                        "lower_tail_miss": float(r_sum.lower_tail_miss),
                        "upper_tail_miss": float(r_sum.upper_tail_miss),
                    }
                )

    df_subgroup_engine = pd.DataFrame(subgroup_engine_records)
    df_subgroup_summary = pd.DataFrame(subgroup_summary_records)

    # =========================================================================
    # SUMMARY AGGREGATION AND BOOTSTRAP CONTRASTS
    # =========================================================================
    log("Computing summary metrics, paired contrasts, and bootstrap statistics...")
    # 1. Ablation Summary
    ablation_summary_rows: list[dict[str, Any]] = []
    for (ds, mf, vid, g, b, r, is_f), grp in df_ablation_engine.groupby(
        [
            "dataset",
            "model_family",
            "variant_id",
            "gamma",
            "beta_code",
            "routing",
            "is_full_method",
        ]
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
        [
            "dataset",
            "model_family",
            "method_id",
            "condition_id",
            "condition_type",
            "param_value",
        ]
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

    # 3. Paired Contrasts & Bootstrap Statistics
    paired_contrast_rows: list[dict[str, Any]] = []
    zero_diff_rows: list[dict[str, Any]] = []
    # Dict by dataset storing replicate contrast arrays of shape (10000,)
    bootstrap_statistics_by_ds: dict[str, dict[str, np.ndarray[Any, Any]]] = {
        ds: {} for ds in CONFIRMATORY_DATASETS
    }

    full_vid = "gamma2_betam1_regime"
    contrast_metrics = (
        "cost",
        "coverage",
        "coverage_abs_error",
        "width",
        "interval_score",
        "rmse",
        "failure_rate",
    )

    for ds in CONFIRMATORY_DATASETS:
        b_draws = bootstrap_draws_by_ds[ds]
        for mf in CONFIRMATORY_MODELS:
            # Seven non-trivial variant-minus-full contrasts
            for variant in ALL_EIGHT_ABLATION_VARIANTS:
                vid = variant.variant_id
                if vid == full_vid:
                    # Record as zero-difference sanity check
                    for col in contrast_metrics:
                        vals_full = ablation_metric_store[(ds, mf, full_vid, col)]
                        pt, lo, hi, reps = compute_paired_bootstrap_contrast(
                            vals_full, vals_full, b_draws
                        )
                        zero_diff_rows.append(
                            {
                                "comparison_type": "ablation_full_minus_full",
                                "dataset": ds,
                                "model_family": mf,
                                "variant_or_condition": vid,
                                "baseline_or_full": full_vid,
                                "metric": col,
                                "delta_point": pt,
                                "ci_95_low": lo,
                                "ci_95_high": hi,
                            }
                        )
                    continue

                for col in contrast_metrics:
                    vals_var = ablation_metric_store[(ds, mf, vid, col)]
                    vals_full = ablation_metric_store[(ds, mf, full_vid, col)]
                    pt, lo, hi, reps = compute_paired_bootstrap_contrast(
                        vals_var, vals_full, b_draws
                    )
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
                        }
                    )
                    stat_key = f"ablation_{ds}_{mf}_{vid}_minus_full_{col}"
                    bootstrap_statistics_by_ds[ds][stat_key] = reps

            # Stress contrasts: Stressed minus Clean
            for mid in ("global_hcp", "regime_hcp", "decision_aware_hcp"):
                for cond in ALL_STRESS_CONDITIONS:
                    cid = cond.condition_id
                    if cid == "clean":
                        for col in contrast_metrics:
                            vals_cln = stress_metric_store[(ds, mf, mid, "clean", col)]
                            pt, lo, hi, reps = compute_paired_bootstrap_contrast(
                                vals_cln, vals_cln, b_draws
                            )
                            zero_diff_rows.append(
                                {
                                    "comparison_type": "stress_clean_minus_clean",
                                    "dataset": ds,
                                    "model_family": mf,
                                    "variant_or_condition": f"{mid}:clean",
                                    "baseline_or_full": f"{mid}:clean",
                                    "metric": col,
                                    "delta_point": pt,
                                    "ci_95_low": lo,
                                    "ci_95_high": hi,
                                }
                            )
                        continue

                    for col in contrast_metrics:
                        vals_str = stress_metric_store[(ds, mf, mid, cid, col)]
                        vals_cln = stress_metric_store[(ds, mf, mid, "clean", col)]
                        pt, lo, hi, reps = compute_paired_bootstrap_contrast(
                            vals_str, vals_cln, b_draws
                        )
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
                            }
                        )
                        stat_key = f"stress_{ds}_{mf}_{mid}_{cid}_minus_clean_{col}"
                        bootstrap_statistics_by_ds[ds][stat_key] = reps

    df_paired_contrasts = pd.DataFrame(paired_contrast_rows)
    df_zero_diff = pd.DataFrame(zero_diff_rows)

    # 4. Factor Main Effects (On minus Off)
    factor_effect_rows: list[dict[str, Any]] = []
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
                for col in contrast_metrics:
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
                    pt, lo, hi, reps = compute_paired_bootstrap_contrast(
                        on_means, off_means, b_draws
                    )
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
                    stat_key = f"factor_{ds}_{mf}_{factor_name}_on_minus_off_{col}"
                    bootstrap_statistics_by_ds[ds][stat_key] = reps

    df_factor_effects = pd.DataFrame(factor_effect_rows)

    # Save bootstrap statistics for each dataset
    for ds in CONFIRMATORY_DATASETS:
        save_arrays: dict[str, Any] = {"draws": bootstrap_draws_by_ds[ds]}
        save_arrays.update(bootstrap_statistics_by_ds[ds])
        np.savez_compressed(
            out_dir / f"bootstrap_statistics_{ds}.npz",
            **save_arrays,
        )

    # =========================================================================
    # SAVE OUTPUT ARTIFACTS
    # =========================================================================
    log("Saving output artifacts...")

    # Engine-level metrics
    write_immutable_csv(out_dir / "ablation_engine_metrics.csv", df_ablation_engine)
    write_immutable_csv(out_dir / "stress_engine_metrics.csv", df_stress_engine)
    write_immutable_csv(out_dir / "ablation_engine_seed_metrics.csv", df_ablation_engine_raw)
    write_immutable_csv(out_dir / "stress_engine_seed_rep_metrics.csv", df_stress_engine_raw)

    # Summaries
    write_immutable_csv(out_dir / "ablation_summary.csv", df_ablation_summary)
    write_immutable_csv(out_dir / "stress_summary.csv", df_stress_summary)

    # Subgroups
    write_immutable_csv(out_dir / "subgroup_metrics.csv", df_subgroup_summary)
    write_immutable_csv(out_dir / "subgroup_engine_metrics.csv", df_subgroup_engine)

    # Contrasts and effects
    write_immutable_csv(out_dir / "paired_contrasts.csv", df_paired_contrasts)
    write_immutable_csv(out_dir / "factor_main_effects.csv", df_factor_effects)
    write_immutable_csv(out_dir / "zero_difference_checks.csv", df_zero_diff)

    # Simulation outcomes
    df_ablation_sim = pd.DataFrame(ablation_sim_rows)
    df_stress_sim = pd.DataFrame(stress_sim_rows)
    write_immutable_csv(out_dir / "ablation_simulation_outcomes.csv", df_ablation_sim)
    write_immutable_csv(out_dir / "stress_simulation_outcomes.csv", df_stress_sim)

    # Compressed per-cycle interval predictions
    log("Writing compressed interval prediction streams...")
    df_ablation_intervals = pd.DataFrame(ablation_interval_rows)
    buf_abl = io.BytesIO()
    with gzip.GzipFile(fileobj=buf_abl, mode="wb", mtime=0.0) as gz:
        df_ablation_intervals.to_csv(gz, index=False)
    (out_dir / "ablation_interval_predictions.csv.gz").write_bytes(buf_abl.getvalue())

    buf_str = io.BytesIO()
    with gzip.GzipFile(fileobj=buf_str, mode="wb", mtime=0.0) as gz:
        df_stress_intervals.to_csv(gz, index=False)
    (out_dir / "stress_interval_predictions.csv.gz").write_bytes(buf_str.getvalue())

    # Perturbation manifest
    perturbation_manifest = {
        "conditions": [c.__dict__ for c in ALL_STRESS_CONDITIONS],
        "sensor_columns": list(SENSOR_COLUMNS),
        "seed_sequence_formula": (
            "[2026, 8, dataset_number, engine_id, perturbation_family, replicate_id]"
        ),
        "total_stream_conditions": 18,
    }
    write_immutable_json(out_dir / "perturbation_manifest.json", perturbation_manifest)

    # Verify protected inputs post-execution
    log("Verifying protected inputs post-execution...")
    post_protected_hashes: dict[str, str] = {}
    for p in protected_paths:
        rel_posix = p.relative_to(base).as_posix()
        post_protected_hashes[rel_posix] = compute_sha256(p)

    if pre_protected_hashes != post_protected_hashes:
        raise RuntimeError("Protected inputs were altered during execution!")

    input_manifest = {
        "raw_source_hashes": raw_hashes,
        "clean_point_predictions_sha256": compute_sha256(clean_point_preds_p),
        "calibration_cache_dir": str(calibration_cache_dir),
        "pre_execution_protected_hashes": pre_protected_hashes,
        "post_execution_protected_hashes": post_protected_hashes,
    }
    write_immutable_json(out_dir / "input_manifest.json", input_manifest)

    # Build artifact hashes using explicit relative POSIX paths
    log("Computing artifact inventory hashes for execution manifest...")
    artifact_hashes: dict[str, str] = {}
    for p in sorted(out_dir.rglob("*")):
        if p.is_file() and p.name not in ("execution_manifest.json", "execution.log"):
            rel_posix = p.relative_to(out_dir).as_posix()
            artifact_hashes[rel_posix] = compute_sha256(p)

    end_time_utc = datetime.now(timezone.utc).isoformat()
    duration_sec = time.perf_counter() - execution_start_perf

    # Derived counts from observed records
    observed_ablation_cells = int(
        df_ablation_engine_raw[["dataset", "model_family", "variant_id", "seed"]]
        .drop_duplicates()
        .shape[0]
    )
    observed_stress_evals = int(
        df_stress_engine_raw[
            ["dataset", "model_family", "method_id", "condition_id", "replicate_id", "seed"]
        ]
        .drop_duplicates()
        .shape[0]
    )

    execution_manifest = {
        "protocol_version": "phase08-v1",
        "schema_version": "phase08-manifest-v2",
        "status": "EXPLORATORY_POST_CONFIRMATORY",
        "git_commit": git_sha,
        "git_dirty": git_dirty,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "start_time_utc": start_time_utc,
        "end_time_utc": end_time_utc,
        "duration_seconds": round(duration_sec, 2),
        "counts": {
            "ablation_configurations": observed_ablation_cells,
            "stress_evaluations": observed_stress_evals,
            "datasets": len(CONFIRMATORY_DATASETS),
            "models": len(CONFIRMATORY_MODELS),
            "seeds": len(CONFIRMATORY_SEEDS),
            "bootstrap_replicates": PHASE08_BOOTSTRAP_REPLICATES,
            "total_test_engines": sum(
                len(partition_engines_by_ds[ds]) for ds in CONFIRMATORY_DATASETS
            ),
        },
        "artifact_hashes": artifact_hashes,
    }
    write_immutable_json(out_dir / "execution_manifest.json", execution_manifest)

    log(f"Phase 8 execution completed in {duration_sec:.2f} seconds.")
    log(
        f"Evaluated {observed_ablation_cells} ablation cells and "
        f"{observed_stress_evals} stress cells."
    )
    (out_dir / "execution.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    return {
        "status": "SUCCESS",
        "output_dir": str(out_dir),
        "execution_manifest": execution_manifest,
    }
