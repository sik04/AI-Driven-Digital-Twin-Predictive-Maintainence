"""Tests for C-MAPSS preprocessing, scaling, regime assignment, and artifact persistence."""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.artifacts import (
    load_preprocessor_artifact,
    save_preprocessor_artifact,
)
from intellitwin.data.preprocessing import (
    CANONICAL_REGIMES,
    FittedPreprocessor,
    ScalerParams,
    _compute_column_stats,
    fit_preprocessor,
)
from intellitwin.data.schema import (
    FEATURE_COLUMNS,
    SENSOR_COLUMNS,
    SETTING_COLUMNS,
)


def _make_training_df(
    n_rows: int = 120,
    regimes: int = 1,
) -> pd.DataFrame:
    """Create synthetic training DataFrame."""
    rng = np.random.RandomState(42)
    units = np.repeat(np.arange(1, 7), n_rows // 6)
    cycles = np.tile(np.arange(1, (n_rows // 6) + 1), 6)

    data: dict[str, np.ndarray[Any, Any]] = {
        "unit": units,
        "cycle": cycles,
    }

    if regimes == 1:
        # Constant setting
        data["setting1"] = np.full(n_rows, 10.0)
        data["setting2"] = np.full(n_rows, 0.2)
        data["setting3"] = np.full(n_rows, 100.0)
    else:
        # Multi-regime setting: 6 distinct well-separated operating clusters
        centers = [
            (0.0, 0.0, 100.0),
            (10.0, 0.2, 80.0),
            (20.0, 0.4, 60.0),
            (30.0, 0.6, 40.0),
            (40.0, 0.8, 20.0),
            (50.0, 1.0, 0.0),
        ]
        s1, s2, s3 = [], [], []
        for i in range(n_rows):
            c = centers[i % 6]
            s1.append(c[0] + rng.normal(0, 0.01))
            s2.append(c[1] + rng.normal(0, 0.01))
            s3.append(c[2] + rng.normal(0, 0.01))
        data["setting1"] = np.array(s1)
        data["setting2"] = np.array(s2)
        data["setting3"] = np.array(s3)

    for s_col in SENSOR_COLUMNS:
        data[s_col] = rng.normal(500.0, 10.0, size=n_rows)

    return pd.DataFrame(data)


def test_column_stats_ddof0_and_zero_variance() -> None:
    """Test that stats use population variance ddof=0 and handle zero variance."""
    arr = np.array([10.0, 20.0, 30.0])
    mean_val, var_val, scale_val, is_zero_var = _compute_column_stats(arr)
    assert mean_val == 20.0
    # Population variance of [10, 20, 30] is ((10-20)^2 + (20-20)^2 + (30-20)^2) / 3 = 200/3
    assert np.isclose(var_val, 200.0 / 3.0)
    assert np.isclose(scale_val, np.sqrt(200.0 / 3.0))
    assert not is_zero_var

    # Constant array
    arr_const = np.array([5.0, 5.0, 5.0, 5.0])
    mean_c, var_c, scale_c, is_zero_c = _compute_column_stats(arr_const)
    assert mean_c == 5.0
    assert var_c == 0.0
    assert scale_c == 1.0
    assert is_zero_c


def test_fd001_preprocessing_single_condition() -> None:
    """Test that FD001 fits global scalers, does NOT fit K-means, and sets regime C1."""
    df_train = _make_training_df(n_rows=60, regimes=1)
    preproc = fit_preprocessor(df_train, "FD001")

    assert preproc.dataset == "FD001"
    assert preproc.regime_mode == "single_condition"
    assert preproc.kmeans_config is None
    assert preproc.canonical_standardized_centroids is None
    assert "C1" in preproc.sensor_scalers_by_regime

    df_trans = preproc.transform(df_train)
    assert "regime" in df_trans.columns
    assert (df_trans["regime"] == "C1").all()
    # Check 17 features preserved and finite
    for col in FEATURE_COLUMNS:
        assert col in df_trans.columns
        assert np.all(np.isfinite(df_trans[col].to_numpy()))


def test_fd002_preprocessing_kmeans_and_canonical_sorting() -> None:
    """Test FD002 multi-regime K-means fitting, lexicographical sorting, and C1..C6 labels."""
    df_train = _make_training_df(n_rows=120, regimes=6)
    preproc = fit_preprocessor(df_train, "FD002")

    assert preproc.dataset == "FD002"
    assert preproc.regime_mode == "kmeans_6"
    assert preproc.kmeans_config is not None
    assert preproc.canonical_standardized_centroids is not None
    assert len(preproc.canonical_standardized_centroids) == 6
    assert preproc.training_cluster_counts is not None
    for reg in CANONICAL_REGIMES:
        assert preproc.training_cluster_counts[reg] > 0
        assert reg in preproc.sensor_scalers_by_regime

    # Verify canonical centroid sorting: lexicographical on (setting1, setting2, setting3)
    centroids = preproc.canonical_standardized_centroids
    for i in range(len(centroids) - 1):
        c_curr = tuple(centroids[i])
        c_next = tuple(centroids[i + 1])
        assert c_curr <= c_next, f"Centroids not lexicographically sorted: {c_curr} > {c_next}"

    df_trans = preproc.transform(df_train)
    assert set(df_trans["regime"].unique()).issubset(set(CANONICAL_REGIMES))


def test_exact_tie_breaks_to_lowest_canonical_index() -> None:
    """Test that equidistant settings tie-break to lowest canonical regime index (C1 over C2)."""
    # Create artificial preprocessor where C1 and C2 are equidistant from a point
    setting_scalers = {
        col: ScalerParams(mean=0.0, variance=1.0, effective_scale=1.0, is_zero_variance=False)
        for col in SETTING_COLUMNS
    }
    # Centroids equidistant from [0, 0, 0]: C1 is [-1, 0, 0], C2 is [1, 0, 0]
    centroids = [
        [-1.0, 0.0, 0.0],  # dist sq to [0,0,0] is 1.0
        [1.0, 0.0, 0.0],  # dist sq to [0,0,0] is 1.0
        [5.0, 0.0, 0.0],
        [6.0, 0.0, 0.0],
        [7.0, 0.0, 0.0],
        [8.0, 0.0, 0.0],
    ]
    sensor_scalers = {
        f"C{k}": {
            s: ScalerParams(mean=0.0, variance=1.0, effective_scale=1.0, is_zero_variance=False)
            for s in SENSOR_COLUMNS
        }
        for k in range(1, 7)
    }

    preproc = FittedPreprocessor(
        dataset="FD002",
        feature_order=FEATURE_COLUMNS,
        setting_scalers=setting_scalers,
        regime_mode="kmeans_6",
        kmeans_config=None,
        canonical_standardized_centroids=centroids,
        canonical_unscaled_centroids=centroids,
        original_cluster_to_canonical_mapping=None,
        training_cluster_counts=None,
        sensor_scalers_by_regime=sensor_scalers,
    )

    labels, indices = preproc.assign_regime(np.array([[0.0, 0.0, 0.0]]))
    assert labels[0] == "C1"
    assert indices[0] == 0


def test_preprocessor_artifact_round_trip(tmp_path: Path) -> None:
    """Test saving and loading preprocessor artifact produces numerically identical transforms."""
    df_train = _make_training_df(n_rows=120, regimes=6)
    preproc = fit_preprocessor(df_train, "FD002")

    art_file = tmp_path / "preprocessor.json"
    save_preprocessor_artifact(
        preprocessor=preproc,
        output_path=art_file,
        source_raw_path="data/raw/cmapss/train_FD002.txt",
        source_raw_sha256="test_sha_raw",
        split_manifest_path="data/splits/fd002.json",
        split_manifest_sha256="test_sha_manifest",
    )

    loaded_preproc, metadata = load_preprocessor_artifact(art_file)
    assert loaded_preproc.dataset == preproc.dataset
    assert metadata["schema_version"] == "step07-data-v1"

    # Compare transforms
    out_original = preproc.transform(df_train)
    out_loaded = loaded_preproc.transform(df_train)

    pd.testing.assert_frame_equal(out_original, out_loaded)


def test_anti_leakage_validation_values_do_not_affect_fitted_scalers() -> None:
    """Explicit anti-leakage test: validation rows must not alter training scalers."""
    df_train = _make_training_df(n_rows=60, regimes=1)
    preproc = fit_preprocessor(df_train, "FD001")

    # Extreme validation data
    df_val = df_train.copy()
    df_val["s2"] = 999999.0
    df_val["setting1"] = -88888.0

    # Transform validation data
    df_val_trans = preproc.transform(df_val)

    # Assert training scaler mean and scale remain completely unaffected
    assert preproc.setting_scalers["setting1"].mean == float(df_train["setting1"].mean())
    assert preproc.sensor_scalers_by_regime["C1"]["s2"].mean == float(df_train["s2"].mean())
    assert np.all(np.isfinite(df_val_trans["s2"].to_numpy()))
