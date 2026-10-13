"""Step 8: Development Execution and Candidate Selection Script.

Protocol: step08-v1
Scope: Validation-only leave-one-engine-out candidate evaluation and selection freeze gate.
Boundary: strictly uses validation partition. Zero calibration or held-out test data accessed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.calibration_pipeline import prepare_partition_windows
from intellitwin.decision.policies import load_primary_reference_cost
from intellitwin.models.registry import (
    EXPECTED_DATASETS,
    EXPECTED_FAMILIES,
    EXPECTED_SEEDS,
    load_frozen_base_model,
)
from intellitwin.uncertainty.artifacts import (
    POINT_PREDICTION_COLUMNS,
    write_atomic_csv,
    write_atomic_json,
)
from intellitwin.uncertainty.schema import (
    FREEZE_SCHEMA_VERSION,
    PROTOCOL_VERSION,
    SELECTION_SCHEMA_VERSION,
)
from intellitwin.uncertainty.selection import (
    run_leave_one_engine_out_evaluation,
    select_winning_candidate,
)


def get_git_info() -> tuple[str, bool]:
    """Retrieve git HEAD SHA and dirty status."""
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        status = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8").strip()
        dirty = len(status) > 0
        return sha, dirty
    except Exception:
        return "unknown", False


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 8: Development Candidate Selection")
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
        help="Base output directory for Step 8 artifacts",
    )
    args = parser.parse_args()

    start_sha, start_dirty = get_git_info()
    exec_time = datetime.now(timezone.utc).isoformat()

    print("=" * 80)
    print("Step 8: Decision-Aware Conformal Calibration — Development Candidate Selection")
    print(f"Protocol: {PROTOCOL_VERSION}")
    print(f"Starting Commit: {start_sha} (dirty: {start_dirty})")
    print("=" * 80)

    print("\n--- Running Step 7 Prediction Reproduction Audit ---")
    audit_cmd = [
        sys.executable,
        "scripts/audit_step07_base_models.py",
        "--reproduce-predictions",
        "--raw-data-dir",
        args.raw_data_dir,
    ]
    subprocess.check_call(audit_cmd)

    cfg_path = Path(args.config_path)
    if not cfg_path.exists():
        print(f"FATAL: Config file missing: {cfg_path}")
        sys.exit(1)
    config_hash = compute_sha256(cfg_path)

    out_base = Path(args.output_dir)
    val_point_pred_base = out_base / "point_predictions" / "validation"
    selection_base = out_base / "selection"
    selection_base.mkdir(parents=True, exist_ok=True)

    cost_config = load_primary_reference_cost()

    # Model registry and predictor hashes
    reg_path = Path("experiments/base_models/model_registry.json")
    if not reg_path.exists():
        print(f"FATAL: Model registry missing: {reg_path}")
        sys.exit(1)
    registry_hash = compute_sha256(reg_path)

    selected_cells_summary: dict[str, Any] = {}
    selection_record_hashes: dict[str, str] = {}
    val_cache_hashes: dict[str, str] = {}

    for ds in EXPECTED_DATASETS:
        # Load validation windows once per dataset
        print(f"\n--- Preparing validation windows for {ds} ---")
        val_windows = prepare_partition_windows(
            dataset_name=ds, partition_name="validation", raw_data_dir=args.raw_data_dir
        )
        val_flat = val_windows.flatten_for_gbr()
        val_seq = val_windows.X_sequence

        for fam in EXPECTED_FAMILIES:
            cell_key = f"{ds}_{fam}"
            print(f"\nEvaluating Cell: {cell_key}")

            # Collect predictions across all 5 seeds
            cell_preds_dfs: list[pd.DataFrame] = []

            for seed in EXPECTED_SEEDS:
                model_id = f"{ds}_{fam}_seed{seed}"
                cache_dir = val_point_pred_base / ds / fam
                cache_p = cache_dir / f"seed_{seed}.csv"

                if cache_p.exists():
                    df_seed_pred = pd.read_csv(cache_p)
                else:
                    frozen_model = load_frozen_base_model(dataset=ds, model_family=fam, seed=seed)
                    X_input = val_flat if fam == "GBR" else val_seq
                    preds = frozen_model.predict(X_input)

                    df_seed_pred = pd.DataFrame(
                        {
                            "unit": val_windows.engine_ids,
                            "endpoint_cycle": val_windows.endpoint_cycles,
                            "rul_true": val_windows.rul_true,
                            "rul_target": val_windows.rul_target,
                            "prediction": preds,
                            "regime": val_windows.regimes,
                            "lifecycle_stage": val_windows.lifecycle_stages,
                        }
                    ).sort_values(["unit", "endpoint_cycle"])

                    write_atomic_csv(cache_p, df_seed_pred[list(POINT_PREDICTION_COLUMNS)])

                val_cache_hashes[model_id] = compute_sha256(cache_p)
                df_with_seed = df_seed_pred.copy()
                df_with_seed["seed"] = seed
                cell_preds_dfs.append(df_with_seed)

            df_cell_preds = pd.concat(cell_preds_dfs, ignore_index=True)

            # Run leave-one-engine-out evaluation
            print(f"Running leave-one-engine-out evaluation across 5 seeds for {cell_key}...")
            aggs, es_records, reg_records, fold_ths = run_leave_one_engine_out_evaluation(
                df_val_preds=df_cell_preds,
                cost_config=cost_config,
            )

            # Candidate selection & tie breaking
            winning_cand, sel_status, tie_log = select_winning_candidate(aggs)
            print(
                f"Selected Winner for {cell_key}: {winning_cand.candidate_id} "
                f"(Status: {sel_status})"
            )

            # Save cell selection artifacts
            cell_sel_dir = selection_base / ds / fam
            cell_sel_dir.mkdir(parents=True, exist_ok=True)

            # 1. Candidate summary CSV
            cand_sum_rows: list[dict[str, Any]] = []
            for cid, res in aggs.items():
                cand_sum_rows.append(
                    {
                        "candidate_id": cid,
                        "marginal_picp": res.marginal_picp,
                        "mpiw": res.mpiw,
                        "interval_score": res.interval_score,
                        "mean_cost": res.mean_cost,
                        "failure_rate": res.failure_rate,
                        "total_failures": res.total_failures,
                        "pm_rate": res.pm_rate,
                        "total_pms": res.total_pms,
                        "mean_wasted_rul": res.mean_wasted_rul,
                        "pm_wasted_rul_mean": res.pm_wasted_rul_mean
                        if res.pm_wasted_rul_mean is not None
                        else "",
                        "is_feasible": res.is_feasible,
                        "feasibility_reasons": "; ".join(res.feasibility_reasons),
                    }
                )
            df_cand_sum = pd.DataFrame(cand_sum_rows).sort_values("candidate_id")
            write_atomic_csv(cell_sel_dir / "candidate_summary.csv", df_cand_sum)

            # 2. Engine seed results CSV
            df_es = pd.DataFrame(es_records).sort_values(["candidate_id", "seed", "unit"])
            write_atomic_csv(cell_sel_dir / "engine_seed_results.csv", df_es)

            # 3. Regime results CSV
            df_reg = (
                pd.DataFrame(reg_records).sort_values(["candidate_id", "regime"])
                if reg_records
                else pd.DataFrame(
                    columns=["candidate_id", "regime", "contributing_engines", "regime_picp"]
                )
            )
            write_atomic_csv(cell_sel_dir / "regime_results.csv", df_reg)

            # 4. Fold thresholds JSON
            write_atomic_json(cell_sel_dir / "fold_thresholds.json", fold_ths)

            # 5. Cell selection JSON
            cell_selection_data: dict[str, Any] = {
                "schema_version": SELECTION_SCHEMA_VERSION,
                "protocol_version": PROTOCOL_VERSION,
                "dataset": ds,
                "model_family": fam,
                "selected_candidate_id": winning_cand.candidate_id,
                "candidate_parameters": {
                    "gamma": winning_cand.gamma,
                    "beta_code": winning_cand.beta_code,
                    "beta": winning_cand.beta,
                },
                "selection_status": sel_status,
                "tie_breaking_log": tie_log,
                "winning_metrics": {
                    "marginal_picp": aggs[winning_cand.candidate_id].marginal_picp,
                    "regime_picp": aggs[winning_cand.candidate_id].regime_picp,
                    "mpiw": aggs[winning_cand.candidate_id].mpiw,
                    "interval_score": aggs[winning_cand.candidate_id].interval_score,
                    "mean_cost": aggs[winning_cand.candidate_id].mean_cost,
                    "failure_rate": aggs[winning_cand.candidate_id].failure_rate,
                    "total_failures": aggs[winning_cand.candidate_id].total_failures,
                },
                "eval_timestamp_utc": exec_time,
                "git_commit": start_sha,
                "git_dirty": start_dirty,
            }
            sel_json_path = cell_sel_dir / "selection.json"
            write_atomic_json(sel_json_path, cell_selection_data)
            selection_record_hashes[cell_key] = compute_sha256(sel_json_path)

            selected_cells_summary[cell_key] = {
                "selected_candidate_id": winning_cand.candidate_id,
                "gamma": winning_cand.gamma,
                "beta_code": winning_cand.beta_code,
                "beta": winning_cand.beta,
                "selection_status": sel_status,
                "selection_json_sha256": selection_record_hashes[cell_key],
            }

    # Consolidated selection freeze manifest
    freeze_manifest: dict[str, Any] = {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "freeze_timestamp_utc": exec_time,
        "declaration": (
            "Selection was performed strictly using validation data and frozen base predictors."
        ),
        "git_commit": start_sha,
        "git_dirty": start_dirty,
        "config_sha256": config_hash,
        "model_registry_sha256": registry_hash,
        "selected_cells": selected_cells_summary,
        "selection_record_hashes": selection_record_hashes,
        "validation_prediction_cache_hashes": val_cache_hashes,
    }

    freeze_path = selection_base / "selection_freeze.json"
    write_atomic_json(freeze_path, freeze_manifest)
    print(f"\nWrote selection freeze manifest to: {freeze_path}")
    print("=" * 80)
    print("DEVELOPMENT SELECTION COMPLETE — ALL 6 CELLS FROZEN")
    print("MANDATORY NEXT STEP: Commit selection artifacts to Git before final calibration.")
    print("=" * 80)


if __name__ == "__main__":
    main()
