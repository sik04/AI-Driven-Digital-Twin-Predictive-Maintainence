"""Step 8: Final Hierarchical Conformal Calibration and Validation Diagnostics Script.

Protocol: step08-v1
Scope: Fits all 90 model-method calibrator bundles on the reserved calibration partition
       and computes post-selection development diagnostics on validation engines.
Requirement: Selection freeze manifest must be committed and verified prior to execution.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.calibration_pipeline import prepare_partition_windows
from intellitwin.data.schema import LIFECYCLE_STAGES
from intellitwin.models.registry import (
    COMMITTED_PREPROCESSOR_HASHES,
    COMMITTED_SPLIT_HASHES,
    EXPECTED_DATASETS,
    EXPECTED_FAMILIES,
    EXPECTED_SEEDS,
    load_frozen_base_model,
)
from intellitwin.provenance import get_git_info
from intellitwin.uncertainty.artifacts import (
    INTERVAL_PREDICTION_COLUMNS,
    POINT_PREDICTION_COLUMNS,
    serialize_calibrator_artifact,
    to_repo_relative_path_posix,
    write_atomic_csv,
    write_atomic_json,
)
from intellitwin.uncertainty.calibration import fit_calibrator_bundle
from intellitwin.uncertainty.metrics import compute_engine_weighted_interval_metrics
from intellitwin.uncertainty.schema import (
    METHOD_DECISION_AWARE,
    NOMINAL_COVERAGES,
    PROTOCOL_VERSION,
    SUPPORTED_METHODS,
    CandidateConfig,
)


def verify_selection_freeze_committed(selection_freeze_path: Path) -> str:
    """Verify that selection_freeze.json exists and is committed in Git."""
    if not selection_freeze_path.exists():
        raise FileNotFoundError(f"Selection freeze manifest missing at {selection_freeze_path}")

    # Check git status for uncommitted changes to selection_freeze.json
    try:
        rel_path = selection_freeze_path.as_posix()
        status_out = (
            subprocess.check_output(["git", "status", "--porcelain", "--", rel_path])
            .decode("utf-8")
            .strip()
        )
        if status_out:
            raise RuntimeError(
                f"Selection freeze manifest {rel_path} has uncommitted changes in Git: "
                f"{status_out}. Commit the selection freeze before running final calibration!"
            )

        # Get commit SHA containing the freeze manifest
        commit_sha = (
            subprocess.check_output(["git", "log", "-1", "--format=%H", "--", rel_path])
            .decode("utf-8")
            .strip()
        )
        if not commit_sha:
            raise RuntimeError(
                f"Selection freeze manifest {rel_path} is untracked or has no git history."
            )
        return commit_sha
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Git verification failed: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 8: Final Hierarchical Conformal Calibration")
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default="data/raw/cmapss",
        help="Directory containing raw C-MAPSS training text files",
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default="research/research_design/step08_calibration_config.json",
        help="Path to Step 8 calibration config JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/calibration",
        help="Base directory for calibration artifacts",
    )
    args = parser.parse_args()

    start_sha, start_dirty = get_git_info()
    exec_time = datetime.now(timezone.utc).isoformat()

    print("=" * 80)
    print("Step 8: Decision-Aware Conformal Calibration — Final Calibration Execution")
    print(f"Protocol: {PROTOCOL_VERSION}")
    print(f"Starting Commit: {start_sha} (dirty: {start_dirty})")
    print("=" * 80)

    out_base = Path(args.output_dir)
    selection_freeze_path = out_base / "selection" / "selection_freeze.json"

    # Enforce Selection-Freeze Gate
    freeze_commit_sha = verify_selection_freeze_committed(selection_freeze_path)
    freeze_sha256 = compute_sha256(selection_freeze_path)
    print(
        f"Verified committed selection freeze "
        f"(Commit: {freeze_commit_sha[:8]}, Hash: {freeze_sha256[:12]}...)"
    )

    with open(selection_freeze_path, encoding="utf-8") as f:
        freeze_data = json.load(f)

    # Verify all 6 selection records exist and match freeze hashes
    selected_candidates: dict[tuple[str, str], CandidateConfig] = {}
    for ds in EXPECTED_DATASETS:
        for fam in EXPECTED_FAMILIES:
            cell_key = f"{ds}_{fam}"
            sel_p = out_base / "selection" / ds / fam / "selection.json"
            if not sel_p.exists():
                raise FileNotFoundError(f"Selection record missing for {cell_key}: {sel_p}")
            actual_sel_hash = compute_sha256(sel_p)
            expected_sel_hash = freeze_data["selection_record_hashes"][cell_key]
            if actual_sel_hash != expected_sel_hash:
                raise ValueError(
                    f"Selection record hash mismatch for {cell_key}: "
                    f"{actual_sel_hash} != {expected_sel_hash}"
                )
            with open(sel_p, encoding="utf-8") as f:
                sel_data = json.load(f)
            cid = sel_data["selected_candidate_id"]
            selected_candidates[(ds, fam)] = CandidateConfig.from_id(cid)

    # Output directories
    cal_point_pred_base = out_base / "point_predictions" / "calibration"
    val_point_pred_base = out_base / "point_predictions" / "validation"
    fitted_base = out_base / "fitted"
    val_diag_base = out_base / "validation"

    reg_path = Path("experiments/base_models/model_registry.json")
    with open(reg_path, encoding="utf-8") as f:
        registry_data = json.load(f)
    registry_list = (
        registry_data if isinstance(registry_data, list) else registry_data.get("entries", [])
    )
    reg_entries = {e["model_id"]: e for e in registry_list}

    source_hashes = {
        "calibration_py": compute_sha256(Path("src/intellitwin/uncertainty/calibration.py")),
        "quantiles_py": compute_sha256(Path("src/intellitwin/uncertainty/quantiles.py")),
        "scores_py": compute_sha256(Path("src/intellitwin/uncertainty/scores.py")),
        "metrics_py": compute_sha256(Path("src/intellitwin/uncertainty/metrics.py")),
        "runner_py": compute_sha256(Path("scripts/run_step08_final_calibration.py")),
    }

    calibration_registry_entries: dict[str, Any] = {}
    validation_summary_rows: list[dict[str, Any]] = []

    # Iterate over 3 datasets x 2 families x 5 seeds
    for ds in EXPECTED_DATASETS:
        print("\n=======================================================")
        print(f"Dataset: {ds}")
        print("=======================================================")

        # Prepare calibration and validation windows from raw data
        cal_windows = prepare_partition_windows(
            dataset_name=ds, partition_name="calibration", raw_data_dir=args.raw_data_dir
        )

        cal_flat = cal_windows.flatten_for_gbr()
        cal_seq = cal_windows.X_sequence

        raw_f = Path(args.raw_data_dir) / f"train_{ds}.txt"
        raw_hash = compute_sha256(raw_f)
        split_hash = COMMITTED_SPLIT_HASHES[ds]
        prep_hash = COMMITTED_PREPROCESSOR_HASHES[ds]

        for fam in EXPECTED_FAMILIES:
            winning_cand = selected_candidates[(ds, fam)]

            for seed in EXPECTED_SEEDS:
                model_id = f"{ds}_{fam}_seed{seed}"
                print(
                    f"Fitting calibrators for {model_id} "
                    f"(Proposed candidate: {winning_cand.candidate_id})..."
                )

                frozen_model = load_frozen_base_model(dataset=ds, model_family=fam, seed=seed)
                ckpt_hash = reg_entries[model_id]["checkpoint_sha256"]

                # Generate or load calibration predictions cache
                cal_cache_p = cal_point_pred_base / ds / fam / f"seed_{seed}.csv"
                if cal_cache_p.exists():
                    df_cal_pred = pd.read_csv(cal_cache_p)
                else:
                    X_cal = cal_flat if fam == "GBR" else cal_seq
                    cal_preds = frozen_model.predict(X_cal)
                    df_cal_pred = pd.DataFrame(
                        {
                            "unit": cal_windows.engine_ids,
                            "endpoint_cycle": cal_windows.endpoint_cycles,
                            "rul_true": cal_windows.rul_true,
                            "rul_target": cal_windows.rul_target,
                            "prediction": cal_preds,
                            "regime": cal_windows.regimes,
                            "lifecycle_stage": cal_windows.lifecycle_stages,
                        }
                    ).sort_values(["unit", "endpoint_cycle"])
                    write_atomic_csv(cal_cache_p, df_cal_pred[list(POINT_PREDICTION_COLUMNS)])

                cal_cache_hash = compute_sha256(cal_cache_p)

                # Validation predictions cache
                val_cache_p = val_point_pred_base / ds / fam / f"seed_{seed}.csv"
                df_val_pred = pd.read_csv(val_cache_p)

                # Fit all three methods on calibration partition
                for method_id in SUPPORTED_METHODS:
                    bundle_id = f"{ds}_{fam}_seed{seed}_{method_id}"

                    cand_for_fit = winning_cand if method_id == METHOD_DECISION_AWARE else None

                    calibrator = fit_calibrator_bundle(
                        method_id=method_id,
                        predictions=df_cal_pred["prediction"].to_numpy(),
                        labels=df_cal_pred["rul_true"].to_numpy(),
                        regimes=df_cal_pred["regime"].to_numpy(),
                        engine_ids=df_cal_pred["unit"].to_numpy(),
                        endpoint_cycles=df_cal_pred["endpoint_cycle"].to_numpy(),
                        dataset_name=ds,
                        model_family=fam,
                        model_seed=seed,
                        candidate=cand_for_fit,
                    )

                    # Serialize calibrator artifact
                    cal_art = serialize_calibrator_artifact(
                        calibrator=calibrator,
                        checkpoint_hash=ckpt_hash,
                        preprocessor_hash=prep_hash,
                        split_manifest_hash=split_hash,
                        raw_dataset_hash=raw_hash,
                        calibration_pred_cache_hash=cal_cache_hash,
                        selection_freeze_hash=freeze_sha256,
                        git_commit=start_sha,
                        source_hashes=source_hashes,
                    )
                    fitted_dir = fitted_base / ds / fam / f"seed_{seed}" / method_id
                    fitted_dir.mkdir(parents=True, exist_ok=True)
                    art_path = fitted_dir / "calibrator.json"
                    write_atomic_json(art_path, cal_art)
                    art_hash = compute_sha256(art_path)

                    # Predict intervals on validation partition for all 3 coverages
                    val_int_rows: list[dict[str, Any]] = []
                    diag_metrics_by_cov: dict[str, Any] = {}

                    val_preds = df_val_pred["prediction"].to_numpy()
                    val_labels = df_val_pred["rul_true"].to_numpy()
                    val_regimes = df_val_pred["regime"].to_numpy()
                    val_eids = df_val_pred["unit"].to_numpy()
                    val_cycles = df_val_pred["endpoint_cycle"].to_numpy()
                    val_stages = df_val_pred["lifecycle_stage"].to_numpy()

                    for cov in NOMINAL_COVERAGES:
                        lower, upper, fallback_used = calibrator.predict_intervals(
                            predictions=val_preds,
                            regimes=val_regimes,
                            nominal_coverage=cov,
                        )

                        for u, ep, rt, p, reg, stg, low, up, fb in zip(
                            val_eids,
                            val_cycles,
                            val_labels,
                            val_preds,
                            val_regimes,
                            val_stages,
                            lower,
                            upper,
                            fallback_used,
                            strict=True,
                        ):
                            val_int_rows.append(
                                {
                                    "unit": int(u),
                                    "endpoint_cycle": int(ep),
                                    "rul_true": float(rt),
                                    "prediction": float(p),
                                    "regime": str(reg),
                                    "lifecycle_stage": str(stg),
                                    "nominal_coverage": float(cov),
                                    "lower": float(low),
                                    "upper": float(up),
                                    "fallback_used": bool(fb),
                                }
                            )

                        # Compute diagnostic metrics (DEVELOPMENT DIAGNOSTICS ONLY)
                        cov_metrics = compute_engine_weighted_interval_metrics(
                            engine_ids=val_eids,
                            endpoint_cycles=val_cycles,
                            labels=val_labels,
                            lower=lower,
                            upper=upper,
                            regimes=val_regimes,
                            alpha=1.0 - cov,
                        )

                        # Stage-level diagnostics
                        stage_picp_dict: dict[str, float] = {}
                        obs_covered = (val_labels >= lower) & (val_labels <= upper)
                        for stg in LIFECYCLE_STAGES:
                            stg_mask = val_stages == stg
                            if np.any(stg_mask):
                                stg_eids = val_eids[stg_mask]
                                stg_cov = obs_covered[stg_mask]
                                eng_stg_covs = [
                                    float(np.mean(stg_cov[stg_eids == e]))
                                    for e in sorted(set(stg_eids))
                                ]
                                stage_picp_dict[stg] = float(np.mean(eng_stg_covs))

                        cov_key = f"coverage_{int(cov * 100)}"
                        diag_metrics_by_cov[cov_key] = {
                            "nominal_coverage": cov,
                            "marginal_picp": cov_metrics["marginal_picp"],
                            "mpiw": cov_metrics["mpiw"],
                            "interval_score": cov_metrics["interval_score"],
                            "lower_miss_rate": cov_metrics["lower_miss_rate"],
                            "upper_miss_rate": cov_metrics["upper_miss_rate"],
                            "regime_picp": cov_metrics.get("regime_picp", {}),
                            "lifecycle_stage_picp": stage_picp_dict,
                            "fallback_fraction": float(np.mean(fallback_used)),
                        }

                        # Add row to validation summary table
                        validation_summary_rows.append(
                            {
                                "dataset": ds,
                                "model_family": fam,
                                "seed": seed,
                                "method_id": method_id,
                                "selected_candidate_id": winning_cand.candidate_id
                                if method_id == METHOD_DECISION_AWARE
                                else "",
                                "nominal_coverage": cov,
                                "marginal_picp": cov_metrics["marginal_picp"],
                                "mpiw": cov_metrics["mpiw"],
                                "interval_score": cov_metrics["interval_score"],
                                "lower_miss_rate": cov_metrics["lower_miss_rate"],
                                "upper_miss_rate": cov_metrics["upper_miss_rate"],
                                "fallback_fraction": float(np.mean(fallback_used)),
                            }
                        )

                    # Save validation interval predictions CSV
                    df_val_intervals = pd.DataFrame(val_int_rows).sort_values(
                        ["nominal_coverage", "unit", "endpoint_cycle"]
                    )
                    val_out_dir = val_diag_base / ds / fam / f"seed_{seed}" / method_id
                    val_out_dir.mkdir(parents=True, exist_ok=True)
                    write_atomic_csv(
                        val_out_dir / "interval_predictions.csv",
                        df_val_intervals[list(INTERVAL_PREDICTION_COLUMNS)],
                    )

                    # Save validation metrics JSON
                    metrics_payload: dict[str, Any] = {
                        "schema_version": "step08-validation-metrics-v1",
                        "protocol_version": PROTOCOL_VERSION,
                        "notice": (
                            "POST-SELECTION DEVELOPMENT DIAGNOSTICS ONLY "
                            "— NOT CONFIRMATORY EVIDENCE"
                        ),
                        "dataset": ds,
                        "model_family": fam,
                        "seed": seed,
                        "method_id": method_id,
                        "selected_candidate_id": winning_cand.candidate_id
                        if method_id == METHOD_DECISION_AWARE
                        else None,
                        "eval_timestamp_utc": exec_time,
                        "metrics": diag_metrics_by_cov,
                    }
                    write_atomic_json(val_out_dir / "metrics.json", metrics_payload)

                    # Add to calibration registry
                    calibration_registry_entries[bundle_id] = {
                        "bundle_id": bundle_id,
                        "dataset": ds,
                        "model_family": fam,
                        "seed": seed,
                        "method_id": method_id,
                        "selected_candidate_id": winning_cand.candidate_id
                        if method_id == METHOD_DECISION_AWARE
                        else None,
                        "calibrator_artifact_path": to_repo_relative_path_posix(
                            art_path, base_dir=Path(".").resolve()
                        ),
                        "artifact_sha256": art_hash,
                        "checkpoint_sha256": ckpt_hash,
                        "preprocessor_sha256": prep_hash,
                        "split_manifest_sha256": split_hash,
                        "coverage_levels": list(NOMINAL_COVERAGES),
                    }

    # 1. Write authoritative calibration_registry.json (exactly 90 unique entries)
    if len(calibration_registry_entries) != 90:
        raise ValueError(
            f"Expected 90 calibration registry entries, got {len(calibration_registry_entries)}"
        )

    registry_artifact: dict[str, Any] = {
        "schema_version": "step08-calibration-registry-v1",
        "protocol_version": PROTOCOL_VERSION,
        "registry_timestamp_utc": exec_time,
        "total_calibrator_bundles": len(calibration_registry_entries),
        "total_coverage_configurations": len(calibration_registry_entries) * len(NOMINAL_COVERAGES),
        "entries": calibration_registry_entries,
    }
    cal_reg_path = out_base / "calibration_registry.json"
    write_atomic_json(cal_reg_path, registry_artifact)
    print(f"\nWrote calibration registry (90 entries) to: {cal_reg_path}")

    # 2. Write validation_summary.csv (270 rows)
    df_val_sum = pd.DataFrame(validation_summary_rows).sort_values(
        ["dataset", "model_family", "seed", "method_id", "nominal_coverage"]
    )
    val_sum_path = out_base / "validation_summary.csv"
    write_atomic_csv(val_sum_path, df_val_sum)
    print(f"Wrote consolidated validation summary ({len(df_val_sum)} rows) to: {val_sum_path}")

    # 3. Write execution_manifest.json
    manifest_data: dict[str, Any] = {
        "schema_version": "step08-execution-manifest-v1",
        "protocol_version": PROTOCOL_VERSION,
        "execution_timestamp_utc": exec_time,
        "git_commit": start_sha,
        "git_dirty": start_dirty,
        "freeze_commit": freeze_commit_sha,
        "selection_freeze_sha256": freeze_sha256,
        "total_calibrator_bundles": 90,
        "total_coverage_configurations": 270,
        "source_hashes": source_hashes,
        "calibration_registry_sha256": compute_sha256(cal_reg_path),
        "validation_summary_sha256": compute_sha256(val_sum_path),
    }
    man_path = out_base / "execution_manifest.json"
    write_atomic_json(man_path, manifest_data)
    print(f"Wrote execution manifest to: {man_path}")

    print("\n" + "=" * 80)
    print("STEP 8 FINAL CALIBRATION COMPLETE — 90 BUNDLES / 270 COVERAGE CONFIGURATIONS FITTED")
    print("=" * 80)


if __name__ == "__main__":
    main()
