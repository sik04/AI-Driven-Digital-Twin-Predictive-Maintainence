"""Evaluation metrics for point-RUL base predictors.

Implements equal-engine-weighted metrics according to ADR-019 and Step 7 specification:
- Equal-engine-weighted uncapped-RUL RMSE (primary selection metric).
- Equal-engine-weighted uncapped-RUL MAE (supporting metric).
- Equal-engine-weighted capped-target RMSE (supporting metric).

Each validation engine contributes equally regardless of its trajectory length.
Engine RMSE values are NOT averaged; instead, engine mean squared errors are averaged,
and the square root is taken.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ModelEvaluationMetrics:
    """Container for equal-engine-weighted evaluation metrics."""

    uncapped_rmse: float
    uncapped_mae: float
    capped_rmse: float
    engine_count: int
    window_count: int


def compute_model_metrics(
    predictions: np.ndarray[Any, Any] | Sequence[float],
    rul_true: np.ndarray[Any, Any] | Sequence[float],
    rul_target: np.ndarray[Any, Any] | Sequence[float],
    engine_ids: np.ndarray[Any, Any] | Sequence[int],
) -> ModelEvaluationMetrics:
    """Compute equal-engine-weighted RUL prediction evaluation metrics.

    Parameters
    ----------
    predictions : array-like of shape (N,)
        Post-processed non-negative RUL predictions.
    rul_true : array-like of shape (N,)
        Uncapped true RUL values.
    rul_target : array-like of shape (N,)
        Capped training RUL targets (e.g., min(rul_true, 125)).
    engine_ids : array-like of shape (N,)
        Engine unit IDs identifying the engine trajectory for each window.

    Returns
    -------
    ModelEvaluationMetrics
        Container with uncapped_rmse, uncapped_mae, capped_rmse, engine_count,
        and window_count.

    Raises
    ------
    ValueError
        If inputs are empty, lengths mismatch, contain non-finite values,
        or have invalid engine IDs.
    """
    preds_arr = np.asarray(predictions, dtype=np.float64).ravel()
    true_arr = np.asarray(rul_true, dtype=np.float64).ravel()
    target_arr = np.asarray(rul_target, dtype=np.float64).ravel()
    engines_arr = np.asarray(engine_ids).ravel()

    n = len(preds_arr)
    if n == 0:
        raise ValueError("Cannot compute metrics on empty predictions array.")

    if len(true_arr) != n or len(target_arr) != n or len(engines_arr) != n:
        raise ValueError(
            f"Input length mismatch: predictions ({n}), rul_true ({len(true_arr)}), "
            f"rul_target ({len(target_arr)}), engine_ids ({len(engines_arr)})."
        )

    if not np.all(np.isfinite(preds_arr)):
        raise ValueError("Non-finite values detected in predictions array.")

    if not np.all(np.isfinite(true_arr)):
        raise ValueError("Non-finite values detected in rul_true array.")

    if not np.all(np.isfinite(target_arr)):
        raise ValueError("Non-finite values detected in rul_target array.")

    # Validate engine IDs: must be valid integers > 0
    try:
        int_engines = engines_arr.astype(np.int64)
        if not np.array_equal(int_engines, engines_arr):
            raise ValueError("Engine IDs must be integer values.")
    except (ValueError, TypeError) as err:
        raise ValueError(f"Invalid engine IDs encountered: {err}") from err

    if np.any(int_engines <= 0):
        raise ValueError(
            "Invalid engine IDs encountered: all engine IDs must be positive integers."
        )

    unique_engines = np.unique(int_engines)
    num_engines = len(unique_engines)
    if num_engines == 0:
        raise ValueError("No engine IDs provided.")

    engine_mses_uncapped: list[float] = []
    engine_maes_uncapped: list[float] = []
    engine_mses_capped: list[float] = []

    for eng in unique_engines:
        mask = int_engines == eng
        eng_preds = preds_arr[mask]
        eng_true = true_arr[mask]
        eng_target = target_arr[mask]

        sq_err_uncapped = (eng_preds - eng_true) ** 2
        engine_mses_uncapped.append(float(np.mean(sq_err_uncapped)))

        abs_err_uncapped = np.abs(eng_preds - eng_true)
        engine_maes_uncapped.append(float(np.mean(abs_err_uncapped)))

        sq_err_capped = (eng_preds - eng_target) ** 2
        engine_mses_capped.append(float(np.mean(sq_err_capped)))

    uncapped_rmse = float(np.sqrt(np.mean(engine_mses_uncapped)))
    uncapped_mae = float(np.mean(engine_maes_uncapped))
    capped_rmse = float(np.sqrt(np.mean(engine_mses_capped)))

    return ModelEvaluationMetrics(
        uncapped_rmse=uncapped_rmse,
        uncapped_mae=uncapped_mae,
        capped_rmse=capped_rmse,
        engine_count=num_engines,
        window_count=n,
    )
