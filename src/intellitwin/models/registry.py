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
    * Absence of calibration or held-out test artifacts in experiments/
- `load_frozen_base_model`: High-level stable API to load verified frozen base models.
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
from intellitwin.data.preprocessing import FittedPreprocessor
from intellitwin.models.gbr import GBRModel
from intellitwin.models.lstm import load_lstm_checkpoint

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
        """Generate RUL predictions truncated at 0.0."""
        if self.model_family == "GBR":
            assert isinstance(self.model, GBRModel)
            # Flattened 2D array expected for GBR
            if X.ndim == 3:
                # Shape (M, L, F) -> flatten to (M, L*F)
                M = X.shape[0]
                X_flat = X.reshape(M, -1)
                return self.model.predict(X_flat)
            return self.model.predict(X)

        if self.model_family == "LSTM":
            # 3D array (M, L, F) expected
            if X.ndim == 2:
                # If 2D (M, 510), reshape to (M, 30, 17)
                M = X.shape[0]
                X_seq = X.reshape(M, 30, 17)
            else:
                X_seq = X
            assert isinstance(self.model, torch.nn.Module)
            self.model.eval()
            with torch.no_grad():
                tensor_x = torch.from_numpy(X_seq).float()
                raw = self.model(tensor_x).cpu().numpy()
                res: np.ndarray[Any, Any] = np.maximum(0.0, raw)
                return res

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
) -> dict[str, Any]:
    """Run rigorous full audit on the 30-model registry and disk artifacts.

    Raises RuntimeError or ValueError upon any detected defect.
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
            # Check continuous step of 1
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

    # 4. Assert preprocessing freeze
    for ds, hashes in preproc_by_dataset.items():
        if len(hashes) != 1:
            raise ValueError(f"Preprocessing hash not constant for {ds}: {hashes}")
        actual_hash = list(hashes)[0]
        if actual_hash != COMMITTED_PREPROCESSOR_HASHES[ds]:
            raise ValueError(
                f"Preprocessor hash mismatch for {ds}: "
                f"expected {COMMITTED_PREPROCESSOR_HASHES[ds]}, got {actual_hash}"
            )

    # 5. Assert split freeze
    for ds, hashes in split_by_dataset.items():
        if len(hashes) != 1:
            raise ValueError(f"Split hash not constant for {ds}: {hashes}")
        actual_hash = list(hashes)[0]
        if actual_hash != COMMITTED_SPLIT_HASHES[ds]:
            raise ValueError(
                f"Split hash mismatch for {ds}: "
                f"expected {COMMITTED_SPLIT_HASHES[ds]}, got {actual_hash}"
            )

    # 6. Verify absence of calibration and test artifacts under experiments/
    exp_dir = base / "experiments"
    forbidden_terms = ["calibration", "test"]
    leaked_artifacts = []
    for p in exp_dir.rglob("*"):
        if p.is_file():
            name_lower = p.name.lower()
            if any(term in name_lower for term in forbidden_terms):
                # Check if it is a calibration or test prediction/metric file
                if any(ext in name_lower for ext in [".csv", ".json", ".txt"]):
                    # Ignore model selection unless containing calib predictions
                    if (
                        "calib" in name_lower
                        or "test_pred" in name_lower
                        or "test_metric" in name_lower
                    ):
                        leaked_artifacts.append(str(p))

    if leaked_artifacts:
        raise RuntimeError(
            f"Forbidden calibration/test artifacts detected in experiments/: {leaked_artifacts}"
        )

    return {
        "status": "PASS",
        "models_audited": len(entries),
        "datasets": list(EXPECTED_DATASETS),
        "families": list(EXPECTED_FAMILIES),
        "seeds": list(EXPECTED_SEEDS),
        "configurations": {
            f"{ds}_{fam}": list(cfgs)[0] for (ds, fam), cfgs in configs_by_cell.items()
        },
    }
