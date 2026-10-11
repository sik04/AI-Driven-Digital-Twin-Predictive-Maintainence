"""Histogram Gradient Boosting Regressor (GBR) for point-RUL prediction.

Implements the frozen GBR base predictor specification from ADR-019 / Step 7.1.
- Wraps sklearn.ensemble.HistGradientBoostingRegressor.
- Fixed hyperparameters:
    loss="squared_error", early_stopping=False, validation_fraction=None,
    min_samples_leaf=20, max_bins=255, max_features=1.0,
    categorical_features=None, warm_start=False, max_iter=300.
- Tunable hyperparameters (8 configurations):
    learning_rate in [0.05, 0.10]
    max_leaf_nodes in [15, 31]
    l2_regularization in [0.0, 1.0]
- Sample weights passed directly during fitting.
- Output post-processing: max(0.0, raw_prediction).
"""

import pickle
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor


@dataclass(frozen=True)
class GBRHyperparameters:
    """Hyperparameter specification for GBR model."""

    config_id: str
    learning_rate: float
    max_leaf_nodes: int
    l2_regularization: float
    loss: str = "squared_error"
    early_stopping: bool = False
    validation_fraction: float | None = None
    min_samples_leaf: int = 20
    max_bins: int = 255
    max_features: float = 1.0
    categorical_features: Any = None
    warm_start: bool = False
    max_iter: int = 300

    def to_dict(self) -> dict[str, Any]:
        """Return hyperparameters dictionary."""
        return asdict(self)


# Exactly 8 deterministic configurations in canonical ordering
GBR_GRID: tuple[GBRHyperparameters, ...] = (
    GBRHyperparameters(
        config_id="gbr_lr005_leaf15_l2_0",
        learning_rate=0.05,
        max_leaf_nodes=15,
        l2_regularization=0.0,
    ),
    GBRHyperparameters(
        config_id="gbr_lr005_leaf15_l2_1",
        learning_rate=0.05,
        max_leaf_nodes=15,
        l2_regularization=1.0,
    ),
    GBRHyperparameters(
        config_id="gbr_lr005_leaf31_l2_0",
        learning_rate=0.05,
        max_leaf_nodes=31,
        l2_regularization=0.0,
    ),
    GBRHyperparameters(
        config_id="gbr_lr005_leaf31_l2_1",
        learning_rate=0.05,
        max_leaf_nodes=31,
        l2_regularization=1.0,
    ),
    GBRHyperparameters(
        config_id="gbr_lr010_leaf15_l2_0",
        learning_rate=0.10,
        max_leaf_nodes=15,
        l2_regularization=0.0,
    ),
    GBRHyperparameters(
        config_id="gbr_lr010_leaf15_l2_1",
        learning_rate=0.10,
        max_leaf_nodes=15,
        l2_regularization=1.0,
    ),
    GBRHyperparameters(
        config_id="gbr_lr010_leaf31_l2_0",
        learning_rate=0.10,
        max_leaf_nodes=31,
        l2_regularization=0.0,
    ),
    GBRHyperparameters(
        config_id="gbr_lr010_leaf31_l2_1",
        learning_rate=0.10,
        max_leaf_nodes=31,
        l2_regularization=1.0,
    ),
)


def get_gbr_grid() -> list[GBRHyperparameters]:
    """Return the frozen 8-configuration GBR hyperparameter search grid."""
    return list(GBR_GRID)


class GBRModel:
    """HistGradientBoostingRegressor wrapper adhering to Step 7 specification."""

    def __init__(self, hyperparameters: GBRHyperparameters, run_seed: int) -> None:
        self.hyperparameters = hyperparameters
        self.run_seed = run_seed
        self._estimator: HistGradientBoostingRegressor = HistGradientBoostingRegressor(
            loss=self.hyperparameters.loss,
            learning_rate=self.hyperparameters.learning_rate,
            max_iter=self.hyperparameters.max_iter,
            max_leaf_nodes=self.hyperparameters.max_leaf_nodes,
            min_samples_leaf=self.hyperparameters.min_samples_leaf,
            l2_regularization=self.hyperparameters.l2_regularization,
            max_bins=self.hyperparameters.max_bins,
            categorical_features=self.hyperparameters.categorical_features,
            warm_start=self.hyperparameters.warm_start,
            early_stopping=self.hyperparameters.early_stopping,
            validation_fraction=self.hyperparameters.validation_fraction,
            max_features=self.hyperparameters.max_features,
            random_state=self.run_seed,
        )
        self._is_fitted: bool = False

    @property
    def is_fitted(self) -> bool:
        """Whether the model has been fitted."""
        return self._is_fitted

    def fit(
        self,
        X: np.ndarray[Any, Any],
        y: np.ndarray[Any, Any] | Sequence[float],
        sample_weight: np.ndarray[Any, Any] | Sequence[float] | None = None,
    ) -> "GBRModel":
        """Fit HistGradientBoostingRegressor on flattened causal windows.

        Parameters
        ----------
        X : np.ndarray of shape (M, 510)
            Flattened causal sequence windows.
        y : array-like of shape (M,)
            Supervised training targets (rul_target capped at 125).
        sample_weight : array-like of shape (M,), optional
            Equal-engine training sample weights.

        Returns
        -------
        GBRModel
            Fitted instance.
        """
        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.asarray(y, dtype=np.float64).ravel()

        if X_arr.ndim != 2:
            raise ValueError(f"X must be 2D array of shape (M, 510), got {X_arr.shape}")

        if len(X_arr) != len(y_arr):
            raise ValueError(
                f"Length mismatch: X has {len(X_arr)} samples, y has {len(y_arr)} samples"
            )

        weights_arr = (
            np.asarray(sample_weight, dtype=np.float64).ravel()
            if sample_weight is not None
            else None
        )
        if weights_arr is not None and len(weights_arr) != len(y_arr):
            raise ValueError(
                f"sample_weight length ({len(weights_arr)}) does not match y ({len(y_arr)})"
            )

        self._estimator.fit(X_arr, y_arr, sample_weight=weights_arr)
        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
        """Predict RUL with non-negative truncation post-processing.

        Parameters
        ----------
        X : np.ndarray of shape (M, 510)
            Flattened causal sequence windows.

        Returns
        -------
        np.ndarray of shape (M,)
            Predicted RUL values truncated at 0.0 (max(0.0, raw_prediction)).
            Values are NOT capped at 125.
        """
        if not self._is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before predict().")

        X_arr = np.asarray(X, dtype=np.float32)
        if X_arr.ndim != 2:
            raise ValueError(f"X must be 2D array of shape (M, 510), got {X_arr.shape}")

        raw_preds: np.ndarray[Any, Any] = self._estimator.predict(X_arr)
        # Non-negative truncation post-processing: prediction = max(0.0, raw_prediction)
        clipped_preds: np.ndarray[Any, Any] = np.maximum(0.0, raw_preds)
        return clipped_preds

    def save(self, filepath: str) -> None:
        """Serialize model to disk."""
        data = {
            "hyperparameters": self.hyperparameters,
            "run_seed": self.run_seed,
            "estimator": self._estimator,
            "is_fitted": self._is_fitted,
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f, protocol=5)

    @classmethod
    def load(cls, filepath: str) -> "GBRModel":
        """Deserialize model from disk."""
        with open(filepath, "rb") as f:
            data = pickle.load(f)  # noqa: S301
        instance = cls(hyperparameters=data["hyperparameters"], run_seed=data["run_seed"])
        instance._estimator = data["estimator"]
        instance._is_fitted = data["is_fitted"]
        return instance
