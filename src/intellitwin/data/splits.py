"""Split manifest loading, strict verification, and partition selection.

Ensures that frozen partition assignments (Train, Calibration, Validation, Test)
are loaded without modification, validated for pairwise disjointness, complete coverage,
exact expected partition counts, and matching dataset name/seed.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

from intellitwin.data.schema import FROZEN_PARTITION_COUNTS

REQUIRED_PARTITIONS: Final[tuple[str, ...]] = (
    "train",
    "calibration",
    "validation",
    "test",
)


@dataclass(frozen=True)
class SplitManifest:
    """Typed container for frozen split manifest partitions."""

    dataset: str
    seed: int
    train: tuple[int, ...]
    calibration: tuple[int, ...]
    validation: tuple[int, ...]
    test: tuple[int, ...]

    def get_partition(self, partition_name: str) -> tuple[int, ...]:
        """Retrieve engine IDs for a named partition."""
        if partition_name == "train":
            return self.train
        if partition_name == "calibration":
            return self.calibration
        if partition_name == "validation":
            return self.validation
        if partition_name == "test":
            return self.test
        raise ValueError(
            f"Unknown partition '{partition_name}'. Expected one of {REQUIRED_PARTITIONS}."
        )


def partition_counts(manifest: SplitManifest) -> dict[str, int]:
    """Derive partition counts directly from a loaded split manifest.

    Parameters
    ----------
    manifest : SplitManifest
        Loaded split manifest.

    Returns
    -------
    dict[str, int]
        Dictionary with keys 'train', 'calibration', 'validation', 'test', 'total'.
    """
    counts = {
        "train": len(manifest.train),
        "calibration": len(manifest.calibration),
        "validation": len(manifest.validation),
        "test": len(manifest.test),
    }
    counts["total"] = sum(counts.values())
    return counts


def load_split_manifest(path: Path | str) -> SplitManifest:
    """Load a split manifest from a JSON file.

    Parameters
    ----------
    path : Path or str
        Path to the JSON manifest file.

    Returns
    -------
    SplitManifest
        Parsed manifest object.
    """
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ValueError(f"Split manifest file not found: {manifest_path}")

    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise ValueError(f"Failed to parse JSON split manifest '{manifest_path}': {exc}") from exc

    if "dataset" not in data or "seed" not in data or "partitions" not in data:
        raise ValueError(
            f"Manifest '{manifest_path}' is missing required top-level keys "
            "('dataset', 'seed', 'partitions')."
        )

    partitions = data["partitions"]
    for p in REQUIRED_PARTITIONS:
        if p not in partitions:
            raise ValueError(f"Manifest '{manifest_path}' partitions section missing '{p}'.")

    return SplitManifest(
        dataset=str(data["dataset"]),
        seed=int(data["seed"]),
        train=tuple(int(x) for x in partitions["train"]),
        calibration=tuple(int(x) for x in partitions["calibration"]),
        validation=tuple(int(x) for x in partitions["validation"]),
        test=tuple(int(x) for x in partitions["test"]),
    )


def validate_split_manifest(
    manifest: SplitManifest,
    expected_dataset: str,
    expected_engine_count: int,
) -> None:
    """Strictly validate that a split manifest conforms to frozen protocol requirements.

    Parameters
    ----------
    manifest : SplitManifest
        Manifest to validate.
    expected_dataset : str
        Expected dataset name (e.g. "FD001", "FD002", "FD004").
    expected_engine_count : int
        Expected total engine count.

    Raises
    ------
    ValueError
        If any validation rule fails.
    """
    if manifest.dataset != expected_dataset:
        raise ValueError(
            f"Manifest dataset mismatch: expected '{expected_dataset}', got '{manifest.dataset}'."
        )

    if manifest.seed != 2026:
        raise ValueError(f"Manifest seed mismatch: expected 2026, got {manifest.seed}.")

    expected_counts = FROZEN_PARTITION_COUNTS.get(expected_dataset)
    if expected_counts is None:
        raise ValueError(f"No frozen counts configured for dataset '{expected_dataset}'.")

    # Verify per-partition counts, uniqueness, positivity
    all_seen: set[int] = set()
    for p_name in REQUIRED_PARTITIONS:
        p_ids = manifest.get_partition(p_name)
        expected_p_count = expected_counts[p_name]

        if len(p_ids) != expected_p_count:
            raise ValueError(
                f"Partition '{p_name}' for '{expected_dataset}' has {len(p_ids)} engines, "
                f"expected frozen count {expected_p_count}."
            )

        # Check positive integers
        for eid in p_ids:
            if eid <= 0:
                raise ValueError(f"Partition '{p_name}' contains non-positive engine ID: {eid}.")

        # Check internal uniqueness
        if len(set(p_ids)) != len(p_ids):
            raise ValueError(f"Partition '{p_name}' contains duplicate engine IDs.")

        # Check disjointness against prior partitions
        overlap = all_seen.intersection(p_ids)
        if overlap:
            raise ValueError(
                f"Partition '{p_name}' overlaps with other partitions: {sorted(overlap)}."
            )
        all_seen.update(p_ids)

    # Verify union equals exactly 1..expected_engine_count
    expected_all = set(range(1, expected_engine_count + 1))
    if all_seen != expected_all:
        missing = expected_all - all_seen
        extra = all_seen - expected_all
        raise ValueError(
            f"Union of partitions does not match engines 1..{expected_engine_count}. "
            f"Missing: {sorted(missing)[:5]}, Extra: {sorted(extra)[:5]}"
        )


def select_partition(
    df: pd.DataFrame,
    manifest: SplitManifest,
    partition_name: str,
) -> pd.DataFrame:
    """Filter DataFrame to only rows belonging to engines in the specified partition.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a 'unit' column.
    manifest : SplitManifest
        Validated split manifest.
    partition_name : str
        Partition name ('train', 'calibration', 'validation', 'test').

    Returns
    -------
    pd.DataFrame
        Subset of df preserving original order and column structure.
    """
    engine_ids = set(manifest.get_partition(partition_name))
    return df[df["unit"].isin(engine_ids)].copy().reset_index(drop=True)
