"""Serialization, hashing, provenance, and registry loading for calibration artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from intellitwin.data.artifacts import compute_sha256
from intellitwin.uncertainty.calibration import Calibrator
from intellitwin.uncertainty.schema import (
    CALIBRATOR_SCHEMA_VERSION,
    METHOD_DECISION_AWARE,
    NOMINAL_COVERAGES,
    PROTOCOL_VERSION,
    CandidateConfig,
    CoverageThresholdBundle,
    RegimeThresholdRecord,
)

POINT_PREDICTION_COLUMNS: tuple[str, ...] = (
    "unit",
    "endpoint_cycle",
    "rul_true",
    "rul_target",
    "prediction",
    "regime",
    "lifecycle_stage",
)

INTERVAL_PREDICTION_COLUMNS: tuple[str, ...] = (
    "unit",
    "endpoint_cycle",
    "rul_true",
    "prediction",
    "regime",
    "lifecycle_stage",
    "nominal_coverage",
    "lower",
    "upper",
    "fallback_used",
)


def write_atomic_json(target_path: Path | str, data: dict[str, Any]) -> None:
    """Serialize dictionary to JSON atomically with stable sorted keys and LF line endings.

    Rejects NaN and Infinity values.
    """
    p = Path(target_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    temp_p = p.with_suffix(f"{p.suffix}.tmp_{os.getpid()}")

    json_str = json.dumps(data, indent=2, sort_keys=True, allow_nan=False)
    with open(temp_p, "w", encoding="utf-8", newline="\n") as f:
        f.write(json_str)
        f.write("\n")

    temp_p.replace(p)


def write_atomic_csv(target_path: Path | str, df: pd.DataFrame) -> None:
    """Serialize DataFrame to CSV atomically with 17 significant digits and LF line endings."""
    p = Path(target_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    temp_p = p.with_suffix(f"{p.suffix}.tmp_{os.getpid()}")

    df.to_csv(
        temp_p,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        float_format="%.17g",
    )
    temp_p.replace(p)


def serialize_calibrator_artifact(
    calibrator: Calibrator,
    checkpoint_hash: str,
    preprocessor_hash: str,
    split_manifest_hash: str,
    raw_dataset_hash: str,
    calibration_pred_cache_hash: str,
    selection_freeze_hash: str,
    git_commit: str,
    source_hashes: dict[str, str],
) -> dict[str, Any]:
    """Build canonical serializable calibrator artifact dictionary."""
    cand = calibrator.candidate
    gamma = cand.gamma if cand is not None else None
    beta_code = cand.beta_code if cand is not None else None
    beta = cand.beta if cand is not None else None
    cand_id = cand.candidate_id if cand is not None else None

    bundles_data: dict[str, Any] = {}
    for cov in NOMINAL_COVERAGES:
        b = calibrator.coverage_bundles[cov]
        bundles_data[f"coverage_{int(cov * 100)}"] = b.to_dict()

    artifact: dict[str, Any] = {
        "schema_version": CALIBRATOR_SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "method_id": calibrator.method_id,
        "dataset": calibrator.dataset_name,
        "model_family": calibrator.model_family,
        "model_seed": calibrator.model_seed,
        "selected_candidate_id": cand_id,
        "candidate_parameters": {
            "gamma": gamma,
            "beta_code": beta_code,
            "beta": beta,
        },
        "target_definition": "rul_true (uncapped remaining useful life)",
        "score_definition": (
            "max((p - y)/a(p), (y - p)/b(p), 0)"
            if calibrator.method_id == METHOD_DECISION_AWARE
            else "abs(y - p)"
        ),
        "quantile_definition": (
            "engine-weighted hierarchical non-interpolated quantile with mass 1/(m+1) at infinity"
        ),
        "threshold_bundles": bundles_data,
        "provenance": {
            "checkpoint_sha256": checkpoint_hash,
            "preprocessor_sha256": preprocessor_hash,
            "split_manifest_sha256": split_manifest_hash,
            "raw_dataset_sha256": raw_dataset_hash,
            "calibration_prediction_cache_sha256": calibration_pred_cache_hash,
            "selection_freeze_sha256": selection_freeze_hash,
            "git_commit": git_commit,
            "source_hashes": source_hashes,
        },
    }
    return artifact


def load_calibrator_from_artifact(artifact: dict[str, Any]) -> Calibrator:
    """Reconstruct in-memory Calibrator container from artifact dictionary."""
    if artifact.get("schema_version") != CALIBRATOR_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version: {artifact.get('schema_version')}. "
            f"Expected {CALIBRATOR_SCHEMA_VERSION}"
        )

    method_id = artifact["method_id"]
    dataset = artifact["dataset"]
    family = artifact["model_family"]
    seed = artifact["model_seed"]
    cand_id = artifact.get("selected_candidate_id")

    cand_obj = CandidateConfig.from_id(cand_id) if cand_id is not None else None

    bundles: dict[float, CoverageThresholdBundle] = {}
    for _key, b_data in artifact["threshold_bundles"].items():
        nom_cov = float(b_data["nominal_coverage"])
        reg_dict: dict[str, RegimeThresholdRecord] = {}
        for r_name, r_data in b_data["regime_thresholds"].items():
            reg_dict[r_name] = RegimeThresholdRecord(
                regime=r_data["regime"],
                threshold=float(r_data["threshold"]),
                m_engines=int(r_data["m_engines"]),
                n_endpoints=int(r_data["n_endpoints"]),
                fallback_used=bool(r_data["fallback_used"]),
                fallback_reason=r_data.get("fallback_reason"),
            )
        bundles[nom_cov] = CoverageThresholdBundle(
            nominal_coverage=nom_cov,
            coverage_fraction=b_data["coverage_fraction"],
            global_threshold=float(b_data["global_threshold"]),
            global_m_engines=int(b_data["global_m_engines"]),
            global_n_endpoints=int(b_data["global_n_endpoints"]),
            regime_thresholds=reg_dict,
        )

    return Calibrator(
        method_id=method_id,
        dataset_name=dataset,
        model_family=family,
        model_seed=seed,
        candidate=cand_obj,
        coverage_bundles=bundles,
    )


def load_frozen_calibrator(
    dataset: str,
    model_family: str,
    seed: int,
    method_id: str,
    registry_path: Path | str = "experiments/calibration/calibration_registry.json",
    base_dir: Path | str = ".",
) -> Calibrator:
    """Load and verify frozen Calibrator artifact against calibration registry.

    Parameters
    ----------
    dataset : str
        "FD001", "FD002", or "FD004".
    model_family : str
        "GBR" or "LSTM".
    seed : int
        Predictor seed (2026..2030).
    method_id : str
        "global_hcp", "regime_hcp", or "decision_aware_hcp".
    registry_path : Path or str
        Path to calibration_registry.json.
    base_dir : Path or str
        Repository root.

    Returns
    -------
    Calibrator
        Verified Calibrator instance.
    """
    base = Path(base_dir)
    reg_p = base / registry_path
    if not reg_p.exists():
        raise FileNotFoundError(f"Calibration registry missing: {reg_p}")

    with open(reg_p, encoding="utf-8") as f:
        registry = json.load(f)

    bundle_id = f"{dataset}_{model_family}_seed{seed}_{method_id}"
    entries = registry.get("entries", {})
    entry = entries.get(bundle_id)
    if entry is None:
        raise KeyError(f"Calibrator bundle '{bundle_id}' not found in registry.")

    rel_path = entry["calibrator_artifact_path"]
    expected_hash = entry["artifact_sha256"]

    art_p = base / rel_path
    if not art_p.exists():
        raise FileNotFoundError(f"Calibrator artifact file missing: {art_p}")

    actual_hash = compute_sha256(art_p)
    if actual_hash != expected_hash:
        raise ValueError(
            f"Calibrator artifact hash mismatch for {bundle_id}: "
            f"expected {expected_hash}, got {actual_hash}"
        )

    with open(art_p, encoding="utf-8") as f:
        artifact_data = json.load(f)

    return load_calibrator_from_artifact(artifact_data)
