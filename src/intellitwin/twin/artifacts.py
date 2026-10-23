"""Artifact manager and validation partition loader for IntelliTwin replay demo.

Restricted strictly to:
- Datasets: FD001, FD002, FD004
- Models: GBR, LSTM
- Methods: global_hcp, regime_hcp, decision_aware_hcp
- Seed: 2026 only
- Nominal coverage: 0.90 only
- Validation engines only from committed split manifests
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import EXPECTED_ENGINE_COUNTS
from intellitwin.data.splits import load_split_manifest
from intellitwin.models.registry import FrozenBaseModel, load_frozen_base_model
from intellitwin.uncertainty.artifacts import load_frozen_calibrator
from intellitwin.uncertainty.calibration import Calibrator

ALLOWED_DATASETS: tuple[str, ...] = ("FD001", "FD002", "FD004")
ALLOWED_MODELS: tuple[str, ...] = ("GBR", "LSTM")
ALLOWED_METHODS: tuple[str, ...] = ("global_hcp", "regime_hcp", "decision_aware_hcp")
FIXED_SEED: int = 2026
FIXED_NOMINAL_COVERAGE: float = 0.90


@dataclass(frozen=True)
class ActiveArtifacts:
    """Container holding the single active model, calibrator, and provenance."""

    dataset: str
    model_family: str
    seed: int
    method_id: str
    nominal_coverage: float
    model: FrozenBaseModel
    calibrator: Calibrator
    model_id: str
    model_config_id: str
    model_checkpoint_sha256: str
    model_metadata_sha256: str
    calibrator_bundle_id: str
    calibrator_artifact_sha256: str
    calibrator_candidate_id: str | None
    preprocessor_sha256: str
    split_manifest_sha256: str


class ArtifactManager:
    """Manages frozen model/calibrator artifacts and telemetry observations for replay."""

    def __init__(self, base_dir: Path | str = ".") -> None:
        self.base_dir = Path(base_dir).resolve()
        self._validation_engines: dict[str, list[int]] = {}
        self._non_validation_engines: dict[str, set[int]] = {}
        self._load_split_catalogs()

    def _load_split_catalogs(self) -> None:
        """Parse committed split manifests for validation and forbidden engines."""
        for ds in ALLOWED_DATASETS:
            split_p = self.base_dir / f"data/splits/{ds.lower()}_engine_split_seed_2026.json"
            if not split_p.exists():
                raise FileNotFoundError(f"Split manifest missing at: {split_p}")
            manifest = load_split_manifest(split_p)
            val_list = sorted(manifest.validation)
            self._validation_engines[ds] = val_list
            forbidden = set(manifest.train) | set(manifest.calibration) | set(manifest.test)
            self._non_validation_engines[ds] = forbidden

    def get_validation_engines(self, dataset: str) -> list[int]:
        """Return permitted validation engine IDs for a dataset."""
        if dataset not in self._validation_engines:
            raise ValueError(f"Unsupported dataset: {dataset}")
        return list(self._validation_engines[dataset])

    def get_all_validation_engines(self) -> dict[str, list[int]]:
        """Return permitted validation engine IDs for all supported datasets."""
        return {ds: list(engines) for ds, engines in self._validation_engines.items()}

    def validate_selection(
        self,
        dataset: str,
        engine_id: int,
        model_family: str,
        method_id: str,
    ) -> None:
        """Validate selection against strict permitted sets before opening a session."""
        if dataset not in ALLOWED_DATASETS:
            raise ValueError(f"Invalid dataset '{dataset}'. Must be one of {ALLOWED_DATASETS}")
        if model_family not in ALLOWED_MODELS:
            raise ValueError(
                f"Invalid model_family '{model_family}'. Must be one of {ALLOWED_MODELS}"
            )
        if method_id not in ALLOWED_METHODS:
            raise ValueError(f"Invalid method_id '{method_id}'. Must be one of {ALLOWED_METHODS}")

        if dataset not in self._validation_engines:
            raise ValueError(f"No validation catalog for dataset '{dataset}'")

        if engine_id in self._non_validation_engines.get(dataset, set()):
            raise PermissionError(
                f"Engine {engine_id} belongs to a forbidden partition in {dataset}. "
                "Replay is strictly limited to validation partition engines."
            )

        allowed_ids = self._validation_engines[dataset]
        if engine_id not in allowed_ids:
            raise ValueError(
                f"Engine {engine_id} is not in validation partition for {dataset}. "
                f"Allowed IDs: {allowed_ids}"
            )

    def load_artifacts(
        self,
        dataset: str,
        model_family: str,
        method_id: str,
    ) -> ActiveArtifacts:
        """Load frozen base model and calibrator for the active configuration."""
        if (
            dataset not in ALLOWED_DATASETS
            or model_family not in ALLOWED_MODELS
            or method_id not in ALLOWED_METHODS
        ):
            raise ValueError(f"Invalid configuration: {dataset}, {model_family}, {method_id}")

        model_reg_p = self.base_dir / "experiments/base_models/model_registry.json"
        calib_reg_p = self.base_dir / "experiments/calibration/calibration_registry.json"

        if not model_reg_p.exists():
            raise FileNotFoundError(f"Model registry missing at: {model_reg_p}")
        if not calib_reg_p.exists():
            raise FileNotFoundError(f"Calibration registry missing at: {calib_reg_p}")

        # Load registries to extract provenance hashes
        with open(model_reg_p, encoding="utf-8") as f:
            m_data = json.load(f)
        m_entries = m_data if isinstance(m_data, list) else m_data.get("models", [])
        m_match = None
        for entry in m_entries:
            if (
                entry["dataset"] == dataset
                and entry["model_family"] == model_family
                and entry["seed"] == FIXED_SEED
            ):
                m_match = entry
                break
        if m_match is None:
            raise KeyError(f"No model found for {dataset}/{model_family}/seed {FIXED_SEED}")

        with open(calib_reg_p, encoding="utf-8") as f:
            c_data = json.load(f)
        c_entries = c_data.get("entries", {})
        bundle_id = f"{dataset}_{model_family}_seed{FIXED_SEED}_{method_id}"
        c_match = c_entries.get(bundle_id)
        if c_match is None:
            raise KeyError(f"No calibrator found for {bundle_id}")

        # Load and verify model & calibrator via existing authoritative verification loaders
        frozen_model = load_frozen_base_model(
            dataset=dataset,
            model_family=model_family,
            seed=FIXED_SEED,
            registry_path=model_reg_p,
            base_dir=self.base_dir,
        )

        frozen_calibrator = load_frozen_calibrator(
            dataset=dataset,
            model_family=model_family,
            seed=FIXED_SEED,
            method_id=method_id,
            registry_path=calib_reg_p,
            base_dir=self.base_dir,
        )

        return ActiveArtifacts(
            dataset=dataset,
            model_family=model_family,
            seed=FIXED_SEED,
            method_id=method_id,
            nominal_coverage=FIXED_NOMINAL_COVERAGE,
            model=frozen_model,
            calibrator=frozen_calibrator,
            model_id=m_match["model_id"],
            model_config_id=m_match["configuration_id"],
            model_checkpoint_sha256=m_match["checkpoint_sha256"],
            model_metadata_sha256=m_match["metadata_sha256"],
            calibrator_bundle_id=bundle_id,
            calibrator_artifact_sha256=c_match["artifact_sha256"],
            calibrator_candidate_id=c_match.get("selected_candidate_id"),
            preprocessor_sha256=m_match["preprocessor_sha256"],
            split_manifest_sha256=m_match["split_manifest_sha256"],
        )

    def load_engine_telemetry(self, dataset: str, engine_id: int) -> pd.DataFrame:
        """Load telemetry observations strictly for a single validation engine.

        Rejects any request for non-validation engines.
        Returns a DataFrame sorted by cycle.
        """
        self.validate_selection(
            dataset=dataset,
            engine_id=engine_id,
            model_family="GBR",
            method_id="decision_aware_hcp",
        )

        raw_path = self.base_dir / f"data/raw/cmapss/train_{dataset}.txt"
        if not raw_path.exists():
            raise FileNotFoundError(f"Raw data file missing at: {raw_path}")

        expected_count = EXPECTED_ENGINE_COUNTS[dataset]
        raw_df = load_cmapss_run_to_failure(
            path=raw_path,
            dataset_name=dataset,
            expected_engine_count=expected_count,
        )

        engine_df = raw_df[raw_df["unit"] == engine_id].sort_values("cycle").reset_index(drop=True)
        if len(engine_df) == 0:
            raise ValueError(f"No records found for engine {engine_id} in {dataset}")

        return engine_df
