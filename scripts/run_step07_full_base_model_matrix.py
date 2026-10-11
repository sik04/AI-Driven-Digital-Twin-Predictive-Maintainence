"""Step 7.4: Official 30-Model Base Predictor Production Matrix Runner.

Trains the complete multi-dataset (FD001, FD002, FD004) / five-seed (2026-2030)
base-model matrix:
- 3 datasets x 2 model families (GBR, LSTM) x 5 seeds = 30 official final models.
- Loads dataset-specific winning configurations from Step 7.3/7.4 selection:
    FD001 GBR & LSTM: from experiments/model_selection/FD001/
    FD002 GBR & LSTM: frozen winners (gbr_lr010_leaf31_l2_0, lstm_h64_lr0010)
    FD004 GBR & LSTM: from experiments/model_selection/FD004/
- Official seeds: 2026, 2027, 2028, 2029, 2030.
- Persists under experiments/base_models/{DATASET}/{FAMILY}/seed_{SEED}/:
    checkpoint, metadata.json, metrics.json, validation_predictions.csv
- Persists 6 five-seed summary files:
    experiments/base_models/{DATASET}/{FAMILY}/summary.json
- Validates that all 30 checkpoints reload on CPU and reproduce saved predictions.
- Strictly keeps calibration and held-out test data untouched.
"""

import argparse
import json
import platform
import subprocess
import time
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
)
from intellitwin.models.gbr import GBRHyperparameters, GBRModel
from intellitwin.models.lstm import (
    LSTMHyperparameters,
    load_lstm_checkpoint,
    save_lstm_checkpoint,
    train_lstm_candidate,
)
from intellitwin.models.metrics import ModelEvaluationMetrics, compute_model_metrics
from intellitwin.models.reproducibility import resolve_device

METADATA_SCHEMA_VERSION = "step07-base-model-v1"
SUMMARY_SCHEMA_VERSION = "step07-base-model-summary-v1"

OFFICIAL_SEEDS: tuple[int, ...] = (2026, 2027, 2028, 2029, 2030)
DATASETS: tuple[str, ...] = ("FD001", "FD002", "FD004")
MODEL_FAMILIES: tuple[str, ...] = ("GBR", "LSTM")

DATASET_SPECS = {
    "FD001": {
        "raw_path": Path("data/raw/cmapss/train_FD001.txt"),
        "raw_sha256": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
        "split_manifest_path": Path("data/splits/fd001_engine_split_seed_2026.json"),
        "split_manifest_sha256": "9b8a9c3a14e6f44f4f76f443ab974166511193476d3d5119f069918b31afaa56",
        "preprocessor_path": Path("experiments/preprocessing/FD001/preprocessor.json"),
        "preprocessor_sha256": "6f88491a46e2a0b5f8955df85a71e991f1cffc600c5e8becb713a1520b1e1c0a",
        "gbr_selection_path": Path("experiments/model_selection/FD001/gbr_selection.json"),
        "lstm_selection_path": Path("experiments/model_selection/FD001/lstm_selection.json"),
    },
    "FD002": {
        "raw_path": Path("data/raw/cmapss/train_FD002.txt"),
        "raw_sha256": "dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f",
        "split_manifest_path": Path("data/splits/fd002_engine_split_seed_2026.json"),
        "split_manifest_sha256": "57c815e4c97d9016bbfe9c91ab90738df0f3487910df889a0c631dde71894e41",
        "preprocessor_path": Path("experiments/preprocessing/FD002/preprocessor.json"),
        "preprocessor_sha256": "cef04b8dafc4c9f53aba7c6bcb0bc67fc981540abdafadc76fafa314684d856c",
        "gbr_selection_path": Path("experiments/model_selection/FD002/gbr_selection.json"),
        "lstm_selection_path": Path("experiments/model_selection/FD002/lstm_selection.json"),
    },
    "FD004": {
        "raw_path": Path("data/raw/cmapss/train_FD004.txt"),
        "raw_sha256": "27ef6160b6a1dcb2613a88de9c239f763b223f02cdc41dc5cdedc5dc189b6218",
        "split_manifest_path": Path("data/splits/fd004_engine_split_seed_2026.json"),
        "split_manifest_sha256": "7ed99876dd045c0a6e6dabb0c27e66b92b8232aa4221901ddf04981678601dc2",
        "preprocessor_path": Path("experiments/preprocessing/FD004/preprocessor.json"),
        "preprocessor_sha256": "fdfa4c0284c38554f8b8026c27c71f56ebd9c157a47f9acd2baf9ae34cbe0502",
        "gbr_selection_path": Path("experiments/model_selection/FD004/gbr_selection.json"),
        "lstm_selection_path": Path("experiments/model_selection/FD004/lstm_selection.json"),
    },
}

BASE_MODELS_ROOT = Path("experiments/base_models")


def _run_git_command(args: list[str]) -> str:
    res = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def check_git_status() -> tuple[str, bool]:
    """Verify Git commit and status."""
    branch = _run_git_command(["branch", "--show-current"])
    if branch == "main":
        raise RuntimeError("Production model runner must not execute directly on main branch.")

    status = _run_git_command(["status", "--porcelain"])
    dirty = bool(status)
    commit_sha = _run_git_command(["rev-parse", "HEAD"])
    return commit_sha, dirty


def load_winning_gbr_configuration(dataset: str) -> GBRHyperparameters:
    """Load winning GBR configuration for dataset."""
    spec = DATASET_SPECS[dataset]
    sel_path: Path = spec["gbr_selection_path"]
    if not sel_path.exists():
        raise FileNotFoundError(f"GBR selection summary not found: {sel_path}")

    with open(sel_path, encoding="utf-8") as f:
        data = json.load(f)

    cfg_dict = data["selected_configuration"]
    if dataset == "FD002" and cfg_dict["config_id"] != "gbr_lr010_leaf31_l2_0":
        raise ValueError(
            f"FD002 GBR winner changed! Expected gbr_lr010_leaf31_l2_0, got {cfg_dict['config_id']}"
        )

    return GBRHyperparameters(
        config_id=cfg_dict["config_id"],
        learning_rate=cfg_dict["learning_rate"],
        max_leaf_nodes=cfg_dict["max_leaf_nodes"],
        l2_regularization=cfg_dict["l2_regularization"],
        loss=cfg_dict.get("loss", "squared_error"),
        early_stopping=cfg_dict.get("early_stopping", False),
        validation_fraction=cfg_dict.get("validation_fraction", None),
        min_samples_leaf=cfg_dict.get("min_samples_leaf", 20),
        max_bins=cfg_dict.get("max_bins", 255),
        max_features=cfg_dict.get("max_features", 1.0),
        categorical_features=cfg_dict.get("categorical_features", None),
        warm_start=cfg_dict.get("warm_start", False),
        max_iter=cfg_dict.get("max_iter", 300),
    )


def load_winning_lstm_configuration(dataset: str) -> LSTMHyperparameters:
    """Load winning LSTM configuration for dataset."""
    spec = DATASET_SPECS[dataset]
    sel_path: Path = spec["lstm_selection_path"]
    if not sel_path.exists():
        raise FileNotFoundError(f"LSTM selection summary not found: {sel_path}")

    with open(sel_path, encoding="utf-8") as f:
        data = json.load(f)

    cfg_dict = data["selected_configuration"]
    if dataset == "FD002" and cfg_dict["config_id"] != "lstm_h64_lr0010":
        raise ValueError(
            f"FD002 LSTM winner changed! Expected lstm_h64_lr0010, got {cfg_dict['config_id']}"
        )

    return LSTMHyperparameters(
        config_id=cfg_dict["config_id"],
        hidden_size=cfg_dict["hidden_size"],
        learning_rate=cfg_dict["learning_rate"],
        batch_size=cfg_dict.get("batch_size", 256),
        weight_decay=cfg_dict.get("weight_decay", 1e-4),
        gradient_clip_norm=cfg_dict.get("gradient_clip_norm", 1.0),
        max_epochs=cfg_dict.get("max_epochs", 100),
        early_stopping_patience=cfg_dict.get("early_stopping_patience", 10),
        early_stopping_min_delta=cfg_dict.get("early_stopping_min_delta", 0.01),
        num_layers=cfg_dict.get("num_layers", 1),
        bidirectional=cfg_dict.get("bidirectional", False),
        dropout=cfg_dict.get("dropout", 0.0),
    )


def train_production_matrix(
    target_datasets: list[str] | None = None,
    allow_dirty: bool = False,
) -> None:
    """Train all 30 production models across datasets and seeds."""
    datasets_to_run = target_datasets or list(DATASETS)

    print("=" * 80)
    print("Step 7.4: Official 30-Model Base Predictor Production Matrix Training")
    print(f"Datasets: {datasets_to_run}")
    print(f"Seeds: {list(OFFICIAL_SEEDS)}")
    print("=" * 80)

    # 1. Provenance check
    git_commit, git_dirty = check_git_status()
    if git_dirty and not allow_dirty:
        raise RuntimeError("Git working tree is dirty! Commit changes or pass --allow-dirty.")
    print(f"Git commit: {git_commit} (dirty: {git_dirty})")

    # 2. System info
    device = resolve_device()
    device_str = str(device)
    python_ver = platform.python_version()
    numpy_ver = np.__version__
    pandas_ver = pd.__version__
    sklearn_ver = sklearn.__version__
    torch_ver = torch.__version__
    os_name = f"{platform.system()} {platform.release()}"
    cpu_info = platform.processor() or platform.machine()
    has_cuda = torch.cuda.is_available()

    total_models_trained = 0
    all_models_verification: list[dict[str, Any]] = []

    for dataset_name in datasets_to_run:
        spec = DATASET_SPECS[dataset_name]
        raw_path: Path = spec["raw_path"]
        split_manifest_path: Path = spec["split_manifest_path"]
        preprocessor_path: Path = spec["preprocessor_path"]

        # Verify hashes
        raw_sha = compute_sha256(raw_path)
        manifest_sha = compute_sha256(split_manifest_path)
        preprocessor_sha = compute_sha256(preprocessor_path)

        if raw_sha != spec["raw_sha256"]:
            raise ValueError(f"Raw hash mismatch for {dataset_name}")
        if manifest_sha != spec["split_manifest_sha256"]:
            raise ValueError(f"Split manifest hash mismatch for {dataset_name}")
        if preprocessor_sha != spec["preprocessor_sha256"]:
            raise ValueError(f"Preprocessor hash mismatch for {dataset_name}")

        print(f"\n[{dataset_name}] Loading dataset and verifying pipeline...")
        dataset = prepare_dataset_for_model_development(
            dataset_name=dataset_name,
            raw_path=raw_path,
            split_manifest_path=split_manifest_path,
        )

        # Confirm strict boundaries
        if hasattr(dataset, "calibration_windows") or hasattr(dataset, "test_windows"):
            raise RuntimeError(f"Calibration or test windows leaked into {dataset_name}!")

        train_engine_count = dataset.provenance["train_engine_count"]
        val_engine_count = dataset.provenance["validation_engine_count"]
        train_window_count = dataset.provenance["train_window_count"]
        val_window_count = dataset.provenance["validation_window_count"]

        # Pre-extract windows
        X_train_gbr = dataset.train_windows.flatten_for_gbr()
        y_train = dataset.train_windows.rul_target
        train_weights = dataset.train_sample_weights

        X_val_gbr = dataset.validation_windows.flatten_for_gbr()
        rul_true_val = dataset.validation_windows.rul_true
        rul_target_val = dataset.validation_windows.rul_target
        val_engine_ids = dataset.validation_windows.engine_ids

        X_train_lstm = dataset.train_windows.X_sequence
        X_val_lstm = dataset.validation_windows.X_sequence

        # Load winning configs
        gbr_cfg = load_winning_gbr_configuration(dataset_name)
        lstm_cfg = load_winning_lstm_configuration(dataset_name)
        print(f"[{dataset_name}] Winning GBR:  {gbr_cfg.config_id}")
        print(f"[{dataset_name}] Winning LSTM: {lstm_cfg.config_id}")

        # ---------------------------------------------------------------------
        # Train GBR (5 seeds)
        # ---------------------------------------------------------------------
        gbr_seed_metrics: dict[int, ModelEvaluationMetrics] = {}
        gbr_seed_durations: dict[int, float] = {}

        for seed in OFFICIAL_SEEDS:
            seed_dir = BASE_MODELS_ROOT / dataset_name / "GBR" / f"seed_{seed}"
            seed_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Training {dataset_name} GBR seed {seed} ...", end=" ", flush=True)

            model = GBRModel(hyperparameters=gbr_cfg, run_seed=seed)
            t0 = time.perf_counter()
            model.fit(X_train_gbr, y_train, sample_weight=train_weights)
            duration = time.perf_counter() - t0
            gbr_seed_durations[seed] = duration

            preds = model.predict(X_val_gbr)
            if not np.all(np.isfinite(preds)):
                raise ValueError(f"Non-finite prediction in {dataset_name} GBR seed {seed}")

            metrics = compute_model_metrics(
                predictions=preds,
                rul_true=rul_true_val,
                rul_target=rul_target_val,
                engine_ids=val_engine_ids,
            )
            gbr_seed_metrics[seed] = metrics
            print(f"done ({duration:.1f}s) | Val RMSE: {metrics.uncapped_rmse:.4f}")

            # 1. Save checkpoint
            ckpt_path = seed_dir / "checkpoint"
            model.save(str(ckpt_path))
            ckpt_sha = compute_sha256(ckpt_path)

            # 2. Save validation predictions CSV
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
            # Ensure sorted by unit asc, endpoint_cycle asc
            df_preds = df_preds.sort_values(
                by=["unit", "endpoint_cycle"],
                ascending=[True, True],
            ).reset_index(drop=True)

            pred_path = seed_dir / "validation_predictions.csv"
            pred_sha = save_prediction_artifact(df_preds, pred_path)

            # 3. Save metrics JSON
            metrics_dict = {
                "uncapped_rmse": metrics.uncapped_rmse,
                "uncapped_mae": metrics.uncapped_mae,
                "capped_rmse": metrics.capped_rmse,
            }
            metrics_path = seed_dir / "metrics.json"
            metrics_path.write_text(json.dumps(metrics_dict, indent=2), encoding="utf-8")

            # 4. Save metadata JSON
            metadata_dict: dict[str, Any] = {
                "schema_version": METADATA_SCHEMA_VERSION,
                "dataset": dataset_name,
                "model_family": "GBR",
                "configuration_id": gbr_cfg.config_id,
                "run_seed": seed,
                "git_commit": git_commit,
                "git_dirty": git_dirty,
                "raw_dataset_sha256": raw_sha,
                "split_manifest_sha256": manifest_sha,
                "preprocessing_artifact_sha256": preprocessor_sha,
                "train_engine_count": train_engine_count,
                "validation_engine_count": val_engine_count,
                "train_window_count": train_window_count,
                "validation_window_count": val_window_count,
                "training_target": "rul_target_cap_125",
                "validation_target": "uncapped_rul_true",
                "complete_hyperparameters": gbr_cfg.to_dict(),
                "python_version": python_ver,
                "numpy_version": numpy_ver,
                "pandas_version": pandas_ver,
                "scikit_learn_version": sklearn_ver,
                "torch_version": torch_ver,
                "operating_system": os_name,
                "cpu": cpu_info,
                "gpu_or_cuda_if_present": has_cuda,
                "actual_device_used": device_str,
                "training_duration_seconds": duration,
                "best_epoch": None,
                "epochs_completed": gbr_cfg.max_iter,
                "validation_uncapped_rmse": metrics.uncapped_rmse,
                "validation_uncapped_mae": metrics.uncapped_mae,
                "validation_capped_rmse": metrics.capped_rmse,
                "checkpoint_sha256": ckpt_sha,
                "validation_prediction_sha256": pred_sha,
            }
            meta_path = seed_dir / "metadata.json"
            meta_path.write_text(json.dumps(metadata_dict, indent=2), encoding="utf-8")

            # Verify reload
            reloaded_gbr = GBRModel.load(str(ckpt_path))
            reloaded_preds = reloaded_gbr.predict(X_val_gbr)
            if not np.allclose(reloaded_preds, preds, atol=1e-5):
                raise RuntimeError(
                    f"Checkpoint reload prediction mismatch for {dataset_name} GBR seed {seed}"
                )

            total_models_trained += 1
            all_models_verification.append(
                {
                    "dataset": dataset_name,
                    "family": "GBR",
                    "seed": seed,
                    "ckpt_sha": ckpt_sha,
                    "reload_verified": True,
                }
            )

        # Build GBR summary.json
        gbr_rmses = [gbr_seed_metrics[s].uncapped_rmse for s in OFFICIAL_SEEDS]
        gbr_maes = [gbr_seed_metrics[s].uncapped_mae for s in OFFICIAL_SEEDS]
        gbr_capped = [gbr_seed_metrics[s].capped_rmse for s in OFFICIAL_SEEDS]
        gbr_durs = [gbr_seed_durations[s] for s in OFFICIAL_SEEDS]

        gbr_summary = {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "dataset": dataset_name,
            "model_family": "GBR",
            "selected_configuration_id": gbr_cfg.config_id,
            "seeds": list(OFFICIAL_SEEDS),
            "validation_uncapped_rmse": {
                "mean": float(np.mean(gbr_rmses)),
                "std": float(np.std(gbr_rmses)),
                "min": float(np.min(gbr_rmses)),
                "max": float(np.max(gbr_rmses)),
            },
            "validation_uncapped_mae": {
                "mean": float(np.mean(gbr_maes)),
                "std": float(np.std(gbr_maes)),
                "min": float(np.min(gbr_maes)),
                "max": float(np.max(gbr_maes)),
            },
            "validation_capped_rmse": {
                "mean": float(np.mean(gbr_capped)),
                "std": float(np.std(gbr_capped)),
                "min": float(np.min(gbr_capped)),
                "max": float(np.max(gbr_capped)),
            },
            "training_duration_seconds": {
                "mean": float(np.mean(gbr_durs)),
                "std": float(np.std(gbr_durs)),
            },
            "note": (
                "Development/validation results only. Not confirmatory test evidence. "
                "Seed variability does not constitute a confidence interval."
            ),
        }
        gbr_summary_path = BASE_MODELS_ROOT / dataset_name / "GBR" / "summary.json"
        gbr_summary_path.write_text(json.dumps(gbr_summary, indent=2), encoding="utf-8")
        print(f"  Persisted summary: {gbr_summary_path}")

        # ---------------------------------------------------------------------
        # Train LSTM (5 seeds)
        # ---------------------------------------------------------------------
        lstm_seed_metrics: dict[int, ModelEvaluationMetrics] = {}
        lstm_seed_durations: dict[int, float] = {}

        for seed in OFFICIAL_SEEDS:
            seed_dir = BASE_MODELS_ROOT / dataset_name / "LSTM" / f"seed_{seed}"
            seed_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Training {dataset_name} LSTM seed {seed} ...", end=" ", flush=True)

            res = train_lstm_candidate(
                hyperparameters=lstm_cfg,
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
            lstm_seed_metrics[seed] = metrics
            lstm_seed_durations[seed] = res.training_duration_seconds
            print(
                f"done ({res.training_duration_seconds:.1f}s, "
                f"best epoch {res.best_epoch}/{res.epochs_completed}) "
                f"| Val RMSE: {metrics.uncapped_rmse:.4f}"
            )

            # 1. Save checkpoint
            ckpt_path = seed_dir / "checkpoint"
            save_lstm_checkpoint(res, ckpt_path)
            ckpt_sha = compute_sha256(ckpt_path)

            # 2. Save validation predictions CSV
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
            df_preds = df_preds.sort_values(
                by=["unit", "endpoint_cycle"],
                ascending=[True, True],
            ).reset_index(drop=True)

            pred_path = seed_dir / "validation_predictions.csv"
            pred_sha = save_prediction_artifact(df_preds, pred_path)

            # 3. Save metrics JSON
            metrics_dict = {
                "uncapped_rmse": metrics.uncapped_rmse,
                "uncapped_mae": metrics.uncapped_mae,
                "capped_rmse": metrics.capped_rmse,
            }
            metrics_path = seed_dir / "metrics.json"
            metrics_path.write_text(json.dumps(metrics_dict, indent=2), encoding="utf-8")

            # 4. Save metadata JSON
            metadata_dict = {
                "schema_version": METADATA_SCHEMA_VERSION,
                "dataset": dataset_name,
                "model_family": "LSTM",
                "configuration_id": lstm_cfg.config_id,
                "run_seed": seed,
                "git_commit": git_commit,
                "git_dirty": git_dirty,
                "raw_dataset_sha256": raw_sha,
                "split_manifest_sha256": manifest_sha,
                "preprocessing_artifact_sha256": preprocessor_sha,
                "train_engine_count": train_engine_count,
                "validation_engine_count": val_engine_count,
                "train_window_count": train_window_count,
                "validation_window_count": val_window_count,
                "training_target": "rul_target_cap_125",
                "validation_target": "uncapped_rul_true",
                "complete_hyperparameters": lstm_cfg.to_dict(),
                "python_version": python_ver,
                "numpy_version": numpy_ver,
                "pandas_version": pandas_ver,
                "scikit_learn_version": sklearn_ver,
                "torch_version": torch_ver,
                "operating_system": os_name,
                "cpu": cpu_info,
                "gpu_or_cuda_if_present": has_cuda,
                "actual_device_used": device_str,
                "training_duration_seconds": res.training_duration_seconds,
                "best_epoch": res.best_epoch,
                "epochs_completed": res.epochs_completed,
                "validation_uncapped_rmse": metrics.uncapped_rmse,
                "validation_uncapped_mae": metrics.uncapped_mae,
                "validation_capped_rmse": metrics.capped_rmse,
                "checkpoint_sha256": ckpt_sha,
                "validation_prediction_sha256": pred_sha,
            }
            meta_path = seed_dir / "metadata.json"
            meta_path.write_text(json.dumps(metadata_dict, indent=2), encoding="utf-8")

            # Verify reload
            reloaded_model, _ = load_lstm_checkpoint(ckpt_path, device="cpu")
            reloaded_model.eval()
            with torch.no_grad():
                tensor_val = torch.from_numpy(X_val_lstm).float()
                raw_reloaded = reloaded_model(tensor_val).cpu().numpy()
                reloaded_preds = np.maximum(0.0, raw_reloaded)

            if not np.allclose(reloaded_preds, res.validation_predictions, atol=1e-5):
                raise RuntimeError(
                    f"Checkpoint reload prediction mismatch for {dataset_name} LSTM seed {seed}"
                )

            total_models_trained += 1
            all_models_verification.append(
                {
                    "dataset": dataset_name,
                    "family": "LSTM",
                    "seed": seed,
                    "ckpt_sha": ckpt_sha,
                    "reload_verified": True,
                }
            )

        # Build LSTM summary.json
        lstm_rmses = [lstm_seed_metrics[s].uncapped_rmse for s in OFFICIAL_SEEDS]
        lstm_maes = [lstm_seed_metrics[s].uncapped_mae for s in OFFICIAL_SEEDS]
        lstm_capped = [lstm_seed_metrics[s].capped_rmse for s in OFFICIAL_SEEDS]
        lstm_durs = [lstm_seed_durations[s] for s in OFFICIAL_SEEDS]

        lstm_summary = {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "dataset": dataset_name,
            "model_family": "LSTM",
            "selected_configuration_id": lstm_cfg.config_id,
            "seeds": list(OFFICIAL_SEEDS),
            "validation_uncapped_rmse": {
                "mean": float(np.mean(lstm_rmses)),
                "std": float(np.std(lstm_rmses)),
                "min": float(np.min(lstm_rmses)),
                "max": float(np.max(lstm_rmses)),
            },
            "validation_uncapped_mae": {
                "mean": float(np.mean(lstm_maes)),
                "std": float(np.std(lstm_maes)),
                "min": float(np.min(lstm_maes)),
                "max": float(np.max(lstm_maes)),
            },
            "validation_capped_rmse": {
                "mean": float(np.mean(lstm_capped)),
                "std": float(np.std(lstm_capped)),
                "min": float(np.min(lstm_capped)),
                "max": float(np.max(lstm_capped)),
            },
            "training_duration_seconds": {
                "mean": float(np.mean(lstm_durs)),
                "std": float(np.std(lstm_durs)),
            },
            "note": (
                "Development/validation results only. Not confirmatory test evidence. "
                "Seed variability does not constitute a confidence interval."
            ),
        }
        lstm_summary_path = BASE_MODELS_ROOT / dataset_name / "LSTM" / "summary.json"
        lstm_summary_path.write_text(json.dumps(lstm_summary, indent=2), encoding="utf-8")
        print(f"  Persisted summary: {lstm_summary_path}")

    print("\n" + "=" * 80)
    print(f"Production Matrix Training Complete! Total models trained: {total_models_trained}")
    verified_count = sum(1 for m in all_models_verification if m["reload_verified"])
    print(f"Reload verification: {verified_count}/{total_models_trained} passed.")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Official 30-Model Base Predictor Production Matrix Runner"
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=["FD001", "FD002", "FD004"],
        default=list(DATASETS),
        help="Datasets to train (default: all three)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow running with uncommitted changes",
    )
    args = parser.parse_args()

    train_production_matrix(target_datasets=args.datasets, allow_dirty=args.allow_dirty)


if __name__ == "__main__":
    main()
