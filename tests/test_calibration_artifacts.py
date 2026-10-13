"""Unit tests for calibration artifact serialization, registry loading, and tampering detection."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from intellitwin.data.artifacts import compute_sha256
from intellitwin.uncertainty.artifacts import (
    load_calibrator_from_artifact,
    load_frozen_calibrator,
    serialize_calibrator_artifact,
    write_atomic_json,
)
from intellitwin.uncertainty.calibration import fit_calibrator_bundle
from intellitwin.uncertainty.schema import METHOD_DECISION_AWARE, CandidateConfig


def test_serialization_and_reload_preserve_interval_outputs(tmp_path: Path) -> None:
    """Verify that serialization to JSON and reload preserve prediction intervals."""
    # Synthetic calibrator
    eids = np.repeat(np.arange(1, 26), 10)
    cycles = np.tile(np.arange(30, 40), 25)
    preds = np.random.default_rng(2026).uniform(10.0, 100.0, size=len(eids))
    labels = preds + np.random.default_rng(2026).normal(0.0, 5.0, size=len(eids))
    labels = np.maximum(0.0, labels)
    regimes = np.array(["C1"] * len(eids), dtype=object)

    cand = CandidateConfig.from_id("gamma1_betap1")
    cal_orig = fit_calibrator_bundle(
        method_id=METHOD_DECISION_AWARE,
        predictions=preds,
        labels=labels,
        regimes=regimes,
        engine_ids=eids,
        endpoint_cycles=cycles,
        dataset_name="FD002",
        model_family="GBR",
        model_seed=2026,
        candidate=cand,
    )

    art_dict = serialize_calibrator_artifact(
        calibrator=cal_orig,
        checkpoint_hash="dummy_ckpt_hash",
        preprocessor_hash="dummy_prep_hash",
        split_manifest_hash="dummy_split_hash",
        raw_dataset_hash="dummy_raw_hash",
        calibration_pred_cache_hash="dummy_cache_hash",
        selection_freeze_hash="dummy_freeze_hash",
        git_commit="dummy_commit",
        source_hashes={"code": "dummy_src"},
    )

    out_file = tmp_path / "calibrator.json"
    write_atomic_json(out_file, art_dict)

    with open(out_file, encoding="utf-8") as f:
        loaded_dict = json.load(f)

    cal_reloaded = load_calibrator_from_artifact(loaded_dict)

    # Test intervals on unseen query points
    q_preds = np.array([15.0, 35.0, 65.0, 95.0])
    q_regimes = np.array(["C1", "C1", "C1", "C1"])

    for cov in (0.80, 0.90, 0.95):
        l_orig, u_orig, fb_orig = cal_orig.predict_intervals(q_preds, q_regimes, cov)
        l_rel, u_rel, fb_rel = cal_reloaded.predict_intervals(q_preds, q_regimes, cov)

        np.testing.assert_allclose(l_orig, l_rel, rtol=1e-14, atol=1e-14)
        np.testing.assert_allclose(u_orig, u_rel, rtol=1e-14, atol=1e-14)
        np.testing.assert_array_equal(fb_orig, fb_rel)


def test_hash_tampering_is_rejected(tmp_path: Path) -> None:
    """Verify that tampering with an artifact causes loader to raise ValueError."""
    # Write dummy artifact
    art_path = tmp_path / "dummy_cal.json"
    write_atomic_json(
        art_path,
        {
            "schema_version": "step08-calibrator-v1",
            "protocol_version": "step08-v1",
            "method_id": "global_hcp",
            "dataset": "FD001",
            "model_family": "GBR",
            "model_seed": 2026,
            "selected_candidate_id": None,
            "candidate_parameters": {"gamma": None, "beta_code": None, "beta": None},
            "target_definition": "rul_true",
            "score_definition": "abs(y - p)",
            "quantile_definition": "engine-weighted",
            "threshold_bundles": {},
            "provenance": {},
        },
    )

    art_hash = compute_sha256(art_path)

    # Registry with matching hash
    reg_path = tmp_path / "calibration_registry.json"
    registry_data = {
        "schema_version": "step08-registry-v1",
        "entries": {
            "FD001_GBR_seed2026_global_hcp": {
                "calibrator_artifact_path": str(art_path.relative_to(tmp_path)),
                "artifact_sha256": art_hash,
            }
        },
    }
    write_atomic_json(reg_path, registry_data)

    # Now tamper with artifact by appending a comment or altering content
    write_atomic_json(art_path, {"schema_version": "step08-calibrator-v1", "tampered": True})

    with pytest.raises(ValueError, match="Calibrator artifact hash mismatch"):
        load_frozen_calibrator(
            dataset="FD001",
            model_family="GBR",
            seed=2026,
            method_id="global_hcp",
            registry_path=reg_path,
            base_dir=tmp_path,
        )


def test_write_atomic_json_rejects_nan_inf(tmp_path: Path) -> None:
    """Verify that write_atomic_json rejects NaN and Infinity."""
    nan_dict = {"val": float("nan")}
    inf_dict = {"val": float("inf")}

    with pytest.raises(ValueError):
        write_atomic_json(tmp_path / "test_nan.json", nan_dict)

    with pytest.raises(ValueError):
        write_atomic_json(tmp_path / "test_inf.json", inf_dict)
