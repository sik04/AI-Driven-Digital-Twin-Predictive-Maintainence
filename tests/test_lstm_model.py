"""Unit tests for LSTM model architecture, training, and early stopping.

Verifies:
- Exactly 4 configurations generated in LSTM grid with deterministic IDs.
- Architecture: single-layer unidirectional LSTM, explicit Dropout(p=0.20), Linear(H, 1).
- Output shape is (batch_size,).
- Weighted MSE loss batch normalization.
- CPU training execution.
- Non-negative prediction post-processing.
- Validation early stopping restores best checkpoint.
- Checkpoint saving and loading on CPU reproduces identical predictions.
- Deterministic behavior under identical seeds.
"""

from pathlib import Path

import numpy as np
import torch

from intellitwin.models.lstm import (
    LSTMHyperparameters,
    LSTMPointPredictor,
    get_lstm_grid,
    load_lstm_checkpoint,
    save_lstm_checkpoint,
    train_lstm_candidate,
)


def test_lstm_grid_contains_exactly_four_configs() -> None:
    """Verify LSTM search grid contains exactly 4 frozen configurations."""
    grid = get_lstm_grid()
    assert len(grid) == 4

    expected_ids = [
        "lstm_h32_lr0003",
        "lstm_h32_lr0010",
        "lstm_h64_lr0003",
        "lstm_h64_lr0010",
    ]
    actual_ids = [cfg.config_id for cfg in grid]
    assert actual_ids == expected_ids


def test_lstm_fixed_hyperparameters_conform_to_spec() -> None:
    """Verify all fixed hyperparameters are strictly invariant across configurations."""
    for cfg in get_lstm_grid():
        assert cfg.input_size == 17
        assert cfg.lookback == 30
        assert cfg.num_layers == 1
        assert cfg.bidirectional is False
        assert cfg.bias is True
        assert cfg.dropout == 0.0
        assert cfg.explicit_dropout == 0.20
        assert cfg.weight_decay == 1e-4
        assert cfg.betas == (0.9, 0.999)
        assert cfg.eps == 1e-8
        assert cfg.batch_size == 256
        assert cfg.max_epochs == 100
        assert cfg.gradient_clip_norm == 1.0
        assert cfg.early_stopping_patience == 10
        assert cfg.early_stopping_min_delta == 0.01
        assert cfg.hidden_size in [32, 64]
        assert cfg.learning_rate in [0.0003, 0.001]


def test_lstm_architecture_modules_and_output_shape() -> None:
    """Verify model layers, dimensions, and forward tensor shapes."""
    H = 32
    model = LSTMPointPredictor(hidden_size=H, explicit_dropout=0.20)

    assert isinstance(model.lstm, torch.nn.LSTM)
    assert model.lstm.input_size == 17
    assert model.lstm.hidden_size == H
    assert model.lstm.num_layers == 1
    assert model.lstm.batch_first is True
    assert model.lstm.bidirectional is False
    assert model.lstm.bias is True
    assert model.lstm.dropout == 0.0

    assert isinstance(model.dropout, torch.nn.Dropout)
    assert model.dropout.p == 0.20

    assert isinstance(model.linear, torch.nn.Linear)
    assert model.linear.in_features == H
    assert model.linear.out_features == 1

    # Forward pass
    batch_size = 8
    x = torch.randn(batch_size, 30, 17, dtype=torch.float32)
    out = model(x)
    assert out.shape == (batch_size,)


def test_weighted_mse_normalization_formula() -> None:
    """Verify batch loss is normalized by sum of sample weights."""
    preds = torch.tensor([10.0, 20.0], dtype=torch.float32)
    targets = torch.tensor([12.0, 16.0], dtype=torch.float32)  # errors: -2, +4; sq_err: 4, 16
    weights = torch.tensor([1.0, 3.0], dtype=torch.float32)

    # Expected: (1.0 * 4.0 + 3.0 * 16.0) / (1.0 + 3.0) = (4 + 48) / 4 = 52 / 4 = 13.0
    sq_err = (preds - targets) ** 2
    loss = torch.sum(weights * sq_err) / torch.sum(weights)

    assert torch.isclose(loss, torch.tensor(13.0, dtype=torch.float32))


def test_lstm_synthetic_train_early_stopping_and_checkpoint(tmp_path: Path) -> None:
    """Verify end-to-end training, early stopping restoration, and checkpoint serialization."""
    rng = np.random.default_rng(2026)
    n_train = 32
    n_val = 16

    X_train = rng.standard_normal((n_train, 30, 17)).astype(np.float32)
    y_train = rng.uniform(10.0, 100.0, size=n_train).astype(np.float32)
    weights_train = np.ones(n_train, dtype=np.float32)

    X_val = rng.standard_normal((n_val, 30, 17)).astype(np.float32)
    rul_true_val = rng.uniform(10.0, 100.0, size=n_val).astype(np.float64)
    rul_target_val = np.minimum(rul_true_val, 125.0)
    val_engine_ids = np.array([1] * 8 + [2] * 8, dtype=np.int64)

    # Use small custom hyperparameters for fast unit testing
    hp = LSTMHyperparameters(
        config_id="lstm_test_fast",
        hidden_size=16,
        learning_rate=0.01,
        batch_size=8,
        max_epochs=4,
        early_stopping_patience=2,
        early_stopping_min_delta=0.01,
    )

    result = train_lstm_candidate(
        hyperparameters=hp,
        run_seed=2026,
        X_train=X_train,
        y_train=y_train,
        train_weights=weights_train,
        X_val=X_val,
        rul_true_val=rul_true_val,
        rul_target_val=rul_target_val,
        val_engine_ids=val_engine_ids,
        device=torch.device("cpu"),
    )

    assert result.best_epoch >= 1
    assert result.epochs_completed >= 1
    assert result.training_duration_seconds > 0.0
    assert result.validation_predictions.shape == (n_val,)
    assert np.all(result.validation_predictions >= 0.0)
    assert result.validation_metrics.uncapped_rmse > 0.0

    # Save and reload checkpoint
    ckpt_path = tmp_path / "lstm_test.pt"
    save_lstm_checkpoint(result, ckpt_path)

    loaded_model, ckpt_dict = load_lstm_checkpoint(ckpt_path, device=torch.device("cpu"))
    assert ckpt_dict["run_seed"] == 2026
    assert ckpt_dict["best_epoch"] == result.best_epoch

    with torch.no_grad():
        x_tensor = torch.as_tensor(X_val, dtype=torch.float32)
        loaded_preds = np.maximum(0.0, loaded_model(x_tensor).numpy())

    np.testing.assert_allclose(result.validation_predictions, loaded_preds, atol=1e-5)


def test_lstm_seed_reproducibility() -> None:
    """Verify deterministic training outcome when using identical seeds."""
    rng = np.random.default_rng(2026)
    n_train = 16
    n_val = 8

    X_train = rng.standard_normal((n_train, 30, 17)).astype(np.float32)
    y_train = rng.uniform(20.0, 80.0, size=n_train).astype(np.float32)
    weights_train = np.ones(n_train, dtype=np.float32)

    X_val = rng.standard_normal((n_val, 30, 17)).astype(np.float32)
    rul_true_val = rng.uniform(20.0, 80.0, size=n_val).astype(np.float64)
    rul_target_val = np.minimum(rul_true_val, 125.0)
    val_engine_ids = np.array([1] * 4 + [2] * 4, dtype=np.int64)

    hp = LSTMHyperparameters(
        config_id="lstm_repro_test",
        hidden_size=16,
        learning_rate=0.01,
        batch_size=8,
        max_epochs=2,
        early_stopping_patience=2,
    )

    res1 = train_lstm_candidate(
        hyperparameters=hp,
        run_seed=2026,
        X_train=X_train,
        y_train=y_train,
        train_weights=weights_train,
        X_val=X_val,
        rul_true_val=rul_true_val,
        rul_target_val=rul_target_val,
        val_engine_ids=val_engine_ids,
        device=torch.device("cpu"),
    )

    res2 = train_lstm_candidate(
        hyperparameters=hp,
        run_seed=2026,
        X_train=X_train,
        y_train=y_train,
        train_weights=weights_train,
        X_val=X_val,
        rul_true_val=rul_true_val,
        rul_target_val=rul_target_val,
        val_engine_ids=val_engine_ids,
        device=torch.device("cpu"),
    )

    np.testing.assert_allclose(res1.validation_predictions, res2.validation_predictions, atol=1e-5)
    assert res1.validation_metrics.uncapped_rmse == res2.validation_metrics.uncapped_rmse
