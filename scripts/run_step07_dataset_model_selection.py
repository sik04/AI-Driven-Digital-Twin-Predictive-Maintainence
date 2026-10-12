"""C-MAPSS base predictor hyperparameter selection runner for FD001 and FD004.

Executes the frozen Step 7.3 / Step 7.4 / ADR-019 model-selection procedure:
- Confirms clean Git worktree and non-main branch.
- Verifies raw dataset, split manifest, and preprocessor hashes.
- Trains exactly 16 GBR candidates (8 configurations x seeds 2026, 2027).
- Trains exactly 8 LSTM candidates (4 configurations x seeds 2026, 2027).
- Generates 24 checkpoints, 24 prediction CSVs, and 24 run record JSONs.
- Builds experiments/model_selection/{DATASET}/gbr_selection.json and lstm_selection.json.
- Strictly excludes calibration and held-out test data.
"""

import argparse
import json
import platform
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
import torch

from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.pipeline import prepare_dataset_for_model_development
from intellitwin.models.artifacts import (
    save_prediction_artifact,
    save_run_record,
    save_selection_summary,
)
from intellitwin.models.gbr import GBRModel, get_gbr_grid
from intellitwin.models.lstm import (
    get_lstm_grid,
    save_lstm_checkpoint,
    train_lstm_candidate,
)
from intellitwin.models.metrics import ModelEvaluationMetrics, compute_model_metrics
from intellitwin.models.reproducibility import resolve_device
from intellitwin.models.selection import (
    SELECTION_SEEDS,
    CandidateEvaluationResult,
    evaluate_candidate,
    select_best_configuration,
)

SCHEMA_VERSION = "step07-selection-v1"

DATASET_CONFIGS = {
    "FD001": {
        "raw_path": Path("data/raw/cmapss/train_FD001.txt"),
        "raw_sha256": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
        "split_manifest_path": Path("data/splits/fd001_engine_split_seed_2026.json"),
        "split_manifest_sha256": "9b8a9c3a14e6f44f4f76f443ab974166511193476d3d5119f069918b31afaa56",
        "preprocessor_path": Path("experiments/preprocessing/FD001/preprocessor.json"),
        "preprocessor_sha256": "6f88491a46e2a0b5f8955df85a71e991f1cffc600c5e8becb713a1520b1e1c0a",
    },
    "FD002": {
        "raw_path": Path("data/raw/cmapss/train_FD002.txt"),
        "raw_sha256": "dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f",
        "split_manifest_path": Path("data/splits/fd002_engine_split_seed_2026.json"),
        "split_manifest_sha256": "57c815e4c97d9016bbfe9c91ab90738df0f3487910df889a0c631dde71894e41",
        "preprocessor_path": Path("experiments/preprocessing/FD002/preprocessor.json"),
        "preprocessor_sha256": "cef04b8dafc4c9f53aba7c6bcb0bc67fc981540abdafadc76fafa314684d856c",
    },
    "FD004": {
        "raw_path": Path("data/raw/cmapss/train_FD004.txt"),
        "raw_sha256": "27ef6160b6a1dcb2613a88de9c239f763b223f02cdc41dc5cdedc5dc189b6218",
        "split_manifest_path": Path("data/splits/fd004_engine_split_seed_2026.json"),
        "split_manifest_sha256": "7ed99876dd045c0a6e6dabb0c27e66b92b8232aa4221901ddf04981678601dc2",
        "preprocessor_path": Path("experiments/preprocessing/FD004/preprocessor.json"),
        "preprocessor_sha256": "fdfa4c0284c38554f8b8026c27c71f56ebd9c157a47f9acd2baf9ae34cbe0502",
    },
}


def _run_git_command(args: list[str]) -> str:
    res = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def check_git_status() -> tuple[str, bool]:
    """Verify clean Git worktree and return commit SHA and dirty flag."""
    branch = _run_git_command(["branch", "--show-current"])
    if branch == "main":
        raise RuntimeError("Model selection runner must not execute directly on main branch.")

    status = _run_git_command(["status", "--porcelain"])
    if status:
        raise RuntimeError(
            f"Git working tree is dirty! Commit all changes before running selection:\n{status}"
        )

    commit_sha = _run_git_command(["rev-parse", "HEAD"])
    return commit_sha, False


def run_dataset_model_selection(
    dataset_name: str,
    allow_dirty: bool = False,
    resume: bool = True,
) -> None:
    """Execute complete GBR and LSTM model selection for a given dataset."""
    if dataset_name not in DATASET_CONFIGS:
        raise ValueError(
            f"Unknown dataset: {dataset_name}. Expected one of {list(DATASET_CONFIGS.keys())}"
        )

    config = DATASET_CONFIGS[dataset_name]
    selection_base_dir = Path("experiments/model_selection") / dataset_name

    print("=" * 80)
    print(f"Starting Base Predictor Configuration Selection: {dataset_name}")
    print("=" * 80)

    # 1. Git provenance check
    if not allow_dirty:
        git_commit, git_dirty = check_git_status()
    else:
        try:
            git_commit = _run_git_command(["rev-parse", "HEAD"])
            git_dirty = bool(_run_git_command(["status", "--porcelain"]))
        except Exception:
            git_commit = "unknown"
            git_dirty = True
    print(f"Verified Git commit: {git_commit} (dirty: {git_dirty})")

    # 2. Verify file presence and hashes
    raw_path: Path = config["raw_path"]
    split_manifest_path: Path = config["split_manifest_path"]
    committed_preprocessor_path: Path = config["preprocessor_path"]

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    if not split_manifest_path.exists():
        raise FileNotFoundError(f"Split manifest not found: {split_manifest_path}")
    if not committed_preprocessor_path.exists():
        raise FileNotFoundError(f"Preprocessor not found: {committed_preprocessor_path}")

    raw_sha256 = compute_sha256(raw_path)
    manifest_sha256 = compute_sha256(split_manifest_path)
    preprocessor_sha256 = compute_sha256(committed_preprocessor_path)

    expected_raw_sha = config["raw_sha256"]
    expected_manifest_sha = config["split_manifest_sha256"]
    expected_preprocessor_sha = config["preprocessor_sha256"]

    if raw_sha256 != expected_raw_sha:
        raise ValueError(
            f"Raw hash mismatch for {dataset_name}: expected {expected_raw_sha}, got {raw_sha256}"
        )
    if manifest_sha256 != expected_manifest_sha:
        raise ValueError(
            f"Split manifest hash mismatch for {dataset_name}: "
            f"expected {expected_manifest_sha}, got {manifest_sha256}"
        )
    if preprocessor_sha256 != expected_preprocessor_sha:
        raise ValueError(
            f"Committed preprocessor hash mismatch for {dataset_name}: "
            f"expected {expected_preprocessor_sha}, got {preprocessor_sha256}"
        )
    print(f"Verified preprocessor SHA-256: {preprocessor_sha256}")

    # 3. Prepare dataset via Step 7.2 pipeline
    print(f"Preparing {dataset_name} dataset using frozen Step 7.2 pipeline...")
    dataset = prepare_dataset_for_model_development(
        dataset_name=dataset_name,
        raw_path=raw_path,
        split_manifest_path=split_manifest_path,
    )

    # Confirm strict boundaries
    if hasattr(dataset, "calibration_windows") or hasattr(dataset, "test_windows"):
        raise RuntimeError("Calibration or test windows leaked into PreparedDataset!")

    train_engine_count = dataset.provenance["train_engine_count"]
    val_engine_count = dataset.provenance["validation_engine_count"]
    train_window_count = dataset.provenance["train_window_count"]
    val_window_count = dataset.provenance["validation_window_count"]

    print(f"Train engines: {train_engine_count}, Val engines: {val_engine_count}")
    print(f"Train windows: {train_window_count}, Val windows: {val_window_count}")

    # Pre-extract numpy arrays
    X_train_gbr = dataset.train_windows.flatten_for_gbr()
    y_train = dataset.train_windows.rul_target
    train_weights = dataset.train_sample_weights

    X_val_gbr = dataset.validation_windows.flatten_for_gbr()
    rul_true_val = dataset.validation_windows.rul_true
    rul_target_val = dataset.validation_windows.rul_target
    val_engine_ids = dataset.validation_windows.engine_ids

    # Environment provenance
    device = resolve_device()
    device_str = str(device)
    python_ver = platform.python_version()
    numpy_ver = np.__version__
    pandas_ver = pd.__version__
    sklearn_ver = sklearn.__version__
    torch_ver = torch.__version__

    # -------------------------------------------------------------------------
    # 4. GBR Selection (16 runs)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"Executing GBR Model Selection for {dataset_name} (8 configs x 2 seeds = 16 runs)")
    print("-" * 80)

    gbr_runs_dir = selection_base_dir / "GBR" / "runs"
    gbr_preds_dir = selection_base_dir / "GBR" / "predictions"
    gbr_ckpts_dir = selection_base_dir / "GBR" / "checkpoints"

    gbr_grid = get_gbr_grid()
    gbr_candidate_results: list[CandidateEvaluationResult] = []

    for cfg in gbr_grid:
        seed_metrics_map: dict[int, ModelEvaluationMetrics] = {}
        for seed in SELECTION_SEEDS:
            run_id = f"{cfg.config_id}_seed{seed}"
            ckpt_path = gbr_ckpts_dir / f"{run_id}.pkl"
            pred_csv_path = gbr_preds_dir / f"{run_id}.csv"
            run_json_path = gbr_runs_dir / f"{run_id}.json"

            if resume and run_json_path.exists() and pred_csv_path.exists() and ckpt_path.exists():
                print(f"Loading cached GBR candidate: {run_id} ...", end=" ", flush=True)
                with open(run_json_path, encoding="utf-8") as f:
                    cached_rec = json.load(f)
                metrics = ModelEvaluationMetrics(
                    uncapped_rmse=cached_rec["validation_uncapped_rmse"],
                    uncapped_mae=cached_rec["validation_uncapped_mae"],
                    capped_rmse=cached_rec["validation_capped_rmse"],
                )
                seed_metrics_map[seed] = metrics
                print(f"cached | Val RMSE: {metrics.uncapped_rmse:.4f}")
                continue

            print(f"Running GBR candidate: {run_id} ...", end=" ", flush=True)

            model = GBRModel(hyperparameters=cfg, run_seed=seed)
            t0 = time.perf_counter()
            model.fit(X_train_gbr, y_train, sample_weight=train_weights)
            duration = time.perf_counter() - t0

            preds = model.predict(X_val_gbr)
            if not np.all(np.isfinite(preds)):
                raise ValueError(f"Non-finite prediction detected in GBR run {run_id}")

            metrics = compute_model_metrics(
                predictions=preds,
                rul_true=rul_true_val,
                rul_target=rul_target_val,
                engine_ids=val_engine_ids,
            )
            seed_metrics_map[seed] = metrics
            print(f"done ({duration:.1f}s) | Val RMSE: {metrics.uncapped_rmse:.4f}")

            # Persist checkpoint
            ckpt_path = gbr_ckpts_dir / f"{run_id}.pkl"
            ckpt_path.parent.mkdir(parents=True, exist_ok=True)
            model.save(str(ckpt_path))
            ckpt_sha256 = compute_sha256(ckpt_path)

            # Persist predictions CSV
            df_preds = pd.DataFrame(
                {
                    "unit": val_engine_ids,
                    "endpoint_cycle": dataset.validation_windows.endpoint_cycles,
                    "rul_true": rul_true_val,
                    "rul_target": rul_target_val,
                    "prediction": preds,
                    "regime": dataset.validation_windows.regimes,
                    "lifecycle_stage": dataset.validation_windows.lifecycle_stages,
                }
            )
            pred_csv_path = gbr_preds_dir / f"{run_id}.csv"
            pred_sha256 = save_prediction_artifact(df_preds, pred_csv_path)

            # Persist run record JSON
            run_record: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "dataset": dataset_name,
                "model_family": "GBR",
                "configuration_id": cfg.config_id,
                "run_seed": seed,
                "git_commit": git_commit,
                "git_dirty": git_dirty,
                "raw_dataset_sha256": raw_sha256,
                "split_manifest_sha256": manifest_sha256,
                "preprocessing_artifact_path": str(committed_preprocessor_path).replace("\\", "/"),
                "preprocessing_artifact_sha256": preprocessor_sha256,
                "train_engine_count": train_engine_count,
                "validation_engine_count": val_engine_count,
                "train_window_count": train_window_count,
                "validation_window_count": val_window_count,
                "training_target": "rul_target_cap_125",
                "selection_target": "uncapped_rul_true",
                "complete_hyperparameters": cfg.to_dict(),
                "device": device_str,
                "python_version": python_ver,
                "numpy_version": numpy_ver,
                "pandas_version": pandas_ver,
                "scikit_learn_version": sklearn_ver,
                "torch_version": torch_ver,
                "training_duration_seconds": duration,
                "best_epoch": None,
                "epochs_completed": cfg.max_iter,
                "validation_uncapped_rmse": metrics.uncapped_rmse,
                "validation_uncapped_mae": metrics.uncapped_mae,
                "validation_capped_rmse": metrics.capped_rmse,
                "prediction_artifact_path": str(pred_csv_path).replace("\\", "/"),
                "prediction_artifact_sha256": pred_sha256,
                "checkpoint_path": str(ckpt_path).replace("\\", "/"),
                "checkpoint_sha256": ckpt_sha256,
            }
            run_json_path = gbr_runs_dir / f"{run_id}.json"
            save_run_record(run_record, run_json_path)

        cand_eval = evaluate_candidate(
            config_id=cfg.config_id,
            hyperparameters=cfg.to_dict(),
            seed_metrics=seed_metrics_map,
        )
        gbr_candidate_results.append(cand_eval)

    gbr_outcome = select_best_configuration(gbr_candidate_results, model_family="GBR")
    print(f"\nSelected GBR Configuration for {dataset_name}: {gbr_outcome.selected_config_id}")
    print(f"Selection Score (Mean RMSE): {gbr_outcome.selection_score:.4f}")
    print(f"Worst-Seed RMSE: {gbr_outcome.selected_worst_seed_rmse:.4f}")

    # Build GBR selection summary JSON
    gbr_summary_candidates: list[dict[str, Any]] = []
    for cand in gbr_candidate_results:
        m2026 = cand.seed_metrics[2026]
        m2027 = cand.seed_metrics[2027]
        gbr_summary_candidates.append(
            {
                "configuration_id": cand.config_id,
                "hyperparameters": cand.hyperparameters,
                "seed_2026": asdict(m2026),
                "seed_2027": asdict(m2027),
                "mean_selection_score": cand.mean_selection_score,
                "worst_seed_rmse": cand.worst_seed_rmse,
            }
        )

    gbr_selection_summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "dataset": dataset_name,
        "model_family": "GBR",
        "selection_seeds": list(SELECTION_SEEDS),
        "selection_metric": "equal-engine-weighted uncapped-RUL RMSE",
        "training_target": "min(rul_true,125)",
        "calibration_data_used": False,
        "test_data_used": False,
        "preprocessing_artifact_sha256": preprocessor_sha256,
        "git_commit": git_commit,
        "selected_configuration_id": gbr_outcome.selected_config_id,
        "selected_configuration": gbr_outcome.selected_hyperparameters,
        "selection_score": gbr_outcome.selection_score,
        "selected_worst_seed_rmse": gbr_outcome.selected_worst_seed_rmse,
        "tie_detected": gbr_outcome.tie_detected,
        "tie_break_rule_used": gbr_outcome.tie_break_rule_used,
        "candidate_configurations": gbr_summary_candidates,
    }

    gbr_summary_path = selection_base_dir / "gbr_selection.json"
    save_selection_summary(gbr_selection_summary, gbr_summary_path)
    print(f"Persisted GBR selection summary: {gbr_summary_path}")

    # -------------------------------------------------------------------------
    # 5. LSTM Selection (8 runs)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"Executing LSTM Model Selection for {dataset_name} (4 configs x 2 seeds = 8 runs)")
    print("-" * 80)

    lstm_runs_dir = selection_base_dir / "LSTM" / "runs"
    lstm_preds_dir = selection_base_dir / "LSTM" / "predictions"
    lstm_ckpts_dir = selection_base_dir / "LSTM" / "checkpoints"

    lstm_grid = get_lstm_grid()
    lstm_candidate_results: list[CandidateEvaluationResult] = []

    X_train_lstm = dataset.train_windows.X_sequence
    X_val_lstm = dataset.validation_windows.X_sequence

    for cfg_lstm in lstm_grid:
        seed_metrics_map = {}
        for seed in SELECTION_SEEDS:
            run_id = f"{cfg_lstm.config_id}_seed{seed}"
            ckpt_path = lstm_ckpts_dir / f"{run_id}.pt"
            pred_csv_path = lstm_preds_dir / f"{run_id}.csv"
            run_json_path = lstm_runs_dir / f"{run_id}.json"

            if resume and run_json_path.exists() and pred_csv_path.exists() and ckpt_path.exists():
                print(f"Loading cached LSTM candidate: {run_id} ...", end=" ", flush=True)
                with open(run_json_path, encoding="utf-8") as f:
                    cached_rec = json.load(f)
                metrics = ModelEvaluationMetrics(
                    uncapped_rmse=cached_rec["validation_uncapped_rmse"],
                    uncapped_mae=cached_rec["validation_uncapped_mae"],
                    capped_rmse=cached_rec["validation_capped_rmse"],
                )
                seed_metrics_map[seed] = metrics
                print(f"cached | Val RMSE: {metrics.uncapped_rmse:.4f}")
                continue

            print(f"Running LSTM candidate: {run_id} ...", end=" ", flush=True)

            res = train_lstm_candidate(
                hyperparameters=cfg_lstm,
                run_seed=seed,
                X_train=X_train_lstm,
                y_train=y_train,
                train_weights=train_weights,
                X_val=X_val_lstm,
                rul_true_val=rul_true_val,
                rul_target_val=rul_target_val,
                val_engine_ids=val_engine_ids,
                device=device,
            )

            metrics = res.validation_metrics
            seed_metrics_map[seed] = metrics
            print(
                f"done ({res.training_duration_seconds:.1f}s, "
                f"best epoch {res.best_epoch}/{res.epochs_completed}) "
                f"| Val RMSE: {metrics.uncapped_rmse:.4f}"
            )

            # Persist checkpoint
            ckpt_path = lstm_ckpts_dir / f"{run_id}.pt"
            save_lstm_checkpoint(res, ckpt_path)
            ckpt_sha256 = compute_sha256(ckpt_path)

            # Persist predictions CSV
            df_preds = pd.DataFrame(
                {
                    "unit": val_engine_ids,
                    "endpoint_cycle": dataset.validation_windows.endpoint_cycles,
                    "rul_true": rul_true_val,
                    "rul_target": rul_target_val,
                    "prediction": res.validation_predictions,
                    "regime": dataset.validation_windows.regimes,
                    "lifecycle_stage": dataset.validation_windows.lifecycle_stages,
                }
            )
            pred_csv_path = lstm_preds_dir / f"{run_id}.csv"
            pred_sha256 = save_prediction_artifact(df_preds, pred_csv_path)

            # Persist run record JSON
            run_record = {
                "schema_version": SCHEMA_VERSION,
                "dataset": dataset_name,
                "model_family": "LSTM",
                "configuration_id": cfg_lstm.config_id,
                "run_seed": seed,
                "git_commit": git_commit,
                "git_dirty": git_dirty,
                "raw_dataset_sha256": raw_sha256,
                "split_manifest_sha256": manifest_sha256,
                "preprocessing_artifact_path": str(committed_preprocessor_path).replace("\\", "/"),
                "preprocessing_artifact_sha256": preprocessor_sha256,
                "train_engine_count": train_engine_count,
                "validation_engine_count": val_engine_count,
                "train_window_count": train_window_count,
                "validation_window_count": val_window_count,
                "training_target": "rul_target_cap_125",
                "selection_target": "uncapped_rul_true",
                "complete_hyperparameters": cfg_lstm.to_dict(),
                "device": device_str,
                "python_version": python_ver,
                "numpy_version": numpy_ver,
                "pandas_version": pandas_ver,
                "scikit_learn_version": sklearn_ver,
                "torch_version": torch_ver,
                "training_duration_seconds": res.training_duration_seconds,
                "best_epoch": res.best_epoch,
                "epochs_completed": res.epochs_completed,
                "validation_uncapped_rmse": metrics.uncapped_rmse,
                "validation_uncapped_mae": metrics.uncapped_mae,
                "validation_capped_rmse": metrics.capped_rmse,
                "prediction_artifact_path": str(pred_csv_path).replace("\\", "/"),
                "prediction_artifact_sha256": pred_sha256,
                "checkpoint_path": str(ckpt_path).replace("\\", "/"),
                "checkpoint_sha256": ckpt_sha256,
            }
            run_json_path = lstm_runs_dir / f"{run_id}.json"
            save_run_record(run_record, run_json_path)

        cand_eval = evaluate_candidate(
            config_id=cfg_lstm.config_id,
            hyperparameters=cfg_lstm.to_dict(),
            seed_metrics=seed_metrics_map,
        )
        lstm_candidate_results.append(cand_eval)

    lstm_outcome = select_best_configuration(lstm_candidate_results, model_family="LSTM")
    print(f"\nSelected LSTM Configuration for {dataset_name}: {lstm_outcome.selected_config_id}")
    print(f"Selection Score (Mean RMSE): {lstm_outcome.selection_score:.4f}")
    print(f"Worst-Seed RMSE: {lstm_outcome.selected_worst_seed_rmse:.4f}")

    # Build LSTM selection summary JSON
    lstm_summary_candidates: list[dict[str, Any]] = []
    for cand in lstm_candidate_results:
        m2026 = cand.seed_metrics[2026]
        m2027 = cand.seed_metrics[2027]
        lstm_summary_candidates.append(
            {
                "configuration_id": cand.config_id,
                "hyperparameters": cand.hyperparameters,
                "seed_2026": asdict(m2026),
                "seed_2027": asdict(m2027),
                "mean_selection_score": cand.mean_selection_score,
                "worst_seed_rmse": cand.worst_seed_rmse,
            }
        )

    lstm_selection_summary = {
        "schema_version": SCHEMA_VERSION,
        "dataset": dataset_name,
        "model_family": "LSTM",
        "selection_seeds": list(SELECTION_SEEDS),
        "selection_metric": "equal-engine-weighted uncapped-RUL RMSE",
        "training_target": "min(rul_true,125)",
        "calibration_data_used": False,
        "test_data_used": False,
        "preprocessing_artifact_sha256": preprocessor_sha256,
        "git_commit": git_commit,
        "selected_configuration_id": lstm_outcome.selected_config_id,
        "selected_configuration": lstm_outcome.selected_hyperparameters,
        "selection_score": lstm_outcome.selection_score,
        "selected_worst_seed_rmse": lstm_outcome.selected_worst_seed_rmse,
        "tie_detected": lstm_outcome.tie_detected,
        "tie_break_rule_used": lstm_outcome.tie_break_rule_used,
        "candidate_configurations": lstm_summary_candidates,
    }

    lstm_summary_path = selection_base_dir / "lstm_selection.json"
    save_selection_summary(lstm_selection_summary, lstm_summary_path)
    print(f"Persisted LSTM selection summary: {lstm_summary_path}")

    print("\n" + "=" * 80)
    print(f"Model Selection for {dataset_name} Complete!")
    print(
        f"Selected GBR:  {gbr_outcome.selected_config_id} "
        f"(Score: {gbr_outcome.selection_score:.4f})"
    )
    print(
        f"Selected LSTM: {lstm_outcome.selected_config_id} "
        f"(Score: {lstm_outcome.selection_score:.4f})"
    )
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Base predictor selection runner for FD001 and FD004"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        choices=["FD001", "FD004", "ALL"],
        help="Dataset to run model selection on (FD001, FD004, or ALL)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow running with uncommitted changes (git_dirty recorded)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not resume/skip already completed runs",
    )
    args = parser.parse_args()

    datasets = ["FD001", "FD004"] if args.dataset == "ALL" else [args.dataset]
    for ds in datasets:
        run_dataset_model_selection(
            ds,
            allow_dirty=args.allow_dirty,
            resume=not args.no_resume,
        )


if __name__ == "__main__":
    main()
