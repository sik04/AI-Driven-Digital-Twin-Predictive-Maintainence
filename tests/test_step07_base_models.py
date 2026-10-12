"""Tests for Step 7.5 Base Predictor Registry, Loader, and Audit Suite.

Verifies:
1. model_registry.json structure, completeness (30 entries), and schema invariants.
2. load_frozen_base_model function for GBR and LSTM with sha256 integrity enforcement.
3. Tamper detection (fails on checkpoint or preprocessor hash mismatch).
4. FrozenBaseModel inference consistency and non-negative truncation.
5. base_predictor_validation_summary.csv match with summary.json files.
6. Full audit_base_model_registry pass.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from intellitwin.models.registry import (
    COMMITTED_PREPROCESSOR_HASHES,
    COMMITTED_SPLIT_HASHES,
    EXPECTED_DATASETS,
    EXPECTED_FAMILIES,
    EXPECTED_SEEDS,
    EXPECTED_TOTAL_MODELS,
    FrozenBaseModel,
    audit_base_model_registry,
    load_frozen_base_model,
)


def test_model_registry_file_completeness() -> None:
    """Verify model_registry.json exists, contains exactly 30 entries, and satisfies schema."""
    reg_path = Path("experiments/base_models/model_registry.json")
    assert reg_path.exists(), "experiments/base_models/model_registry.json missing"

    with open(reg_path, encoding="utf-8") as f:
        data = json.load(f)

    entries = data if isinstance(data, list) else data.get("models", [])
    assert len(entries) == EXPECTED_TOTAL_MODELS

    seen_cells: set[tuple[str, str, int]] = set()
    for entry in entries:
        assert entry["dataset"] in EXPECTED_DATASETS
        assert entry["model_family"] in EXPECTED_FAMILIES
        assert entry["seed"] in EXPECTED_SEEDS
        assert entry["status"] == "verified"

        cell = (entry["dataset"], entry["model_family"], entry["seed"])
        assert cell not in seen_cells, f"Duplicate cell {cell}"
        seen_cells.add(cell)

        # Check paths exist
        assert Path(entry["checkpoint_path"]).exists()
        assert Path(entry["metadata_path"]).exists()
        assert Path(entry["validation_prediction_path"]).exists()

        # Check preprocessor and split hashes match committed constants
        ds = entry["dataset"]
        assert entry["preprocessor_sha256"] == COMMITTED_PREPROCESSOR_HASHES[ds]
        assert entry["split_manifest_sha256"] == COMMITTED_SPLIT_HASHES[ds]


def test_load_frozen_base_model_gbr() -> None:
    """Verify load_frozen_base_model successfully loads a GBR model and performs inference."""
    model_obj = load_frozen_base_model(
        dataset="FD001",
        model_family="GBR",
        seed=2026,
    )
    assert isinstance(model_obj, FrozenBaseModel)
    assert model_obj.model_id == "FD001_GBR_seed2026"
    assert model_obj.dataset == "FD001"
    assert model_obj.model_family == "GBR"
    assert model_obj.seed == 2026

    # Test prediction on 2D input (M, 510)
    X_fake_flat = np.random.randn(5, 510)
    preds_flat = model_obj.predict(X_fake_flat)
    assert isinstance(preds_flat, np.ndarray)
    assert preds_flat.shape == (5,)
    assert np.all(preds_flat >= 0.0)

    # Test prediction on 3D input (M, 30, 17)
    X_fake_3d = np.random.randn(5, 30, 17)
    preds_3d = model_obj.predict(X_fake_3d)
    assert isinstance(preds_3d, np.ndarray)
    assert preds_3d.shape == (5,)
    assert np.all(preds_3d >= 0.0)


def test_load_frozen_base_model_lstm() -> None:
    """Verify load_frozen_base_model successfully loads an LSTM model and performs inference."""
    model_obj = load_frozen_base_model(
        dataset="FD001",
        model_family="LSTM",
        seed=2026,
    )
    assert isinstance(model_obj, FrozenBaseModel)
    assert model_obj.model_id == "FD001_LSTM_seed2026"
    assert model_obj.dataset == "FD001"
    assert model_obj.model_family == "LSTM"
    assert model_obj.seed == 2026

    # Test prediction on 3D input (M, 30, 17)
    X_fake_3d = np.random.randn(4, 30, 17).astype(np.float32)
    preds_3d = model_obj.predict(X_fake_3d)
    assert isinstance(preds_3d, np.ndarray)
    assert preds_3d.shape == (4,)
    assert np.all(preds_3d >= 0.0)

    # Test prediction on 2D input (M, 510)
    X_fake_flat = np.random.randn(4, 510).astype(np.float32)
    preds_flat = model_obj.predict(X_fake_flat)
    assert isinstance(preds_flat, np.ndarray)
    assert preds_flat.shape == (4,)
    assert np.all(preds_flat >= 0.0)


def test_load_frozen_base_model_rejection_and_tampering(tmp_path: Path) -> None:
    """Verify loader rejects invalid cell queries and tampered artifacts."""
    # Query non-existent seed
    with pytest.raises(KeyError, match="No registered model found"):
        load_frozen_base_model(
            dataset="FD001",
            model_family="GBR",
            seed=9999,
        )

    # Test hash mismatch tampering
    reg_path = Path("experiments/base_models/model_registry.json")
    with open(reg_path, encoding="utf-8") as f:
        data = json.load(f)

    # Mutate checkpoint hash in first entry
    tampered_data = list(data)
    tampered_data[0] = dict(tampered_data[0])
    tampered_data[0]["checkpoint_sha256"] = (
        "0000000000000000000000000000000000000000000000000000000000000000"
    )

    tampered_reg = tmp_path / "tampered_registry.json"
    tampered_reg.write_text(json.dumps(tampered_data), encoding="utf-8")

    first_entry = tampered_data[0]
    with pytest.raises(ValueError, match="Checkpoint SHA-256 mismatch"):
        load_frozen_base_model(
            dataset=first_entry["dataset"],
            model_family=first_entry["model_family"],
            seed=first_entry["seed"],
            registry_path=tampered_reg,
        )


def test_validation_summary_table_exactness() -> None:
    """Verify base_predictor_validation_summary.csv matches summary.json files exactly."""
    csv_path = Path("experiments/base_models/base_predictor_validation_summary.csv")
    assert csv_path.exists(), "Validation summary CSV missing"

    df = pd.read_csv(csv_path)
    assert len(df) == 6
    expected_cols = [
        "dataset",
        "model_family",
        "selected_configuration_id",
        "rmse_mean",
        "rmse_std",
        "mae_mean",
        "mae_std",
        "capped_rmse_mean",
        "capped_rmse_std",
        "training_duration_mean",
        "training_duration_std",
    ]
    assert list(df.columns) == expected_cols

    for _, row in df.iterrows():
        ds = row["dataset"]
        fam = row["model_family"]
        sum_p = Path(f"experiments/base_models/{ds}/{fam}/summary.json")
        with open(sum_p, encoding="utf-8") as f:
            sum_data: dict[str, Any] = json.load(f)

        assert row["selected_configuration_id"] == sum_data["selected_configuration_id"]
        assert np.isclose(row["rmse_mean"], sum_data["validation_uncapped_rmse"]["mean"])
        assert np.isclose(row["rmse_std"], sum_data["validation_uncapped_rmse"]["std"])
        assert np.isclose(row["mae_mean"], sum_data["validation_uncapped_mae"]["mean"])
        assert np.isclose(row["mae_std"], sum_data["validation_uncapped_mae"]["std"])
        assert np.isclose(row["capped_rmse_mean"], sum_data["validation_capped_rmse"]["mean"])
        assert np.isclose(row["capped_rmse_std"], sum_data["validation_capped_rmse"]["std"])


def test_full_registry_audit_pass() -> None:
    """Verify that audit_base_model_registry passes completely."""
    res = audit_base_model_registry(reload_checkpoints=True)
    assert res["status"] == "PASS"
    assert res["models_audited"] == 30
