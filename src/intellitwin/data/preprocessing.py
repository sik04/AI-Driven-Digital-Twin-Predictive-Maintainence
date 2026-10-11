"""Deterministic C-MAPSS preprocessing, regime assignment, and feature scaling.

Implements strict training-only parameter fitting:
- Global setting standard scaling
- FD001: Global sensor scaling, constant regime metadata ("C1")
- FD002/FD004: Standardized-setting K-means (k=6), canonical centroid ordering (C1..C6),
  nearest-centroid assignment with lower-index tie breaking, and regime-specific
  sensor normalization.
"""

from dataclasses import dataclass
from typing import Any, Final

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from intellitwin.data.schema import (
    FEATURE_COLUMNS,
    SENSOR_COLUMNS,
    SETTING_COLUMNS,
)

PROTOCOL_VERSION: Final[str] = "step07-data-v1"
CANONICAL_REGIMES: Final[tuple[str, ...]] = ("C1", "C2", "C3", "C4", "C5", "C6")


def _compute_column_stats(
    arr: np.ndarray[Any, Any],
) -> tuple[float, float, float, bool]:
    """Compute mean, population variance (ddof=0), effective scale, and zero-variance flag.

    Parameters
    ----------
    arr : np.ndarray
        1D float64 array of observations.

    Returns
    -------
    tuple of (mean, variance, effective_scale, is_zero_variance)
    """
    if len(arr) == 0:
        raise ValueError("Cannot compute statistics on empty array.")

    mean_val = float(np.mean(arr))
    var_val = float(np.var(arr, ddof=0))
    std_val = float(np.sqrt(var_val))

    if std_val == 0.0:
        effective_scale = 1.0
        is_zero_variance = True
    else:
        effective_scale = std_val
        is_zero_variance = False

    return mean_val, var_val, effective_scale, is_zero_variance


@dataclass(frozen=True)
class ScalerParams:
    """Mean and scale parameters for a single feature."""

    mean: float
    variance: float
    effective_scale: float
    is_zero_variance: bool

    def transform(self, values: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
        """Standardize values with frozen parameters."""
        z = (values - self.mean) / self.effective_scale
        if not np.all(np.isfinite(z)):
            raise ValueError("Transformed values contain non-finite elements.")
        return z


@dataclass(frozen=True)
class FittedPreprocessor:
    """Typed representation of a frozen preprocessor fitted on training engines."""

    dataset: str
    feature_order: tuple[str, ...]
    setting_scalers: dict[str, ScalerParams]
    regime_mode: str  # "single_condition" or "kmeans_6"
    kmeans_config: dict[str, Any] | None
    canonical_standardized_centroids: list[list[float]] | None  # 6x3
    canonical_unscaled_centroids: list[list[float]] | None  # 6x3
    original_cluster_to_canonical_mapping: dict[int, str] | None
    training_cluster_counts: dict[str, int] | None
    sensor_scalers_by_regime: dict[str, dict[str, ScalerParams]]
    protocol_version: str = PROTOCOL_VERSION

    def assign_regime(
        self, setting_values: np.ndarray[Any, Any]
    ) -> tuple[list[str], np.ndarray[Any, Any]]:
        """Assign canonical regime labels to standardized setting rows.

        Parameters
        ----------
        setting_values : np.ndarray
            Shape (N, 3), standardized setting columns in order (setting1, setting2, setting3).

        Returns
        -------
        tuple of (list[str] canonical_labels, np.ndarray regime_indices)
        """
        if self.regime_mode == "single_condition":
            labels = ["C1"] * len(setting_values)
            indices = np.zeros(len(setting_values), dtype=np.int64)
            return labels, indices

        if self.canonical_standardized_centroids is None:
            raise ValueError("Canonical centroids missing for multi-regime preprocessor.")

        centroids = np.array(self.canonical_standardized_centroids, dtype=np.float64)  # (6, 3)
        # Compute squared Euclidean distances: shape (N, 6)
        # diff: (N, 1, 3) - (1, 6, 3) -> (N, 6, 3)
        diff = setting_values[:, np.newaxis, :] - centroids[np.newaxis, :, :]
        sq_dist = np.sum(diff**2, axis=2)  # (N, 6)

        # argmin over axis 1 breaks ties on smallest canonical index (C1 over C2, etc.)
        nearest_indices = np.argmin(sq_dist, axis=1)
        labels = [f"C{idx + 1}" for idx in nearest_indices]
        return labels, nearest_indices

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform a C-MAPSS DataFrame using frozen parameters.

        Preserves unit, cycle, and row order.
        Adds 'regime' column.
        Standardizes FEATURE_COLUMNS in exact frozen order.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing unit, cycle, and FEATURE_COLUMNS.

        Returns
        -------
        pd.DataFrame
            Transformed DataFrame with standardized features and assigned regimes.
        """
        for req_col in ("unit", "cycle") + FEATURE_COLUMNS:
            if req_col not in df.columns:
                raise ValueError(f"Required column '{req_col}' missing from DataFrame.")

        n_rows = len(df)
        out_df = pd.DataFrame(index=df.index)
        out_df["unit"] = df["unit"].astype(int).values
        out_df["cycle"] = df["cycle"].astype(int).values

        # Standardize settings globally
        std_settings = np.empty((n_rows, len(SETTING_COLUMNS)), dtype=np.float64)
        for j, col in enumerate(SETTING_COLUMNS):
            col_vals = df[col].to_numpy(dtype=np.float64)
            scaler = self.setting_scalers[col]
            std_settings[:, j] = scaler.transform(col_vals)
            out_df[col] = std_settings[:, j]

        # Assign regimes
        regime_labels, _ = self.assign_regime(std_settings)
        out_df["regime"] = regime_labels

        # Standardize sensors by regime (vectorized)
        regime_labels_arr = np.array(regime_labels)
        raw_sensor_mat = df[list(SENSOR_COLUMNS)].to_numpy(dtype=np.float64)
        std_sensors = np.empty((n_rows, len(SENSOR_COLUMNS)), dtype=np.float64)

        for reg_label, reg_scalers in self.sensor_scalers_by_regime.items():
            mask = regime_labels_arr == reg_label
            if not np.any(mask):
                continue
            for j, sensor_col in enumerate(SENSOR_COLUMNS):
                scaler = reg_scalers[sensor_col]
                std_sensors[mask, j] = scaler.transform(raw_sensor_mat[mask, j])

        # Verify all rows were processed
        unassigned_mask = np.isin(
            regime_labels_arr, list(self.sensor_scalers_by_regime.keys()), invert=True
        )
        if np.any(unassigned_mask):
            raise ValueError("Some rows were assigned regimes with missing sensor scalers.")

        for j, sensor_col in enumerate(SENSOR_COLUMNS):
            out_df[sensor_col] = std_sensors[:, j]

        # Verify no non-finite values in features
        feature_mat = out_df[list(FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
        if not np.all(np.isfinite(feature_mat)):
            raise ValueError("Transformed features contain non-finite numbers.")

        return out_df


def fit_preprocessor(
    df_train: pd.DataFrame,
    dataset_name: str,
) -> FittedPreprocessor:
    """Fit preprocessor strictly on training engine data.

    Parameters
    ----------
    df_train : pd.DataFrame
        Training data containing unit, cycle, and FEATURE_COLUMNS.
    dataset_name : str
        Dataset identifier ("FD001", "FD002", or "FD004").

    Returns
    -------
    FittedPreprocessor
        Frozen fitted preprocessor.
    """
    if len(df_train) == 0:
        raise ValueError(f"Cannot fit preprocessor on empty training data for '{dataset_name}'.")

    # Ensure deterministic row sorting by (unit, cycle) before fitting
    df_train_sorted = df_train.sort_values(by=["unit", "cycle"]).reset_index(drop=True)

    # 1. Fit global setting scalers on training rows
    setting_scalers: dict[str, ScalerParams] = {}
    for col in SETTING_COLUMNS:
        vals = df_train_sorted[col].to_numpy(dtype=np.float64)
        m, v, s, z = _compute_column_stats(vals)
        setting_scalers[col] = ScalerParams(
            mean=m, variance=v, effective_scale=s, is_zero_variance=z
        )

    # Standardize training settings
    n_train = len(df_train_sorted)
    std_settings_train = np.empty((n_train, len(SETTING_COLUMNS)), dtype=np.float64)
    for j, col in enumerate(SETTING_COLUMNS):
        std_settings_train[:, j] = setting_scalers[col].transform(
            df_train_sorted[col].to_numpy(dtype=np.float64)
        )

    if dataset_name == "FD001":
        # Single operating condition: no K-means
        regime_mode = "single_condition"
        training_regimes = ["C1"] * n_train
        cluster_counts = {"C1": n_train}

        # Global sensor normalization on training rows
        global_sensor_scalers: dict[str, ScalerParams] = {}
        for col in SENSOR_COLUMNS:
            vals = df_train_sorted[col].to_numpy(dtype=np.float64)
            m, v, s, z = _compute_column_stats(vals)
            global_sensor_scalers[col] = ScalerParams(
                mean=m, variance=v, effective_scale=s, is_zero_variance=z
            )

        sensor_scalers_by_regime = {"C1": global_sensor_scalers}

        return FittedPreprocessor(
            dataset=dataset_name,
            feature_order=FEATURE_COLUMNS,
            setting_scalers=setting_scalers,
            regime_mode=regime_mode,
            kmeans_config=None,
            canonical_standardized_centroids=None,
            canonical_unscaled_centroids=None,
            original_cluster_to_canonical_mapping=None,
            training_cluster_counts=cluster_counts,
            sensor_scalers_by_regime=sensor_scalers_by_regime,
        )

    if dataset_name in ("FD002", "FD004"):
        # Multi-regime datasets: fit K-means (k=6) strictly on standardized settings
        kmeans_kwargs: dict[str, Any] = {
            "n_clusters": 6,
            "init": "k-means++",
            "n_init": 10,
            "max_iter": 300,
            "tol": 1e-4,
            "random_state": 2026,
            "algorithm": "lloyd",
        }
        kmeans = KMeans(**kmeans_kwargs)
        kmeans.fit(std_settings_train)

        raw_centroids = kmeans.cluster_centers_  # shape (6, 3)

        # Check for duplicate centroids
        unique_centroids = np.unique(raw_centroids, axis=0)
        if len(unique_centroids) != 6:
            raise ValueError(
                f"K-means fitted duplicate centroids on '{dataset_name}': "
                f"{len(unique_centroids)} unique out of 6."
            )

        # Lexicographical sort on (setting1, setting2, setting3) coordinates
        sorted_cluster_indices = sorted(
            range(6),
            key=lambda idx: tuple(float(raw_centroids[idx, c]) for c in range(3)),
        )

        canonical_std_centroids = [
            [float(raw_centroids[idx, c]) for c in range(3)] for idx in sorted_cluster_indices
        ]

        # Inverse transform to original unscaled setting space
        # c_orig = c_std * scale + mean
        canonical_unscaled_centroids: list[list[float]] = []
        for c_std in canonical_std_centroids:
            c_orig = [
                float(
                    c_std[j] * setting_scalers[SETTING_COLUMNS[j]].effective_scale
                    + setting_scalers[SETTING_COLUMNS[j]].mean
                )
                for j in range(3)
            ]
            canonical_unscaled_centroids.append(c_orig)

        # Mapping: raw sklearn cluster index -> canonical label ("C1".."C6")
        raw_to_canonical: dict[int, str] = {}
        for rank, raw_idx in enumerate(sorted_cluster_indices):
            raw_to_canonical[raw_idx] = f"C{rank + 1}"

        # Assign training rows to canonical labels using nearest canonical centroid
        centroids_arr = np.array(canonical_std_centroids, dtype=np.float64)  # (6, 3)
        diff = std_settings_train[:, np.newaxis, :] - centroids_arr[np.newaxis, :, :]
        sq_dist = np.sum(diff**2, axis=2)
        nearest_canonical_idx = np.argmin(sq_dist, axis=1)
        training_regimes = [f"C{idx + 1}" for idx in nearest_canonical_idx]

        # Check training cluster counts
        unique_assigned, counts = np.unique(training_regimes, return_counts=True)
        cluster_counts = {f"C{k}": 0 for k in range(1, 7)}
        for u, c in zip(unique_assigned, counts, strict=True):
            cluster_counts[str(u)] = int(c)

        for reg in CANONICAL_REGIMES:
            if cluster_counts[reg] == 0:
                raise ValueError(
                    f"Training regime '{reg}' in dataset '{dataset_name}' "
                    "contains zero observations."
                )

        # Fit regime-specific sensor normalization
        sensor_scalers_by_regime = {}
        for reg in CANONICAL_REGIMES:
            reg_mask = np.array(training_regimes) == reg
            df_reg = df_train_sorted[reg_mask]
            reg_scalers: dict[str, ScalerParams] = {}
            for col in SENSOR_COLUMNS:
                vals = df_reg[col].to_numpy(dtype=np.float64)
                m, v, s, z = _compute_column_stats(vals)
                reg_scalers[col] = ScalerParams(
                    mean=m, variance=v, effective_scale=s, is_zero_variance=z
                )
            sensor_scalers_by_regime[reg] = reg_scalers

        return FittedPreprocessor(
            dataset=dataset_name,
            feature_order=FEATURE_COLUMNS,
            setting_scalers=setting_scalers,
            regime_mode="kmeans_6",
            kmeans_config=kmeans_kwargs,
            canonical_standardized_centroids=canonical_std_centroids,
            canonical_unscaled_centroids=canonical_unscaled_centroids,
            original_cluster_to_canonical_mapping=raw_to_canonical,
            training_cluster_counts=cluster_counts,
            sensor_scalers_by_regime=sensor_scalers_by_regime,
        )

    raise ValueError(f"Unsupported dataset for preprocessor fitting: '{dataset_name}'.")
