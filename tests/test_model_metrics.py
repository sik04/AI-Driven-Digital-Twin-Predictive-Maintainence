"""Unit tests for model evaluation metrics.

Verifies:
- Equal-engine-weighted RMSE formula.
- RMSE is sqrt(mean(engine_MSE)), NOT mean(engine_RMSE).
- Equal-engine-weighted MAE formula.
- Capped target RMSE formula.
- Long engine does not dominate short engine.
- Rejection of prediction length mismatch, empty arrays, NaN, inf, invalid engine IDs.
"""

import math

import numpy as np
import pytest

from intellitwin.models.metrics import ModelEvaluationMetrics, compute_model_metrics


def test_hand_computable_engine_weighted_metrics() -> None:
    """Verify metrics match exact hand-computed values across unequal engines."""
    # Engine 1: 2 windows
    # Window 1: pred=100.0, true=110.0 (err=-10, sq=100, abs=10), target=100.0 (err=0, sq=0)
    # Window 2: pred=90.0,  true=80.0  (err=+10, sq=100, abs=10), target=80.0  (err=10, sq=100)
    # Engine 1 MSE_uncapped = (100 + 100) / 2 = 100.0
    # Engine 1 MAE_uncapped = (10 + 10) / 2 = 10.0
    # Engine 1 MSE_capped   = (0 + 100) / 2 = 50.0

    # Engine 2: 1 window
    # Window 3: pred=50.0,  true=40.0  (err=+10, sq=100, abs=10), target=40.0  (err=10, sq=100)
    # Engine 2 MSE_uncapped = 100.0
    # Engine 2 MAE_uncapped = 10.0
    # Engine 2 MSE_capped   = 100.0

    # Engine-weighted aggregate:
    # Mean uncapped MSE = (100.0 + 100.0) / 2 = 100.0 -> RMSE = 10.0
    # Mean uncapped MAE = (10.0 + 10.0) / 2 = 10.0
    # Mean capped MSE   = (50.0 + 100.0) / 2 = 75.0 -> RMSE = sqrt(75.0)

    predictions = [100.0, 90.0, 50.0]
    rul_true = [110.0, 80.0, 40.0]
    rul_target = [100.0, 80.0, 40.0]
    engine_ids = [1, 1, 2]

    metrics: ModelEvaluationMetrics = compute_model_metrics(
        predictions=predictions,
        rul_true=rul_true,
        rul_target=rul_target,
        engine_ids=engine_ids,
    )

    assert metrics.engine_count == 2
    assert metrics.window_count == 3
    assert math.isclose(metrics.uncapped_rmse, 10.0, rel_tol=1e-7)
    assert math.isclose(metrics.uncapped_mae, 10.0, rel_tol=1e-7)
    assert math.isclose(metrics.capped_rmse, math.sqrt(75.0), rel_tol=1e-7)


def test_rmse_is_sqrt_of_mean_mse_not_mean_of_engine_rmse() -> None:
    """Verify that engine-weighted RMSE is sqrt(mean(MSE_i)), NOT mean(RMSE_i)."""
    # Engine 1: 1 window with sq_err = 4 (RMSE_1 = 2)
    # Engine 2: 1 window with sq_err = 16 (RMSE_2 = 4)
    # Correct formula: sqrt((4 + 16) / 2) = sqrt(10) ≈ 3.162277
    # Incorrect formula: (2 + 4) / 2 = 3.0

    predictions = [12.0, 14.0]
    rul_true = [10.0, 10.0]
    rul_target = [10.0, 10.0]
    engine_ids = [1, 2]

    metrics = compute_model_metrics(
        predictions=predictions,
        rul_true=rul_true,
        rul_target=rul_target,
        engine_ids=engine_ids,
    )

    expected_rmse = math.sqrt((4.0 + 16.0) / 2.0)
    assert math.isclose(metrics.uncapped_rmse, expected_rmse, rel_tol=1e-7)
    assert not math.isclose(metrics.uncapped_rmse, 3.0, rel_tol=1e-3)


def test_long_engine_does_not_dominate_short_engine() -> None:
    """A long engine with 100 predictions does not drown out a 1-window engine with error."""
    # Engine 1: 99 windows with zero error
    # Engine 2: 1 window with error = 10 (sq_err = 100)
    # If window-averaged: MSE = 100 / 100 = 1.0 -> RMSE = 1.0
    # If engine-weighted: MSE_1 = 0, MSE_2 = 100 -> mean MSE = 50.0 -> RMSE = sqrt(50) ≈ 7.071

    n_long = 99
    preds = [50.0] * n_long + [60.0]
    trues = [50.0] * n_long + [50.0]
    targets = [50.0] * n_long + [50.0]
    engines = [1] * n_long + [2]

    metrics = compute_model_metrics(
        predictions=preds,
        rul_true=trues,
        rul_target=targets,
        engine_ids=engines,
    )

    expected_rmse = math.sqrt(50.0)
    assert math.isclose(metrics.uncapped_rmse, expected_rmse, rel_tol=1e-6)
    # Confirms window-level pooling was NOT used
    assert not math.isclose(metrics.uncapped_rmse, 1.0, rel_tol=1e-2)


def test_metrics_rejects_empty_inputs() -> None:
    with pytest.raises(ValueError, match="empty"):
        compute_model_metrics([], [], [], [])


def test_metrics_rejects_length_mismatch() -> None:
    with pytest.raises(ValueError, match="mismatch"):
        compute_model_metrics([1.0, 2.0], [1.0], [1.0, 2.0], [1, 2])


def test_metrics_rejects_nan_prediction() -> None:
    with pytest.raises(ValueError, match="Non-finite"):
        compute_model_metrics([np.nan, 2.0], [1.0, 2.0], [1.0, 2.0], [1, 2])


def test_metrics_rejects_inf_prediction() -> None:
    with pytest.raises(ValueError, match="Non-finite"):
        compute_model_metrics([np.inf, 2.0], [1.0, 2.0], [1.0, 2.0], [1, 2])


def test_metrics_rejects_invalid_engine_ids() -> None:
    # Non-positive engine ID
    with pytest.raises(ValueError, match="Invalid engine IDs"):
        compute_model_metrics([1.0, 2.0], [1.0, 2.0], [1.0, 2.0], [0, 1])

    # Negative engine ID
    with pytest.raises(ValueError, match="Invalid engine IDs"):
        compute_model_metrics([1.0, 2.0], [1.0, 2.0], [1.0, 2.0], [-1, 2])
