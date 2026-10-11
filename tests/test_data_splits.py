"""Tests for split manifest loading and validation using synthetic manifests."""

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from intellitwin.data.splits import (
    SplitManifest,
    load_split_manifest,
    select_partition,
    validate_split_manifest,
)


def _write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _valid_fd001_dict() -> dict[str, Any]:
    # 50 train, 20 cal, 10 val, 20 test = 100 total
    all_engines = list(range(1, 101))
    return {
        "dataset": "FD001",
        "seed": 2026,
        "partitions": {
            "train": all_engines[:50],
            "calibration": all_engines[50:70],
            "validation": all_engines[70:80],
            "test": all_engines[80:100],
        },
    }


def test_splits_valid_load_and_validate(tmp_path: Path) -> None:
    """Test loading and validating a valid synthetic split manifest."""
    m_dict = _valid_fd001_dict()
    m_path = tmp_path / "manifest.json"
    _write_manifest(m_path, m_dict)

    manifest = load_split_manifest(m_path)
    assert manifest.dataset == "FD001"
    assert manifest.seed == 2026
    assert len(manifest.train) == 50
    assert len(manifest.calibration) == 20
    assert len(manifest.validation) == 10
    assert len(manifest.test) == 20

    validate_split_manifest(manifest, "FD001", expected_engine_count=100)


def test_splits_select_partition() -> None:
    """Test partition filtering on a DataFrame."""
    m_dict = _valid_fd001_dict()
    manifest = SplitManifest(
        dataset="FD001",
        seed=2026,
        train=tuple(m_dict["partitions"]["train"]),
        calibration=tuple(m_dict["partitions"]["calibration"]),
        validation=tuple(m_dict["partitions"]["validation"]),
        test=tuple(m_dict["partitions"]["test"]),
    )

    df = pd.DataFrame(
        {
            "unit": [1, 2, 51, 71, 81],
            "cycle": [1, 1, 1, 1, 1],
            "value": [10, 20, 30, 40, 50],
        }
    )

    df_train = select_partition(df, manifest, "train")
    assert df_train["unit"].tolist() == [1, 2]

    df_val = select_partition(df, manifest, "validation")
    assert df_val["unit"].tolist() == [71]


def test_splits_missing_partition_key(tmp_path: Path) -> None:
    """Test rejection when a required partition is missing."""
    m_dict = _valid_fd001_dict()
    del m_dict["partitions"]["test"]
    m_path = tmp_path / "bad_manifest.json"
    _write_manifest(m_path, m_dict)

    with pytest.raises(ValueError, match="missing 'test'"):
        load_split_manifest(m_path)


def test_splits_wrong_dataset() -> None:
    """Test rejection when dataset does not match."""
    m_dict = _valid_fd001_dict()
    manifest = SplitManifest(
        dataset="FD001",
        seed=2026,
        train=tuple(m_dict["partitions"]["train"]),
        calibration=tuple(m_dict["partitions"]["calibration"]),
        validation=tuple(m_dict["partitions"]["validation"]),
        test=tuple(m_dict["partitions"]["test"]),
    )
    with pytest.raises(ValueError, match="dataset mismatch"):
        validate_split_manifest(manifest, "FD002", 100)


def test_splits_wrong_seed() -> None:
    """Test rejection when seed is not 2026."""
    m_dict = _valid_fd001_dict()
    manifest = SplitManifest(
        dataset="FD001",
        seed=9999,
        train=tuple(m_dict["partitions"]["train"]),
        calibration=tuple(m_dict["partitions"]["calibration"]),
        validation=tuple(m_dict["partitions"]["validation"]),
        test=tuple(m_dict["partitions"]["test"]),
    )
    with pytest.raises(ValueError, match="seed mismatch"):
        validate_split_manifest(manifest, "FD001", 100)


def test_splits_count_mismatch() -> None:
    """Test rejection when partition counts do not match frozen counts."""
    m_dict = _valid_fd001_dict()
    # Remove one engine from train
    bad_train = list(m_dict["partitions"]["train"][:-1])
    manifest = SplitManifest(
        dataset="FD001",
        seed=2026,
        train=tuple(bad_train),
        calibration=tuple(m_dict["partitions"]["calibration"]),
        validation=tuple(m_dict["partitions"]["validation"]),
        test=tuple(m_dict["partitions"]["test"]),
    )
    with pytest.raises(ValueError, match="expected frozen count 50"):
        validate_split_manifest(manifest, "FD001", 100)


def test_splits_duplicate_ids_within_partition() -> None:
    """Test rejection when IDs within partition are duplicated."""
    m_dict = _valid_fd001_dict()
    # 50 items with duplicate 1
    dup_train = [1] * 50
    manifest = SplitManifest(
        dataset="FD001",
        seed=2026,
        train=tuple(dup_train),
        calibration=tuple(m_dict["partitions"]["calibration"]),
        validation=tuple(m_dict["partitions"]["validation"]),
        test=tuple(m_dict["partitions"]["test"]),
    )
    with pytest.raises(ValueError, match="duplicate engine IDs"):
        validate_split_manifest(manifest, "FD001", 100)


def test_splits_overlap_between_partitions() -> None:
    """Test rejection when partitions overlap."""
    m_dict = _valid_fd001_dict()
    # Put engine 1 into calibration as well, but keep count 20
    bad_cal = [1] + list(m_dict["partitions"]["calibration"][:-1])
    manifest = SplitManifest(
        dataset="FD001",
        seed=2026,
        train=tuple(m_dict["partitions"]["train"]),
        calibration=tuple(bad_cal),
        validation=tuple(m_dict["partitions"]["validation"]),
        test=tuple(m_dict["partitions"]["test"]),
    )
    with pytest.raises(ValueError, match="overlaps"):
        validate_split_manifest(manifest, "FD001", 100)


def test_splits_invalid_non_positive_engine_id() -> None:
    """Test rejection when engine ID is <= 0."""
    m_dict = _valid_fd001_dict()
    bad_train = [-1] + list(m_dict["partitions"]["train"][1:])
    manifest = SplitManifest(
        dataset="FD001",
        seed=2026,
        train=tuple(bad_train),
        calibration=tuple(m_dict["partitions"]["calibration"]),
        validation=tuple(m_dict["partitions"]["validation"]),
        test=tuple(m_dict["partitions"]["test"]),
    )
    with pytest.raises(ValueError, match="non-positive engine ID"):
        validate_split_manifest(manifest, "FD001", 100)
