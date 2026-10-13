"""Integration and data boundary tests for Step 8 calibration pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from intellitwin.data.calibration_pipeline import prepare_partition_windows


def test_test_partition_access_is_forbidden() -> None:
    """Verify that attempting to prepare windows for the 'test' partition raises PermissionError."""
    with pytest.raises(PermissionError, match="strictly forbidden in Step 8"):
        prepare_partition_windows(dataset_name="FD001", partition_name="test")

    with pytest.raises(PermissionError, match="strictly forbidden in Step 8"):
        prepare_partition_windows(dataset_name="FD002", partition_name="held_out")


@pytest.mark.integration
def test_prepare_calibration_windows_raw_data() -> None:
    """Integration test verifying calibration window generation on real local C-MAPSS data."""
    raw_f = Path("data/raw/cmapss/train_FD001.txt")
    if not raw_f.exists():
        pytest.skip(f"Required raw data missing: {raw_f}")

    cal_windows = prepare_partition_windows(dataset_name="FD001", partition_name="calibration")
    assert len(cal_windows.engine_ids) > 0
    # FD001 has 20 calibration engines
    unique_engines = set(cal_windows.engine_ids)
    assert len(unique_engines) == 20
    assert cal_windows.X_sequence.shape[1:] == (30, 17)


@pytest.mark.integration
def test_prepare_validation_windows_raw_data() -> None:
    """Integration test verifying validation window generation on real local C-MAPSS data."""
    raw_f = Path("data/raw/cmapss/train_FD001.txt")
    if not raw_f.exists():
        pytest.skip(f"Required raw data missing: {raw_f}")

    val_windows = prepare_partition_windows(dataset_name="FD001", partition_name="validation")
    assert len(val_windows.engine_ids) > 0
    # FD001 has 10 validation engines
    unique_engines = set(val_windows.engine_ids)
    assert len(unique_engines) == 10
    assert val_windows.X_sequence.shape[1:] == (30, 17)
