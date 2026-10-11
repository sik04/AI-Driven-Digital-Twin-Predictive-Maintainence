"""Automated unit and integration tests for the deterministic engine split generator."""

import hashlib
import json
import random
from pathlib import Path
from typing import Any

import pytest

from scripts.generate_engine_splits import (
    FD001_ALLOCATIONS,
    FD004_ALLOCATIONS,
    generate_split_manifest,
    write_or_verify_manifest,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SPLITS_DIR = REPO_ROOT / "data" / "splits"
RAW_DATA_DIR = REPO_ROOT / "data" / "raw" / "cmapss"
RAW_FD001_PATH = RAW_DATA_DIR / "train_FD001.txt"
RAW_FD004_PATH = RAW_DATA_DIR / "train_FD004.txt"

FD002_FROZEN_SHA256 = "57c815e4c97d9016bbfe9c91ab90738df0f3487910df889a0c631dde71894e41"


def _create_synthetic_raw_file(
    filepath: Path,
    engine_lifetimes: dict[int, int],
    shuffle_rows: bool = False,
    extra_cols: int = 3,
) -> None:
    """Helper to write synthetic C-MAPSS formatted files."""
    rows: list[str] = []
    for unit, lifetime in engine_lifetimes.items():
        for cycle in range(1, lifetime + 1):
            extra = " ".join([f"{float(i):.4f}" for i in range(extra_cols)])
            rows.append(f"{unit} {cycle} {extra}")

    if shuffle_rows:
        random.seed(42)
        random.shuffle(rows)

    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(rows) + "\n", encoding="utf-8")


SYNTHETIC_ALLOCATIONS_8 = [
    (1, 0, 0, 1),  # Q1 (2 engines: 1 train, 0 cal, 0 val, 1 test)
    (1, 1, 0, 0),  # Q2 (2 engines: 1 train, 1 cal, 0 val, 0 test)
    (0, 1, 1, 0),  # Q3 (2 engines: 0 train, 1 cal, 1 val, 0 test)
    (1, 0, 0, 1),  # Q4 (2 engines: 1 train, 0 cal, 0 val, 1 test)
]


# ==============================================================================
# SECTION A: Core Synthetic Tests (Never skip, run without NASA raw data)
# ==============================================================================


def test_synthetic_counts_and_disjointness(tmp_path: Path) -> None:
    """Verify synthetic split counts, disjointness, and full engine coverage."""
    raw_file = tmp_path / "train_SYNTH.txt"
    lifetimes = {i: 10 + i * 5 for i in range(1, 9)}
    _create_synthetic_raw_file(raw_file, lifetimes)

    manifest = generate_split_manifest(
        "SYNTH",
        raw_file.name,
        expected_unit_count=8,
        allocations=SYNTHETIC_ALLOCATIONS_8,
        seed=2026,
        raw_dir=tmp_path,
    )

    counts = manifest["counts"]
    assert counts["train"] == 3
    assert counts["calibration"] == 2
    assert counts["validation"] == 1
    assert counts["test"] == 2
    assert counts["total"] == 8

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
    assert tr | ca | va | te == set(range(1, 9))


def test_synthetic_exact_quartile_allocations_and_metadata(tmp_path: Path) -> None:
    """Verify quartile allocations and engine_ids metadata."""
    raw_file = tmp_path / "train_SYNTH.txt"
    lifetimes = {i: 10 + i * 5 for i in range(1, 9)}
    _create_synthetic_raw_file(raw_file, lifetimes)

    manifest = generate_split_manifest(
        "SYNTH",
        raw_file.name,
        expected_unit_count=8,
        allocations=SYNTHETIC_ALLOCATIONS_8,
        seed=2026,
        raw_dir=tmp_path,
    )

    qm = manifest["quartile_membership"]
    assert len(qm) == 4
    for q_idx, entry in enumerate(qm):
        expected_alloc = {
            "train": SYNTHETIC_ALLOCATIONS_8[q_idx][0],
            "calibration": SYNTHETIC_ALLOCATIONS_8[q_idx][1],
            "validation": SYNTHETIC_ALLOCATIONS_8[q_idx][2],
            "test": SYNTHETIC_ALLOCATIONS_8[q_idx][3],
        }
        assert entry["allocations"] == expected_alloc
        assert "engine_ids" in entry
        assert len(entry["engine_ids"]) == entry["size"]
        assert entry["size"] == 2


def test_synthetic_deterministic_reproducibility(tmp_path: Path) -> None:
    """Verify same input and seed produce identical manifests."""
    raw_file = tmp_path / "train_SYNTH.txt"
    lifetimes = {i: 10 + i * 5 for i in range(1, 9)}
    _create_synthetic_raw_file(raw_file, lifetimes)

    m1 = generate_split_manifest(
        "SYNTH",
        raw_file.name,
        expected_unit_count=8,
        allocations=SYNTHETIC_ALLOCATIONS_8,
        seed=2026,
        raw_dir=tmp_path,
    )
    m2 = generate_split_manifest(
        "SYNTH",
        raw_file.name,
        expected_unit_count=8,
        allocations=SYNTHETIC_ALLOCATIONS_8,
        seed=2026,
        raw_dir=tmp_path,
    )

    assert m1["partitions"] == m2["partitions"]
    assert m1["quartile_membership"] == m2["quartile_membership"]


def test_synthetic_stable_under_row_shuffling(tmp_path: Path) -> None:
    """Verify row shuffling in raw file does not alter generated manifest."""
    raw_sorted = tmp_path / "train_sorted.txt"
    raw_shuffled = tmp_path / "train_shuffled.txt"
    lifetimes = {i: 10 + i * 5 for i in range(1, 9)}

    _create_synthetic_raw_file(raw_sorted, lifetimes, shuffle_rows=False)
    _create_synthetic_raw_file(raw_shuffled, lifetimes, shuffle_rows=True)

    m_sorted = generate_split_manifest(
        "SYNTH",
        raw_sorted.name,
        expected_unit_count=8,
        allocations=SYNTHETIC_ALLOCATIONS_8,
        seed=2026,
        raw_dir=tmp_path,
    )
    m_shuffled = generate_split_manifest(
        "SYNTH",
        raw_shuffled.name,
        expected_unit_count=8,
        allocations=SYNTHETIC_ALLOCATIONS_8,
        seed=2026,
        raw_dir=tmp_path,
    )

    assert m_sorted["partitions"] == m_shuffled["partitions"]
    assert m_sorted["quartile_membership"] == m_shuffled["quartile_membership"]


def test_synthetic_lifetime_ties_resolved_by_engine_id(tmp_path: Path) -> None:
    """Verify engines with identical lifetimes are ordered by engine_id."""
    raw_file = tmp_path / "train_ties.txt"
    # Engines 1, 2, 3, 4 all have identical lifetime 50
    # Engines 5, 6, 7, 8 all have identical lifetime 100
    lifetimes = {1: 50, 2: 50, 3: 50, 4: 50, 5: 100, 6: 100, 7: 100, 8: 100}
    _create_synthetic_raw_file(raw_file, lifetimes, shuffle_rows=True)

    manifest = generate_split_manifest(
        "SYNTH",
        raw_file.name,
        expected_unit_count=8,
        allocations=SYNTHETIC_ALLOCATIONS_8,
        seed=2026,
        raw_dir=tmp_path,
    )

    qm = manifest["quartile_membership"]
    # Q1 and Q2 partition engines {1, 2, 3, 4} sorted by engine ID: [1, 2] in Q1, [3, 4] in Q2
    assert qm[0]["engine_ids"] == [1, 2]
    assert qm[1]["engine_ids"] == [3, 4]
    # Q3 and Q4 partition engines {5, 6, 7, 8} sorted by engine ID: [5, 6] in Q3, [7, 8] in Q4
    assert qm[2]["engine_ids"] == [5, 6]
    assert qm[3]["engine_ids"] == [7, 8]


def test_synthetic_invalid_inputs_rejection(tmp_path: Path) -> None:
    """Verify rejection of invalid IDs, cycles, duplicates, gaps, and missing files."""
    # 1. Missing file
    with pytest.raises(FileNotFoundError):
        generate_split_manifest(
            "SYNTH",
            "nonexistent.txt",
            8,
            SYNTHETIC_ALLOCATIONS_8,
            raw_dir=tmp_path,
        )

    # 2. Empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Input dataframe is empty"):
        generate_split_manifest(
            "SYNTH",
            empty_file.name,
            8,
            SYNTHETIC_ALLOCATIONS_8,
            raw_dir=tmp_path,
        )

    # 3. Duplicate (unit, cycle)
    dup_file = tmp_path / "dup.txt"
    dup_file.write_text("1 1 0.0\n1 1 0.0\n1 2 0.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        generate_split_manifest(
            "SYNTH",
            dup_file.name,
            1,
            [(1, 0, 0, 0)] * 4,
            raw_dir=tmp_path,
        )

    # 4. Cycle gap (1, 3 instead of 1, 2, 3)
    gap_file = tmp_path / "gap.txt"
    gap_file.write_text("1 1 0.0\n1 3 0.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cycles do not match"):
        generate_split_manifest(
            "SYNTH",
            gap_file.name,
            1,
            [(1, 0, 0, 0)] * 4,
            raw_dir=tmp_path,
        )

    # 5. Missing cycle 1 (starts at 2)
    nocycle1_file = tmp_path / "nocycle1.txt"
    nocycle1_file.write_text("1 2 0.0\n1 3 0.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="does not start at cycle 1"):
        generate_split_manifest(
            "SYNTH",
            nocycle1_file.name,
            1,
            [(1, 0, 0, 0)] * 4,
            raw_dir=tmp_path,
        )

    # 6. Fractional cycle
    frac_file = tmp_path / "frac.txt"
    frac_file.write_text("1 1.5 0.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fractional"):
        generate_split_manifest(
            "SYNTH",
            frac_file.name,
            1,
            [(1, 0, 0, 0)] * 4,
            raw_dir=tmp_path,
        )

    # 7. Non-positive ID
    neg_file = tmp_path / "neg.txt"
    neg_file.write_text("-1 1 0.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-positive"):
        generate_split_manifest(
            "SYNTH",
            neg_file.name,
            1,
            [(1, 0, 0, 0)] * 4,
            raw_dir=tmp_path,
        )

    # 8. Missing required column (only 1 column)
    single_col = tmp_path / "single_col.txt"
    single_col.write_text("1\n2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        generate_split_manifest(
            "SYNTH",
            single_col.name,
            1,
            [(1, 0, 0, 0)] * 4,
            raw_dir=tmp_path,
        )


def test_write_or_verify_manifest_lifecycle(tmp_path: Path) -> None:
    """Verify write-or-verify helper correctly writes, preserves, and rejects on conflict."""
    out_file = tmp_path / "manifest.json"
    manifest: dict[str, Any] = {
        "dataset": "SYNTH",
        "seed": 2026,
        "generator_version": "lifetime_rank_quartiles_v1",
        "rng_algorithm": "PCG64",
        "source_filename": "train_SYNTH.txt",
        "source_sha256": "abcdef123456",
        "python_version": "3.10.0",
        "numpy_version": "1.25.0",
        "counts": {"train": 1, "calibration": 1, "validation": 1, "test": 1, "total": 4},
        "ratios": {"train": 0.25, "calibration": 0.25, "validation": 0.25, "test": 0.25},
        "quartile_membership": [
            {
                "quartile": "Q1",
                "size": 1,
                "allocations": {"train": 1, "calibration": 0, "validation": 0, "test": 0},
                "min_T": 10,
                "max_T": 10,
                "engine_ids": [1],
            }
        ],
        "partitions": {
            "train": [1],
            "calibration": [2],
            "validation": [3],
            "test": [4],
        },
    }

    # 1. Missing output: writes manifest, returns True
    written = write_or_verify_manifest(out_file, manifest)
    assert written is True
    assert out_file.exists()
    original_bytes = out_file.read_bytes()

    # 2. Existing matching output with different package versions: leaves file byte-identical
    manifest_diff_env = dict(manifest)
    manifest_diff_env["python_version"] = "3.13.0"
    manifest_diff_env["numpy_version"] = "2.0.0"
    verified = write_or_verify_manifest(out_file, manifest_diff_env)
    assert verified is False
    assert out_file.read_bytes() == original_bytes, "Matching file must remain byte-identical"

    # 3. Conflicting partitions: raises ValueError and leaves file byte-identical
    conflicting_parts = dict(manifest)
    conflicting_parts["partitions"] = {
        "train": [2],
        "calibration": [1],
        "validation": [3],
        "test": [4],
    }
    with pytest.raises(ValueError, match="Conflicting partition membership"):
        write_or_verify_manifest(out_file, conflicting_parts)
    assert out_file.read_bytes() == original_bytes, "File must remain byte-identical after conflict"

    # 4. Conflicting source hash: raises ValueError and leaves file byte-identical
    conflicting_hash = dict(manifest)
    conflicting_hash["source_sha256"] = "wronghash999"
    with pytest.raises(ValueError, match="Conflicting source_sha256"):
        write_or_verify_manifest(out_file, conflicting_hash)
    assert out_file.read_bytes() == original_bytes, (
        "File must remain byte-identical after hash mismatch"
    )

    # 5. Conflicting quartile membership: raises ValueError and leaves file byte-identical
    conflicting_qm = dict(manifest)
    conflicting_qm["quartile_membership"] = []
    with pytest.raises(ValueError, match="Conflicting quartile_membership"):
        write_or_verify_manifest(out_file, conflicting_qm)
    assert out_file.read_bytes() == original_bytes, "File must remain byte-identical after conflict"


# ==============================================================================
# SECTION B: Always-Running Committed Manifest Checks (No raw NASA data needed)
# ==============================================================================


def test_committed_manifests_integrity() -> None:
    """Verify committed FD001, FD004, and FD002 manifests counts, IDs, disjointness, coverage."""
    manifest_specs = [
        ("fd001_engine_split_seed_2026.json", 100, (50, 20, 10, 20)),
        ("fd004_engine_split_seed_2026.json", 249, (124, 50, 25, 50)),
        ("fd002_engine_split_seed_2026.json", 260, (130, 52, 26, 52)),
    ]

    for filename, expected_total, (exp_tr, exp_ca, exp_va, exp_te) in manifest_specs:
        path = SPLITS_DIR / filename
        assert path.exists(), f"Committed manifest {filename} must exist"

        data = json.loads(path.read_text(encoding="utf-8"))
        counts = data["counts"]
        assert counts["total"] == expected_total
        assert counts["train"] == exp_tr
        assert counts["calibration"] == exp_ca
        assert counts["validation"] == exp_va
        assert counts["test"] == exp_te

        parts = data["partitions"]
        tr = set(parts["train"])
        ca = set(parts["calibration"])
        va = set(parts["validation"])
        te = set(parts["test"])

        assert len(tr) == exp_tr
        assert len(ca) == exp_ca
        assert len(va) == exp_va
        assert len(te) == exp_te

        # Disjointness
        assert tr.isdisjoint(ca)
        assert tr.isdisjoint(va)
        assert tr.isdisjoint(te)
        assert ca.isdisjoint(va)
        assert ca.isdisjoint(te)
        assert va.isdisjoint(te)

        # Full coverage
        assert tr | ca | va | te == set(range(1, expected_total + 1))


def test_fd002_byte_hash_preservation() -> None:
    """Verify FD002 manifest SHA-256 byte hash matches starting main revision exactly."""
    fd002_path = SPLITS_DIR / "fd002_engine_split_seed_2026.json"
    assert fd002_path.exists(), "FD002 manifest must exist"
    actual_hash = hashlib.sha256(fd002_path.read_bytes()).hexdigest()
    assert actual_hash == FD002_FROZEN_SHA256, (
        f"FD002 byte hash changed: {actual_hash} != {FD002_FROZEN_SHA256}"
    )


# ==============================================================================
# SECTION C: Real-Data Integration Tests (Marked with @pytest.mark.integration)
# ==============================================================================


@pytest.mark.integration
def test_real_data_fd001_regeneration() -> None:
    """Verify FD001 manifest regeneration matches committed manifest exactly."""
    if not RAW_FD001_PATH.exists():
        pytest.skip(f"NASA raw data file not present: {RAW_FD001_PATH}")

    committed = json.loads(
        (SPLITS_DIR / "fd001_engine_split_seed_2026.json").read_text(encoding="utf-8")
    )
    generated = generate_split_manifest(
        "FD001",
        "train_FD001.txt",
        100,
        FD001_ALLOCATIONS,
        seed=2026,
    )

    assert generated["partitions"] == committed["partitions"]
    assert generated["counts"] == committed["counts"]
    assert generated["source_sha256"] == committed["source_sha256"]
    assert generated["quartile_membership"] == committed["quartile_membership"]


@pytest.mark.integration
def test_real_data_fd004_regeneration() -> None:
    """Verify FD004 manifest regeneration matches committed manifest exactly."""
    if not RAW_FD004_PATH.exists():
        pytest.skip(f"NASA raw data file not present: {RAW_FD004_PATH}")

    committed = json.loads(
        (SPLITS_DIR / "fd004_engine_split_seed_2026.json").read_text(encoding="utf-8")
    )
    generated = generate_split_manifest(
        "FD004",
        "train_FD004.txt",
        249,
        FD004_ALLOCATIONS,
        seed=2026,
    )

    assert generated["partitions"] == committed["partitions"]
    assert generated["counts"] == committed["counts"]
    assert generated["source_sha256"] == committed["source_sha256"]
    assert generated["quartile_membership"] == committed["quartile_membership"]
