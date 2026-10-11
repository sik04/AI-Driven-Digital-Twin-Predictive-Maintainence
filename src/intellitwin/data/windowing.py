"""Causal sequence window construction, label derivation, and sample weighting.

Implements:
- Fixed 30-cycle causal lookback with stride 1 and strictly zero padding.
- Isolation across engines (zero cross-engine windows).
- Explicit anti-leakage: window ending at t contains only observations <= t.
- Endpoint-based metadata (regime at cycle t, retrospective lifecycle stage).
- Uncapped rul_true and 125-cycle capped rul_target.
- Flattening for GBR into row-major 510-element vectors.
- Equal-engine sample weighting: w_{i,t} = M / (N * n_i).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.schema import (
    FEATURE_COLUMNS,
    FLATTENED_FEATURE_DIM,
    LOOKBACK,
    RUL_CAP,
    get_lifecycle_stage,
)


@dataclass(frozen=True)
class WindowDataset:
    """Typed container for causal sequence windows and associated target/metadata arrays."""

    X_sequence: np.ndarray[Any, Any]  # Shape: (M, 30, 17), float32
    engine_ids: np.ndarray[Any, Any]  # Shape: (M,), int64
    endpoint_cycles: np.ndarray[Any, Any]  # Shape: (M,), int64
    failure_cycles: np.ndarray[Any, Any]  # Shape: (M,), int64
    rul_true: np.ndarray[Any, Any]  # Shape: (M,), float64
    rul_target: np.ndarray[Any, Any]  # Shape: (M,), float64
    regimes: np.ndarray[Any, Any]  # Shape: (M,), object (str)
    lifecycle_stages: np.ndarray[Any, Any]  # Shape: (M,), object (str)

    def __post_init__(self) -> None:
        """Validate array dimensions and data types."""
        m = len(self.X_sequence)
        if m == 0:
            if len(self.engine_ids) != 0:
                raise ValueError("X_sequence is empty but engine_ids is not.")
            return

        if self.X_sequence.ndim != 3 or self.X_sequence.shape[1:] != (
            LOOKBACK,
            len(FEATURE_COLUMNS),
        ):
            raise ValueError(
                f"X_sequence has shape {self.X_sequence.shape}, "
                f"expected (M, {LOOKBACK}, {len(FEATURE_COLUMNS)})."
            )

        if self.X_sequence.dtype != np.float32:
            raise ValueError(f"X_sequence must have dtype float32, got {self.X_sequence.dtype}.")

        for name, arr in (
            ("engine_ids", self.engine_ids),
            ("endpoint_cycles", self.endpoint_cycles),
            ("failure_cycles", self.failure_cycles),
            ("rul_true", self.rul_true),
            ("rul_target", self.rul_target),
            ("regimes", self.regimes),
            ("lifecycle_stages", self.lifecycle_stages),
        ):
            if len(arr) != m:
                raise ValueError(
                    f"Array '{name}' length ({len(arr)}) does not match X_sequence length ({m})."
                )

    def __len__(self) -> int:
        return len(self.X_sequence)

    def flatten_for_gbr(self) -> np.ndarray[Any, Any]:
        """Flatten 3D sequences into 2D row-major arrays of shape (M, 510) for GBR.

        Order:
        cycle t-29 (all 17 features), cycle t-28 (all 17 features), ..., cycle t (all 17 features).

        Returns
        -------
        np.ndarray
            Shape (M, 510), float32.
        """
        if len(self.X_sequence) == 0:
            return np.empty((0, FLATTENED_FEATURE_DIM), dtype=np.float32)

        # Standard C-order reshape maintains (time, feature) row-major ordering without transpose
        flat = self.X_sequence.reshape(len(self.X_sequence), FLATTENED_FEATURE_DIM)
        return flat


def construct_windows(
    df_transformed: pd.DataFrame,
) -> WindowDataset:
    """Construct causal 30-cycle lookback sequence windows per engine.

    Parameters
    ----------
    df_transformed : pd.DataFrame
        Transformed DataFrame containing unit, cycle, regime, and normalized FEATURE_COLUMNS.

    Returns
    -------
    WindowDataset
        Dataset of valid causal windows and associated metadata.
    """
    for col in ("unit", "cycle", "regime") + FEATURE_COLUMNS:
        if col not in df_transformed.columns:
            raise ValueError(f"Required column '{col}' missing from transformed DataFrame.")

    x_list: list[np.ndarray[Any, Any]] = []
    unit_list: list[int] = []
    endpoint_list: list[int] = []
    failure_list: list[int] = []
    rul_true_list: list[float] = []
    rul_target_list: list[float] = []
    regime_list: list[str] = []
    stage_list: list[str] = []

    # Process each engine independently to guarantee zero cross-engine leakage
    for unit_id, group in df_transformed.groupby("unit", sort=False):
        group_sorted = group.sort_values(by="cycle").reset_index(drop=True)
        cycles = group_sorted["cycle"].to_numpy(dtype=np.int64)
        t_max = int(cycles[-1])
        t_min = int(cycles[0])

        if t_min != 1:
            raise ValueError(f"Engine {unit_id} trajectory does not start at cycle 1.")

        # Check consecutively
        if len(cycles) != t_max:
            raise ValueError(
                f"Engine {unit_id} has {len(cycles)} rows but max cycle is {t_max} (gap detected)."
            )

        if t_max < LOOKBACK:
            # Fewer than lookback cycles: 0 windows
            continue

        feat_mat = group_sorted[list(FEATURE_COLUMNS)].to_numpy(dtype=np.float32)
        regimes = group_sorted["regime"].to_numpy()

        # Endpoints t in [LOOKBACK, t_max]
        for t in range(LOOKBACK, t_max + 1):
            # 0-based indexing: cycle t is at index t-1. Window [t-LOOKBACK : t]
            start_idx = t - LOOKBACK
            end_idx = t
            win = feat_mat[start_idx:end_idx]  # Shape: (30, 17)

            x_list.append(win)
            unit_list.append(int(unit_id))
            endpoint_list.append(t)
            failure_list.append(t_max)

            rul_t = float(t_max - t)
            rul_tgt = float(min(rul_t, float(RUL_CAP)))
            rul_true_list.append(rul_t)
            rul_target_list.append(rul_tgt)

            endpoint_regime = str(regimes[t - 1])
            regime_list.append(endpoint_regime)

            stage = get_lifecycle_stage(cycle=t, failure_cycle=t_max)
            stage_list.append(stage)

    if len(x_list) == 0:
        return WindowDataset(
            X_sequence=np.empty((0, LOOKBACK, len(FEATURE_COLUMNS)), dtype=np.float32),
            engine_ids=np.empty(0, dtype=np.int64),
            endpoint_cycles=np.empty(0, dtype=np.int64),
            failure_cycles=np.empty(0, dtype=np.int64),
            rul_true=np.empty(0, dtype=np.float64),
            rul_target=np.empty(0, dtype=np.float64),
            regimes=np.empty(0, dtype=object),
            lifecycle_stages=np.empty(0, dtype=object),
        )

    return WindowDataset(
        X_sequence=np.array(x_list, dtype=np.float32),
        engine_ids=np.array(unit_list, dtype=np.int64),
        endpoint_cycles=np.array(endpoint_list, dtype=np.int64),
        failure_cycles=np.array(failure_list, dtype=np.int64),
        rul_true=np.array(rul_true_list, dtype=np.float64),
        rul_target=np.array(rul_target_list, dtype=np.float64),
        regimes=np.array(regime_list, dtype=object),
        lifecycle_stages=np.array(stage_list, dtype=object),
    )


def compute_equal_engine_sample_weights(
    engine_ids: np.ndarray[Any, Any] | Sequence[int],
) -> np.ndarray[Any, Any]:
    """Compute equal-engine training sample weights: w_{i,t} = M / (N * n_i).

    Parameters
    ----------
    engine_ids : np.ndarray or Sequence[int]
        Engine ID for each window in the training WindowDataset. Length M.

    Returns
    -------
    np.ndarray
        Shape (M,), dtype float64. Sample weights.

    Raises
    ------
    ValueError
        If engine_ids is empty or contains non-positive values.
    """
    arr = np.asarray(engine_ids, dtype=np.int64)
    m = len(arr)
    if m == 0:
        raise ValueError("Cannot compute sample weights for an empty dataset.")

    if (arr <= 0).any():
        raise ValueError("Engine IDs must be positive integers.")

    unique_engines, counts = np.unique(arr, return_counts=True)
    n = len(unique_engines)
    engine_count_map = dict(zip(unique_engines, counts, strict=True))

    # Compute weights: w_{i,t} = M / (N * n_i)
    weights = np.empty(m, dtype=np.float64)
    for idx, eid in enumerate(arr):
        n_i = engine_count_map[eid]
        weights[idx] = m / (n * n_i)

    # Invariant validations
    # 1. Total weight for every engine must equal M / N
    expected_engine_mass = m / n
    for eid in unique_engines:
        engine_mask = arr == eid
        sum_w = float(np.sum(weights[engine_mask]))
        if abs(sum_w - expected_engine_mass) > 1e-6:
            raise ValueError(
                f"Weight sum for engine {eid} is {sum_w:.8f}, expected {expected_engine_mass:.8f}."
            )

    # 2. Mean of all weights must equal 1.0
    mean_w = float(np.mean(weights))
    if abs(mean_w - 1.0) > 1e-6:
        raise ValueError(f"Mean sample weight is {mean_w:.8f}, expected 1.0.")

    return weights
