"""Tests for checkpoint environment verification and reproduction wrapper.

Validates all 9 mandatory failure and boundary cases:
1. Incorrect runtime versions stop execution before model loading.
2. Conflicting metadata declarations across 30 base models are rejected.
3. sklearn version warnings fail the audit.
4. Failed pip check prevents PASS.
5. Missing or duplicate reproduction records are rejected.
6. Unexpected datasets, seeds, models, or partitions are rejected.
7. Non-finite or over-tolerance (>1e-4) errors are rejected.
8. Modified protected inputs prevent PASS.
9. Missing raw data cannot yield a successful audit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from sklearn.exceptions import InconsistentVersionWarning

from scripts.verify_checkpoint_environment import (
    EXPECTED_DATASETS,
    EXPECTED_FAMILIES,
    EXPECTED_PARTITIONS,
    EXPECTED_SEEDS,
    REQUIRED_VERSIONS,
    hash_raw_files,
    run_checkpoint_verification,
    verify_metadata_agreement,
    verify_runtime_versions,
    verify_step08_reproduction_records,
)


def generate_valid_60_records() -> list[dict[str, Any]]:
    """Helper to generate a complete, valid set of 60 reproduction records."""
    records: list[dict[str, Any]] = []
    for ds in EXPECTED_DATASETS:
        for fam in EXPECTED_FAMILIES:
            for seed in EXPECTED_SEEDS:
                for part in EXPECTED_PARTITIONS:
                    records.append(
                        {
                            "dataset": ds,
                            "model_family": fam,
                            "seed": seed,
                            "partition": part,
                            "max_abs_diff": 0.0,
                            "status": "PASS",
                        }
                    )
    return records


def test_incorrect_runtime_versions_stop_execution_before_model_loading() -> None:
    """Test that an incorrect runtime version raises RuntimeError before model loading."""
    with patch("scripts.verify_checkpoint_environment.np.__version__", "2.5.4"):
        with pytest.raises(RuntimeError, match="Runtime environment mismatch"):
            verify_runtime_versions()

    with patch("scripts.verify_checkpoint_environment.sklearn.__version__", "1.8.0"):
        with pytest.raises(RuntimeError, match="Runtime environment mismatch"):
            verify_runtime_versions()

    with patch("scripts.verify_checkpoint_environment.torch.__version__", "2.14.1+cu121"):
        with pytest.raises(RuntimeError, match="Runtime environment mismatch"):
            verify_runtime_versions()


def test_conflicting_metadata_declarations_rejected(tmp_path: Path) -> None:
    """Test that conflicting metadata declarations across base models are rejected."""
    base_models_dir = tmp_path / "experiments" / "base_models"

    # Create 30 metadata files, with one having a conflicting declaration
    for ds in EXPECTED_DATASETS:
        for fam in EXPECTED_FAMILIES:
            for seed in EXPECTED_SEEDS:
                meta_dir = base_models_dir / ds / fam / f"seed_{seed}"
                meta_dir.mkdir(parents=True, exist_ok=True)
                meta_file = meta_dir / "metadata.json"

                meta_data = {
                    "python_version": REQUIRED_VERSIONS["python"],
                    "numpy_version": REQUIRED_VERSIONS["numpy"],
                    "pandas_version": REQUIRED_VERSIONS["pandas"],
                    "scikit_learn_version": REQUIRED_VERSIONS["scikit-learn"],
                    "torch_version": REQUIRED_VERSIONS["torch"],
                }

                # Introduce deliberate mismatch on one file
                if ds == "FD002" and fam == "LSTM" and seed == 2028:
                    meta_data["scikit_learn_version"] = "1.8.0"

                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(meta_data, f)

    with pytest.raises(ValueError, match="Conflicting or non-matching metadata declarations"):
        verify_metadata_agreement(tmp_path)


def test_sklearn_version_warnings_fail_audit(tmp_path: Path) -> None:
    """Test that any sklearn InconsistentVersionWarning fails the audit."""
    out_dir = tmp_path / "output"

    def mock_run_step08_audit(*args: Any, **kwargs: Any) -> dict[str, Any]:
        import warnings

        warnings.warn(
            InconsistentVersionWarning(
                estimator_name="DecisionTreeRegressor",
                current_sklearn_version="1.9.1",
                original_sklearn_version="1.8.0",
            ),
            stacklevel=2,
        )
        return {"overall_status": "PASS", "details": {}}

    with patch(
        "scripts.verify_checkpoint_environment.run_step08_audit",
        side_effect=mock_run_step08_audit,
    ):
        with pytest.raises(RuntimeError, match="InconsistentVersionWarning detected"):
            run_checkpoint_verification(
                output_dir=out_dir,
                allow_dirty=True,
                skip_raw_reproduction=True,
            )


def test_failed_pip_check_prevents_pass(tmp_path: Path) -> None:
    """Test that a failed pip check prevents PASS and halts verification."""
    out_dir = tmp_path / "output"

    with patch(
        "scripts.verify_checkpoint_environment.execute_pip_check",
        return_value=(1, "broken dependencies: package A requires B<1.0, but you have B 2.0"),
    ):
        with pytest.raises(RuntimeError, match="pip check failed with exit code 1"):
            run_checkpoint_verification(
                output_dir=out_dir,
                allow_dirty=True,
                skip_raw_reproduction=True,
            )


def test_missing_or_duplicate_reproduction_records_rejected() -> None:
    """Test that missing or duplicate reproduction records are rejected."""
    valid_records = generate_valid_60_records()
    res_valid = verify_step08_reproduction_records(valid_records)
    assert res_valid["status"] == "PASS"
    assert res_valid["reproduction_records_complete"] is True

    # Missing one record (59 total)
    incomplete_records = valid_records[:-1]
    res_missing = verify_step08_reproduction_records(incomplete_records)
    assert res_missing["status"] == "FAIL"
    assert res_missing["reproduction_records_complete"] is False
    assert any("Missing expected reproduction keys" in err for err in res_missing["errors"])

    # Duplicate record (replace last record with a duplicate of the first)
    duplicate_records = valid_records[:-1] + [valid_records[0].copy()]
    res_dup = verify_step08_reproduction_records(duplicate_records)
    assert res_dup["status"] == "FAIL"
    assert res_dup["reproduction_records_complete"] is False
    assert any("Duplicate reproduction record key" in err for err in res_dup["errors"])


def test_unexpected_datasets_seeds_models_partitions_rejected() -> None:
    """Test that unexpected datasets, seeds, models, or partitions are rejected."""
    records = generate_valid_60_records()

    # Mutate one record to an unexpected dataset
    records[0]["dataset"] = "FD003"
    res = verify_step08_reproduction_records(records)
    assert res["status"] == "FAIL"
    assert res["reproduction_records_complete"] is False
    assert any("Unexpected reproduction keys" in err for err in res["errors"])

    # Mutate to an unexpected model family
    records = generate_valid_60_records()
    records[0]["model_family"] = "RandomForest"
    res_fam = verify_step08_reproduction_records(records)
    assert res_fam["status"] == "FAIL"
    assert res_fam["reproduction_records_complete"] is False

    # Mutate to an unexpected seed
    records = generate_valid_60_records()
    records[0]["seed"] = 1999
    res_seed = verify_step08_reproduction_records(records)
    assert res_seed["status"] == "FAIL"
    assert res_seed["reproduction_records_complete"] is False

    # Mutate to forbidden held-out partition
    records = generate_valid_60_records()
    records[0]["partition"] = "test"
    res_part = verify_step08_reproduction_records(records)
    assert res_part["status"] == "FAIL"
    assert res_part["reproduction_records_complete"] is False


def test_nonfinite_or_over_tolerance_errors_rejected() -> None:
    """Test that non-finite or over-tolerance (>1e-4) prediction errors are rejected."""
    records = generate_valid_60_records()

    # Tolerance exceeded (1.01e-4 > 1e-4)
    records[5]["max_abs_diff"] = 1.01e-4
    res_tol = verify_step08_reproduction_records(records)
    assert res_tol["status"] == "FAIL"
    assert res_tol["reproduction_records_complete"] is False
    assert any("exceeded error tolerance" in err for err in res_tol["errors"])

    # Non-finite (NaN)
    records = generate_valid_60_records()
    records[5]["max_abs_diff"] = float("nan")
    res_nan = verify_step08_reproduction_records(records)
    assert res_nan["status"] == "FAIL"
    assert res_nan["reproduction_records_complete"] is False
    assert any("non-finite difference" in err for err in res_nan["errors"])

    # Non-finite (Infinity)
    records = generate_valid_60_records()
    records[5]["max_abs_diff"] = float("inf")
    res_inf = verify_step08_reproduction_records(records)
    assert res_inf["status"] == "FAIL"
    assert res_inf["reproduction_records_complete"] is False
    assert any("non-finite difference" in err for err in res_inf["errors"])


def test_modified_protected_inputs_prevent_pass(tmp_path: Path) -> None:
    """Test that any modification to protected inputs during execution fails the verification."""
    out_dir = tmp_path / "output"

    from scripts.verify_checkpoint_environment import hash_protected_inputs

    real_pre = hash_protected_inputs(Path("."))
    mod_post = {k: v.copy() for k, v in real_pre.items()}
    mod_post["model_registry"]["experiments/base_models/model_registry.json"] = "deadbeef" * 8

    with patch(
        "scripts.verify_checkpoint_environment.hash_protected_inputs",
        side_effect=[real_pre, mod_post],
    ):
        with pytest.raises(RuntimeError, match="Protected inputs were modified during execution"):
            run_checkpoint_verification(
                output_dir=out_dir,
                allow_dirty=True,
                skip_raw_reproduction=True,
            )


def test_missing_raw_data_cannot_yield_successful_audit(tmp_path: Path) -> None:
    """Test that missing raw data cannot yield a successful audit."""
    empty_raw_dir = tmp_path / "empty_raw"
    empty_raw_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(FileNotFoundError, match="Raw C-MAPSS dataset missing"):
        hash_raw_files(base_dir=tmp_path, raw_data_dir=empty_raw_dir)
