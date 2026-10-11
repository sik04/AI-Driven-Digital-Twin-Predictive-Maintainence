"""Strict raw C-MAPSS run-to-failure data loader with full integrity validation.

Enforces zero missing values, non-infinite data, exact consecutive engine IDs (1..N),
consecutive unit cycle trajectories starting at 1, and deterministic sorting.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from intellitwin.data.schema import RAW_COLUMNS


def load_cmapss_run_to_failure(
    path: Path | str,
    dataset_name: str,
    expected_engine_count: int,
) -> pd.DataFrame:
    """Load and strictly validate a C-MAPSS run-to-failure dataset file.

    Parameters
    ----------
    path : Path or str
        Path to the whitespace-delimited raw C-MAPSS file.
    dataset_name : str
        Name of the dataset (e.g. "FD001", "FD002", "FD004").
    expected_engine_count : int
        Expected total number of distinct engines (e.g. 100, 260, 249).

    Returns
    -------
    pd.DataFrame
        Validated DataFrame sorted ascending by (unit, cycle) with exactly 26 columns.

    Raises
    ------
    ValueError
        If the file is missing or violates any integrity or formatting constraint.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError(f"Raw C-MAPSS file not found for dataset '{dataset_name}': {file_path}")

    # Read whitespace-delimited file
    try:
        df = pd.read_csv(file_path, sep=r"\s+", header=None)
    except Exception as exc:
        raise ValueError(f"Failed to read C-MAPSS raw file '{file_path}': {exc}") from exc

    if df.shape[1] != len(RAW_COLUMNS):
        raise ValueError(
            f"Dataset '{dataset_name}' raw file has {df.shape[1]} columns, "
            f"expected exactly {len(RAW_COLUMNS)}."
        )

    df.columns = list(RAW_COLUMNS)

    # 1. Null / NaN check
    if df.isna().any().any():
        null_cols = df.columns[df.isna().any()].tolist()
        raise ValueError(
            f"Dataset '{dataset_name}' contains null/NaN values in columns: {null_cols}"
        )

    # 2. Check for infinite values across all numeric columns
    numeric_df = df.apply(pd.to_numeric, errors="coerce")
    if numeric_df.isna().any().any():
        non_num_cols = df.columns[numeric_df.isna().any()].tolist()
        raise ValueError(
            f"Dataset '{dataset_name}' contains non-numeric values in columns: {non_num_cols}"
        )

    is_infinite = np.isinf(numeric_df.to_numpy())
    if is_infinite.any():
        raise ValueError(f"Dataset '{dataset_name}' contains positive or negative infinite values.")

    # 3. Validate integral unit and cycle IDs
    unit_raw = df["unit"].to_numpy()
    cycle_raw = df["cycle"].to_numpy()

    if not np.all(np.equal(np.mod(unit_raw, 1), 0)):
        raise ValueError(f"Dataset '{dataset_name}' contains non-integral engine IDs in 'unit'.")
    if not np.all(np.equal(np.mod(cycle_raw, 1), 0)):
        raise ValueError(f"Dataset '{dataset_name}' contains non-integral cycle IDs in 'cycle'.")

    df["unit"] = df["unit"].astype(int)
    df["cycle"] = df["cycle"].astype(int)

    # Convert all feature columns to float64 explicitly
    for col in RAW_COLUMNS[2:]:
        df[col] = df[col].astype(np.float64)

    # 4. Engine and cycle positivity
    if (df["unit"] <= 0).any():
        raise ValueError(f"Dataset '{dataset_name}' contains engine IDs <= 0.")
    if (df["cycle"] <= 0).any():
        raise ValueError(f"Dataset '{dataset_name}' contains cycle IDs <= 0.")

    # 5. Duplicate (unit, cycle) rows
    duplicates = df.duplicated(subset=["unit", "cycle"])
    if duplicates.any():
        dup_count = int(duplicates.sum())
        raise ValueError(
            f"Dataset '{dataset_name}' contains {dup_count} duplicate (unit, cycle) rows."
        )

    # 6. Sort deterministically by unit ascending, cycle ascending
    df = df.sort_values(by=["unit", "cycle"]).reset_index(drop=True)

    # 7. Validate engine IDs are exactly consecutive 1..expected_engine_count
    unique_units = np.sort(df["unit"].unique())
    if len(unique_units) != expected_engine_count:
        raise ValueError(
            f"Dataset '{dataset_name}' contains {len(unique_units)} unique engines, "
            f"expected exactly {expected_engine_count}."
        )

    expected_units = np.arange(1, expected_engine_count + 1)
    if not np.array_equal(unique_units, expected_units):
        missing = set(expected_units) - set(unique_units)
        extra = set(unique_units) - set(expected_units)
        raise ValueError(
            f"Dataset '{dataset_name}' engine IDs are not consecutive 1..{expected_engine_count}. "
            f"Missing: {sorted(missing)[:5]}, Extra: {sorted(extra)[:5]}"
        )

    # 8. Per-engine trajectory validation: starts at cycle 1, consecutive, monotonic
    for unit_id, group in df.groupby("unit", sort=False):
        cycles = group["cycle"].to_numpy()
        if len(cycles) == 0:
            raise ValueError(f"Engine {unit_id} has no observations.")
        if cycles[0] != 1:
            raise ValueError(
                f"Engine {unit_id} trajectory does not start at cycle 1 (starts at {cycles[0]})."
            )
        # Check consecutive increments of exactly 1
        diffs = np.diff(cycles)
        if not np.all(diffs == 1):
            bad_idx = int(np.where(diffs != 1)[0][0])
            raise ValueError(
                f"Engine {unit_id} has non-consecutive or non-monotonic cycles: "
                f"cycle {cycles[bad_idx]} followed by {cycles[bad_idx + 1]}."
            )

    return df
