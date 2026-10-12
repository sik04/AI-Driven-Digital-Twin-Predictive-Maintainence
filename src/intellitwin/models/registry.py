"""Base predictor registry, verification, and loading API.

Provides:
- Authoritative 30-model registry schema and construction.
- Strict audit asserting all 30 base predictors meet ADR-019 / Step 7.4-7.5 criteria:
    * Datasets: FD001, FD002, FD004
    * Families: GBR, LSTM
    * Seeds: 2026, 2027, 2028, 2029, 2030
    * Exactly 30 unique cells
    * Configuration freeze (same configuration across all 5 seeds for each dataset/family)
    * Preprocessing freeze (all models reference committed preprocessor SHA)
    * Split freeze (all models reference committed split manifest SHA)
    * Complete validation prediction endpoints (cycles 30 through T for each engine)
    * Non-negative prediction post-processing (prediction >= 0.0)
    * Checkpoint loadability and numerical reproduction on CPU
    * Absence of calibration or held-out test artifacts in Step 7 base models
- `load_frozen_base_model`: High-level stable API to load verified frozen base models.
- Explicit prediction-reproduction audit mode (`reproduce_predictions=True`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from intellitwin.data.artifacts import compute_sha256, load_preprocessor_artifact
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.preprocessing import FittedPreprocessor
from intellitwin.data.schema import EXPECTED_ENGINE_COUNTS
from intellitwin.data.splits import load_split_manifest, select_partition
from intellitwin.data.windowing import construct_windows
from intellitwin.models.gbr import GBRModel
from intellitwin.models.lstm import load_lstm_checkpoint
from intellitwin.models.metrics import compute_model_metrics

EXPECTED_DATASETS: tuple[str, ...] = ("FD001", "FD002", "FD004")
EXPECTED_FAMILIES: tuple[str, ...] = ("GBR", "LSTM")
EXPECTED_SEEDS: tuple[int, ...] = (2026, 2027, 2028, 2029, 2030)
EXPECTED_TOTAL_MODELS: int = 30

COMMITTED_PREPROCESSOR_HASHES = {
    "FD001": "6f88491a46e2a0b5f8955df85a71e991f1cffc600c5e8becb713a1520b1e1c0a",
    "FD002": "cef04b8dafc4c9f53aba7c6bcb0bc67fc981540abdafadc76fafa314684d856c",
    "FD004": "fdfa4c0284c38554f8b8026c27c71f56ebd9c157a47f9acd2baf9ae34cbe0502",
}

COMMITTED_SPLIT_HASHES = {
    "FD001": "9b8a9c3a14e6f44f4f76f443ab974166511193476d3d5119f069918b31afaa56",
    "FD002": "57c815e4c97d9016bbfe9c91ab90738df0f3487910df889a0c631dde71894e41",
    "FD004": "7ed99876dd045c0a6e6dabb0c27e66b92b8232aa4221901ddf04981678601dc2",
}


@dataclass
class FrozenBaseModel:
    """Wrapper encapsulating a frozen, verified base predictor."""

    model_id: str
    dataset: str
    model_family: str
    seed: int
    configuration_id: str
    model: GBRModel | torch.nn.Module
    preprocessor: FittedPreprocessor
    metadata: dict[str, Any]

    def predict(self, X: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
        """Generate RUL predictions truncated at 0.0.

        Parameters
        ----------
        X : np.ndarray
            Input array of shape (M, 510) or (M, 30, 17).

        Returns
        -------
        np.ndarray
            Non-negative 1D array of predictions of shape (M,).
        """
        if not isinstance(X, np.ndarray):
            raise TypeError(f"X must be a numpy ndarray, got {type(X)}")
        if not np.issubdtype(X.dtype, np.number):
            raise TypeError(f"X must be numeric, got dtype {X.dtype}")
        if not np.all(np.isfinite(X)):
            raise ValueError("X contains NaN or infinite values")

        if X.ndim == 2:
            if X.shape[1] != 510:
                raise ValueError(f"2D input must have shape (M, 510), got {X.shape}")
            M = X.shape[0]
            X_seq = np.ascontiguousarray(X).reshape(M, 30, 17)
            X_flat = np.ascontiguousarray(X)
        elif X.ndim == 3:
            if X.shape[1] != 30 or X.shape[2] != 17:
                raise ValueError(f"3D input must have shape (M, 30, 17), got {X.shape}")
            M = X.shape[0]
            X_seq = np.ascontiguousarray(X)
            X_flat = np.ascontiguousarray(X).reshape(M, -1)
        else:
            raise ValueError(f"Input X must be 2D or 3D, got ndim={X.ndim} with shape {X.shape}")

        if M == 0:
            return np.empty(0, dtype=np.float64)

        if self.model_family == "GBR":
            assert isinstance(self.model, GBRModel)
            preds = self.model.predict(X_flat)
            if preds.shape != (M,):
                raise ValueError(f"GBR output shape mismatch: expected ({M},), got {preds.shape}")
            res = np.maximum(0.0, preds)
            return np.asarray(res, dtype=np.float64)

        if self.model_family == "LSTM":
            assert isinstance(self.model, torch.nn.Module)
            self.model.eval()
            batch_size = 256
            out_list: list[np.ndarray[Any, Any]] = []
            with torch.no_grad():
                for start_idx in range(0, M, batch_size):
                    batch_x = torch.from_numpy(X_seq[start_idx : start_idx + batch_size]).float()
                    batch_raw = self.model(batch_x).cpu().numpy().reshape(-1)
                    out_list.append(batch_raw)
            raw = np.concatenate(out_list, axis=0) if out_list else np.empty(0, dtype=np.float32)
            if not np.all(np.isfinite(raw)):
                raise ValueError("LSTM generated non-finite predictions")
            if raw.shape != (M,):
                raise ValueError(f"LSTM output shape mismatch: expected ({M},), got {raw.shape}")
            lstm_res = np.maximum(0.0, raw)
            return np.asarray(lstm_res, dtype=np.float64)

        raise ValueError(f"Unsupported model family: {self.model_family}")


def load_frozen_base_model(
    dataset: str,
    model_family: str,
    seed: int,
    registry_path: Path | str = "experiments/base_models/model_registry.json",
    base_dir: Path | str = ".",
) -> FrozenBaseModel:
    """Load an official frozen base model from the authoritative registry.

    Parameters
    ----------
    dataset : str
        One of 'FD001', 'FD002', 'FD004'.
    model_family : str
        One of 'GBR', 'LSTM'.
    seed : int
        One of 2026, 2027, 2028, 2029, 2030.
    registry_path : Path | str
        Path to experiments/base_models/model_registry.json.
    base_dir : Path | str
        Root repository path for resolving relative artifact paths.

    Returns
    -------
    FrozenBaseModel
        Verified model wrapper ready for inference.
    """
    reg_p = Path(registry_path)
    if not reg_p.exists():
        raise FileNotFoundError(f"Model registry not found at: {reg_p}")

    with open(reg_p, encoding="utf-8") as f:
        registry_data = json.load(f)

    entries = registry_data if isinstance(registry_data, list) else registry_data.get("models", [])

    match_entry = None
    for entry in entries:
        if (
            entry["dataset"] == dataset
            and entry["model_family"] == model_family
            and entry["seed"] == seed
        ):
            match_entry = entry
            break

    if match_entry is None:
        raise KeyError(
            f"No registered model found for dataset={dataset}, family={model_family}, seed={seed}"
        )

    base = Path(base_dir)
    ckpt_path = base / match_entry["checkpoint_path"]
    meta_path = base / match_entry["metadata_path"]
    pred_path = base / match_entry["validation_prediction_path"]
    prep_path = base / f"experiments/preprocessing/{dataset}/preprocessor.json"

    # Verify hashes
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint artifact missing: {ckpt_path}")
    if compute_sha256(ckpt_path) != match_entry["checkpoint_sha256"]:
        raise ValueError(f"Checkpoint SHA-256 mismatch for {match_entry['model_id']}")

    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata artifact missing: {meta_path}")
    if compute_sha256(meta_path) != match_entry["metadata_sha256"]:
        raise ValueError(f"Metadata SHA-256 mismatch for {match_entry['model_id']}")

    if not pred_path.exists():
        raise FileNotFoundError(f"Validation prediction artifact missing: {pred_path}")
    if compute_sha256(pred_path) != match_entry["validation_prediction_sha256"]:
        raise ValueError(f"Validation prediction SHA-256 mismatch for {match_entry['model_id']}")

    if not prep_path.exists():
        raise FileNotFoundError(f"Preprocessor artifact missing: {prep_path}")
    if compute_sha256(prep_path) != match_entry["preprocessor_sha256"]:
        raise ValueError(f"Preprocessor SHA-256 mismatch for {match_entry['model_id']}")

    # Load metadata
    with open(meta_path, encoding="utf-8") as f:
        meta_dict = json.load(f)

    # Load preprocessor
    preprocessor, _ = load_preprocessor_artifact(prep_path)

    # Load model
    if model_family == "GBR":
        model: GBRModel | torch.nn.Module = GBRModel.load(str(ckpt_path))
    elif model_family == "LSTM":
        model, _ = load_lstm_checkpoint(ckpt_path, device="cpu")
    else:
        raise ValueError(f"Unsupported family: {model_family}")

    return FrozenBaseModel(
        model_id=match_entry["model_id"],
        dataset=dataset,
        model_family=model_family,
        seed=seed,
        configuration_id=match_entry["configuration_id"],
        model=model,
        preprocessor=preprocessor,
        metadata=meta_dict,
    )


def audit_base_model_registry(
    registry_path: Path | str = "experiments/base_models/model_registry.json",
    base_dir: Path | str = ".",
    reload_checkpoints: bool = True,
    reproduce_predictions: bool = False,
    raw_data_dir: Path | str = "data/raw/cmapss",
) -> dict[str, Any]:
    """Run rigorous full audit on the 30-model registry and disk artifacts.

    Parameters
    ----------
    registry_path : Path | str
        Path to model_registry.json.
    base_dir : Path | str
        Root repository directory.
    reload_checkpoints : bool
        Whether to reload and verify checkpoints on CPU.
    reproduce_predictions : bool
        Whether to re-evaluate raw validation data and verify exact prediction match.
    raw_data_dir : Path | str
        Directory containing raw C-MAPSS run-to-failure text files.

    Returns
    -------
    dict[str, Any]
        Audit results summary.

    Raises
    ------
    RuntimeError | ValueError | FileNotFoundError
        Upon any detected defect.
    """
    base = Path(base_dir)
    reg_p = base / registry_path if not Path(registry_path).is_absolute() else Path(registry_path)
    if not reg_p.exists():
        raise FileNotFoundError(f"Model registry not found at: {reg_p}")

    with open(reg_p, encoding="utf-8") as f:
        registry_data = json.load(f)

    entries = registry_data if isinstance(registry_data, list) else registry_data.get("models", [])

    if len(entries) != EXPECTED_TOTAL_MODELS:
        raise ValueError(
            f"Registry must contain exactly {EXPECTED_TOTAL_MODELS} entries, found {len(entries)}"
        )

    # 1. Structure and uniqueness
    seen_cells: set[tuple[str, str, int]] = set()
    configs_by_cell: dict[tuple[str, str], set[str]] = {}
    preproc_by_dataset: dict[str, set[str]] = {}
    split_by_dataset: dict[str, set[str]] = {}

    for entry in entries:
        required_keys = (
            "model_id",
            "dataset",
            "model_family",
            "seed",
            "configuration_id",
            "checkpoint_path",
            "checkpoint_sha256",
            "metadata_path",
            "metadata_sha256",
            "validation_prediction_path",
            "validation_prediction_sha256",
            "preprocessor_sha256",
            "split_manifest_sha256",
            "git_commit",
            "status",
        )
        for k in required_keys:
            if k not in entry:
                raise KeyError(f"Registry entry missing required key '{k}': {entry}")

        if entry["status"] != "verified":
            raise ValueError(f"Entry status is not 'verified': {entry['status']}")

        ds = entry["dataset"]
        fam = entry["model_family"]
        seed = entry["seed"]

        if ds not in EXPECTED_DATASETS:
            raise ValueError(f"Unexpected dataset: {ds}")
        if fam not in EXPECTED_FAMILIES:
            raise ValueError(f"Unexpected model family: {fam}")
        if seed not in EXPECTED_SEEDS:
            raise ValueError(f"Unexpected seed: {seed}")

        cell = (ds, fam, seed)
        if cell in seen_cells:
            raise ValueError(f"Duplicate model cell detected: {cell}")
        seen_cells.add(cell)

        # Track configuration freeze
        configs_by_cell.setdefault((ds, fam), set()).add(entry["configuration_id"])
        # Track preprocessing freeze
        preproc_by_dataset.setdefault(ds, set()).add(entry["preprocessor_sha256"])
        # Track split freeze
        split_by_dataset.setdefault(ds, set()).add(entry["split_manifest_sha256"])

        # Verify artifacts exist and hashes match
        ckpt_p = base / entry["checkpoint_path"]
        meta_p = base / entry["metadata_path"]
        pred_p = base / entry["validation_prediction_path"]

        if not ckpt_p.exists():
            raise FileNotFoundError(f"Checkpoint file missing: {ckpt_p}")
        if compute_sha256(ckpt_p) != entry["checkpoint_sha256"]:
            raise ValueError(f"Checkpoint hash mismatch: {ckpt_p}")

        if not meta_p.exists():
            raise FileNotFoundError(f"Metadata file missing: {meta_p}")
        if compute_sha256(meta_p) != entry["metadata_sha256"]:
            raise ValueError(f"Metadata hash mismatch: {meta_p}")

        if not pred_p.exists():
            raise FileNotFoundError(f"Prediction file missing: {pred_p}")
        if compute_sha256(pred_p) != entry["validation_prediction_sha256"]:
            raise ValueError(f"Prediction hash mismatch: {pred_p}")

        # Check metadata semantics
        with open(meta_p, encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("training_target") != "rul_target_cap_125":
            raise ValueError(f"Invalid training target in {meta_p}: {meta.get('training_target')}")
        if meta.get("validation_target") != "uncapped_rul_true":
            raise ValueError(
                f"Invalid validation target in {meta_p}: {meta.get('validation_target')}"
            )
        if meta.get("dataset") != ds:
            raise ValueError(
                f"Dataset mismatch in metadata {meta_p}: {meta.get('dataset')} != {ds}"
            )
        if meta.get("model_family") != fam:
            raise ValueError(f"Family mismatch in metadata {meta_p}")
        if meta.get("run_seed") != seed:
            raise ValueError(f"Seed mismatch in metadata {meta_p}")
        if meta.get("configuration_id") != entry["configuration_id"]:
            raise ValueError(f"Configuration mismatch in metadata {meta_p}")
        if fam == "GBR" and meta.get("best_epoch") is not None:
            raise ValueError(f"GBR best_epoch must be null in {meta_p}")

        # Verify validation endpoint completeness
        df_pred = pd.read_csv(pred_p)
        expected_cols = [
            "unit",
            "endpoint_cycle",
            "rul_true",
            "rul_target",
            "prediction",
            "regime",
            "lifecycle_stage",
        ]
        if list(df_pred.columns) != expected_cols:
            raise ValueError(f"Prediction CSV columns mismatch in {pred_p}")

        # Non-negative predictions
        if (df_pred["prediction"] < 0.0).any():
            raise ValueError(f"Negative predictions detected in {pred_p}")

        # Verify endpoint cycles 30..T per unit
        for unit, grp in df_pred.groupby("unit"):
            cycles = grp["endpoint_cycle"].tolist()
            if cycles != sorted(cycles):
                raise ValueError(f"Cycles not sorted for unit {unit} in {pred_p}")
            if cycles[0] != 30:
                raise ValueError(f"First cycle is not 30 for unit {unit} in {pred_p}: {cycles[0]}")
            expected_seq = list(range(30, 30 + len(cycles)))
            if cycles != expected_seq:
                raise ValueError(f"Non-contiguous cycles for unit {unit} in {pred_p}")

        # Checkpoint loadability check
        if reload_checkpoints:
            if fam == "GBR":
                m_gbr = GBRModel.load(str(ckpt_p))
                if not m_gbr.is_fitted:
                    raise RuntimeError(f"Loaded GBR model is not fitted: {ckpt_p}")
            elif fam == "LSTM":
                m_lstm, ckpt_dict = load_lstm_checkpoint(ckpt_p, device="cpu")
                if "state_dict" not in ckpt_dict:
                    raise RuntimeError(f"LSTM checkpoint missing state_dict: {ckpt_p}")

    # 2. Assert all 30 unique cells present
    if len(seen_cells) != 30:
        raise ValueError(f"Expected 30 unique cells, got {len(seen_cells)}")

    # 3. Assert configuration freeze (exactly 1 config per (dataset, family))
    for (ds, fam), cfgs in configs_by_cell.items():
        if len(cfgs) != 1:
            raise ValueError(f"Configuration not frozen for ({ds}, {fam}): found multiple: {cfgs}")

    # Specific check for FD002 frozen winners
    if list(configs_by_cell[("FD002", "GBR")])[0] != "gbr_lr010_leaf31_l2_0":
        raise ValueError("FD002 GBR winner does not match frozen gbr_lr010_leaf31_l2_0")
    if list(configs_by_cell[("FD002", "LSTM")])[0] != "lstm_h64_lr0010":
        raise ValueError("FD002 LSTM winner does not match frozen lstm_h64_lr0010")

    # 4. Assert preprocessing freeze against disk files
    for ds, hashes in preproc_by_dataset.items():
        if len(hashes) != 1:
            raise ValueError(f"Preprocessing hash not constant for {ds}: {hashes}")
        actual_hash = list(hashes)[0]
        disk_prep = base / f"experiments/preprocessing/{ds}/preprocessor.json"
        if not disk_prep.exists():
            raise FileNotFoundError(f"Committed preprocessor missing: {disk_prep}")
        disk_hash = compute_sha256(disk_prep)
        if disk_hash != actual_hash:
            raise ValueError(
                f"Disk preprocessor hash mismatch for {ds}: {disk_hash} != {actual_hash}"
            )
        if actual_hash != COMMITTED_PREPROCESSOR_HASHES[ds]:
            raise ValueError(
                f"Preprocessor hash mismatch for {ds}: "
                f"expected {COMMITTED_PREPROCESSOR_HASHES[ds]}, got {actual_hash}"
            )

    # 5. Assert split freeze against disk files
    for ds, hashes in split_by_dataset.items():
        if len(hashes) != 1:
            raise ValueError(f"Split hash not constant for {ds}: {hashes}")
        actual_hash = list(hashes)[0]
        disk_split = base / f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        if not disk_split.exists():
            raise FileNotFoundError(f"Committed split manifest missing: {disk_split}")
        disk_hash = compute_sha256(disk_split)
        if disk_hash != actual_hash:
            raise ValueError(
                f"Disk split manifest hash mismatch for {ds}: {disk_hash} != {actual_hash}"
            )
        if actual_hash != COMMITTED_SPLIT_HASHES[ds]:
            raise ValueError(
                f"Split hash mismatch for {ds}: "
                f"expected {COMMITTED_SPLIT_HASHES[ds]}, got {actual_hash}"
            )

    # 6. Step 7 Isolation and Partition Role Checks
    # Verify engine counts and roles declared in Step 7 artifacts
    for entry in entries:
        ds = entry["dataset"]
        split_path = base / f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
        manifest = load_split_manifest(split_path)

        meta_p = base / entry["metadata_path"]
        with open(meta_p, encoding="utf-8") as f:
            meta = json.load(f)

        if meta.get("train_engine_count") != len(manifest.train):
            raise ValueError(
                f"train_engine_count mismatch in {meta_p}: "
                f"{meta.get('train_engine_count')} != {len(manifest.train)}"
            )
        if meta.get("validation_engine_count") != len(manifest.validation):
            raise ValueError(
                f"validation_engine_count mismatch in {meta_p}: "
                f"{meta.get('validation_engine_count')} != {len(manifest.validation)}"
            )

        # Check prediction CSV engine IDs belong exclusively to validation engines
        pred_p = base / entry["validation_prediction_path"]
        df_pred = pd.read_csv(pred_p)
        pred_units = set(df_pred["unit"].unique())
        val_units = set(manifest.validation)
        if pred_units != val_units:
            raise ValueError(
                f"Prediction CSV {pred_p} engines mismatch validation: {pred_units ^ val_units}"
            )

    # Verify absence of held-out test prediction/metric artifacts across experiments/
    exp_dir = base / "experiments"
    forbidden_terms = ["test_pred", "test_metric", "test_eval", "confirmatory_test"]
    leaked_test_artifacts: list[str] = []
    for p in exp_dir.rglob("*"):
        if p.is_file():
            name_lower = p.name.lower()
            if any(term in name_lower for term in forbidden_terms):
                leaked_test_artifacts.append(str(p))

    if leaked_test_artifacts:
        raise RuntimeError(
            f"Forbidden held-out test artifacts detected in experiments/: {leaked_test_artifacts}"
        )

    # 7. Explicit Prediction Reproduction Mode (when requested)
    reproduction_results: dict[str, Any] = {}
    if reproduce_predictions:
        raw_base = base / raw_data_dir
        # Require all three official raw training files
        for ds in EXPECTED_DATASETS:
            raw_f = raw_base / f"train_{ds}.txt"
            if not raw_f.exists():
                raise FileNotFoundError(f"Required raw C-MAPSS training file missing: {raw_f}")

        # Cache prepared validation windows per dataset
        dataset_windows: dict[str, Any] = {}
        dataset_true_trajectories: dict[str, dict[int, int]] = {}

        for ds in EXPECTED_DATASETS:
            raw_f = raw_base / f"train_{ds}.txt"
            df_raw = load_cmapss_run_to_failure(
                raw_f, dataset_name=ds, expected_engine_count=EXPECTED_ENGINE_COUNTS[ds]
            )
            # Trajectory length T_i per unit
            true_T = df_raw.groupby("unit")["cycle"].max().to_dict()
            dataset_true_trajectories[ds] = true_T

            split_path = base / f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
            manifest = load_split_manifest(split_path)
            df_val_raw = select_partition(df_raw, manifest, partition_name="validation")

            prep_path = base / f"experiments/preprocessing/{ds}/preprocessor.json"
            preproc, _ = load_preprocessor_artifact(prep_path)

            df_val_trans = preproc.transform(df_val_raw)
            val_windows = construct_windows(df_val_trans)

            # Assert endpoints 30 through engine's actual T
            val_units_unique = sorted(set(val_windows.engine_ids))
            expected_val_units = sorted(manifest.validation)
            if val_units_unique != expected_val_units:
                raise ValueError(
                    f"Validation window engines mismatch for {ds}: "
                    f"{val_units_unique} != {expected_val_units}"
                )

            for unit in expected_val_units:
                u_endpoints = [
                    ep
                    for u, ep in zip(
                        val_windows.engine_ids, val_windows.endpoint_cycles, strict=True
                    )
                    if u == unit
                ]
                expected_endpoints = list(range(30, true_T[unit] + 1))
                if u_endpoints != expected_endpoints:
                    raise ValueError(
                        f"Unit {unit} endpoints mismatch for {ds}: "
                        f"expected 30..{true_T[unit]}, got {u_endpoints}"
                    )

            # Verify rul_true = T - endpoint_cycle and rul_target = min(rul_true, 125)
            for u, ep, rt, rtarget in zip(
                val_windows.engine_ids,
                val_windows.endpoint_cycles,
                val_windows.rul_true,
                val_windows.rul_target,
                strict=True,
            ):
                expected_rt = float(true_T[u] - ep)
                if abs(rt - expected_rt) > 1e-6:
                    raise ValueError(
                        f"rul_true mismatch for unit {u} cycle {ep}: {rt} != {expected_rt}"
                    )
                if abs(rtarget - min(expected_rt, 125.0)) > 1e-6:
                    raise ValueError(f"rul_target mismatch for unit {u} cycle {ep}")

            dataset_windows[ds] = val_windows

        # Evaluate all 30 models
        for entry in entries:
            model_id = entry["model_id"]
            ds = entry["dataset"]
            fam = entry["model_family"]
            seed = entry["seed"]
            ckpt_path = base / entry["checkpoint_path"]
            pred_path = base / entry["validation_prediction_path"]
            meta_path = base / entry["metadata_path"]
            metrics_path = base / f"experiments/base_models/{ds}/{fam}/seed_{seed}/metrics.json"

            val_windows = dataset_windows[ds]

            if fam == "GBR":
                m_gbr = GBRModel.load(str(ckpt_path))
                repro_preds = m_gbr.predict(val_windows.flatten_for_gbr())
            elif fam == "LSTM":
                m_lstm, _ = load_lstm_checkpoint(ckpt_path, device="cpu")
                m_lstm.eval()
                preds_list: list[np.ndarray[Any, Any]] = []
                with torch.no_grad():
                    for start_idx in range(0, len(val_windows.X_sequence), 256):
                        bx = torch.from_numpy(
                            val_windows.X_sequence[start_idx : start_idx + 256]
                        ).float()
                        preds_list.append(m_lstm(bx).cpu().numpy().reshape(-1))
                raw_lstm_preds = (
                    np.concatenate(preds_list, axis=0)
                    if preds_list
                    else np.empty(0, dtype=np.float32)
                )
                repro_preds = np.maximum(0.0, raw_lstm_preds)
            else:
                raise ValueError(f"Unsupported model family: {fam}")

            if not np.all(np.isfinite(repro_preds)):
                raise ValueError(f"Non-finite predictions reproduced in {model_id}")
            if not np.all(repro_preds >= 0.0):
                raise ValueError(f"Negative predictions reproduced in {model_id}")

            df_saved = pd.read_csv(pred_path)
            df_repro = pd.DataFrame(
                {
                    "unit": val_windows.engine_ids,
                    "endpoint_cycle": val_windows.endpoint_cycles,
                    "repro_pred": repro_preds,
                }
            )
            df_joined = pd.merge(
                df_saved, df_repro, on=["unit", "endpoint_cycle"], how="outer", indicator=True
            )
            if (df_joined["_merge"] != "both").any():
                raise ValueError(f"Prediction reproduction key mismatch in {model_id}")

            max_abs_diff = float(np.max(np.abs(df_joined["prediction"] - df_joined["repro_pred"])))
            if max_abs_diff > 1e-4:
                raise ValueError(
                    f"Prediction max abs difference {max_abs_diff:.6e} > 1e-4 in {model_id}"
                )

            # Recompute engine-weighted metrics
            recomp_metrics = compute_model_metrics(
                predictions=repro_preds,
                rul_true=val_windows.rul_true,
                rul_target=val_windows.rul_target,
                engine_ids=val_windows.engine_ids,
            )

            with open(metrics_path, encoding="utf-8") as f:
                saved_metrics = json.load(f)
            rmse_diff = abs(recomp_metrics.uncapped_rmse - float(saved_metrics["uncapped_rmse"]))
            mae_diff = abs(recomp_metrics.uncapped_mae - float(saved_metrics["uncapped_mae"]))
            capped_rmse_diff = abs(recomp_metrics.capped_rmse - float(saved_metrics["capped_rmse"]))

            if rmse_diff > 1e-4 or mae_diff > 1e-4 or capped_rmse_diff > 1e-4:
                raise ValueError(
                    f"Recomputed metrics mismatch for {model_id}: RMSE diff {rmse_diff:.6e}, "
                    f"MAE diff {mae_diff:.6e}, Capped RMSE diff {capped_rmse_diff:.6e}"
                )

            with open(meta_path, encoding="utf-8") as f:
                saved_meta = json.load(f)
            meta_rmse_diff = abs(
                recomp_metrics.uncapped_rmse - float(saved_meta["validation_uncapped_rmse"])
            )
            meta_mae_diff = abs(
                recomp_metrics.uncapped_mae - float(saved_meta["validation_uncapped_mae"])
            )
            meta_capped_diff = abs(
                recomp_metrics.capped_rmse - float(saved_meta["validation_capped_rmse"])
            )

            if meta_rmse_diff > 1e-4 or meta_mae_diff > 1e-4 or meta_capped_diff > 1e-4:
                raise ValueError(f"Metadata metrics mismatch for {model_id}")

            reproduction_results[model_id] = {
                "dataset": ds,
                "model_family": fam,
                "seed": seed,
                "configuration_id": entry["configuration_id"],
                "max_abs_prediction_diff": max_abs_diff,
                "recomputed_uncapped_rmse": recomp_metrics.uncapped_rmse,
                "saved_uncapped_rmse": float(saved_metrics["uncapped_rmse"]),
                "rmse_diff": rmse_diff,
                "recomputed_uncapped_mae": recomp_metrics.uncapped_mae,
                "saved_uncapped_mae": float(saved_metrics["uncapped_mae"]),
                "mae_diff": mae_diff,
                "recomputed_capped_rmse": recomp_metrics.capped_rmse,
                "saved_capped_rmse": float(saved_metrics["capped_rmse"]),
                "capped_rmse_diff": capped_rmse_diff,
                "status": "PASS",
            }

    return {
        "status": "PASS",
        "models_audited": len(entries),
        "datasets": list(EXPECTED_DATASETS),
        "families": list(EXPECTED_FAMILIES),
        "seeds": list(EXPECTED_SEEDS),
        "configurations": {
            f"{ds}_{fam}": list(cfgs)[0] for (ds, fam), cfgs in configs_by_cell.items()
        },
        "checkpoint_integrity": "PASS",
        "prediction_reproduction": "PASS" if reproduce_predictions else "NOT RUN",
        "reproduction_details": reproduction_results if reproduce_predictions else None,
    }
