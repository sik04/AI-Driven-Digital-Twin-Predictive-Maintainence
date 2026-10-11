"""Tests for end-to-end data preparation pipeline with synthetic data."""

import json
from pathlib import Path

import numpy as np

from intellitwin.data.pipeline import prepare_dataset_for_model_development


def _create_synthetic_raw_and_manifest(tmp_path: Path) -> tuple[Path, Path]:
    """Create a complete synthetic raw dataset and frozen split manifest for FD001."""
    # 100 engines for FD001, each with 35 cycles
    lines: list[str] = []
    for unit in range(1, 101):
        for cycle in range(1, 36):
            settings = [10.0, 0.2, 100.0]
            sensors = [float(s * 10 + cycle) for s in range(1, 22)]
            row = [str(unit), str(cycle)] + [str(x) for x in settings] + [str(s) for s in sensors]
            lines.append(" ".join(row))

    raw_file = tmp_path / "train_FD001.txt"
    raw_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    all_engines = list(range(1, 101))
    manifest_data = {
        "dataset": "FD001",
        "seed": 2026,
        "partitions": {
            "train": all_engines[:50],  # 50
            "calibration": all_engines[50:70],  # 20
            "validation": all_engines[70:80],  # 10
            "test": all_engines[80:100],  # 20
        },
    }
    manifest_file = tmp_path / "manifest_FD001.json"
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return raw_file, manifest_file


def test_pipeline_end_to_end_isolation_and_artifacts(tmp_path: Path) -> None:
    """Test full pipeline execution: train-only fitting, weights, and calibration/test exclusion."""
    raw_file, manifest_file = _create_synthetic_raw_and_manifest(tmp_path)

    prepared = prepare_dataset_for_model_development(
        dataset_name="FD001",
        raw_path=raw_file,
        split_manifest_path=manifest_file,
    )

    assert prepared.dataset_name == "FD001"
    assert prepared.fitted_preprocessor is not None
    assert prepared.train_windows is not None
    assert prepared.validation_windows is not None
    assert prepared.train_sample_weights is not None

    # Verify calibration and test engines are completely absent from window datasets
    # (train: 1..50, validation: 71..80; cal: 51..70, test: 81..100)
    train_units = set(np.unique(prepared.train_windows.engine_ids))
    val_units = set(np.unique(prepared.validation_windows.engine_ids))

    assert train_units == set(range(1, 51))
    assert val_units == set(range(71, 81))
    assert train_units.isdisjoint(val_units)

    # Disjoint from calibration (51..70) and test (81..100)
    cal_test_units = set(range(51, 71)).union(set(range(81, 101)))
    assert train_units.isdisjoint(cal_test_units)
    assert val_units.isdisjoint(cal_test_units)

    # Window shapes: each engine has 35 cycles -> 6 windows (endpoints 30..35)
    # Train: 50 engines * 6 windows = 300 windows
    # Val: 10 engines * 6 windows = 60 windows
    assert len(prepared.train_windows) == 300
    assert len(prepared.validation_windows) == 60
    assert prepared.train_windows.X_sequence.shape == (300, 30, 17)
    assert prepared.validation_windows.X_sequence.shape == (60, 30, 17)

    # Verify sample weights
    assert len(prepared.train_sample_weights) == 300
    assert np.isclose(np.mean(prepared.train_sample_weights), 1.0)

    # Verify deterministic repeated execution produces identical results
    prepared_2 = prepare_dataset_for_model_development(
        dataset_name="FD001",
        raw_path=raw_file,
        split_manifest_path=manifest_file,
    )
    np.testing.assert_array_equal(
        prepared.train_windows.X_sequence,
        prepared_2.train_windows.X_sequence,
    )
    np.testing.assert_array_equal(
        prepared.train_sample_weights,
        prepared_2.train_sample_weights,
    )
