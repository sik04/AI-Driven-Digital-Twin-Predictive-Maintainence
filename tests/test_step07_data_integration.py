"""Integration tests for Step 7 data pipeline against actual C-MAPSS raw files."""

from pathlib import Path

import numpy as np
import pytest

from intellitwin.data.pipeline import prepare_dataset_for_model_development
from intellitwin.data.schema import (
    FROZEN_PARTITION_COUNTS,
    RAW_FILENAMES,
    SPLIT_MANIFEST_PATHS,
    SUPPORTED_DATASETS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _raw_files_available() -> bool:
    """Check if all raw C-MAPSS files exist locally."""
    for ds in SUPPORTED_DATASETS:
        p = REPO_ROOT / RAW_FILENAMES[ds]
        if not p.is_file():
            return False
    return True


@pytest.mark.integration
@pytest.mark.parametrize("dataset_name", ["FD001", "FD002", "FD004"])
def test_step07_data_pipeline_real_dataset(dataset_name: str) -> None:
    """Validate full data pipeline on actual raw C-MAPSS dataset."""
    if not _raw_files_available():
        pytest.skip("Local raw C-MAPSS dataset files not available.")

    raw_path = REPO_ROOT / RAW_FILENAMES[dataset_name]
    manifest_path = REPO_ROOT / SPLIT_MANIFEST_PATHS[dataset_name]

    prepared = prepare_dataset_for_model_development(
        dataset_name=dataset_name,
        raw_path=raw_path,
        split_manifest_path=manifest_path,
    )

    # 1. Structural invariants
    train_win = prepared.train_windows
    val_win = prepared.validation_windows

    assert train_win.X_sequence.shape[1:] == (30, 17)
    assert val_win.X_sequence.shape[1:] == (30, 17)
    assert train_win.X_sequence.dtype == np.float32
    assert val_win.X_sequence.dtype == np.float32

    # 2. Check all transformed feature values are finite
    assert np.all(np.isfinite(train_win.X_sequence))
    assert np.all(np.isfinite(val_win.X_sequence))

    # 3. Check partition counts match frozen counts
    frozen_counts = FROZEN_PARTITION_COUNTS[dataset_name]
    assert len(np.unique(train_win.engine_ids)) == frozen_counts["train"]
    assert len(np.unique(val_win.engine_ids)) == frozen_counts["validation"]

    # 4. Check sample weights invariant
    weights = prepared.train_sample_weights
    assert len(weights) == len(train_win)
    assert np.isclose(np.mean(weights), 1.0, atol=1e-5)

    # 5. Check endpoints
    assert np.all(train_win.endpoint_cycles >= 30)
    assert np.all(val_win.endpoint_cycles >= 30)
    assert np.all(train_win.rul_true >= 0.0)
    assert np.all(train_win.rul_target <= 125.0)

    # 6. Multi-regime check for FD002 and FD004
    if dataset_name in ("FD002", "FD004"):
        assert prepared.fitted_preprocessor.regime_mode == "kmeans_6"
        assert prepared.fitted_preprocessor.canonical_standardized_centroids is not None
        assert len(prepared.fitted_preprocessor.canonical_standardized_centroids) == 6
        regimes_in_train = set(np.unique(train_win.regimes))
        assert regimes_in_train == {"C1", "C2", "C3", "C4", "C5", "C6"}
    else:
        assert prepared.fitted_preprocessor.regime_mode == "single_condition"
        assert set(np.unique(train_win.regimes)) == {"C1"}
