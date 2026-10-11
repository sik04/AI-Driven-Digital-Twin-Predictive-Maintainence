"""Deterministic FD002 lifetime-quartile provenance reconstruction utility.

This script reconstructs the lifetime-quartile stratification metadata for FD002
from the raw C-MAPSS run-to-failure trajectories (data/raw/cmapss/train_FD002.txt)
according to the documented original split procedure:
1. Load unit and cycle from train_FD002.txt.
2. Validate strictly (260 engines, positive consecutive 1..260, cycles 1..T with no gaps).
3. Compute engine lifetime T_i = max(cycle).
4. Sort engines ascending by (T_i, engine_id).
5. Divide into 4 contiguous quartiles of 65 engines:
   Q1 (1-65), Q2 (66-130), Q3 (131-195), Q4 (196-260).
6. Verify against frozen manifest (data/splits/fd002_engine_split_seed_2026.json).
7. Write or verify data/splits/fd002_lifetime_quartile_provenance.json.

This script contains NO random operations. It does not modify frozen split partitions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_FILE = REPO_ROOT / "data" / "raw" / "cmapss" / "train_FD002.txt"
DEFAULT_MANIFEST_FILE = REPO_ROOT / "data" / "splits" / "fd002_engine_split_seed_2026.json"
DEFAULT_OUTPUT_FILE = REPO_ROOT / "data" / "splits" / "fd002_lifetime_quartile_provenance.json"

EXPECTED_FROZEN_MANIFEST_SHA256 = "57c815e4c97d9016bbfe9c91ab90738df0f3487910df889a0c631dde71894e41"
EXPECTED_ENGINE_COUNT = 260
EXPECTED_QUARTILE_SIZE = 65


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _validate_integral_series(s: pd.Series, name: str) -> np.ndarray:
    """Validate series contains positive integral values, rejecting booleans, floats, NaN, inf."""
    if len(s) == 0:
        raise ValueError(f"Empty series for {name}")
    if pd.api.types.is_bool_dtype(s.dtype):
        raise ValueError(f"Column '{name}' contains boolean values")
    if s.dtype == object and s.map(lambda x: isinstance(x, bool)).any():
        raise ValueError(f"Column '{name}' contains boolean values")

    try:
        numeric = pd.to_numeric(s, errors="raise")
    except Exception as e:
        raise ValueError(f"Column '{name}' contains non-numeric values: {e}") from e

    vals = numeric.to_numpy(dtype=np.float64)
    if not np.all(np.isfinite(vals)):
        raise ValueError(f"Column '{name}' contains null, NaN, or infinite values")
    if np.any(vals <= 0):
        raise ValueError(f"Column '{name}' contains non-positive values (<= 0)")
    if np.any(vals != np.floor(vals)):
        raise ValueError(f"Column '{name}' contains fractional values")
    max_safe = np.iinfo(np.int64).max
    if np.any(vals > max_safe):
        raise ValueError(f"Column '{name}' contains values exceeding integer range")
    from typing import cast

    return cast(np.ndarray[Any, Any], vals.astype(np.int64))


def validate_raw_fd002_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Strictly validate raw FD002 run-to-failure records."""
    if df is None or df.empty:
        raise ValueError("Raw dataframe is empty or None")
    if "unit" not in df.columns or "cycle" not in df.columns:
        raise ValueError("Missing required columns 'unit' and 'cycle'")

    units = _validate_integral_series(df["unit"], "unit")
    cycles = _validate_integral_series(df["cycle"], "cycle")

    clean_df = pd.DataFrame({"unit": units, "cycle": cycles})

    if clean_df.duplicated(subset=["unit", "cycle"]).any():
        raise ValueError("Duplicate (unit, cycle) records detected in raw FD002")

    clean_df = clean_df.sort_values(by=["unit", "cycle"]).reset_index(drop=True)

    unique_units = clean_df["unit"].unique()
    if len(unique_units) != EXPECTED_ENGINE_COUNT:
        raise ValueError(f"Expected {EXPECTED_ENGINE_COUNT} engines, got {len(unique_units)}")

    expected_ids = np.arange(1, EXPECTED_ENGINE_COUNT + 1)
    if not np.array_equal(np.sort(unique_units), expected_ids):
        raise ValueError(
            f"Expected unit IDs 1 through {EXPECTED_ENGINE_COUNT}, "
            f"got min={unique_units.min()}, max={unique_units.max()}"
        )

    for unit, group in clean_df.groupby("unit", sort=False):
        c_vals = group["cycle"].to_numpy()
        if len(c_vals) == 0:
            raise ValueError(f"Engine {unit}: empty trajectory")
        if c_vals[0] != 1:
            raise ValueError(f"Engine {unit}: does not start at cycle 1 (starts at {c_vals[0]})")
        expected_cycles = np.arange(1, len(c_vals) + 1)
        if not np.array_equal(c_vals, expected_cycles):
            raise ValueError(f"Engine {unit}: cycles do not match 1..{len(c_vals)} without gaps")

    return clean_df


def reconstruct_quartiles(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Compute engine lifetimes, sort by (T, engine_id), and split into 4 equal quartiles."""
    clean_df = validate_raw_fd002_dataframe(df)

    max_cycles = (
        clean_df.groupby("unit")["cycle"]
        .max()
        .reset_index()
        .rename(columns={"unit": "engine_id", "cycle": "T"})
    )

    sorted_df = max_cycles.sort_values(by=["T", "engine_id"]).reset_index(drop=True)

    if len(sorted_df) != EXPECTED_ENGINE_COUNT:
        raise ValueError(f"Expected {EXPECTED_ENGINE_COUNT} engine lifetimes, got {len(sorted_df)}")

    quartiles: dict[str, dict[str, Any]] = {}
    seen_ids: set[int] = set()

    for q_idx in range(4):
        q_name = f"Q{q_idx + 1}"
        start_idx = q_idx * EXPECTED_QUARTILE_SIZE
        end_idx = (q_idx + 1) * EXPECTED_QUARTILE_SIZE
        q_slice = sorted_df.iloc[start_idx:end_idx]

        engine_ids = [int(eid) for eid in q_slice["engine_id"].tolist()]
        min_t = int(q_slice["T"].min())
        max_t = int(q_slice["T"].max())

        if len(engine_ids) != EXPECTED_QUARTILE_SIZE:
            raise ValueError(
                f"Quartile {q_name} size mismatch: got {len(engine_ids)}, "
                f"expected {EXPECTED_QUARTILE_SIZE}"
            )

        if len(set(engine_ids)) != EXPECTED_QUARTILE_SIZE:
            raise ValueError(f"Duplicate engine IDs in {q_name}")

        if seen_ids.intersection(engine_ids):
            raise ValueError(
                f"Overlap detected between {q_name} and previous quartiles: "
                f"{seen_ids.intersection(engine_ids)}"
            )

        seen_ids.update(engine_ids)

        quartiles[q_name] = {
            "engine_ids": engine_ids,
            "min_T": min_t,
            "max_T": max_t,
            "engine_count": EXPECTED_QUARTILE_SIZE,
        }

    if len(seen_ids) != EXPECTED_ENGINE_COUNT:
        raise ValueError(f"Total engines in quartiles ({len(seen_ids)}) != {EXPECTED_ENGINE_COUNT}")
    if seen_ids != set(range(1, EXPECTED_ENGINE_COUNT + 1)):
        raise ValueError("Quartiles union does not match exact engines 1..260")

    return quartiles


def verify_frozen_manifest(manifest_path: Path) -> dict[str, Any]:
    """Verify frozen FD002 split manifest exists and has expected byte hash and partition counts."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Frozen FD002 split manifest not found: {manifest_path}")

    actual_sha256 = compute_sha256(manifest_path)
    if actual_sha256 != EXPECTED_FROZEN_MANIFEST_SHA256:
        raise ValueError(
            f"Frozen manifest SHA-256 mismatch: expected {EXPECTED_FROZEN_MANIFEST_SHA256}, "
            f"got {actual_sha256}"
        )

    content = json.loads(manifest_path.read_text(encoding="utf-8"))
    partitions = content.get("partitions", {})

    expected_counts = {"train": 130, "calibration": 52, "validation": 26, "test": 52}
    actual_counts = {k: len(v) for k, v in partitions.items()}

    for part, exp_cnt in expected_counts.items():
        if actual_counts.get(part) != exp_cnt:
            raise ValueError(
                f"Manifest partition '{part}' count mismatch: expected {exp_cnt}, "
                f"got {actual_counts.get(part)}"
            )

    all_part_ids: set[int] = set()
    for part_ids in partitions.values():
        int_ids = set(part_ids)
        if all_part_ids.intersection(int_ids):
            raise ValueError("Overlapping engine IDs across partitions in frozen manifest")
        all_part_ids.update(int_ids)

    if len(all_part_ids) != EXPECTED_ENGINE_COUNT:
        raise ValueError(
            f"Total unique engines across partitions ({len(all_part_ids)}) "
            f"!= {EXPECTED_ENGINE_COUNT}"
        )
    if all_part_ids != set(range(1, EXPECTED_ENGINE_COUNT + 1)):
        raise ValueError("Frozen manifest partitions do not cover exact engines 1..260")

    return {
        "manifest_sha256": actual_sha256,
        "partition_counts": {**actual_counts, "total": len(all_part_ids)},
    }


def build_provenance_record(
    raw_file: Path,
    manifest_file: Path,
    df_raw: pd.DataFrame,
) -> dict[str, Any]:
    """Build complete provenance record from verified data."""
    raw_sha256 = compute_sha256(raw_file)
    manifest_verification = verify_frozen_manifest(manifest_file)
    quartiles = reconstruct_quartiles(df_raw)

    return {
        "dataset": "FD002",
        "status": "reconstructed_from_documented_original_rule",
        "reconstruction_method": (
            "Deterministic reconstruction of lifetime-rank quartiles from raw C-MAPSS FD002 "
            "run-to-failure trajectories (T_i = max(cycle)) sorted by (T_i, engine_id) ascending, "
            "divided into four equal contiguous strata of 65 engines each, following the "
            "documented original split procedure."
        ),
        "source_raw_file": "data/raw/cmapss/train_FD002.txt",
        "source_raw_sha256": raw_sha256,
        "frozen_split_manifest": "data/splits/fd002_engine_split_seed_2026.json",
        "frozen_split_manifest_sha256": manifest_verification["manifest_sha256"],
        "original_split_seed": 2026,
        "sort_rule": ["engine_lifetime_T", "engine_id"],
        "quartile_definition": (
            "Contiguous slices of 65 engines from the 260 engines sorted ascending by "
            "(T_i, engine_id): Q1 (positions 1-65), Q2 (positions 66-130), "
            "Q3 (positions 131-195), Q4 (positions 196-260)."
        ),
        "quartile_size": EXPECTED_QUARTILE_SIZE,
        "quartile_membership": quartiles,
        "verification": {
            "engine_count_total": EXPECTED_ENGINE_COUNT,
            "quartiles_disjoint": True,
            "quartiles_union_equals_all_engines": True,
            "frozen_manifest_partitions_unchanged": True,
            "frozen_partition_counts": manifest_verification["partition_counts"],
        },
    }


def write_or_verify_provenance(output_file: Path, record: dict[str, Any]) -> None:
    """Write provenance artifact or verify existing file matches exact scientific content."""
    if output_file.exists():
        existing_content = json.loads(output_file.read_text(encoding="utf-8"))
        if existing_content != record:
            raise ValueError(
                f"Existing provenance file '{output_file}' conflicts with regenerated content!\n"
                f"Existing keys: {list(existing_content.keys())}\n"
                f"New keys: {list(record.keys())}"
            )
        print(f"Verified: existing provenance '{output_file}' matches regenerated record exactly.")
    else:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"Successfully wrote reconstructed provenance artifact to '{output_file}'.")


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Reconstruct and verify FD002 lifetime-quartile provenance."
    )
    parser.add_argument(
        "--raw-file",
        type=Path,
        default=DEFAULT_RAW_FILE,
        help="Path to raw train_FD002.txt",
    )
    parser.add_argument(
        "--manifest-file",
        type=Path,
        default=DEFAULT_MANIFEST_FILE,
        help="Path to frozen fd002_engine_split_seed_2026.json",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to output fd002_lifetime_quartile_provenance.json",
    )
    args = parser.parse_args(argv)

    if not args.raw_file.exists():
        print(f"ERROR: Raw data file not found: {args.raw_file}", file=sys.stderr)
        return 1

    if not args.manifest_file.exists():
        print(f"ERROR: Frozen manifest file not found: {args.manifest_file}", file=sys.stderr)
        return 1

    try:
        df_raw = pd.read_csv(
            args.raw_file,
            sep=r"\s+",
            header=None,
            usecols=[0, 1],
            names=["unit", "cycle"],
        )
        record = build_provenance_record(args.raw_file, args.manifest_file, df_raw)
        write_or_verify_provenance(args.output_file, record)
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
