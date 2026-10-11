"""Deterministic persistence and round-trip loading of fitted preprocessing artifacts.

Enforces:
- Deterministic JSON serialization (UTF-8, sort_keys=True, indent=2, trailing newline)
- Strict exclusion of non-deterministic elements (timestamps, pickled objects)
- SHA-256 provenance calculation for raw files, split manifests, and preprocessor artifacts
- Exact numeric reconstruction of FittedPreprocessor objects
"""

import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd
import sklearn

from intellitwin.data.preprocessing import (
    PROTOCOL_VERSION,
    FittedPreprocessor,
    ScalerParams,
)
from intellitwin.data.schema import (
    FEATURE_COLUMNS,
    LOOKBACK,
    STRIDE,
)

ARTIFACT_SCHEMA_VERSION: Final[str] = "step07-data-v1"
PROTOCOL_REFERENCE: Final[str] = "ADR-019"


def compute_sha256(path: Path | str) -> str:
    """Compute the SHA-256 hexadecimal digest of a file.

    Parameters
    ----------
    path : Path or str
        Path to the file.

    Returns
    -------
    str
        64-character lowercase hexadecimal hash.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError(f"File not found for hash calculation: {file_path}")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Compute SHA-256 of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


def preprocessor_to_dict(
    preprocessor: FittedPreprocessor,
    source_raw_path: str,
    source_raw_sha256: str,
    split_manifest_path: str,
    split_manifest_sha256: str,
) -> dict[str, Any]:
    """Convert FittedPreprocessor to a deterministic JSON-serializable dictionary."""
    setting_scalers_dict = {
        col: {
            "mean": scaler.mean,
            "variance": scaler.variance,
            "effective_scale": scaler.effective_scale,
            "is_zero_variance": scaler.is_zero_variance,
        }
        for col, scaler in preprocessor.setting_scalers.items()
    }

    sensor_scalers_dict: dict[str, dict[str, Any]] = {}
    for reg, col_dict in preprocessor.sensor_scalers_by_regime.items():
        sensor_scalers_dict[reg] = {
            col: {
                "mean": scaler.mean,
                "variance": scaler.variance,
                "effective_scale": scaler.effective_scale,
                "is_zero_variance": scaler.is_zero_variance,
            }
            for col, scaler in col_dict.items()
        }

    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "dataset": preprocessor.dataset,
        "protocol_reference": PROTOCOL_REFERENCE,
        "source_raw_file": source_raw_path.replace("\\", "/"),
        "source_raw_sha256": source_raw_sha256,
        "split_manifest_file": split_manifest_path.replace("\\", "/"),
        "split_manifest_sha256": split_manifest_sha256,
        "fitted_partition": "train",
        "feature_order": list(preprocessor.feature_order),
        "lookback": LOOKBACK,
        "stride": STRIDE,
        "padding": False,
        "software_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "setting_scalers": setting_scalers_dict,
        "regime_configuration": {
            "regime_mode": preprocessor.regime_mode,
            "kmeans_config": preprocessor.kmeans_config,
            "canonical_standardized_centroids": preprocessor.canonical_standardized_centroids,
            "canonical_unscaled_centroids": preprocessor.canonical_unscaled_centroids,
            "original_cluster_to_canonical_mapping": (
                {str(k): v for k, v in preprocessor.original_cluster_to_canonical_mapping.items()}
                if preprocessor.original_cluster_to_canonical_mapping is not None
                else None
            ),
            "training_cluster_counts": preprocessor.training_cluster_counts,
        },
        "sensor_normalization": sensor_scalers_dict,
    }


def dict_to_preprocessor(data: dict[str, Any]) -> FittedPreprocessor:
    """Reconstruct a FittedPreprocessor from a loaded artifact dictionary."""
    if data.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported artifact schema version: {data.get('schema_version')} "
            f"(expected '{ARTIFACT_SCHEMA_VERSION}')."
        )

    setting_scalers = {
        col: ScalerParams(
            mean=float(params["mean"]),
            variance=float(params["variance"]),
            effective_scale=float(params["effective_scale"]),
            is_zero_variance=bool(params["is_zero_variance"]),
        )
        for col, params in data["setting_scalers"].items()
    }

    reg_cfg = data["regime_configuration"]
    regime_mode = reg_cfg["regime_mode"]
    kmeans_config = reg_cfg.get("kmeans_config")
    can_std = reg_cfg.get("canonical_standardized_centroids")
    can_unscaled = reg_cfg.get("canonical_unscaled_centroids")
    raw_mapping = reg_cfg.get("original_cluster_to_canonical_mapping")
    orig_to_can = (
        {int(k): str(v) for k, v in raw_mapping.items()} if raw_mapping is not None else None
    )
    cluster_counts = reg_cfg.get("training_cluster_counts")

    sensor_scalers: dict[str, dict[str, ScalerParams]] = {}
    for reg, cols in data["sensor_normalization"].items():
        sensor_scalers[reg] = {
            col: ScalerParams(
                mean=float(params["mean"]),
                variance=float(params["variance"]),
                effective_scale=float(params["effective_scale"]),
                is_zero_variance=bool(params["is_zero_variance"]),
            )
            for col, params in cols.items()
        }

    return FittedPreprocessor(
        dataset=str(data["dataset"]),
        feature_order=tuple(data.get("feature_order", FEATURE_COLUMNS)),
        setting_scalers=setting_scalers,
        regime_mode=regime_mode,
        kmeans_config=kmeans_config,
        canonical_standardized_centroids=can_std,
        canonical_unscaled_centroids=can_unscaled,
        original_cluster_to_canonical_mapping=orig_to_can,
        training_cluster_counts=cluster_counts,
        sensor_scalers_by_regime=sensor_scalers,
        protocol_version=PROTOCOL_VERSION,
    )


def save_preprocessor_artifact(
    preprocessor: FittedPreprocessor,
    output_path: Path | str,
    source_raw_path: str,
    source_raw_sha256: str,
    split_manifest_path: str,
    split_manifest_sha256: str,
) -> str:
    """Save FittedPreprocessor to a deterministic JSON artifact file.

    Parameters
    ----------
    preprocessor : FittedPreprocessor
        Fitted preprocessor object.
    output_path : Path or str
        Destination path for JSON file.
    source_raw_path : str
        Relative path to source raw data file.
    source_raw_sha256 : str
        SHA-256 of source raw data file.
    split_manifest_path : str
        Relative path to split manifest.
    split_manifest_sha256 : str
        SHA-256 of split manifest.

    Returns
    -------
    str
        SHA-256 digest of written artifact file.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    data = preprocessor_to_dict(
        preprocessor=preprocessor,
        source_raw_path=source_raw_path,
        source_raw_sha256=source_raw_sha256,
        split_manifest_path=split_manifest_path,
        split_manifest_sha256=split_manifest_sha256,
    )

    # Deterministic JSON formatting
    json_bytes = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")

    with open(out_file, "wb") as f:
        f.write(json_bytes)

    return compute_bytes_sha256(json_bytes)


def load_preprocessor_artifact(path: Path | str) -> tuple[FittedPreprocessor, dict[str, Any]]:
    """Load FittedPreprocessor and full artifact metadata from a JSON artifact file.

    Parameters
    ----------
    path : Path or str
        Path to JSON file.

    Returns
    -------
    tuple of (FittedPreprocessor, dict[str, Any])
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError(f"Preprocessor artifact file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    preprocessor = dict_to_preprocessor(data)
    return preprocessor, data
