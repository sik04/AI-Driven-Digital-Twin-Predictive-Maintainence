"""Data pipeline for Step 8 calibration and validation partitions with strict anti-leakage."""

from __future__ import annotations

from pathlib import Path

from intellitwin.data.artifacts import load_preprocessor_artifact
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import EXPECTED_ENGINE_COUNTS, SUPPORTED_DATASETS
from intellitwin.data.splits import load_split_manifest, select_partition
from intellitwin.data.windowing import WindowDataset, construct_windows

ALLOWED_CALIBRATION_PARTITIONS: tuple[str, ...] = ("calibration", "validation")


def prepare_partition_windows(
    dataset_name: str,
    partition_name: str,
    raw_data_dir: Path | str = "data/raw/cmapss",
    base_dir: Path | str = ".",
) -> WindowDataset:
    """Prepare causal sequence windows for explicitly permitted Step 8 partitions.

    Strict Anti-Leakage Boundary:
    Only 'calibration' and 'validation' partitions are allowed.
    Requests for 'test' or any other partition are strictly rejected.

    Parameters
    ----------
    dataset_name : str
        Dataset identifier ("FD001", "FD002", "FD004").
    partition_name : str
        Partition name ('calibration' or 'validation').
    raw_data_dir : Path or str
        Directory containing raw C-MAPSS training text files.
    base_dir : Path or str
        Repository root directory.

    Returns
    -------
    WindowDataset
        Container with causal sequence windows and metadata for the requested partition.
    """
    if dataset_name not in SUPPORTED_DATASETS:
        raise ValueError(
            f"Dataset '{dataset_name}' not supported. Expected one of {SUPPORTED_DATASETS}"
        )

    if partition_name not in ALLOWED_CALIBRATION_PARTITIONS:
        raise PermissionError(
            f"Access to partition '{partition_name}' is strictly forbidden in Step 8. "
            f"Only {ALLOWED_CALIBRATION_PARTITIONS} partitions are permitted."
        )

    base = Path(base_dir)
    raw_p = base / raw_data_dir / f"train_{dataset_name}.txt"
    if not raw_p.exists():
        raise FileNotFoundError(f"Raw C-MAPSS file missing: {raw_p}")

    split_p = base / f"data/splits/{dataset_name.lower()}_engine_split_seed_2026.json"
    if not split_p.exists():
        raise FileNotFoundError(f"Split manifest missing: {split_p}")

    prep_p = base / f"experiments/preprocessing/{dataset_name}/preprocessor.json"
    if not prep_p.exists():
        raise FileNotFoundError(f"Fitted preprocessor artifact missing: {prep_p}")

    # Load raw data with expected engine count
    expected_count = EXPECTED_ENGINE_COUNTS[dataset_name]
    df_raw = load_cmapss_run_to_failure(
        path=raw_p,
        dataset_name=dataset_name,
        expected_engine_count=expected_count,
    )

    # Load split manifest and select strictly allowed partition
    manifest = load_split_manifest(split_p)
    df_part = select_partition(df_raw, manifest, partition_name=partition_name)

    # Double check no test engines present
    test_engines = set(manifest.test)
    part_engines = set(df_part["unit"].unique())
    leakage = part_engines.intersection(test_engines)
    if leakage:
        raise RuntimeError(f"FATAL: Test engines {leakage} detected in partition {partition_name}!")

    # Transform through frozen preprocessor (no refitting!)
    preproc, _ = load_preprocessor_artifact(prep_p)
    df_trans = preproc.transform(df_part)

    # Construct causal windows (endpoints 30..T)
    windows = construct_windows(df_trans)

    return windows
