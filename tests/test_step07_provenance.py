"""Regression test suite for Step 7 model-selection provenance and split reporting.

Verifies that partition counts derive directly from authoritative split manifests,
that manual or prose reporting cannot override frozen manifests, that calibration
and test data access are strictly prohibited during base-model selection, and that
committed FD002 selection artifacts and split manifests maintain their frozen invariants.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from intellitwin.data.splits import (
    SplitManifest,
    load_split_manifest,
    partition_counts,
)
from intellitwin.models.provenance import validate_selection_provenance

REPO_ROOT = Path(__file__).resolve().parent.parent
FD002_MANIFEST_PATH = REPO_ROOT / "data" / "splits" / "fd002_engine_split_seed_2026.json"
GBR_SELECTION_PATH = REPO_ROOT / "experiments" / "model_selection" / "FD002" / "gbr_selection.json"
LSTM_SELECTION_PATH = (
    REPO_ROOT / "experiments" / "model_selection" / "FD002" / "lstm_selection.json"
)


DUMMY_SHA = "cef04b8dafc4c9f53aba7c6bcb0bc67fc981540abdafadc76fafa314684d856c"


def _make_synthetic_manifest(
    dataset: str = "FD002",
    seed: int = 2026,
    train: tuple[int, ...] = (1, 2, 3, 4),
    calibration: tuple[int, ...] = (5, 6),
    validation: tuple[int, ...] = (7,),
    test: tuple[int, ...] = (8, 9),
) -> SplitManifest:
    """Create a lightweight synthetic SplitManifest for unit testing."""
    return SplitManifest(
        dataset=dataset,
        seed=seed,
        train=train,
        calibration=calibration,
        validation=validation,
        test=test,
    )


def _make_valid_summary(
    dataset: str = "FD002",
    selected_id: str = "gbr_lr010_leaf31_l2_0",
    calibration_used: bool = False,
    test_used: bool = False,
    seeds: list[int] | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a minimal valid model selection summary dictionary."""
    summary: dict[str, Any] = {
        "schema_version": "step07-selection-v1",
        "dataset": dataset,
        "model_family": "GBR",
        "selection_seeds": [2026, 2027] if seeds is None else seeds,
        "selection_metric": "equal-engine-weighted uncapped-RUL RMSE",
        "training_target": "min(rul_true,125)",
        "calibration_data_used": calibration_used,
        "test_data_used": test_used,
        "preprocessing_artifact_sha256": DUMMY_SHA,
        "selected_configuration_id": selected_id,
    }
    if extra_fields:
        summary.update(extra_fields)
    return summary


def test_partition_counts_derive_correctly() -> None:
    """Test 1: Verify partition_counts helper calculates exact counts from SplitManifest."""
    manifest = _make_synthetic_manifest(
        train=(1, 2, 3, 4),
        calibration=(5, 6),
        validation=(7,),
        test=(8, 9),
    )
    counts = partition_counts(manifest)
    assert counts == {
        "train": 4,
        "calibration": 2,
        "validation": 1,
        "test": 2,
        "total": 9,
    }


def test_wrong_manually_reported_counts_cannot_override_manifest() -> None:
    """Test 2: Bogus manually reported partition counts cannot override manifest-derived counts."""
    manifest = _make_synthetic_manifest(
        train=(1, 2, 3, 4),
        calibration=(5, 6),
        validation=(7,),
        test=(8, 9),
    )
    # Summary contains fraudulent partition counts claiming 999 engines
    fraudulent_summary = _make_valid_summary(
        extra_fields={
            "train_engine_count": 999,
            "calibration_engine_count": 888,
            "validation_engine_count": 777,
            "test_engine_count": 666,
            "total_engine_count": 3330,
        }
    )
    report = validate_selection_provenance("FD002", manifest, fraudulent_summary)
    # Authoritative report must reflect manifest, not prose
    assert report.train_count == 4
    assert report.calibration_count == 2
    assert report.validation_count == 1
    assert report.test_count == 2
    assert report.total_count == 9


def test_calibration_use_rejected() -> None:
    """Test 3: Selection summary claiming calibration_data_used = True must be rejected."""
    manifest = _make_synthetic_manifest()
    summary = _make_valid_summary(calibration_used=True)
    with pytest.raises(ValueError, match="calibration_data_used must be False"):
        validate_selection_provenance("FD002", manifest, summary)


def test_test_use_rejected() -> None:
    """Test 4: Selection summary claiming test_data_used = True must be rejected."""
    manifest = _make_synthetic_manifest()
    summary = _make_valid_summary(test_used=True)
    with pytest.raises(ValueError, match="test_data_used must be False"):
        validate_selection_provenance("FD002", manifest, summary)


def test_wrong_selection_seeds_rejected() -> None:
    """Test 5: Anything other than [2026, 2027] for Step 7.3 selection must be rejected."""
    manifest = _make_synthetic_manifest()

    for invalid_seeds in ([2026], [2026, 2027, 2028], [2028, 2029], [], [2027, 2026]):
        summary = _make_valid_summary(seeds=invalid_seeds)
        with pytest.raises(ValueError, match="Expected selection_seeds to be \\[2026, 2027\\]"):
            validate_selection_provenance("FD002", manifest, summary)


def test_wrong_dataset_rejected() -> None:
    """Test 6: A summary or manifest claiming FD001 or FD004 when auditing FD002 must fail."""
    manifest_fd002 = _make_synthetic_manifest(dataset="FD002")
    manifest_fd001 = _make_synthetic_manifest(dataset="FD001")

    # Mismatched summary dataset
    summary_fd001 = _make_valid_summary(dataset="FD001")
    with pytest.raises(ValueError, match="Selection summary dataset 'FD001' does not match"):
        validate_selection_provenance("FD002", manifest_fd002, summary_fd001)

    summary_fd004 = _make_valid_summary(dataset="FD004")
    with pytest.raises(ValueError, match="Selection summary dataset 'FD004' does not match"):
        validate_selection_provenance("FD002", manifest_fd002, summary_fd004)

    # Mismatched manifest dataset
    summary_valid = _make_valid_summary(dataset="FD002")
    with pytest.raises(ValueError, match="Manifest dataset 'FD001' does not match"):
        validate_selection_provenance("FD002", manifest_fd001, summary_valid)


def test_missing_selected_configuration_rejected() -> None:
    """Test 7: Missing or blank selected_configuration_id must be rejected."""
    manifest = _make_synthetic_manifest()

    # Empty string
    summary_empty = _make_valid_summary(selected_id="")
    with pytest.raises(ValueError, match="Missing or invalid 'selected_configuration_id'"):
        validate_selection_provenance("FD002", manifest, summary_empty)

    # Whitespace only
    summary_blank = _make_valid_summary(selected_id="   ")
    with pytest.raises(ValueError, match="Missing or invalid 'selected_configuration_id'"):
        validate_selection_provenance("FD002", manifest, summary_blank)

    # Omitted key
    summary_omitted = _make_valid_summary()
    del summary_omitted["selected_configuration_id"]
    with pytest.raises(ValueError, match="Missing or invalid 'selected_configuration_id'"):
        validate_selection_provenance("FD002", manifest, summary_omitted)


def test_real_committed_manifest_regression() -> None:
    """Test 8: Real committed data/splits/fd002_engine_split_seed_2026.json partition counts."""
    assert FD002_MANIFEST_PATH.is_file(), f"Manifest missing: {FD002_MANIFEST_PATH}"
    manifest = load_split_manifest(FD002_MANIFEST_PATH)

    assert manifest.dataset == "FD002"
    assert manifest.seed == 2026

    counts = partition_counts(manifest)
    assert counts == {
        "train": 130,
        "calibration": 52,
        "validation": 26,
        "test": 52,
        "total": 260,
    }


def test_real_selection_json_regression() -> None:
    """Test 9: Real experiments/model_selection/FD002/{gbr,lstm}_selection.json regression."""
    assert FD002_MANIFEST_PATH.is_file(), f"Manifest missing: {FD002_MANIFEST_PATH}"
    assert GBR_SELECTION_PATH.is_file(), f"GBR selection missing: {GBR_SELECTION_PATH}"
    assert LSTM_SELECTION_PATH.is_file(), f"LSTM selection missing: {LSTM_SELECTION_PATH}"

    manifest = load_split_manifest(FD002_MANIFEST_PATH)

    with open(GBR_SELECTION_PATH, encoding="utf-8") as f:
        gbr_summary = json.load(f)
    with open(LSTM_SELECTION_PATH, encoding="utf-8") as f:
        lstm_summary = json.load(f)

    gbr_report = validate_selection_provenance("FD002", manifest, gbr_summary)
    assert gbr_report.selected_configuration_id == "gbr_lr010_leaf31_l2_0"
    assert gbr_report.calibration_data_used is False
    assert gbr_report.test_data_used is False
    assert gbr_report.train_count == 130
    assert gbr_report.calibration_count == 52
    assert gbr_report.validation_count == 26
    assert gbr_report.test_count == 52
    assert gbr_report.total_count == 260

    lstm_report = validate_selection_provenance("FD002", manifest, lstm_summary)
    assert lstm_report.selected_configuration_id == "lstm_h64_lr0010"
    assert lstm_report.calibration_data_used is False
    assert lstm_report.test_data_used is False
    assert lstm_report.train_count == 130
    assert lstm_report.calibration_count == 52
    assert lstm_report.validation_count == 26
    assert lstm_report.test_count == 52
    assert lstm_report.total_count == 260
