"""Data preparation, integrity verification, and prediction generation.

This module provides strict partition isolation and inference execution for Step 9
confirmatory evaluation:
- Verifies raw C-MAPSS training file hashes against frozen authoritative hashes.
- Selects the requested manifest partition BEFORE preprocessing or windowing.
- Rejects training and calibration partition access (preserves Step 8 boundaries).
- Enforces explicit authorization (--confirm-held-out) for test partition access.
- Executes CPU predictions with batching and validates trajectory continuity.
- Produces DataFrames conforming exactly to the frozen validation cache schema.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from intellitwin.data.artifacts import compute_sha256, load_preprocessor_artifact
from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import (
    EXPECTED_ENGINE_COUNTS,
    LOOKBACK,
    RUL_CAP,
    SUPPORTED_DATASETS,
)
from intellitwin.data.splits import SplitManifest, load_split_manifest, select_partition
from intellitwin.data.windowing import WindowDataset, construct_windows
from intellitwin.models.registry import (
    EXPECTED_FAMILIES,
    EXPECTED_SEEDS,
    FrozenBaseModel,
    load_frozen_base_model,
)
from intellitwin.uncertainty.artifacts import (
    POINT_PREDICTION_COLUMNS,
    resolve_repo_relative_path,
)

FROZEN_RAW_SOURCE_HASHES: dict[str, str] = {
    "FD001": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
    "FD002": "dac6c4dbc4e7c1bdeb5747da3d313d05c395bb99801b44a002b26a2ba13d788f",
    "FD004": "27ef6160b6a1dcb2613a88de9c239f763b223f02cdc41dc5cdedc5dc189b6218",
}

ALLOWED_CONFIRMATORY_PARTITIONS: tuple[str, ...] = ("validation", "test")
FORBIDDEN_CONFIRMATORY_PARTITIONS: tuple[str, ...] = ("train", "calibration")


def verify_raw_data_hashes(
    raw_data_dir: Path | str = "data/raw/cmapss",
    base_dir: Path | str = ".",
) -> dict[str, str]:
    """Verify raw C-MAPSS training file hashes against authoritative frozen hashes.

    Parameters
    ----------
    raw_data_dir : Path or str
        Directory containing raw C-MAPSS text files.
    base_dir : Path or str
        Root repository path.

    Returns
    -------
    dict[str, str]
        Mapping from dataset name to computed SHA-256 hash.

    Raises
    ------
    FileNotFoundError
        If any raw C-MAPSS file is missing.
    ValueError
        If any raw file SHA-256 hash does not match the frozen authoritative hash.
    """
    base = Path(base_dir).resolve()
    raw_dir = resolve_repo_relative_path(base, raw_data_dir)
    computed_hashes: dict[str, str] = {}

    for ds in SUPPORTED_DATASETS:
        raw_p = raw_dir / f"train_{ds}.txt"
        if not raw_p.exists():
            raise FileNotFoundError(f"Authoritative raw C-MAPSS file missing: {raw_p}")
        h = compute_sha256(raw_p)
        expected_h = FROZEN_RAW_SOURCE_HASHES.get(ds)
        if expected_h is None or h != expected_h:
            raise ValueError(
                f"Raw C-MAPSS file {raw_p.name} hash mismatch: computed {h}, expected {expected_h}"
            )
        computed_hashes[ds] = h

    return computed_hashes


def load_and_prepare_partition_windows(
    dataset: str,
    partition: str,
    raw_data_dir: Path | str = "data/raw/cmapss",
    base_dir: Path | str = ".",
    confirm_held_out: bool = False,
) -> tuple[WindowDataset, list[int], SplitManifest]:
    """Prepare causal sequence windows for explicitly permitted confirmatory partitions.

    Strict Anti-Leakage & Governance Rules:
    1. Only 'validation' and 'test' partitions are accepted.
    2. 'train' and 'calibration' are strictly forbidden (preserves Step 8 freeze).
    3. 'test' requires confirm_held_out=True.
    4. Raw file hashes are verified before reading.
    5. Partition selection occurs strictly BEFORE preprocessor transformation and windowing.
    6. Never accesses NASA's separate test_FD00x.txt files.

    Parameters
    ----------
    dataset : str
        One of 'FD001', 'FD002', 'FD004'.
    partition : str
        'validation' or 'test'.
    raw_data_dir : Path or str
        Directory containing raw C-MAPSS run-to-failure text files.
    base_dir : Path or str
        Root repository directory.
    confirm_held_out : bool
        Explicit gate required to authorize access to held-out test data.

    Returns
    -------
    tuple[WindowDataset, list[int], SplitManifest]
        Constructed windows, sorted partition engine IDs, and loaded split manifest.

    Raises
    ------
    PermissionError
        If unauthorized partition or unconfirmed test partition is requested.
    ValueError
        If unsupported dataset or partition is requested.
    """
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(
            f"Dataset '{dataset}' not supported for confirmatory evaluation. "
            f"Expected one of {SUPPORTED_DATASETS}"
        )

    if partition in FORBIDDEN_CONFIRMATORY_PARTITIONS:
        raise PermissionError(
            f"Access to partition '{partition}' is strictly forbidden in confirmatory pipeline. "
            f"Only {ALLOWED_CONFIRMATORY_PARTITIONS} partitions are permitted."
        )

    if partition not in ALLOWED_CONFIRMATORY_PARTITIONS:
        raise ValueError(
            f"Partition '{partition}' is invalid. Expected one of {ALLOWED_CONFIRMATORY_PARTITIONS}"
        )

    if partition == "test" and not confirm_held_out:
        raise PermissionError(
            "Access to held-out 'test' partition requires explicit "
            "confirm_held_out=True authorization."
        )

    base = Path(base_dir).resolve()
    raw_dir = resolve_repo_relative_path(base, raw_data_dir)
    raw_p = raw_dir / f"train_{dataset}.txt"
    if not raw_p.exists():
        raise FileNotFoundError(f"Raw C-MAPSS file missing: {raw_p}")

    # Verify raw file integrity
    raw_hash = compute_sha256(raw_p)
    expected_hash = FROZEN_RAW_SOURCE_HASHES.get(dataset)
    if raw_hash != expected_hash:
        raise ValueError(
            f"Raw file {raw_p.name} integrity violation: "
            f"computed {raw_hash}, expected {expected_hash}"
        )

    # Load split manifest
    split_rel = f"data/splits/{dataset.lower()}_engine_split_seed_2026.json"
    split_p = resolve_repo_relative_path(base, split_rel)
    if not split_p.exists():
        raise FileNotFoundError(f"Split manifest missing: {split_p}")
    split_manifest = load_split_manifest(split_p)

    expected_partition_engines = sorted(split_manifest.get_partition(partition))

    # Preprocessor artifact
    prep_rel = f"experiments/preprocessing/{dataset}/preprocessor.json"
    prep_p = resolve_repo_relative_path(base, prep_rel)
    if not prep_p.exists():
        raise FileNotFoundError(f"Preprocessor artifact missing: {prep_p}")

    # Load full run-to-failure raw data
    expected_count = EXPECTED_ENGINE_COUNTS[dataset]
    df_raw = load_cmapss_run_to_failure(
        path=raw_p,
        dataset_name=dataset,
        expected_engine_count=expected_count,
    )

    # SELECT PARTITION BEFORE PREPROCESSING OR WINDOWING
    df_part = select_partition(df_raw, split_manifest, partition_name=partition)
    actual_partition_engines = sorted(df_part["unit"].unique())

    if actual_partition_engines != expected_partition_engines:
        raise RuntimeError(
            f"Partition selection mismatch for {dataset} {partition}: "
            f"found {actual_partition_engines}, expected {expected_partition_engines}"
        )

    # Anti-leakage verification
    if partition == "validation":
        test_units = set(split_manifest.get_partition("test"))
        leakage = set(actual_partition_engines).intersection(test_units)
        if leakage:
            raise RuntimeError(
                f"FATAL: Test engines {leakage} detected in validation partition for {dataset}!"
            )
    elif partition == "test":
        train_units = set(split_manifest.get_partition("train"))
        cal_units = set(split_manifest.get_partition("calibration"))
        leakage = set(actual_partition_engines).intersection(train_units | cal_units)
        if leakage:
            raise RuntimeError(
                f"FATAL: Training/calibration engines {leakage} "
                f"detected in test partition for {dataset}!"
            )

    # Transform through frozen preprocessor (no refitting!)
    preproc, _ = load_preprocessor_artifact(prep_p)
    df_trans = preproc.transform(df_part)

    # Construct causal sequence windows (lookback 30, endpoints 30..T)
    windows = construct_windows(df_trans)

    return windows, expected_partition_engines, split_manifest


def generate_predictions_for_cell(
    windows: WindowDataset,
    dataset: str,
    model_family: str,
    seed: int,
    base_dir: Path | str = ".",
    frozen_model: FrozenBaseModel | None = None,
) -> pd.DataFrame:
    """Generate base model point predictions on prepared causal windows on CPU in batches of 256.

    Parameters
    ----------
    windows : WindowDataset
        Causal windows constructed from the selected partition.
    dataset : str
        Dataset identifier ('FD001', 'FD002', 'FD004').
    model_family : str
        Model family ('GBR', 'LSTM').
    seed : int
        Model training seed (2026, 2027, 2028, 2029, 2030).
    base_dir : Path or str
        Root repository directory.
    frozen_model : FrozenBaseModel, optional
        Pre-loaded frozen model instance to avoid reloading from disk on each call.

    Returns
    -------
    pd.DataFrame
        DataFrame matching the schema and dtypes of existing point prediction caches:
        ['unit', 'endpoint_cycle', 'rul_true', 'rul_target', 'prediction',
         'regime', 'lifecycle_stage']
    """
    if model_family not in EXPECTED_FAMILIES:
        raise ValueError(f"Unsupported model family: {model_family}")
    if seed not in EXPECTED_SEEDS:
        raise ValueError(f"Unsupported seed: {seed}")

    if frozen_model is None:
        base = Path(base_dir).resolve()
        frozen_model = load_frozen_base_model(
            dataset=dataset,
            model_family=model_family,
            seed=seed,
            base_dir=base,
        )

    # Set CPU inference constraints
    torch.set_num_threads(2)

    m = len(windows)
    if m == 0:
        return pd.DataFrame(
            columns=list(POINT_PREDICTION_COLUMNS),
        ).astype(
            {
                "unit": np.int64,
                "endpoint_cycle": np.int64,
                "rul_true": np.int64,
                "rul_target": np.int64,
                "prediction": np.float64,
                "regime": str,
                "lifecycle_stage": str,
            }
        )

    preds: np.ndarray[Any, Any]
    if model_family == "GBR":
        X_flat = windows.flatten_for_gbr()
        # Batch predictions in chunks of 256 for consistent memory and thread control
        batch_size = 256
        pred_chunks: list[np.ndarray[Any, Any]] = []
        for i in range(0, m, batch_size):
            chunk = X_flat[i : i + batch_size]
            pred_chunks.append(frozen_model.predict(chunk))
        preds = np.concatenate(pred_chunks, axis=0) if pred_chunks else np.empty(0, dtype=float)
    elif model_family == "LSTM":
        # FrozenBaseModel.predict for LSTM uses batches of 256 on CPU internally
        preds = frozen_model.predict(windows.X_sequence)
    else:
        raise ValueError(f"Unsupported model family: {model_family}")

    if len(preds) != m:
        raise RuntimeError(f"Prediction count ({len(preds)}) != window count ({m})")
    if not np.all(np.isfinite(preds)):
        raise ValueError(f"Non-finite predictions generated for {dataset}/{model_family}/{seed}")
    if np.any(preds < 0.0):
        raise ValueError(f"Negative predictions generated for {dataset}/{model_family}/{seed}")

    df_out = pd.DataFrame(
        {
            "unit": windows.engine_ids.astype(np.int64),
            "endpoint_cycle": windows.endpoint_cycles.astype(np.int64),
            "rul_true": np.round(windows.rul_true).astype(np.int64),
            "rul_target": np.round(windows.rul_target).astype(np.int64),
            "prediction": preds.astype(np.float64),
            "regime": windows.regimes.astype(str),
            "lifecycle_stage": windows.lifecycle_stages.astype(str),
        }
    )

    # Validate output structure
    validate_point_predictions_dataframe(df_out, expected_units=sorted(windows.engine_ids))

    return df_out


def validate_point_predictions_dataframe(
    df: pd.DataFrame,
    expected_units: Sequence[int] | None = None,
) -> None:
    """Validate point prediction DataFrame schema, keys, dtypes, and trajectory continuity.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame of point predictions.
    expected_units : Sequence[int], optional
        Expected partition engine IDs.
    """
    for col in POINT_PREDICTION_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Point predictions DataFrame missing required column: {col}")

    # Check dtypes
    if not pd.api.types.is_integer_dtype(df["unit"]):
        raise TypeError(f"Column 'unit' must be integer, got {df['unit'].dtype}")
    if not pd.api.types.is_integer_dtype(df["endpoint_cycle"]):
        raise TypeError(
            f"Column 'endpoint_cycle' must be integer, got {df['endpoint_cycle'].dtype}"
        )
    if not pd.api.types.is_numeric_dtype(df["prediction"]):
        raise TypeError(f"Column 'prediction' must be numeric, got {df['prediction'].dtype}")

    # Key uniqueness
    dups = df.duplicated(subset=["unit", "endpoint_cycle"]).sum()
    if dups > 0:
        raise ValueError(
            f"Duplicate (unit, endpoint_cycle) keys found in predictions: count={dups}"
        )

    # Trajectory continuity per engine
    for unit, grp in df.groupby("unit"):
        u_val = int(unit)
        grp_sort = grp.sort_values("endpoint_cycle")
        cycles = grp_sort["endpoint_cycle"].to_numpy(dtype=int)
        if len(cycles) == 0:
            raise ValueError(f"Engine {u_val} has 0 evaluation endpoints.")
        if cycles[0] != LOOKBACK:
            raise ValueError(f"Engine {u_val} first endpoint is {cycles[0]}, expected {LOOKBACK}")
        expected_cycles = np.arange(LOOKBACK, cycles[-1] + 1, dtype=int)
        if not np.array_equal(cycles, expected_cycles):
            raise ValueError(
                f"Engine {u_val} endpoint sequence is not contiguous "
                f"from {LOOKBACK} to {cycles[-1]}"
            )

        # Uncapped vs capped RUL verification
        rul_trues = grp_sort["rul_true"].to_numpy(dtype=float)
        rul_targets = grp_sort["rul_target"].to_numpy(dtype=float)
        expected_targets = np.minimum(rul_trues, float(RUL_CAP))
        if not np.allclose(rul_targets, expected_targets, atol=1e-6):
            raise ValueError(f"Engine {u_val} rul_target does not match capped rul_true (cap=125).")

    if expected_units is not None:
        actual_units = sorted(df["unit"].unique())
        exp_sorted = sorted(set(expected_units))
        if actual_units != exp_sorted:
            raise ValueError(
                f"Prediction units mismatch: found {actual_units}, expected {exp_sorted}"
            )


def load_or_generate_point_predictions(
    dataset: str,
    model_family: str,
    seed: int,
    partition: str,
    cache_dir: Path | str | None = None,
    raw_data_dir: Path | str = "data/raw/cmapss",
    base_dir: Path | str = ".",
    confirm_held_out: bool = False,
    use_validation_cache: bool = True,
) -> pd.DataFrame:
    """Load cached predictions or generate fresh predictions for a specific cell.

    Rules:
    - If partition == 'validation' and use_validation_cache is True:
      Loads from cache_dir or default experiments/calibration/point_predictions/validation.
    - If partition == 'test':
      MUST generate fresh predictions from raw test partition windows.
      Never loads from validation caches.

    Parameters
    ----------
    dataset : str
        Dataset identifier ('FD001', 'FD002', 'FD004').
    model_family : str
        Model family ('GBR', 'LSTM').
    seed : int
        Seed (2026..2030).
    partition : str
        'validation' or 'test'.
    cache_dir : Path or str, optional
        Custom directory containing cached predictions.
    raw_data_dir : Path or str
        Directory containing raw C-MAPSS text files.
    base_dir : Path or str
        Root repository path.
    confirm_held_out : bool
        Authorization gate for held-out test data.
    use_validation_cache : bool
        Whether to load from validation cache when partition == 'validation'.

    Returns
    -------
    pd.DataFrame
        Point predictions for the specified cell.
    """
    base = Path(base_dir).resolve()

    if partition == "validation" and use_validation_cache:
        c_dir = (
            resolve_repo_relative_path(base, cache_dir)
            if cache_dir is not None
            else resolve_repo_relative_path(
                base, "experiments/calibration/point_predictions/validation"
            )
        )
        cache_p = c_dir / dataset / model_family / f"seed_{seed}.csv"
        if cache_p.exists():
            df_cache = pd.read_csv(cache_p, float_precision="round_trip")
            validate_point_predictions_dataframe(df_cache)
            return df_cache

    # Otherwise, generate fresh predictions
    windows, expected_engines, _ = load_and_prepare_partition_windows(
        dataset=dataset,
        partition=partition,
        raw_data_dir=raw_data_dir,
        base_dir=base,
        confirm_held_out=confirm_held_out,
    )
    df_fresh = generate_predictions_for_cell(
        windows=windows,
        dataset=dataset,
        model_family=model_family,
        seed=seed,
        base_dir=base,
    )
    return df_fresh
