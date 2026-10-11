"""Artifact serialization and hashing for base-model development.

Handles:
- Validation prediction CSV serialization and verification.
- Machine-readable candidate run record JSON persistence.
- Selection summary JSON persistence.
- SHA-256 integrity verification.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from intellitwin.data.artifacts import compute_sha256

PREDICTION_COLUMNS: tuple[str, ...] = (
    "unit",
    "endpoint_cycle",
    "rul_true",
    "rul_target",
    "prediction",
    "regime",
    "lifecycle_stage",
)


def save_prediction_artifact(df_predictions: pd.DataFrame, filepath: Path | str) -> str:
    """Save validation predictions to deterministic CSV and compute SHA-256.

    Columns strictly: unit, endpoint_cycle, rul_true, rul_target, prediction,
    regime, lifecycle_stage.
    Sorted strictly by unit ascending, endpoint_cycle ascending.

    Parameters
    ----------
    df_predictions : pd.DataFrame
        Predictions DataFrame.
    filepath : Path or str
        Destination path.

    Returns
    -------
    str
        SHA-256 hex digest of saved CSV.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Check columns
    missing_cols = [c for c in PREDICTION_COLUMNS if c not in df_predictions.columns]
    if missing_cols:
        raise ValueError(f"Missing required prediction columns: {missing_cols}")

    df_out = df_predictions.loc[:, list(PREDICTION_COLUMNS)].copy()
    # Sort strictly by unit ascending, endpoint_cycle ascending
    df_out = df_out.sort_values(by=["unit", "endpoint_cycle"], ascending=[True, True])

    # Save deterministic CSV
    csv_text = df_out.to_csv(index=False, lineterminator="\n", float_format="%.6f")
    path.write_text(csv_text, encoding="utf-8")

    return compute_sha256(path)


def save_run_record(record_dict: dict[str, Any], filepath: Path | str) -> str:
    """Save candidate run record to machine-readable JSON and compute SHA-256.

    Parameters
    ----------
    record_dict : dict[str, Any]
        Metadata and evaluation record.
    filepath : Path or str
        Destination path.

    Returns
    -------
    str
        SHA-256 hex digest of saved JSON.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    json_text = json.dumps(record_dict, indent=2) + "\n"
    path.write_text(json_text, encoding="utf-8")

    return compute_sha256(path)


def save_selection_summary(summary_dict: dict[str, Any], filepath: Path | str) -> str:
    """Save model selection summary to machine-readable JSON and compute SHA-256.

    Parameters
    ----------
    summary_dict : dict[str, Any]
        Selection summary.
    filepath : Path or str
        Destination path.

    Returns
    -------
    str
        SHA-256 hex digest of saved JSON.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    json_text = json.dumps(summary_dict, indent=2) + "\n"
    path.write_text(json_text, encoding="utf-8")

    return compute_sha256(path)
