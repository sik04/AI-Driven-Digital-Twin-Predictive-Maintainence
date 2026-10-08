"""Deterministic engine-level split manifest generator for C-MAPSS datasets.

Generates stratified engine-level partition split manifests for FD001 and FD004
using lifetime-rank quartile stratification with PCG64 PRNG.

FD002 manifest is preserved byte-for-byte and not modified by this script.
"""

# ruff: noqa: E402
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "raw" / "cmapss"
SPLITS_DIR = REPO_ROOT / "data" / "splits"

FD001_ALLOCATIONS = [
    # (train, cal, val, test)
    (13, 5, 2, 5),  # Q1 (25)
    (12, 5, 3, 5),  # Q2 (25)
    (13, 5, 2, 5),  # Q3 (25)
    (12, 5, 3, 5),  # Q4 (25)
]

FD004_ALLOCATIONS = [
    # (train, cal, val, test)
    (31, 13, 6, 13),  # Q1 (63)
    (31, 13, 6, 12),  # Q2 (62)
    (31, 12, 7, 12),  # Q3 (62)
    (31, 12, 6, 13),  # Q4 (62)
]


def _compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_trajectory(df: pd.DataFrame, expected_unit_count: int, dataset_name: str) -> None:
    """Validate engine count, cycle monotonicity, and non-empty trajectories."""
    units = df["unit"].unique()
    if len(units) != expected_unit_count:
        raise ValueError(
            f"{dataset_name}: Expected {expected_unit_count} engines, got {len(units)}"
        )

    for unit, group in df.groupby("unit"):
        cycles = group["cycle"].values
        if len(cycles) == 0:
            raise ValueError(f"{dataset_name} Engine {unit}: empty trajectory")
        if cycles[0] != 1:
            raise ValueError(f"{dataset_name} Engine {unit}: does not start at cycle 1")
        if not np.array_equal(cycles, np.arange(1, len(cycles) + 1)):
            raise ValueError(f"{dataset_name} Engine {unit}: cycles are not strictly consecutive")


def generate_split_manifest(
    dataset_name: str,
    raw_filename: str,
    expected_unit_count: int,
    allocations: list[tuple[int, int, int, int]],
    seed: int = 2026,
) -> dict[str, Any]:
    """Generate engine split manifest according to locked lifetime quartile algorithm."""
    file_path = DATA_DIR / raw_filename
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    file_hash = _compute_sha256(file_path)

    # 1. Read unit and cycle columns
    df = pd.read_csv(
        file_path,
        sep=r"\s+",
        header=None,
        usecols=[0, 1],
        names=["unit", "cycle"],
    )

    # 2. Validate trajectory integrity
    validate_trajectory(df, expected_unit_count, dataset_name)

    # 3. Compute T = max(cycle) per engine
    max_cycles = (
        df.groupby("unit")["cycle"]
        .max()
        .reset_index()
        .rename(columns={"unit": "engine_id", "cycle": "T"})
    )

    # 4. Sort engines by (T, engine_id)
    max_cycles_sorted = max_cycles.sort_values(by=["T", "engine_id"]).reset_index(drop=True)

    # 5. Divide into 4 lifetime quartiles
    quartile_arrays = np.array_split(max_cycles_sorted["engine_id"].values, 4)

    # 7. Initialize separate PRNG
    rng = np.random.Generator(np.random.PCG64(seed))

    train_ids: list[int] = []
    cal_ids: list[int] = []
    val_ids: list[int] = []
    test_ids: list[int] = []

    quartile_membership_info: list[dict[str, Any]] = []

    # 8-10. Process quartiles
    for q_idx, (q_engines, (n_tr, n_ca, n_va, n_te)) in enumerate(
        zip(quartile_arrays, allocations, strict=True)
    ):
        if len(q_engines) != (n_tr + n_ca + n_va + n_te):
            raise ValueError(
                f"Allocation mismatch for Quartile {q_idx + 1}: "
                f"len={len(q_engines)}, expected={n_tr + n_ca + n_va + n_te}"
            )

        permuted = rng.permutation(q_engines)

        q_tr = permuted[:n_tr].tolist()
        q_ca = permuted[n_tr : n_tr + n_ca].tolist()
        q_va = permuted[n_tr + n_ca : n_tr + n_ca + n_va].tolist()
        q_te = permuted[n_tr + n_ca + n_va :].tolist()

        train_ids.extend(q_tr)
        cal_ids.extend(q_ca)
        val_ids.extend(q_va)
        test_ids.extend(q_te)

        quartile_membership_info.append(
            {
                "quartile": f"Q{q_idx + 1}",
                "size": len(q_engines),
                "allocations": {
                    "train": n_tr,
                    "calibration": n_ca,
                    "validation": n_va,
                    "test": n_te,
                },
                "min_T": int(max_cycles[max_cycles["engine_id"].isin(q_engines)]["T"].min()),
                "max_T": int(max_cycles[max_cycles["engine_id"].isin(q_engines)]["T"].max()),
            }
        )

    # 11. Combine and sort partition IDs
    train_ids.sort()
    cal_ids.sort()
    val_ids.sort()
    test_ids.sort()

    total_count = len(train_ids) + len(cal_ids) + len(val_ids) + len(test_ids)
    if total_count != expected_unit_count:
        raise ValueError(
            f"Total partitioned engines ({total_count}) != expected ({expected_unit_count})"
        )

    # Check pairwise disjointness
    all_sets = [set(train_ids), set(cal_ids), set(val_ids), set(test_ids)]
    for i in range(len(all_sets)):
        for j in range(i + 1, len(all_sets)):
            overlap = all_sets[i].intersection(all_sets[j])
            if overlap:
                raise ValueError(f"Partition overlap detected between {i} and {j}: {overlap}")

    union_set = set(train_ids) | set(cal_ids) | set(val_ids) | set(test_ids)
    expected_set = set(max_cycles["engine_id"].values)
    if union_set != expected_set:
        raise ValueError("Union of partition engine IDs does not match full engine set")

    manifest = {
        "dataset": dataset_name,
        "seed": seed,
        "generator_version": "lifetime_rank_quartiles_v1",
        "rng_algorithm": "PCG64",
        "source_filename": raw_filename,
        "source_sha256": file_hash,
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "counts": {
            "train": len(train_ids),
            "calibration": len(cal_ids),
            "validation": len(val_ids),
            "test": len(test_ids),
            "total": total_count,
        },
        "ratios": {
            "train": round(len(train_ids) / total_count, 4),
            "calibration": round(len(cal_ids) / total_count, 4),
            "validation": round(len(val_ids) / total_count, 4),
            "test": round(len(test_ids) / total_count, 4),
        },
        "quartile_membership": quartile_membership_info,
        "partitions": {
            "train": [int(x) for x in train_ids],
            "calibration": [int(x) for x in cal_ids],
            "validation": [int(x) for x in val_ids],
            "test": [int(x) for x in test_ids],
        },
    }

    return manifest


def main() -> None:
    """Generate and write FD001 and FD004 split manifests."""
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    tasks = [
        ("FD001", "train_FD001.txt", 100, FD001_ALLOCATIONS, "fd001_engine_split_seed_2026.json"),
        ("FD004", "train_FD004.txt", 249, FD004_ALLOCATIONS, "fd004_engine_split_seed_2026.json"),
    ]

    for dataset_name, raw_filename, expected_units, allocations, output_filename in tasks:
        out_path = SPLITS_DIR / output_filename
        manifest = generate_split_manifest(
            dataset_name, raw_filename, expected_units, allocations, seed=2026
        )

        if out_path.exists():
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            if existing.get("partitions") != manifest["partitions"]:
                raise ValueError(
                    f"Discrepancy detected! Existing {output_filename} partitions "
                    "do not match newly generated partitions."
                )
            print(f"{output_filename} exists and matches newly generated partitions.")
        else:
            out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            print(f"Successfully generated {out_path}")


if __name__ == "__main__":
    main()
