"""Tests for FD002 lifetime-quartile provenance reconstruction."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.reconstruct_fd002_quartile_provenance import (
    DEFAULT_MANIFEST_FILE,
    DEFAULT_OUTPUT_FILE,
    DEFAULT_RAW_FILE,
    EXPECTED_ENGINE_COUNT,
    EXPECTED_QUARTILE_SIZE,
    build_provenance_record,
    reconstruct_quartiles,
    validate_raw_fd002_dataframe,
    verify_frozen_manifest,
    write_or_verify_provenance,
)


def _create_synthetic_run_to_failure(
    lifetimes: dict[int, int],
) -> pd.DataFrame:
    """Create synthetic (unit, cycle) DataFrame from a mapping of unit -> lifetime T."""
    rows: list[dict[str, int]] = []
    for unit, T in sorted(lifetimes.items()):
        for c in range(1, T + 1):
            rows.append({"unit": unit, "cycle": c})
    return pd.DataFrame(rows)


def test_synthetic_sorting_by_t_and_engine_id() -> None:
    """Verify that sorting orders engines by lifetime T ascending, then engine_id ascending."""
    # 260 engines with varying lifetimes
    lifetimes = {i: 100 + (i % 20) for i in range(1, EXPECTED_ENGINE_COUNT + 1)}
    df = _create_synthetic_run_to_failure(lifetimes)

    quartiles = reconstruct_quartiles(df)

    # Collect all engines in quartile order
    all_ordered_engines: list[int] = []
    for q_name in ["Q1", "Q2", "Q3", "Q4"]:
        all_ordered_engines.extend(quartiles[q_name]["engine_ids"])

    # Verify overall sorting condition
    sorted_pairs = [(lifetimes[eid], eid) for eid in all_ordered_engines]
    expected_pairs = sorted([(lifetimes[eid], eid) for eid in range(1, EXPECTED_ENGINE_COUNT + 1)])
    assert sorted_pairs == expected_pairs


def test_synthetic_tie_breaking_equal_lifetime() -> None:
    """Verify that tie-breaking on equal lifetime uses ascending engine_id."""
    # All engines have the exact same lifetime T=150
    lifetimes = dict.fromkeys(range(1, EXPECTED_ENGINE_COUNT + 1), 150)
    df = _create_synthetic_run_to_failure(lifetimes)

    quartiles = reconstruct_quartiles(df)

    assert quartiles["Q1"]["engine_ids"] == list(range(1, 66))
    assert quartiles["Q2"]["engine_ids"] == list(range(66, 131))
    assert quartiles["Q3"]["engine_ids"] == list(range(131, 196))
    assert quartiles["Q4"]["engine_ids"] == list(range(196, 261))


def test_synthetic_four_equal_quartiles_and_disjointness() -> None:
    """Verify 4 equal quartiles are produced, disjoint, and union covers 1..260."""
    lifetimes = {i: 100 + i for i in range(1, EXPECTED_ENGINE_COUNT + 1)}
    df = _create_synthetic_run_to_failure(lifetimes)

    quartiles = reconstruct_quartiles(df)

    seen: set[int] = set()
    for q_name in ["Q1", "Q2", "Q3", "Q4"]:
        q_data = quartiles[q_name]
        assert q_data["engine_count"] == EXPECTED_QUARTILE_SIZE
        assert len(q_data["engine_ids"]) == EXPECTED_QUARTILE_SIZE
        eids = set(q_data["engine_ids"])
        assert len(eids) == EXPECTED_QUARTILE_SIZE
        assert not seen.intersection(eids), f"Overlap in {q_name}"
        seen.update(eids)

    assert seen == set(range(1, EXPECTED_ENGINE_COUNT + 1))


def test_synthetic_invalid_engine_ids_rejected() -> None:
    """Verify that non-positive, non-consecutive, or float engine IDs are rejected."""
    # Missing engine 260, engine 261 instead
    lifetimes = dict.fromkeys(range(1, EXPECTED_ENGINE_COUNT), 100)
    lifetimes[EXPECTED_ENGINE_COUNT + 1] = 100
    df = _create_synthetic_run_to_failure(lifetimes)

    with pytest.raises(ValueError, match="Expected unit IDs 1 through 260"):
        validate_raw_fd002_dataframe(df)

    # Float unit
    df_float = pd.DataFrame({"unit": [1.5, 2.0], "cycle": [1, 1]})
    with pytest.raises(ValueError, match="fractional values"):
        validate_raw_fd002_dataframe(df_float)

    # Boolean unit
    df_bool = pd.DataFrame({"unit": [True, False], "cycle": [1, 2]})
    with pytest.raises(ValueError, match="boolean"):
        validate_raw_fd002_dataframe(df_bool)


def test_synthetic_non_consecutive_cycles_rejected() -> None:
    """Verify that cycles not starting at 1 or containing gaps are rejected."""
    # Engine 1 starts at cycle 2
    lifetimes = dict.fromkeys(range(1, EXPECTED_ENGINE_COUNT + 1), 100)
    df = _create_synthetic_run_to_failure(lifetimes)
    # Corrupt engine 1 to start at cycle 2
    df.loc[df["unit"] == 1, "cycle"] = df.loc[df["unit"] == 1, "cycle"] + 1
    with pytest.raises(ValueError, match="does not start at cycle 1"):
        validate_raw_fd002_dataframe(df)

    # Engine 1 has gap: replace cycle 2 with cycle 3
    df_gap = _create_synthetic_run_to_failure(lifetimes)
    df_gap.loc[(df_gap["unit"] == 1) & (df_gap["cycle"] == 2), "cycle"] = 3
    with pytest.raises(ValueError, match="(without gaps|Duplicate)"):
        validate_raw_fd002_dataframe(df_gap)


def test_synthetic_duplicate_unit_cycle_rejected() -> None:
    """Verify that duplicate (unit, cycle) pairs are rejected."""
    df = pd.DataFrame({"unit": [1, 1], "cycle": [1, 1]})
    with pytest.raises(ValueError, match="Duplicate"):
        validate_raw_fd002_dataframe(df)


def test_synthetic_reconstruction_does_not_alter_frozen_partitions(tmp_path: Path) -> None:
    """Verify that verify_frozen_manifest validates exact counts and SHA-256."""
    assert DEFAULT_MANIFEST_FILE.exists()
    verif = verify_frozen_manifest(DEFAULT_MANIFEST_FILE)
    assert (
        verif["manifest_sha256"]
        == "57c815e4c97d9016bbfe9c91ab90738df0f3487910df889a0c631dde71894e41"
    )
    assert verif["partition_counts"]["train"] == 130
    assert verif["partition_counts"]["calibration"] == 52
    assert verif["partition_counts"]["validation"] == 26
    assert verif["partition_counts"]["test"] == 52
    assert verif["partition_counts"]["total"] == 260


def test_synthetic_conflicting_provenance_rejected(tmp_path: Path) -> None:
    """Verify write_or_verify_provenance fails loudly when existing content differs."""
    out_file = tmp_path / "provenance.json"
    record1 = {"dataset": "FD002", "status": "reconstructed", "value": 1}
    record2 = {"dataset": "FD002", "status": "reconstructed", "value": 2}

    # Write initial
    write_or_verify_provenance(out_file, record1)
    assert out_file.exists()

    # Re-verify identical succeeds
    write_or_verify_provenance(out_file, record1)

    # Conflicting record raises ValueError
    with pytest.raises(ValueError, match="conflicts with regenerated"):
        write_or_verify_provenance(out_file, record2)


@pytest.mark.integration
def test_real_fd002_quartile_provenance_reconstruction() -> None:
    """Integration test validating actual C-MAPSS FD002 raw data and committed provenance."""
    if not DEFAULT_RAW_FILE.exists():
        pytest.skip(f"Raw data file {DEFAULT_RAW_FILE} not available")

    assert DEFAULT_OUTPUT_FILE.exists(), (
        f"Committed provenance artifact {DEFAULT_OUTPUT_FILE} missing"
    )

    df_raw = pd.read_csv(
        DEFAULT_RAW_FILE,
        sep=r"\s+",
        header=None,
        usecols=[0, 1],
        names=["unit", "cycle"],
    )

    record = build_provenance_record(DEFAULT_RAW_FILE, DEFAULT_MANIFEST_FILE, df_raw)
    committed = json.loads(DEFAULT_OUTPUT_FILE.read_text(encoding="utf-8"))

    assert record == committed
    assert record["verification"]["quartiles_disjoint"] is True
    assert record["verification"]["quartiles_union_equals_all_engines"] is True
    assert record["verification"]["frozen_manifest_partitions_unchanged"] is True
