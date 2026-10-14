"""Serialization, hashing, provenance, and registry loading for calibration artifacts."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import pandas as pd

from intellitwin.data.artifacts import compute_sha256
from intellitwin.uncertainty.calibration import DATASET_VOCABULARY, Calibrator
from intellitwin.uncertainty.schema import (
    CALIBRATOR_SCHEMA_VERSION,
    METHOD_DECISION_AWARE,
    METHOD_GLOBAL,
    METHOD_REGIME,
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


def resolve_repo_relative_path(
    base_dir: Path | str,
    relative_path: Path | str,
) -> Path:
    """Resolve a repo-relative path against base_dir with security and portability checks.

    Requirements:
    - Accepts existing relative paths containing either forward slashes or backslashes.
    - Resolves paths relative to the supplied repository root, not process working directory.
    - Rejects absolute paths, Windows drive-qualified paths, UNC paths, and path escapes.
    """
    raw_str = str(relative_path).strip()
    if not raw_str:
        raise ValueError("Path cannot be empty")

    # Reject Windows drive qualification (e.g. C:, D:)
    if len(raw_str) >= 2 and raw_str[1] == ":" and raw_str[0].isalpha():
        raise ValueError(f"Drive-qualified paths are forbidden: '{raw_str}'")

    # Reject UNC paths (\\server\share or //server/share)
    if raw_str.startswith(("\\\\", "//")):
        raise ValueError(f"UNC paths are forbidden: '{raw_str}'")

    # Reject leading slashes (root-relative / absolute on POSIX)
    if raw_str.startswith(("/", "\\")):
        raise ValueError(f"Absolute or root-prefixed paths are forbidden: '{raw_str}'")

    # Normalize backslashes to forward slashes
    norm_posix = raw_str.replace("\\", "/")

    # Check for path traversal components
    parts = norm_posix.split("/")
    if any(p == ".." for p in parts):
        raise ValueError(f"Path traversal ('..') is forbidden: '{raw_str}'")

    p = Path(norm_posix)
    if p.is_absolute():
        raise ValueError(f"Absolute paths are forbidden: '{raw_str}'")

    base = Path(base_dir).resolve()
    target = (base / p).resolve()

    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Path '{raw_str}' escapes repository root '{base}'") from exc

    return target


def to_repo_relative_path_posix(path: Path | str, base_dir: Path | str = ".") -> str:
    """Serialize repository-relative artifact path using forward slashes."""
    base = Path(base_dir).resolve()
    p = Path(path)
    if p.is_absolute():
        try:
            rel = p.resolve().relative_to(base)
            return rel.as_posix()
        except ValueError as exc:
            raise ValueError(f"Path '{p}' escapes repository root '{base}'") from exc
    norm = str(path).replace("\\", "/")
    _ = resolve_repo_relative_path(base_dir, norm)
    return norm


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
        Path to calibration_registry.json (relative or absolute).
    base_dir : Path or str
        Repository root.

    Returns
    -------
    Calibrator
        Verified Calibrator instance.
    """
    base = Path(base_dir).resolve()
    p_reg = Path(registry_path)
    if p_reg.is_absolute():
        reg_p = p_reg.resolve()
    else:
        reg_p = resolve_repo_relative_path(base, registry_path)

    if not reg_p.exists():
        raise FileNotFoundError(f"Calibration registry missing: {reg_p}")

    with open(reg_p, encoding="utf-8") as f:
        registry = json.load(f)

    bundle_id = f"{dataset}_{model_family}_seed{seed}_{method_id}"
    entries = registry.get("entries", {})
    entry = entries.get(bundle_id)
    if entry is None:
        raise KeyError(f"Calibrator bundle '{bundle_id}' not found in registry.")

    # 1. Resolve artifact path and verify artifact SHA-256 FIRST
    rel_path = entry["calibrator_artifact_path"]
    art_p = resolve_repo_relative_path(base, rel_path)
    if not art_p.exists():
        raise FileNotFoundError(f"Calibrator artifact file missing: {art_p}")

    expected_hash = entry["artifact_sha256"]
    actual_hash = compute_sha256(art_p)
    if actual_hash != expected_hash:
        raise ValueError(
            f"Calibrator artifact hash mismatch for {bundle_id}: "
            f"expected {expected_hash}, got {actual_hash}"
        )

    # 2. Verify requested dataset/family/seed/method matches registry entry if present
    if "dataset" in entry and entry["dataset"] != dataset:
        raise ValueError(f"Registry entry dataset '{entry['dataset']}' != requested '{dataset}'")
    if "model_family" in entry and entry["model_family"] != model_family:
        raise ValueError(
            f"Registry entry model_family '{entry['model_family']}' != requested '{model_family}'"
        )
    if "seed" in entry and entry["seed"] != seed:
        raise ValueError(f"Registry entry seed '{entry['seed']}' != requested '{seed}'")
    if "method_id" in entry and entry["method_id"] != method_id:
        raise ValueError(
            f"Registry entry method_id '{entry['method_id']}' != requested '{method_id}'"
        )

    with open(art_p, encoding="utf-8") as f:
        artifact_data = json.load(f)

    # 3. Validate supported schema and protocol
    if artifact_data.get("schema_version") != CALIBRATOR_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version: {artifact_data.get('schema_version')}. "
            f"Expected {CALIBRATOR_SCHEMA_VERSION}"
        )
    if artifact_data.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError(
            f"Unsupported protocol_version: {artifact_data.get('protocol_version')}. "
            f"Expected {PROTOCOL_VERSION}"
        )

    # 4. Verify artifact matches requested identity
    if artifact_data.get("dataset") != dataset:
        raise ValueError(
            f"Artifact dataset '{artifact_data.get('dataset')}' != requested '{dataset}'"
        )
    if artifact_data.get("model_family") != model_family:
        raise ValueError(
            f"Artifact model_family '{artifact_data.get('model_family')}' "
            f"!= requested '{model_family}'"
        )
    if artifact_data.get("model_seed") != seed:
        raise ValueError(
            f"Artifact model_seed '{artifact_data.get('model_seed')}' != requested '{seed}'"
        )
    if artifact_data.get("method_id") != method_id:
        raise ValueError(
            f"Artifact method_id '{artifact_data.get('method_id')}' != requested '{method_id}'"
        )

    # 5. Require all three expected nominal coverage bundles
    threshold_bundles = artifact_data.get("threshold_bundles", {})
    for cov in NOMINAL_COVERAGES:
        cov_key = f"coverage_{int(cov * 100)}"
        if cov_key not in threshold_bundles:
            raise ValueError(f"Missing expected coverage bundle '{cov_key}' in {bundle_id}")

    # 6. Validate finite nonnegative thresholds and legal regime labels
    allowed_regimes = DATASET_VOCABULARY.get(dataset)
    if allowed_regimes is None:
        raise ValueError(f"Unknown dataset '{dataset}'")

    for cov in NOMINAL_COVERAGES:
        cov_key = f"coverage_{int(cov * 100)}"
        b_data = threshold_bundles[cov_key]
        g_th = float(b_data["global_threshold"])
        if not math.isfinite(g_th) or g_th < 0.0:
            raise ValueError(f"Invalid global threshold in {bundle_id} at {cov_key}: {g_th}")
        if int(b_data["global_m_engines"]) <= 0 or int(b_data["global_n_endpoints"]) <= 0:
            raise ValueError(f"Invalid global counts in {bundle_id} at {cov_key}")

        reg_data = b_data.get("regime_thresholds", {})
        for r_name, r_rec in reg_data.items():
            if r_name not in allowed_regimes:
                raise ValueError(
                    f"Illegal regime label '{r_name}' in {bundle_id}; allowed: {allowed_regimes}"
                )
            r_th = float(r_rec["threshold"])
            if not math.isfinite(r_th) or r_th < 0.0:
                raise ValueError(f"Invalid regime threshold for {r_name} in {bundle_id}: {r_th}")
            if int(r_rec["m_engines"]) < 0 or int(r_rec["n_endpoints"]) < 0:
                raise ValueError(
                    f"Invalid regime engine/endpoint counts for {r_name} in {bundle_id}"
                )

    # 7. Verify candidate ID and candidate parameters agree
    art_cand_id = artifact_data.get("selected_candidate_id")
    reg_cand_id = entry.get("selected_candidate_id")
    if "selected_candidate_id" in entry and art_cand_id != reg_cand_id:
        raise ValueError(
            f"Candidate ID mismatch between registry ({reg_cand_id}) and artifact ({art_cand_id}) "
            f"for {bundle_id}"
        )

    cand_params = artifact_data.get("candidate_parameters", {})
    if method_id in (METHOD_GLOBAL, METHOD_REGIME):
        if art_cand_id is not None:
            raise ValueError(f"Candidate ID must be None for {method_id}, got: {art_cand_id}")
        if any(v is not None for v in cand_params.values()):
            raise ValueError(f"Candidate parameters must be None for {method_id}")
    elif method_id == METHOD_DECISION_AWARE:
        if art_cand_id is None:
            raise ValueError(f"Candidate ID required for {METHOD_DECISION_AWARE}")
        cand_obj = CandidateConfig.from_id(art_cand_id)
        if cand_params.get("gamma") != cand_obj.gamma:
            raise ValueError("gamma mismatch in candidate parameters")
        if cand_params.get("beta_code") != cand_obj.beta_code:
            raise ValueError("beta_code mismatch in candidate parameters")
        if abs(float(cand_params.get("beta", 0.0)) - cand_obj.beta) > 1e-12:
            raise ValueError("beta mismatch in candidate parameters")

    # 8. Verify references to checkpoint, preprocessor, split, and selection freeze
    prov = artifact_data.get("provenance", {})
    ckpt_path = resolve_repo_relative_path(
        base, f"experiments/base_models/{dataset}/{model_family}/seed_{seed}/checkpoint"
    )
    prep_path = resolve_repo_relative_path(
        base, f"experiments/preprocessing/{dataset}/preprocessor.json"
    )
    split_path = resolve_repo_relative_path(
        base, f"data/splits/{dataset.lower()}_engine_split_seed_2026.json"
    )
    freeze_path = resolve_repo_relative_path(
        base, "experiments/calibration/selection/selection_freeze.json"
    )

    if ckpt_path.exists():
        actual_ckpt_hash = compute_sha256(ckpt_path)
        if (entry.get("checkpoint_sha256") and entry["checkpoint_sha256"] != actual_ckpt_hash) or (
            prov.get("checkpoint_sha256") and prov["checkpoint_sha256"] != actual_ckpt_hash
        ):
            raise ValueError(f"Checkpoint hash mismatch for {bundle_id}")

    if prep_path.exists():
        actual_prep_hash = compute_sha256(prep_path)
        if (
            entry.get("preprocessor_sha256") and entry["preprocessor_sha256"] != actual_prep_hash
        ) or (prov.get("preprocessor_sha256") and prov["preprocessor_sha256"] != actual_prep_hash):
            raise ValueError(f"Preprocessor hash mismatch for {bundle_id}")

    if split_path.exists():
        actual_split_hash = compute_sha256(split_path)
        if (
            entry.get("split_manifest_sha256")
            and entry["split_manifest_sha256"] != actual_split_hash
        ) or (
            prov.get("split_manifest_sha256") and prov["split_manifest_sha256"] != actual_split_hash
        ):
            raise ValueError(f"Split manifest hash mismatch for {bundle_id}")

    if freeze_path.exists():
        actual_freeze_hash = compute_sha256(freeze_path)
        if (
            prov.get("selection_freeze_sha256")
            and prov["selection_freeze_sha256"] != actual_freeze_hash
        ):
            raise ValueError(
                f"Selection freeze hash mismatch in artifact provenance for {bundle_id}"
            )

    return load_calibrator_from_artifact(artifact_data)
