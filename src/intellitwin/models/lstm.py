"""Single-layer unidirectional LSTM for point-RUL prediction.

Implements the frozen LSTM base predictor specification from ADR-019 / Step 7.1:
- Input shape: (batch_size, 30, 17), float32.
- Architecture:
    nn.LSTM(input_size=17, hidden_size=H, num_layers=1, batch_first=True,
            bidirectional=False, bias=True, dropout=0.0)
    Slice final sequence step: lstm_out[:, -1, :] -> (batch_size, H)
    nn.Dropout(p=0.20)
    nn.Linear(hidden_size, 1) -> (batch_size,)
- Fixed training configuration:
    optimizer = AdamW(weight_decay=1e-4, betas=(0.9, 0.999), eps=1e-8)
    batch_size = 256
    max_epochs = 100
    gradient_clip_norm = 1.0
    explicit_dropout = 0.20
    early_stopping_patience = 10
    early_stopping_min_delta = 0.01 cycles
- Tunable hyperparameters (4 configurations):
    hidden_size in [32, 64]
    learning_rate in [0.0003, 0.001]
- Training loss:
    Equal-engine-weighted squared error normalized by batch weight sum:
    loss = sum(w_j * (pred_j - rul_target_j)^2) / sum(w_j)
- Validation early stopping:
    Evaluates frozen validation engines after every epoch using uncapped-RUL RMSE.
    Restores best checkpoint state upon completion.
"""

import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from intellitwin.models.metrics import ModelEvaluationMetrics, compute_model_metrics
from intellitwin.models.reproducibility import resolve_device, set_global_seed


@dataclass(frozen=True)
class LSTMHyperparameters:
    """Hyperparameter specification for LSTM base predictor."""

    config_id: str
    hidden_size: int
    learning_rate: float
    input_size: int = 17
    lookback: int = 30
    num_layers: int = 1
    bidirectional: bool = False
    bias: bool = True
    dropout: float = 0.0
    explicit_dropout: float = 0.20
    weight_decay: float = 1e-4
    betas: tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    batch_size: int = 256
    max_epochs: int = 100
    gradient_clip_norm: float = 1.0
    early_stopping_patience: int = 10
    early_stopping_min_delta: float = 0.01

    def to_dict(self) -> dict[str, Any]:
        """Convert hyperparameters to dictionary."""
        d = asdict(self)
        d["betas"] = list(self.betas)
        return d


# Exactly 4 deterministic configurations
LSTM_GRID: tuple[LSTMHyperparameters, ...] = (
    LSTMHyperparameters(
        config_id="lstm_h32_lr0003",
        hidden_size=32,
        learning_rate=0.0003,
    ),
    LSTMHyperparameters(
        config_id="lstm_h32_lr0010",
        hidden_size=32,
        learning_rate=0.0010,
    ),
    LSTMHyperparameters(
        config_id="lstm_h64_lr0003",
        hidden_size=64,
        learning_rate=0.0003,
    ),
    LSTMHyperparameters(
        config_id="lstm_h64_lr0010",
        hidden_size=64,
        learning_rate=0.0010,
    ),
)


def get_lstm_grid() -> list[LSTMHyperparameters]:
    """Return the frozen 4-configuration LSTM hyperparameter search grid."""
    return list(LSTM_GRID)


class LSTMPointPredictor(nn.Module):
    """Single-layer unidirectional LSTM point-RUL predictor."""

    def __init__(self, hidden_size: int, explicit_dropout: float = 0.20) -> None:
        super().__init__()
        self.hidden_size = hidden_size
        self.lstm = nn.LSTM(
            input_size=17,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=False,
            bias=True,
            dropout=0.0,
        )
        self.dropout = nn.Dropout(p=explicit_dropout)
        self.linear = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Parameters
        ----------
        x : torch.Tensor of shape (batch_size, 30, 17)

        Returns
        -------
        torch.Tensor of shape (batch_size,)
        """
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]  # Shape: (batch_size, hidden_size)
        dropped = self.dropout(last_step)
        out = self.linear(dropped)  # Shape: (batch_size, 1)
        return cast(torch.Tensor, out.squeeze(-1))  # Shape: (batch_size,)


class SequenceDataset(Dataset[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]):
    """Simple PyTorch Dataset for sequences, targets, and sample weights."""

    def __init__(
        self,
        X: np.ndarray[Any, Any],
        y: np.ndarray[Any, Any] | Sequence[float],
        weights: np.ndarray[Any, Any] | Sequence[float],
    ) -> None:
        self.X = torch.as_tensor(X, dtype=torch.float32)
        self.y = torch.as_tensor(y, dtype=torch.float32)
        self.weights = torch.as_tensor(weights, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx], self.weights[idx]


@dataclass(frozen=True)
class LSTMTrainingResult:
    """Outcome of LSTM model training."""

    model: LSTMPointPredictor
    hyperparameters: LSTMHyperparameters
    run_seed: int
    best_epoch: int
    epochs_completed: int
    training_duration_seconds: float
    validation_metrics: ModelEvaluationMetrics
    validation_predictions: np.ndarray[Any, Any]


def train_lstm_candidate(
    hyperparameters: LSTMHyperparameters,
    run_seed: int,
    X_train: np.ndarray[Any, Any],
    y_train: np.ndarray[Any, Any],
    train_weights: np.ndarray[Any, Any],
    X_val: np.ndarray[Any, Any],
    rul_true_val: np.ndarray[Any, Any],
    rul_target_val: np.ndarray[Any, Any],
    val_engine_ids: np.ndarray[Any, Any],
    device: torch.device | None = None,
) -> LSTMTrainingResult:
    """Train single LSTM candidate configuration with frozen validation early stopping.

    Parameters
    ----------
    hyperparameters : LSTMHyperparameters
        Model and training configuration.
    run_seed : int
        Deterministic random seed.
    X_train : np.ndarray
        Training causal sequences of shape (N_train, 30, 17).
    y_train : np.ndarray
        Training targets (capped at 125 cycles).
    train_weights : np.ndarray
        Equal-engine training sample weights.
    X_val : np.ndarray
        Validation causal sequences of shape (N_val, 30, 17).
    rul_true_val : np.ndarray
        Uncapped validation true RUL.
    rul_target_val : np.ndarray
        Capped validation targets.
    val_engine_ids : np.ndarray
        Validation engine IDs.
    device : torch.device, optional
        Target device (defaults to resolve_device()).

    Returns
    -------
    LSTMTrainingResult
        Restored best model, metrics, and training provenance.
    """
    set_global_seed(run_seed)
    if device is None:
        device = resolve_device()

    start_time = time.perf_counter()

    # Instantiate model
    model = LSTMPointPredictor(
        hidden_size=hyperparameters.hidden_size,
        explicit_dropout=hyperparameters.explicit_dropout,
    ).to(device)

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=hyperparameters.learning_rate,
        betas=hyperparameters.betas,
        eps=hyperparameters.eps,
        weight_decay=hyperparameters.weight_decay,
    )

    # Data loaders
    train_dataset = SequenceDataset(X_train, y_train, train_weights)
    generator = torch.Generator()
    generator.manual_seed(run_seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=hyperparameters.batch_size,
        shuffle=True,
        generator=generator,
    )

    val_dataset = SequenceDataset(
        X_val,
        rul_target_val,
        np.ones(len(X_val), dtype=np.float32),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=hyperparameters.batch_size,
        shuffle=False,
    )

    # Early stopping state
    best_val_rmse: float = float("inf")
    best_epoch: int = 1
    best_state_dict: dict[str, torch.Tensor] = {
        k: v.cpu().clone() for k, v in model.state_dict().items()
    }
    patience_counter: int = 0
    epochs_completed: int = 0

    for epoch in range(1, hyperparameters.max_epochs + 1):
        epochs_completed = epoch
        model.train()

        for batch_x, batch_y, batch_w in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            batch_w = batch_w.to(device)

            optimizer.zero_grad()
            preds = model(batch_x)

            # Equal-engine-weighted squared error normalized by batch weight mass
            sq_err = (preds - batch_y) ** 2
            loss = torch.sum(batch_w * sq_err) / torch.sum(batch_w)

            loss.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=hyperparameters.gradient_clip_norm,
            )
            optimizer.step()

        # Validation evaluation
        model.eval()
        val_preds_list: list[np.ndarray[Any, Any]] = []
        with torch.no_grad():
            for batch_vx, _, _ in val_loader:
                batch_vx = batch_vx.to(device)
                v_out = model(batch_vx)
                val_preds_list.append(v_out.cpu().numpy())

        raw_val_preds = np.concatenate(val_preds_list, axis=0)
        # Non-negative truncation post-processing: max(0.0, raw)
        clipped_val_preds = np.maximum(0.0, raw_val_preds)

        current_metrics = compute_model_metrics(
            predictions=clipped_val_preds,
            rul_true=rul_true_val,
            rul_target=rul_target_val,
            engine_ids=val_engine_ids,
        )
        current_rmse = current_metrics.uncapped_rmse

        # Check early stopping improvement (at least min_delta improvement)
        if current_rmse <= best_val_rmse - hyperparameters.early_stopping_min_delta:
            best_val_rmse = current_rmse
            best_epoch = epoch
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= hyperparameters.early_stopping_patience:
                break

    # Restore best checkpoint state
    model.load_state_dict(best_state_dict)
    model.eval()

    # Compute final validation predictions using restored best checkpoint
    final_preds_list: list[np.ndarray[Any, Any]] = []
    with torch.no_grad():
        for batch_vx, _, _ in val_loader:
            batch_vx = batch_vx.to(device)
            v_out = model(batch_vx)
            final_preds_list.append(v_out.cpu().numpy())

    final_raw_preds = np.concatenate(final_preds_list, axis=0)
    final_val_preds = np.maximum(0.0, final_raw_preds)

    final_metrics = compute_model_metrics(
        predictions=final_val_preds,
        rul_true=rul_true_val,
        rul_target=rul_target_val,
        engine_ids=val_engine_ids,
    )

    duration = time.perf_counter() - start_time

    return LSTMTrainingResult(
        model=model,
        hyperparameters=hyperparameters,
        run_seed=run_seed,
        best_epoch=best_epoch,
        epochs_completed=epochs_completed,
        training_duration_seconds=duration,
        validation_metrics=final_metrics,
        validation_predictions=final_val_preds,
    )


def save_lstm_checkpoint(
    result: LSTMTrainingResult,
    filepath: Path | str,
) -> None:
    """Save CPU-loadable PyTorch checkpoint for trained LSTM candidate."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure all tensors in state_dict are on CPU
    cpu_state_dict = {k: v.cpu() for k, v in result.model.state_dict().items()}
    checkpoint = {
        "state_dict": cpu_state_dict,
        "configuration": result.hyperparameters.to_dict(),
        "run_seed": result.run_seed,
        "best_epoch": result.best_epoch,
        "epochs_completed": result.epochs_completed,
        "validation_uncapped_rmse": result.validation_metrics.uncapped_rmse,
    }
    torch.save(checkpoint, path)


def load_lstm_checkpoint(
    filepath: Path | str,
    device: torch.device | None = None,
) -> tuple[LSTMPointPredictor, dict[str, Any]]:
    """Load PyTorch checkpoint on CPU or specified device."""
    target_device = device if device is not None else torch.device("cpu")
    checkpoint = torch.load(filepath, map_location="cpu", weights_only=False)

    cfg_dict = checkpoint["configuration"]
    hidden_size = cfg_dict["hidden_size"]
    explicit_dropout = cfg_dict.get("explicit_dropout", 0.20)

    model = LSTMPointPredictor(hidden_size=hidden_size, explicit_dropout=explicit_dropout)
    model.load_state_dict(checkpoint["state_dict"])
    model.to(target_device)
    model.eval()

    return model, checkpoint
