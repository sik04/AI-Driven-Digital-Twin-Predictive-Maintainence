"""Targeted regression tests for documentation path portability and resolution.

Requirements:
- Relative inputs resolve against base_dir when process cwd is elsewhere.
- Repository root containing spaces works.
- Absolute in-repository inputs render as relative POSIX references.
- Audit outside evidence dir but inside repository retains complete relative path.
- Outside-root published references raise ValueError before output creation.
- Handoff contains no temporary root prefix, Windows drive, or file:/// references.
- All expected evidence paths are present in handoff.
- Audit copying preserves exact bytes (including newlines).
- Final receipt artifact hashes match actual bytes and exclude itself.
- Existing no-overwrite behavior remains intact.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from test_phase08_submission_verification import _build_valid_contrasts_df

from intellitwin.data.artifacts import compute_sha256
from intellitwin.robustness.reporting import (
    resolve_repo_path,
    to_repo_relative_posix,
)
from scripts.finalize_phase08_reporting import finalize_phase08_reporting


def _build_synthetic_factor_effects_df() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    datasets = ["FD001", "FD002", "FD004"]
    models = ["GBR", "LSTM"]
    factors = ["gamma_scale", "beta_asymmetry", "regime_routing"]

    for ds in datasets:
        for m in models:
            for fac in factors:
                eff = -1.5 if fac != "regime_routing" else 0.2
                rows.append(
                    {
                        "dataset": ds,
                        "model_family": m,
                        "factor": fac,
                        "metric": "cost",
                        "effect_on_minus_off": eff,
                        "ci_95_low": eff - 0.5,
                        "ci_95_high": eff + 0.5,
                    }
                )
    return pd.DataFrame(rows)


def _setup_synthetic_repo(base: Path) -> dict[str, Path]:
    conf_dir = base / "experiments/confirmatory_v1"
    conf_dir.mkdir(parents=True, exist_ok=True)
    (conf_dir / "rq_decisions.json").write_text("{}", encoding="utf-8")
    (conf_dir / "component_evidence.csv").write_text("dataset,value\nFD001,1.0\n", encoding="utf-8")
    (conf_dir / "independent_audit.json").write_text("{}", encoding="utf-8")

    ev_dir = base / "experiments/phase08_exploratory_v3"
    ev_dir.mkdir(parents=True, exist_ok=True)

    df_fac = _build_synthetic_factor_effects_df()
    df_fac.to_csv(ev_dir / "factor_main_effects.csv", index=False)

    df_contrasts = _build_valid_contrasts_df()
    df_contrasts.to_csv(ev_dir / "paired_contrasts.csv", index=False)

    datasets = ["FD001", "FD002", "FD004"]
    models = ["GBR", "LSTM"]
    abl_rows = []
    stress_rows = []
    sub_rows = []
    for ds in datasets:
        for mf in models:
            abl_rows.append(
                {
                    "dataset": ds,
                    "model_family": mf,
                    "variant_id": "gamma0_beta0_global",
                    "coverage_mean": 0.90,
                    "cost_mean": 10.0,
                    "width_mean": 20.0,
                    "interval_score_mean": 25.0,
                    "rmse_mean": 15.0,
                }
            )
            stress_rows.append(
                {
                    "dataset": ds,
                    "model_family": mf,
                    "method_id": "global_hcp",
                    "condition_id": "clean",
                    "coverage_mean": 0.90,
                    "cost_mean": 10.0,
                    "width_mean": 20.0,
                    "interval_score_mean": 25.0,
                    "rmse_mean": 15.0,
                }
            )
            sub_rows.append(
                {
                    "evaluation_type": "ablation",
                    "dataset": ds,
                    "model_family": mf,
                    "variant_id": "gamma0_beta0_global",
                    "method_id": "",
                    "condition_id": "clean",
                    "subgroup_family": "regime",
                    "subgroup": "C1",
                    "n_endpoints": 100,
                    "n_engines": 20,
                    "is_eligible": True,
                    "coverage": 0.90,
                    "coverage_abs_error": 0.0,
                    "lower_tail_miss": 0.05,
                    "upper_tail_miss": 0.05,
                }
            )

    pd.DataFrame(abl_rows).to_csv(ev_dir / "ablation_summary.csv", index=False)
    pd.DataFrame(stress_rows).to_csv(ev_dir / "stress_summary.csv", index=False)
    pd.DataFrame(sub_rows).to_csv(ev_dir / "subgroup_metrics.csv", index=False)
    (ev_dir / "zero_difference_checks.csv").write_text(
        "dataset,delta\nFD001,0.0\n", encoding="utf-8"
    )
    (ev_dir / "input_manifest.json").write_text("{}", encoding="utf-8")

    csv_files = [
        "factor_main_effects.csv",
        "paired_contrasts.csv",
        "ablation_summary.csv",
        "stress_summary.csv",
        "zero_difference_checks.csv",
        "subgroup_metrics.csv",
    ]
    art_hashes = {c_name: compute_sha256(ev_dir / c_name) for c_name in csv_files}

    man = {
        "schema_version": "phase08-execution-manifest-v1",
        "status": "EXPLORATORY_POST_CONFIRMATORY",
        "artifact_hashes": art_hashes,
    }
    man_p = ev_dir / "execution_manifest.json"
    man_p.write_text(json.dumps(man, indent=2), encoding="utf-8")
    man_hash = compute_sha256(man_p)

    audit_dir = base / "experiments/phase08_submission_verification_v1"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_data = {
        "schema_version": "phase08-independent-audit-v3",
        "overall_status": "PASS",
        "failing_reasons": [],
        "execution_manifest_sha256": man_hash,
        "checks": {
            chk: {"status": "PASS", "expected_count": 1, "checked_count": 1}
            for chk in [
                "exact_endpoint_membership",
                "calibration_reconstruction",
                "full_checkpoint_prediction_parity",
                "full_interval_reconstruction",
                "full_simulation_reconstruction",
                "endpoint_to_engine_metric_reconstruction",
                "full_subgroup_reconstruction",
                "full_bootstrap_reconstruction",
                "artifact_and_provenance_integrity",
                "protected_input_integrity",
            ]
        },
    }
    audit_p = audit_dir / "independent_audit.json"
    audit_p.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")

    rep_dir = base / "research/results/phase08_submission_v2"
    return {
        "base": base,
        "ev_dir": ev_dir,
        "rep_dir": rep_dir,
        "audit_p": audit_p,
    }


def test_relative_inputs_resolve_against_base_dir_when_cwd_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify relative paths resolve against base_dir rather than os.getcwd()."""
    repo = tmp_path / "repo"
    other = tmp_path / "other_cwd"
    repo.mkdir()
    other.mkdir()

    paths = _setup_synthetic_repo(repo)
    monkeypatch.chdir(other)

    resolved = resolve_repo_path("experiments/phase08_exploratory_v3", repo)
    assert resolved == paths["ev_dir"].resolve()
    assert resolved != (other / "experiments/phase08_exploratory_v3").resolve()

    # Finalize reporting with relative paths while cwd is elsewhere
    receipt_p = finalize_phase08_reporting(
        evidence_dir="experiments/phase08_exploratory_v3",
        output_report_dir="research/results/phase08_submission_v2",
        audit_path="experiments/phase08_submission_verification_v1/independent_audit.json",
        base_dir=repo,
    )
    assert receipt_p.exists()
    assert (repo / "research/results/phase08_submission_v2/writing_handoff.md").exists()


def test_repository_root_containing_spaces_works(tmp_path: Path) -> None:
    """Verify repository root containing spaces resolves and generates reports cleanly."""
    repo = tmp_path / "repo with spaces in name"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    receipt_p = finalize_phase08_reporting(
        evidence_dir="experiments/phase08_exploratory_v3",
        output_report_dir="research/results/phase08_submission_v2",
        audit_path="experiments/phase08_submission_verification_v1/independent_audit.json",
        base_dir=repo,
    )
    assert receipt_p.exists()
    handoff_text = (paths["rep_dir"] / "writing_handoff.md").read_text(encoding="utf-8")
    assert "repo with spaces in name" not in handoff_text
    assert "`experiments/phase08_exploratory_v3`" in handoff_text


def test_absolute_in_repository_inputs_render_as_relative_posix(tmp_path: Path) -> None:
    """Verify absolute paths within the repository render as relative POSIX paths."""
    repo = tmp_path / "repo"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    abs_ev = paths["ev_dir"].resolve()
    abs_rep = paths["rep_dir"].resolve()

    rel_ev = to_repo_relative_posix(abs_ev, repo)
    rel_rep = to_repo_relative_posix(abs_rep, repo)

    assert rel_ev == "experiments/phase08_exploratory_v3"
    assert rel_rep == "research/results/phase08_submission_v2"


def test_audit_outside_evidence_dir_retains_complete_relative_path(tmp_path: Path) -> None:
    """Verify audit outside evidence dir retains full repository-relative path."""
    repo = tmp_path / "repo"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    finalize_phase08_reporting(
        evidence_dir=paths["ev_dir"],
        output_report_dir=paths["rep_dir"],
        audit_path=paths["audit_p"],
        base_dir=repo,
    )

    handoff_text = (paths["rep_dir"] / "writing_handoff.md").read_text(encoding="utf-8")
    expected_rel = "experiments/phase08_submission_verification_v1/independent_audit.json"
    assert f"- **Independent Audit Path**: `{expected_rel}`" in handoff_text
    assert f"| **Independent Audit** | `{expected_rel}` |" in handoff_text


def test_outside_root_published_references_raise_value_error_before_output_creation(
    tmp_path: Path,
) -> None:
    """Verify published references outside base_dir raise ValueError before output creation."""
    repo = tmp_path / "repo"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    outside_evidence = tmp_path / "outside_evidence"
    outside_evidence.mkdir()
    output_dir = repo / "research/results/phase08_never_created"

    with pytest.raises(ValueError, match="is outside repository root"):
        finalize_phase08_reporting(
            evidence_dir=outside_evidence,
            output_report_dir=output_dir,
            base_dir=repo,
        )

    # Output directory must NOT have been created
    assert not output_dir.exists()

    # Also test outside output_report_dir
    outside_report = tmp_path / "outside_reports"
    with pytest.raises(ValueError, match="is outside repository root"):
        finalize_phase08_reporting(
            evidence_dir=paths["ev_dir"],
            output_report_dir=outside_report,
            base_dir=repo,
        )
    assert not outside_report.exists()


def test_handoff_contains_no_temporary_root_prefix_or_windows_drive_or_file_uri(
    tmp_path: Path,
) -> None:
    """Verify handoff text contains no temp prefixes, drive letters, or file:/// links."""
    repo = tmp_path / "repo"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    finalize_phase08_reporting(
        evidence_dir=paths["ev_dir"],
        output_report_dir=paths["rep_dir"],
        audit_path=paths["audit_p"],
        base_dir=repo,
    )

    handoff_text = (paths["rep_dir"] / "writing_handoff.md").read_text(encoding="utf-8")

    assert str(repo) not in handoff_text
    assert repo.as_posix() not in handoff_text
    assert "file:///" not in handoff_text

    # No Windows drive paths in markdown links or inline code
    drive_matches = re.findall(r"`[A-Za-z]:[/\\][^`]+`", handoff_text)
    assert drive_matches == [], f"Found Windows drive paths in handoff: {drive_matches}"


def test_all_expected_evidence_paths_are_present_in_handoff(tmp_path: Path) -> None:
    """Verify all 10 evidence items and report bundle are present with repo-relative paths."""
    repo = tmp_path / "repo"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    finalize_phase08_reporting(
        evidence_dir=paths["ev_dir"],
        output_report_dir=paths["rep_dir"],
        audit_path=paths["audit_p"],
        base_dir=repo,
    )

    handoff_text = (paths["rep_dir"] / "writing_handoff.md").read_text(encoding="utf-8")

    assert "All paths below are relative to the repository root." in handoff_text
    expected_paths = [
        "experiments/phase08_exploratory_v3",
        "research/results/phase08_submission_v2",
        "experiments/phase08_submission_verification_v1/independent_audit.json",
        "experiments/phase08_exploratory_v3/execution_manifest.json",
        "experiments/phase08_exploratory_v3/input_manifest.json",
        "experiments/phase08_exploratory_v3/ablation_summary.csv",
        "experiments/phase08_exploratory_v3/stress_summary.csv",
        "experiments/phase08_exploratory_v3/paired_contrasts.csv",
        "experiments/phase08_exploratory_v3/factor_main_effects.csv",
        "experiments/phase08_exploratory_v3/zero_difference_checks.csv",
        "experiments/phase08_exploratory_v3/subgroup_metrics.csv",
    ]
    for p_str in expected_paths:
        assert f"`{p_str}`" in handoff_text, f"Missing expected path `{p_str}` in handoff"


def test_audit_copying_preserves_bytes_including_newlines(tmp_path: Path) -> None:
    """Verify shutil.copyfile binary copying preserves exact bytes and newlines."""
    repo = tmp_path / "repo"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    # Write audit with explicit mixed newlines
    custom_bytes = (
        b'{\r\n  "schema_version": "phase08-independent-audit-v3",\n'
        b'  "overall_status": "PASS"\r\n}\n'
    )
    paths["audit_p"].write_bytes(custom_bytes)

    # Update manifest to match
    man_p = paths["ev_dir"] / "execution_manifest.json"
    man_hash = compute_sha256(man_p)
    # Write valid audit with custom newlines
    audit_data = {
        "schema_version": "phase08-independent-audit-v3",
        "overall_status": "PASS",
        "failing_reasons": [],
        "execution_manifest_sha256": man_hash,
        "checks": {
            chk: {"status": "PASS", "expected_count": 1, "checked_count": 1}
            for chk in [
                "exact_endpoint_membership",
                "calibration_reconstruction",
                "full_checkpoint_prediction_parity",
                "full_interval_reconstruction",
                "full_simulation_reconstruction",
                "endpoint_to_engine_metric_reconstruction",
                "full_subgroup_reconstruction",
                "full_bootstrap_reconstruction",
                "artifact_and_provenance_integrity",
                "protected_input_integrity",
            ]
        },
    }
    raw_json = json.dumps(audit_data, indent=2)
    # inject CRLF
    crlf_bytes = raw_json.replace("\n", "\r\n").encode("utf-8")
    paths["audit_p"].write_bytes(crlf_bytes)

    finalize_phase08_reporting(
        evidence_dir=paths["ev_dir"],
        output_report_dir=paths["rep_dir"],
        audit_path=paths["audit_p"],
        base_dir=repo,
    )

    copied_audit = paths["rep_dir"] / "independent_audit.json"
    assert copied_audit.read_bytes() == crlf_bytes
    assert compute_sha256(copied_audit) == compute_sha256(paths["audit_p"])


def test_new_receipt_artifact_hashes_match_actual_bytes_and_exclude_itself(tmp_path: Path) -> None:
    """Verify final receipt hashes match all generated report files and exclude receipt itself."""
    repo = tmp_path / "repo"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    finalize_phase08_reporting(
        evidence_dir=paths["ev_dir"],
        output_report_dir=paths["rep_dir"],
        audit_path=paths["audit_p"],
        base_dir=repo,
    )

    receipt_p = paths["rep_dir"] / "final_receipt.json"
    receipt = json.loads(receipt_p.read_text(encoding="utf-8"))

    report_hashes = receipt["report_artifact_hashes"]
    assert "final_receipt.json" not in report_hashes

    # Check that each file in receipt exists and has matching hash
    for rel_path, expected_hash in report_hashes.items():
        art_p = paths["rep_dir"] / rel_path
        assert art_p.exists(), f"Report artifact {rel_path} does not exist"
        actual_hash = compute_sha256(art_p)
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}"


def test_existing_no_overwrite_behavior_intact(tmp_path: Path) -> None:
    """Verify finalize_phase08_reporting refuses to overwrite without --overwrite."""
    repo = tmp_path / "repo"
    repo.mkdir()
    paths = _setup_synthetic_repo(repo)

    finalize_phase08_reporting(
        evidence_dir=paths["ev_dir"],
        output_report_dir=paths["rep_dir"],
        audit_path=paths["audit_p"],
        base_dir=repo,
    )

    with pytest.raises(FileExistsError, match="contains completed reports"):
        finalize_phase08_reporting(
            evidence_dir=paths["ev_dir"],
            output_report_dir=paths["rep_dir"],
            audit_path=paths["audit_p"],
            base_dir=repo,
            overwrite=False,
        )
