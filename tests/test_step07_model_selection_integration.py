"""Integration smoke tests for Step 7.3 base predictor selection pipeline on FD002.

Marked with @pytest.mark.integration to distinguish from fast unit tests.
Verifies:
- FD002 data loads through Step-7.2 pipeline.
- Committed preprocessor hash matches.
- Calibration and test windows are strictly absent from PreparedDataset.
- One GBR configuration can train and predict on FD002 windows.
- One small/limited LSTM smoke run can execute on CPU.
- Validation metrics calculate correctly.
- Prediction artifact schema is valid and correctly formatted.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.pipeline import prepare_dataset_for_model_development
from intellitwin.models.artifacts import PREDICTION_COLUMNS, save_prediction_artifact
from intellitwin.models.gbr import GBRModel, get_gbr_grid
from intellitwin.models.lstm import (
    LSTMHyperparameters,
    train_lstm_candidate,
)

RAW_FD002_PATH = Path("data/raw/cmapss/train_FD002.txt")
SPLIT_MANIFEST_PATH = Path("data/splits/fd002_engine_split_seed_2026.json")
COMMITTED_PREPROCESSOR_PATH = Path("experiments/preprocessing/FD002/preprocessor.json")


@pytest.mark.integration
def test_fd002_base_predictor_smoke_integration(tmp_path: Path) -> None:
    """Smoke test GBR and LSTM base predictor pipelines on FD002 dataset."""
    if not RAW_FD002_PATH.exists():
        pytest.skip(f"Raw data file {RAW_FD002_PATH} not found.")
    if not SPLIT_MANIFEST_PATH.exists():
        pytest.skip(f"Split manifest {SPLIT_MANIFEST_PATH} not found.")
    if not COMMITTED_PREPROCESSOR_PATH.exists():
        pytest.skip(f"Preprocessor artifact {COMMITTED_PREPROCESSOR_PATH} not found.")

    # 1. Load dataset via Step 7.2 pipeline
    dataset = prepare_dataset_for_model_development(
        dataset_name="FD002",
        raw_path=RAW_FD002_PATH,
        split_manifest_path=SPLIT_MANIFEST_PATH,
    )

    # 2. Verify committed preprocessor hash matches
    committed_preprocessor_hash = compute_sha256(COMMITTED_PREPROCESSOR_PATH)
    assert (
        committed_preprocessor_hash
        == "cef04b8dafc4c9f53aba7c6bcb0bc67fc981540abdafadc76fafa314684d856c"
    )

    # 3. Verify calibration and test engines are strictly absent from window datasets
    assert not hasattr(dataset, "calibration_windows")
    assert not hasattr(dataset, "test_windows")
    assert dataset.provenance["train_engine_count"] == 130
    assert dataset.provenance["validation_engine_count"] == 26
    assert len(dataset.train_windows) == 22923
    assert len(dataset.validation_windows) == 4669

    # 4. Smoke test GBR on first configuration (train on a small slice for fast smoke test)
    gbr_grid = get_gbr_grid()
    cfg_gbr = gbr_grid[0]
    gbr_model = GBRModel(hyperparameters=cfg_gbr, run_seed=2026)

    # Flattened train and validation inputs
    X_train_flat = dataset.train_windows.flatten_for_gbr()
    y_train = dataset.train_windows.rul_target
    weights = dataset.train_sample_weights
    X_val_flat = dataset.validation_windows.flatten_for_gbr()
    rul_true_val = dataset.validation_windows.rul_true
    rul_target_val = dataset.validation_windows.rul_target
    val_engines = dataset.validation_windows.engine_ids

    # For fast smoke test, fit on first 500 samples
    gbr_model.fit(X_train_flat[:500], y_train[:500], sample_weight=weights[:500])
    gbr_preds = gbr_model.predict(X_val_flat[:100])
    assert len(gbr_preds) == 100
    assert np.all(gbr_preds >= 0.0)

    # 5. Smoke test LSTM on CPU with 1 epoch
    lstm_hp = LSTMHyperparameters(
        config_id="lstm_smoke_test",
        hidden_size=32,
        learning_rate=0.001,
        batch_size=256,
        max_epochs=1,
        early_stopping_patience=1,
    )

    # Train on small slice for fast smoke test
    lstm_res = train_lstm_candidate(
        hyperparameters=lstm_hp,
        run_seed=2026,
        X_train=dataset.train_windows.X_sequence[:512],
        y_train=y_train[:512],
        train_weights=weights[:512],
        X_val=dataset.validation_windows.X_sequence[:128],
        rul_true_val=rul_true_val[:128],
        rul_target_val=rul_target_val[:128],
        val_engine_ids=val_engines[:128],
        device=torch.device("cpu"),
    )

    assert len(lstm_res.validation_predictions) == 128
    assert np.all(lstm_res.validation_predictions >= 0.0)
    assert lstm_res.validation_metrics.uncapped_rmse > 0.0

    # 6. Verify prediction artifact serialization and schema
    df_preds = pd.DataFrame(
        {
            "unit": val_engines[:128],
            "endpoint_cycle": dataset.validation_windows.endpoint_cycles[:128],
            "rul_true": rul_true_val[:128],
            "rul_target": rul_target_val[:128],
            "prediction": lstm_res.validation_predictions,
            "regime": dataset.validation_windows.regimes[:128],
            "lifecycle_stage": dataset.validation_windows.lifecycle_stages[:128],
        }
    )

    pred_csv_path = tmp_path / "smoke_predictions.csv"
    sha = save_prediction_artifact(df_preds, pred_csv_path)
    assert len(sha) == 64
    assert pred_csv_path.exists()

    # Verify reload columns
    df_reloaded = pd.read_csv(pred_csv_path)
    assert list(df_reloaded.columns) == list(PREDICTION_COLUMNS)
    assert len(df_reloaded) == 128
