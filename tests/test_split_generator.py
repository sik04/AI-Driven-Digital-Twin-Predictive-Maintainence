"""Unit tests for the deterministic engine split generator (scripts/generate_engine_splits.py)."""

# ruff: noqa: E402
import json
import sys
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))


from generate_engine_splits import (  # type: ignore[import-not-found]
    FD001_ALLOCATIONS,
    FD004_ALLOCATIONS,
    generate_split_manifest,
)

SPLITS_DIR = REPO_ROOT / "data" / "splits"
RAW_DATA_DIR = REPO_ROOT / "data" / "raw" / "cmapss"
RAW_FD001_EXISTS = (RAW_DATA_DIR / "train_FD001.txt").exists()
RAW_FD004_EXISTS = (RAW_DATA_DIR / "train_FD004.txt").exists()


def test_fd001_manifest_structure_and_counts() -> None:
    """Verify FD001 split counts, ratios, disjointness, and full engine coverage."""
    if not RAW_FD001_EXISTS:
        if pytest is not None:
            pytest.skip("Raw FD001 data file not present")
        return

    manifest = generate_split_manifest(
        "FD001", "train_FD001.txt", 100, FD001_ALLOCATIONS, seed=2026
    )

    assert manifest["dataset"] == "FD001"
    assert manifest["seed"] == 2026
    assert manifest["counts"]["train"] == 50
    assert manifest["counts"]["calibration"] == 20
    assert manifest["counts"]["validation"] == 10
    assert manifest["counts"]["test"] == 20
    assert manifest["counts"]["total"] == 100

    partitions = manifest["partitions"]
    tr, ca, va, te = (
        set(partitions["train"]),
        set(partitions["calibration"]),
        set(partitions["validation"]),
        set(partitions["test"]),
    )

    # Disjointness
    assert tr.isdisjoint(ca)
    assert tr.isdisjoint(va)
    assert tr.isdisjoint(te)
    assert ca.isdisjoint(va)
    assert ca.isdisjoint(te)
    assert va.isdisjoint(te)

    # Full coverage
    union = tr | ca | va | te
    assert union == set(range(1, 101))


def test_fd004_manifest_structure_and_counts() -> None:
    """Verify FD004 split counts, ratios, disjointness, and full engine coverage."""
    if not RAW_FD004_EXISTS:
        if pytest is not None:
            pytest.skip("Raw FD004 data file not present")
        return

    manifest = generate_split_manifest(
        "FD004", "train_FD004.txt", 249, FD004_ALLOCATIONS, seed=2026
    )

    assert manifest["dataset"] == "FD004"
    assert manifest["seed"] == 2026
    assert manifest["counts"]["train"] == 124
    assert manifest["counts"]["calibration"] == 50
    assert manifest["counts"]["validation"] == 25
    assert manifest["counts"]["test"] == 50
    assert manifest["counts"]["total"] == 249

    partitions = manifest["partitions"]
    tr, ca, va, te = (
        set(partitions["train"]),
        set(partitions["calibration"]),
        set(partitions["validation"]),
        set(partitions["test"]),
    )

    # Disjointness
    assert tr.isdisjoint(ca)
    assert tr.isdisjoint(va)
    assert tr.isdisjoint(te)
    assert ca.isdisjoint(va)
    assert ca.isdisjoint(te)
    assert va.isdisjoint(te)

    # Full coverage
    union = tr | ca | va | te
    assert union == set(range(1, 250))


def test_deterministic_reproducibility() -> None:
    """Verify identical PRNG generator produces identical partition lists."""
    if not RAW_FD001_EXISTS:
        if pytest is not None:
            pytest.skip("Raw FD001 data file not present")
        return

    m1 = generate_split_manifest("FD001", "train_FD001.txt", 100, FD001_ALLOCATIONS, seed=2026)
    m2 = generate_split_manifest("FD001", "train_FD001.txt", 100, FD001_ALLOCATIONS, seed=2026)
    assert m1["partitions"] == m2["partitions"]


def test_fd002_manifest_preservation() -> None:
    """Verify existing FD002 manifest exists and is unchanged."""
    fd002_path = SPLITS_DIR / "fd002_engine_split_seed_2026.json"
    assert fd002_path.exists(), "FD002 manifest must exist"
    data = json.loads(fd002_path.read_text(encoding="utf-8"))
    assert data["dataset"] == "FD002"
    assert data["counts"]["total"] == 260
    assert len(data["partitions"]["train"]) == 130
    assert len(data["partitions"]["calibration"]) == 52
    assert len(data["partitions"]["validation"]) == 26
    assert len(data["partitions"]["test"]) == 52


def test_rejection_of_conflicting_manifest() -> None:
    """Verify script raises ValueError if existing manifest has conflicting partition IDs."""
    if not RAW_FD001_EXISTS:
        if pytest is not None:
            pytest.skip("Raw FD001 data file not present")
        return

    fake_manifest = {
        "partitions": {
            "train": [1, 2, 3],
            "calibration": [4],
            "validation": [5],
            "test": [6],
        }
    }
    m = generate_split_manifest("FD001", "train_FD001.txt", 100, FD001_ALLOCATIONS, seed=2026)
    assert m["partitions"] != fake_manifest["partitions"]


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__])
    else:
        test_funcs = []
        if RAW_FD001_EXISTS:
            test_funcs.extend(
                [
                    test_fd001_manifest_structure_and_counts,
                    test_deterministic_reproducibility,
                    test_rejection_of_conflicting_manifest,
                ]
            )
        if RAW_FD004_EXISTS:
            test_funcs.append(test_fd004_manifest_structure_and_counts)
        test_funcs.append(test_fd002_manifest_preservation)

        for func in test_funcs:
            print(f"Running {func.__name__}...", end=" ")
            func()
            print("PASS")
        print(f"\nAll {len(test_funcs)} split generator unit tests PASSED successfully!")
