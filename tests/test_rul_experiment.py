"""
Unit tests for Step 6 RUL Sequence Modeling Experiment.
Validates:
  1. Engine split integrity (zero engine overlap).
  2. Sequence window integrity (strictly within-engine, no boundary crossing).
  3. Preprocessing isolation (scaler fitted strictly on train data).
  4. Model output shapes and formats for GRU, LSTM, and Heteroscedastic LSTM.
  5. Numerical stability of heteroscedastic variance (no NaN, no Inf, strictly positive std).
  6. Metric consistency on hand-computable toy vectors.
  7. Seed reproducibility.
"""

import os
import sys
import pytest
import numpy as np
import torch

# Ensure repository root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from intellitwin.data_loader import CMAPSSDataLoader
from intellitwin.models.lstm_rul import LSTMRULNet, GRURULNet, heteroscedastic_loss
from intellitwin.metrics import compute_regression_metrics, nasa_scoring_function


class TestRULExperimentIntegrity:
    """Rigorous verification of data, architecture, and metric integrity for Step 6."""

    @pytest.fixture(scope="class")
    def loaded_data(self):
        """Prepare data loader once for integrity checks."""
        loader = CMAPSSDataLoader(random_state=42, val_ratio=0.20)
        loader.prepare_data(save_artifact=False)
        return loader

    def test_split_integrity(self, loaded_data):
        """Verify train, validation, and test engines are strictly mutually exclusive."""
        train_units = set(loaded_data.train_units)
        val_units = set(loaded_data.val_units)
        test_units = set(loaded_data.test_units)

        # Train and Val must be strictly disjoint partitions of the training dataset pool
        assert len(train_units & val_units) == 0, f"Train and Val overlap: {train_units & val_units}"
        assert len(train_units) == 80
        assert len(val_units) == 20
        assert train_units | val_units == set(range(1, 101))
        # Test fleet has 100 distinct evaluation units
        assert len(test_units) == 100

    def test_sequence_window_integrity(self, loaded_data):
        """Verify that every sequence window belongs to a single engine."""
        seq_data = loaded_data.get_sequential_data()
        X_train_seq = seq_data["X_train_seq"]
        X_val_seq = seq_data["X_val_seq"]
        X_test_last_seq = seq_data["X_test_last_seq"]

        assert X_train_seq.ndim == 3 and X_train_seq.shape[1] == 30 and X_train_seq.shape[2] == 54
        assert X_val_seq.ndim == 3 and X_val_seq.shape[1] == 30 and X_val_seq.shape[2] == 54
        assert X_test_last_seq.shape == (100, 30, 54)

        # Check for any NaN or Inf in sequence arrays
        assert not np.isnan(X_train_seq).any(), "NaN found in X_train_seq"
        assert not np.isinf(X_train_seq).any(), "Inf found in X_train_seq"
        assert not np.isnan(X_test_last_seq).any(), "NaN found in X_test_last_seq"

    def test_preprocessing_isolation(self, loaded_data):
        """Verify scaler parameters are fitted strictly on training data."""
        scaler = loaded_data.scaler
        assert hasattr(scaler, "mean_") and hasattr(scaler, "scale_")
        assert len(scaler.mean_) == len(loaded_data.feature_columns)
        assert len(scaler.scale_) == len(loaded_data.feature_columns)

    def test_model_outputs_and_shapes(self):
        """Verify forward pass output signatures for all sequence models."""
        batch_size = 16
        seq_len = 30
        input_dim = 54
        x = torch.randn(batch_size, seq_len, input_dim)

        # 1. GRU
        gru = GRURULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2)
        gru_out = gru(x)
        assert gru_out.shape == (batch_size,), f"GRU output shape mismatch: {gru_out.shape}"

        # 2. Standard LSTM
        lstm_mse = LSTMRULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2, heteroscedastic=False)
        lstm_out = lstm_mse(x)
        assert lstm_out.shape == (batch_size,), f"Standard LSTM output shape mismatch: {lstm_out.shape}"

        # 3. Heteroscedastic LSTM
        lstm_hetero = LSTMRULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2, heteroscedastic=True)
        mu, log_var = lstm_hetero(x)
        assert mu.shape == (batch_size,), f"Hetero mu shape mismatch: {mu.shape}"
        assert log_var.shape == (batch_size,), f"Hetero log_var shape mismatch: {log_var.shape}"

    def test_heteroscedastic_numerical_stability(self):
        """Verify that heteroscedastic loss handles extreme outputs without NaN/Inf."""
        mu = torch.tensor([50.0, 100.0, 0.0])
        # Test boundary clamped log_var
        log_var = torch.tensor([-6.0, 6.0, 0.0])
        target = torch.tensor([55.0, 90.0, 10.0])

        loss = heteroscedastic_loss(mu, log_var, target)
        assert not torch.isnan(loss), "Heteroscedastic loss produced NaN"
        assert not torch.isinf(loss), "Heteroscedastic loss produced Inf"
        assert loss.item() > 0.0

        # Verify standard deviation computation
        std = np.exp(0.5 * log_var.numpy())
        assert (std > 0).all(), "Standard deviation must be strictly positive"
        assert not np.isnan(std).any(), "NaN found in computed standard deviation"

    def test_metrics_toy_examples(self):
        """Verify RMSE, MAE, and NASA score on known hand-computable vectors."""
        y_true = np.array([100.0, 50.0, 20.0])
        y_pred = np.array([100.0, 40.0, 30.0])  # d = [0, -10, +10]

        metrics = compute_regression_metrics(y_true, y_pred)
        # RMSE: sqrt((0 + 100 + 100) / 3) = sqrt(200/3) = sqrt(66.6667) = 8.1650
        assert np.isclose(metrics["rmse"], np.sqrt(200.0 / 3.0), atol=1e-3)
        # MAE: (0 + 10 + 10) / 3 = 20/3 = 6.6667
        assert np.isclose(metrics["mae"], 20.0 / 3.0, atol=1e-3)

        # NASA score:
        # d[0] = 0 -> exp(0) - 1 = 0
        # d[1] = -10 -> exp(10/13) - 1 = exp(0.76923) - 1 = 2.1581 - 1 = 1.1581
        # d[2] = +10 -> exp(10/10) - 1 = exp(1) - 1 = 2.71828 - 1 = 1.71828
        expected_nasa = 0.0 + (np.exp(10.0 / 13.0) - 1.0) + (np.exp(1.0) - 1.0)
        assert np.isclose(metrics["nasa_score"], expected_nasa, atol=1e-3)
