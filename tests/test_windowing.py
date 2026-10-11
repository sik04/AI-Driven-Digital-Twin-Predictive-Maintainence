"""Tests for causal sequence window construction and equal-engine sample weighting."""

from typing import Any

import numpy as np
import pandas as pd
import pytest

from intellitwin.data.schema import FEATURE_COLUMNS
from intellitwin.data.windowing import (
    compute_equal_engine_sample_weights,
    construct_windows,
)


def _make_dummy_engine(
    unit_id: int,
    num_cycles: int,
    base_val: float = 1.0,
) -> pd.DataFrame:
    """Create a dummy transformed trajectory for a single engine."""
    cycles = np.arange(1, num_cycles + 1)
    data: dict[str, np.ndarray[Any, Any]] = {
        "unit": np.full(num_cycles, unit_id, dtype=int),
        "cycle": cycles,
        "regime": np.array([f"C{(c % 6) + 1}" for c in cycles]),
    }
    for j, col in enumerate(FEATURE_COLUMNS):
        # Feature value encodes (feature_idx * 1000 + cycle) to detect any leakage
        data[col] = base_val + j * 1000.0 + cycles
    return pd.DataFrame(data)


def test_windowing_boundary_lengths() -> None:
    """Test behavior for T < 30, T == 30, and T == 31."""
    # T < 30 -> 0 windows
    df_short = _make_dummy_engine(unit_id=1, num_cycles=29)
    ds_short = construct_windows(df_short)
    assert len(ds_short) == 0

    # T == 30 -> 1 window
    df_30 = _make_dummy_engine(unit_id=1, num_cycles=30)
    ds_30 = construct_windows(df_30)
    assert len(ds_30) == 1
    assert ds_30.endpoint_cycles[0] == 30
    assert ds_30.rul_true[0] == 0.0
    assert ds_30.rul_target[0] == 0.0

    # T == 31 -> 2 windows
    df_31 = _make_dummy_engine(unit_id=1, num_cycles=31)
    ds_31 = construct_windows(df_31)
    assert len(ds_31) == 2
    assert ds_31.endpoint_cycles.tolist() == [30, 31]
    assert ds_31.rul_true.tolist() == [1.0, 0.0]


def test_window_geometry_and_flatten_for_gbr() -> None:
    """Test 3D shape (M, 30, 17) and GBR row-major flattening (M, 510)."""
    df = _make_dummy_engine(unit_id=1, num_cycles=35)
    ds = construct_windows(df)
    assert ds.X_sequence.shape == (6, 30, 17)
    assert ds.X_sequence.dtype == np.float32

    flat_gbr = ds.flatten_for_gbr()
    assert flat_gbr.shape == (6, 510)
    assert flat_gbr.dtype == np.float32

    # Check chronological ordering: first 17 values correspond to cycle t-29
    # (cycle 1 for first window)
    first_window_3d = ds.X_sequence[0]  # (30, 17)
    first_window_flat = flat_gbr[0]  # (510,)
    np.testing.assert_array_equal(first_window_flat[:17], first_window_3d[0])
    np.testing.assert_array_equal(first_window_flat[-17:], first_window_3d[-1])


def test_endpoint_metadata_and_labels() -> None:
    """Test endpoint regime, retrospective lifecycle stage, and RUL cap at 125."""
    df = _make_dummy_engine(unit_id=1, num_cycles=200)
    ds = construct_windows(df)

    # First window ends at cycle 30
    assert ds.endpoint_cycles[0] == 30
    assert ds.failure_cycles[0] == 200
    assert ds.rul_true[0] == 170.0
    assert ds.rul_target[0] == 125.0  # Capped at 125
    assert ds.lifecycle_stages[0] == "early"  # 3 * 30 = 90 <= 200

    # Mid stage window: e.g. cycle 100 -> 3 * 100 = 300 (between 200 and 400) -> mid
    idx_100 = int(np.where(ds.endpoint_cycles == 100)[0][0])
    assert ds.rul_true[idx_100] == 100.0
    assert ds.rul_target[idx_100] == 100.0
    assert ds.lifecycle_stages[idx_100] == "mid"

    # Terminal endpoint: cycle 200
    assert ds.endpoint_cycles[-1] == 200
    assert ds.rul_true[-1] == 0.0
    assert ds.rul_target[-1] == 0.0
    assert ds.lifecycle_stages[-1] == "late"


def test_anti_leakage_future_cycles_do_not_affect_current_window() -> None:
    """Anti-leakage: changing cycle t+1 must not affect window ending at t."""
    df_a = _make_dummy_engine(unit_id=1, num_cycles=50)
    df_b = df_a.copy()
    # Mutate all observations after cycle 30 in df_b
    mask_future = df_b["cycle"] > 30
    df_b.loc[mask_future, FEATURE_COLUMNS] += 9999.0

    ds_a = construct_windows(df_a)
    ds_b = construct_windows(df_b)

    # Window ending at cycle 30 (index 0) must be identical
    np.testing.assert_array_equal(ds_a.X_sequence[0], ds_b.X_sequence[0])


def test_anti_leakage_cross_engine_isolation() -> None:
    """Anti-leakage: windows must never contain observations across engines."""
    df1 = _make_dummy_engine(unit_id=1, num_cycles=30, base_val=100.0)
    df2 = _make_dummy_engine(unit_id=2, num_cycles=30, base_val=500.0)
    df_combined = pd.concat([df1, df2], ignore_index=True)

    ds = construct_windows(df_combined)
    assert len(ds) == 2
    assert ds.engine_ids[0] == 1
    assert ds.engine_ids[1] == 2
    # First window has only engine 1 data (around base 100)
    assert np.all(ds.X_sequence[0, :, 0] < 300.0)
    # Second window has only engine 2 data (around base 500)
    assert np.all(ds.X_sequence[1, :, 0] >= 500.0)


def test_equal_engine_sample_weights_formula_and_invariants() -> None:
    """Test sample weight computation: w_{i,t} = M / (N * n_i)."""
    # 3 engines: engine 1 has 10 windows, engine 2 has 20 windows, engine 3 has 30 windows
    # Total windows M = 60, N = 3
    # M / N = 20
    # Engine 1 weight per window: 20 / 10 = 2.0
    # Engine 2 weight per window: 20 / 20 = 1.0
    # Engine 3 weight per window: 20 / 30 = 2/3
    engine_ids = ([1] * 10) + ([2] * 20) + ([3] * 30)
    weights = compute_equal_engine_sample_weights(engine_ids)

    assert len(weights) == 60
    assert np.allclose(weights[:10], 2.0)
    assert np.allclose(weights[10:30], 1.0)
    assert np.allclose(weights[30:], 20.0 / 30.0)

    # Equal total weight per engine
    assert np.isclose(np.sum(weights[:10]), 20.0)
    assert np.isclose(np.sum(weights[10:30]), 20.0)
    assert np.isclose(np.sum(weights[30:]), 20.0)

    # Mean weight is exactly 1.0
    assert np.isclose(np.mean(weights), 1.0)


def test_equal_engine_sample_weights_invalid_inputs() -> None:
    """Test sample weight error handling for empty or non-positive engine IDs."""
    with pytest.raises(ValueError, match="empty dataset"):
        compute_equal_engine_sample_weights([])

    with pytest.raises(ValueError, match="positive integers"):
        compute_equal_engine_sample_weights([1, 2, -1])
