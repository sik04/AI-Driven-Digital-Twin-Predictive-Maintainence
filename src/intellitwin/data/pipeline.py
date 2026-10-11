"""High-level dataset preparation pipeline for model development.

Loads and validates raw data and frozen split manifests, fits preprocessing strictly
on training engines, transforms training and validation data, constructs causal sequence
windows, and computes equal-engine sample weights.

Calibration and held-out test data are strictly excluded from window construction
and transformation during model development.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from intellitwin.data.artifacts import compute_sha256
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.preprocessing import FittedPreprocessor, fit_preprocessor
from intellitwin.data.schema import EXPECTED_ENGINE_COUNTS, SUPPORTED_DATASETS
from intellitwin.data.splits import (
    load_split_manifest,
    select_partition,
    validate_split_manifest,
)
from intellitwin.data.windowing import (
    WindowDataset,
    compute_equal_engine_sample_weights,
    construct_windows,
)


@dataclass(frozen=True)
class PreparedDataset:
    """Dataset bundle prepared strictly for model development."""

    dataset_name: str
    fitted_preprocessor: FittedPreprocessor
    train_windows: WindowDataset
    validation_windows: WindowDataset
    train_sample_weights: np.ndarray
    provenance: dict[str, Any]


def prepare_dataset_for_model_development(
    dataset_name: str,
    raw_path: Path | str,
    split_manifest_path: Path | str,
) -> PreparedDataset:
    """Execute end-to-end dataset preparation for model development.

    Parameters
    ----------
    dataset_name : str
        Dataset identifier ("FD001", "FD002", "FD004").
    raw_path : Path or str
        Path to raw whitespace-delimited C-MAPSS run-to-failure file.
    split_manifest_path : Path or str
        Path to frozen split manifest JSON file.

    Returns
    -------
    PreparedDataset
        Container with fitted preprocessor, train/val windows, weights, and provenance.
        Calibration and test windows are strictly absent.
    """
    if dataset_name not in SUPPORTED_DATASETS:
        raise ValueError(
            f"Dataset '{dataset_name}' not supported. Expected one of {SUPPORTED_DATASETS}."
        )

    expected_count = EXPECTED_ENGINE_COUNTS[dataset_name]

    # Compute provenance hashes
    raw_file = Path(raw_path)
    manifest_file = Path(split_manifest_path)
    raw_sha256 = compute_sha256(raw_file)
    manifest_sha256 = compute_sha256(manifest_file)

    # 1. Load and strictly validate raw data
    df_raw = load_cmapss_run_to_failure(
        path=raw_file,
        dataset_name=dataset_name,
        expected_engine_count=expected_count,
    )

    # 2. Load and strictly validate split manifest
    manifest = load_split_manifest(manifest_file)
    validate_split_manifest(
        manifest=manifest,
        expected_dataset=dataset_name,
        expected_engine_count=expected_count,
    )

    # 3. Select training partition only and fit preprocessor
    df_train_raw = select_partition(df_raw, manifest, "train")
    preprocessor = fit_preprocessor(df_train=df_train_raw, dataset_name=dataset_name)

    # 4. Transform training partition and build causal windows
    df_train_transformed = preprocessor.transform(df_train_raw)
    train_windows = construct_windows(df_train_transformed)

    # 5. Compute equal-engine training sample weights
    train_weights = compute_equal_engine_sample_weights(train_windows.engine_ids)

    # 6. Select validation partition, transform using frozen training preprocessor,
    # and construct validation windows
    df_val_raw = select_partition(df_raw, manifest, "validation")
    df_val_transformed = preprocessor.transform(df_val_raw)
    val_windows = construct_windows(df_val_transformed)

    provenance: dict[str, Any] = {
        "dataset": dataset_name,
        "raw_file": str(raw_file).replace("\\", "/"),
        "raw_sha256": raw_sha256,
        "manifest_file": str(manifest_file).replace("\\", "/"),
        "manifest_sha256": manifest_sha256,
        "train_engine_count": len(manifest.train),
        "validation_engine_count": len(manifest.validation),
        "calibration_engine_count": len(manifest.calibration),
        "test_engine_count": len(manifest.test),
        "train_window_count": len(train_windows),
        "validation_window_count": len(val_windows),
        "train_features_shape": train_windows.X_sequence.shape,
        "validation_features_shape": val_windows.X_sequence.shape,
    }

    return PreparedDataset(
        dataset_name=dataset_name,
        fitted_preprocessor=preprocessor,
        train_windows=train_windows,
        validation_windows=val_windows,
        train_sample_weights=train_weights,
        provenance=provenance,
    )
