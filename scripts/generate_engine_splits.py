"""Deterministic engine-level split manifest generator for C-MAPSS datasets.

Generates stratified engine-level partition split manifests for FD001 and FD004
using lifetime-rank quartile stratification with PCG64 PRNG.

FD002 manifest is preserved byte-for-byte and not modified by this script.
"""

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


def _validate_integral_series(s: pd.Series, name: str, dataset_name: str) -> np.ndarray[Any, Any]:
    """Validate series contains positive integral values, rejecting booleans, floats, NaN, inf."""
    if len(s) == 0:
        raise ValueError(f"{dataset_name}: Empty series for {name}")
    if pd.api.types.is_bool_dtype(s.dtype):
        raise ValueError(f"{dataset_name}: Column '{name}' contains boolean values")
    if s.dtype == object and s.map(lambda x: isinstance(x, bool)).any():
        raise ValueError(f"{dataset_name}: Column '{name}' contains boolean values")

    try:
        numeric = pd.to_numeric(s, errors="raise")
    except Exception as e:
        raise ValueError(f"{dataset_name}: Column '{name}' contains non-numeric values: {e}") from e

    vals = numeric.to_numpy(dtype=np.float64)
    if not np.all(np.isfinite(vals)):
        raise ValueError(f"{dataset_name}: Column '{name}' contains null, NaN, or infinite values")
    if np.any(vals <= 0):
        raise ValueError(f"{dataset_name}: Column '{name}' contains non-positive values (<= 0)")
    if np.any(vals != np.floor(vals)):
        raise ValueError(f"{dataset_name}: Column '{name}' contains fractional values")
    max_safe = np.iinfo(np.int64).max
    if np.any(vals > max_safe):
        raise ValueError(f"{dataset_name}: Column '{name}' contains values exceeding integer range")
    from typing import cast

    return cast(np.ndarray[Any, Any], vals.astype(np.int64))


def validate_and_normalize_records(
    df: pd.DataFrame,
    expected_unit_count: int,
    dataset_name: str,
    require_consecutive_units: bool = False,
) -> pd.DataFrame:
    """Validate engine count, cycle monotonicity, and return sorted normalized records."""
    if df is None or df.empty:
        raise ValueError(f"{dataset_name}: Input dataframe is empty")
    if "unit" not in df.columns or "cycle" not in df.columns:
        raise ValueError(f"{dataset_name}: Missing required columns 'unit' and 'cycle'")

    units = _validate_integral_series(df["unit"], "unit", dataset_name)
    cycles = _validate_integral_series(df["cycle"], "cycle", dataset_name)

    clean_df = pd.DataFrame({"unit": units, "cycle": cycles})

    if clean_df.duplicated(subset=["unit", "cycle"]).any():
        raise ValueError(f"{dataset_name}: Duplicate (unit, cycle) records detected")

    # Sort validated records by unit and cycle
    clean_df = clean_df.sort_values(by=["unit", "cycle"]).reset_index(drop=True)

    unique_units = clean_df["unit"].unique()
    if len(unique_units) != expected_unit_count:
        raise ValueError(
            f"{dataset_name}: Expected {expected_unit_count} engines, got {len(unique_units)}"
        )

    if require_consecutive_units:
        expected_ids = np.arange(1, expected_unit_count + 1)
        if not np.array_equal(np.sort(unique_units), expected_ids):
            raise ValueError(
                f"{dataset_name}: Expected unit IDs 1 through {expected_unit_count}, "
                f"got min={unique_units.min()}, max={unique_units.max()}"
            )

    for unit, group in clean_df.groupby("unit", sort=False):
        c_vals = group["cycle"].to_numpy()
        if len(c_vals) == 0:
            raise ValueError(f"{dataset_name} Engine {unit}: empty trajectory")
        if c_vals[0] != 1:
            raise ValueError(f"{dataset_name} Engine {unit}: does not start at cycle 1")
        expected_cycles = np.arange(1, len(c_vals) + 1)
        if not np.array_equal(c_vals, expected_cycles):
            raise ValueError(
                f"{dataset_name} Engine {unit}: cycles do not match 1..{len(c_vals)} without gaps"
            )

    return clean_df


def validate_trajectory(df: pd.DataFrame, expected_unit_count: int, dataset_name: str) -> None:
    """Backward compatibility wrapper for trajectory validation."""
    validate_and_normalize_records(df, expected_unit_count, dataset_name)


def generate_split_manifest(
    dataset_name: str,
    raw_filename: str,
    expected_unit_count: int,
    allocations: list[tuple[int, int, int, int]],
    seed: int = 2026,
    *,
    raw_dir: Path | None = None,
    require_consecutive_units: bool = False,
) -> dict[str, Any]:
    """Generate engine split manifest according to locked lifetime quartile algorithm."""
    target_raw_dir = raw_dir or DATA_DIR
    file_path = target_raw_dir / raw_filename
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    file_hash = _compute_sha256(file_path)

    # 1. Read unit and cycle columns
    df_raw = pd.read_csv(
        file_path,
        sep=r"\s+",
        header=None,
        usecols=[0, 1],
        names=["unit", "cycle"],
    )

    # 2. Validate trajectory integrity and normalize records
    df = validate_and_normalize_records(
        df_raw,
        expected_unit_count,
        dataset_name,
        require_consecutive_units=require_consecutive_units or (dataset_name in ("FD001", "FD004")),
    )

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
                "engine_ids": [int(x) for x in q_engines],
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


def write_or_verify_manifest(
    output_path: Path,
    manifest: dict[str, Any],
) -> bool:
    """Write manifest if missing, or verify existing manifest against generated content.

    Returns True if written, False if verified and left unchanged.
    Raises ValueError on conflict.
    """
    if not output_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return True

    existing_bytes = output_path.read_bytes()
    existing = json.loads(existing_bytes.decode("utf-8"))

    # Conflicting dataset, seed, source hash, or generator identity
    for key in (
        "dataset",
        "seed",
        "generator_version",
        "rng_algorithm",
        "source_filename",
        "source_sha256",
    ):
        if existing.get(key) != manifest.get(key):
            raise ValueError(
                f"Conflicting {key} in {output_path.name}: "
                f"existing={existing.get(key)}, generated={manifest.get(key)}"
            )

    # Conflicting partition membership
    if existing.get("partitions") != manifest.get("partitions"):
        raise ValueError(
            f"Conflicting partition membership in {output_path.name}: "
            f"existing partitions do not match generated partitions."
        )

    # Conflicting counts or ratios
    if existing.get("counts") != manifest.get("counts"):
        raise ValueError(f"Conflicting counts in {output_path.name}")
    if existing.get("ratios") != manifest.get("ratios"):
        raise ValueError(f"Conflicting ratios in {output_path.name}")

    # Conflicting quartile membership
    existing_qm = existing.get("quartile_membership", [])
    gen_qm = manifest.get("quartile_membership", [])
    if existing_qm != gen_qm:
        raise ValueError(f"Conflicting quartile_membership in {output_path.name}")

    # Output matches: leave it unchanged (do not overwrite original generation environment)
    return False


def main(*, raw_dir: Path | None = None, splits_dir: Path | None = None) -> None:
    """Generate and write FD001 and FD004 split manifests."""
    target_raw_dir = raw_dir or DATA_DIR
    target_splits_dir = splits_dir or SPLITS_DIR
    target_splits_dir.mkdir(parents=True, exist_ok=True)

    tasks = [
        ("FD001", "train_FD001.txt", 100, FD001_ALLOCATIONS, "fd001_engine_split_seed_2026.json"),
        ("FD004", "train_FD004.txt", 249, FD004_ALLOCATIONS, "fd004_engine_split_seed_2026.json"),
    ]

    # Validate both production manifests before writing either one
    generated: list[tuple[Path, dict[str, Any]]] = []
    for dataset_name, raw_filename, expected_units, allocations, output_filename in tasks:
        out_path = target_splits_dir / output_filename
        manifest = generate_split_manifest(
            dataset_name,
            raw_filename,
            expected_units,
            allocations,
            seed=2026,
            raw_dir=target_raw_dir,
            require_consecutive_units=True,
        )
        generated.append((out_path, manifest))

    for out_path, manifest in generated:
        written = write_or_verify_manifest(out_path, manifest)
        if written:
            print(f"Successfully wrote {out_path}")
        else:
            print(f"{out_path.name} exists and matches generated content; left unchanged.")


if __name__ == "__main__":
    main()
