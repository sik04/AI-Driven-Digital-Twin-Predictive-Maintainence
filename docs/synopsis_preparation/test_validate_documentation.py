"""
Unit tests for docs/synopsis_preparation/validate_documentation.py.

Uses isolated temporary fixtures to verify that validation fails closed on:
- a missing table row;
- a duplicate table row;
- a malformed table boundary;
- a missing component;
- a duplicate component;
- an unresolved citation;
- a missing LaTeX input;
- a broken active source path;
- an incorrect numerical beta;
- an unsupported populated held-out result.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT / "docs" / "synopsis_preparation") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "docs" / "synopsis_preparation"))

from validate_documentation import (  # noqa: E402
    DOCS_DIR,
    check_calibration_math,
    check_component_manifest,
    check_latex_inputs_and_citations,
    check_no_fabricated_results,
    check_source_manifest,
    check_table_templates,
    run_all_validations,
)


def test_real_documentation_passes_all_checks() -> None:
    """Verify that the active, committed documentation suite passes all checks."""
    passed, report = run_all_validations()
    assert passed, f"Expected active documentation to pass, but failed: {report}"


def test_reject_missing_table_row(tmp_path: Path) -> None:
    """Verify fail-closed rejection when a required point-prediction row is missing."""
    orig_tables = DOCS_DIR / "results_table_templates.md"
    content = orig_tables.read_text(encoding="utf-8")

    # Remove FD004 LSTM point row
    row_to_remove = (
        "| **FD004** | LSTM (`lstm_h64_lr0010`) | 50 | "
        "`PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |"
    )
    mutated = content.replace(row_to_remove, "")
    mutated_file = tmp_path / "results_table_templates.md"
    mutated_file.write_text(mutated, encoding="utf-8")

    res = check_table_templates(mutated_file)
    assert res["status"] == "FAIL"
    assert any("T3 missing required point prediction rows" in issue for issue in res["issues"])


def test_reject_duplicate_table_row(tmp_path: Path) -> None:
    """Verify fail-closed rejection when a duplicate point row exists."""
    orig_tables = DOCS_DIR / "results_table_templates.md"
    content = orig_tables.read_text(encoding="utf-8")

    # Duplicate FD001 GBR point row
    row_to_dup = (
        "| **FD001** | GBR (`gbr_lr010_leaf15_l2_0`) | 20 | "
        "`PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |"
    )
    mutated = content.replace(row_to_dup, f"{row_to_dup}\n{row_to_dup}")
    mutated_file = tmp_path / "results_table_templates.md"
    mutated_file.write_text(mutated, encoding="utf-8")

    res = check_table_templates(mutated_file)
    assert res["status"] == "FAIL"
    assert any("T3 duplicate point row" in issue for issue in res["issues"])


def test_reject_malformed_table_boundary(tmp_path: Path) -> None:
    """Verify fail-closed rejection when table boundary runs directly into next header."""
    orig_tables = DOCS_DIR / "results_table_templates.md"
    content = orig_tables.read_text(encoding="utf-8")

    # Malform boundary: inject header directly into pipe row
    target_row = (
        "| **FD004** | LSTM (`lstm_h64_lr0010`) | 50 | "
        "`PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |"
    )
    bad_row = "| **FD004** | LSTM | 50 | `PENDING` | `PENDING` | `PENDING` | ## Table T4: Bug |"
    mutated = content.replace(target_row, bad_row)
    mutated_file = tmp_path / "results_table_templates.md"
    mutated_file.write_text(mutated, encoding="utf-8")

    res = check_table_templates(mutated_file)
    assert res["status"] == "FAIL"
    assert any("Malformed table boundary" in issue for issue in res["issues"])


def test_reject_missing_component(tmp_path: Path) -> None:
    """Verify fail-closed rejection when a component ID is removed from manifest CSV."""
    orig_csv = DOCS_DIR / "component_reporting_template.csv"
    lines = orig_csv.read_text(encoding="utf-8").splitlines()

    # Drop one row (not header)
    mutated_lines = [lines[0]] + lines[2:]
    mutated_file = tmp_path / "component_reporting_template.csv"
    mutated_file.write_text("\n".join(mutated_lines), encoding="utf-8")

    res = check_component_manifest(mutated_file)
    assert res["status"] == "FAIL"
    assert any("Expected 152 components, found 151" in issue for issue in res["issues"])


def test_reject_duplicate_component(tmp_path: Path) -> None:
    """Verify fail-closed rejection when a component ID is duplicated."""
    orig_csv = DOCS_DIR / "component_reporting_template.csv"
    lines = orig_csv.read_text(encoding="utf-8").splitlines()

    # Duplicate row 1
    mutated_lines = [lines[0], lines[1], lines[1]] + lines[2:]
    mutated_file = tmp_path / "component_reporting_template.csv"
    mutated_file.write_text("\n".join(mutated_lines), encoding="utf-8")

    res = check_component_manifest(mutated_file)
    assert res["status"] == "FAIL"
    assert any("Duplicate components found" in issue for issue in res["issues"])


def test_reject_unresolved_citation(tmp_path: Path) -> None:
    """Verify fail-closed rejection when a LaTeX file contains an unresolved citation."""
    tex_dir = tmp_path / "latex"
    tex_dir.mkdir()
    bad_tex = tex_dir / "test.tex"
    bad_tex.write_text(r"\section{Test} \cite{nonexistent_citation_key_2026}", encoding="utf-8")

    res = check_latex_inputs_and_citations(latex_root=tex_dir, valid_keys={"saxena2008damage"})
    assert res["status"] == "FAIL"
    assert len(res["undefined_citations"]) == 1
    assert res["undefined_citations"][0]["key"] == "nonexistent_citation_key_2026"


def test_reject_missing_latex_input(tmp_path: Path) -> None:
    """Verify fail-closed rejection when \\input points to a nonexistent file."""
    tex_dir = tmp_path / "latex"
    tex_dir.mkdir()
    bad_tex = tex_dir / "main.tex"
    bad_tex.write_text(r"\input{sections/missing_section}", encoding="utf-8")

    res = check_latex_inputs_and_citations(latex_root=tex_dir, valid_keys={"key"})
    assert res["status"] == "FAIL"
    assert len(res["missing_inputs"]) == 1
    assert res["missing_inputs"][0]["target"] == "sections/missing_section"


def test_reject_broken_active_source_path(tmp_path: Path) -> None:
    """Verify fail-closed rejection when source_manifest.csv contains a nonexistent local path."""
    manifest_csv = tmp_path / "source_manifest.csv"
    with open(manifest_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source_id", "category", "path_or_url", "description", "status"])
        writer.writerow(
            [
                "SRC-TEST",
                "code",
                "nonexistent/directory/broken_file.py",
                "Fake broken path",
                "active",
            ]
        )

    res = check_source_manifest(manifest_csv)
    assert res["status"] == "FAIL"
    assert len(res["missing_paths"]) == 1
    assert res["missing_paths"][0]["path"] == "nonexistent/directory/broken_file.py"


def test_reject_incorrect_numerical_beta(tmp_path: Path) -> None:
    """Verify fail-closed rejection when mathematical beta = -1 without -ln(2)."""
    fake_docs = tmp_path / "docs"
    fake_docs.mkdir()
    fake_fig = fake_docs / "figure_plan.md"
    fake_fig.write_text("At numerical beta = -1, the interval changes.", encoding="utf-8")

    res = check_calibration_math(fake_docs)
    assert res["status"] == "FAIL"
    assert len(res["issues"]) > 0


def test_reject_unsupported_populated_held_out_result(tmp_path: Path) -> None:
    """Verify fail-closed rejection when held-out tables contain fabricated numeric results."""
    orig_tables = DOCS_DIR / "results_table_templates.md"
    content = orig_tables.read_text(encoding="utf-8")

    # Replace PENDING in T3 with a fabricated number 24.15
    target_row = (
        "| **FD001** | GBR (`gbr_lr010_leaf15_l2_0`) | 20 | "
        "`PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |"
    )
    fabricated_row = (
        "| **FD001** | GBR (`gbr_lr010_leaf15_l2_0`) | 20 | 24.15 | 18.20 | 22.05 | COMPLETED |"
    )
    mutated = content.replace(target_row, fabricated_row)
    mutated_file = tmp_path / "results_table_templates.md"
    mutated_file.write_text(mutated, encoding="utf-8")

    res = check_no_fabricated_results(mutated_file)
    assert res["status"] == "FAIL"
    assert any("Fabricated numerical result found" in issue for issue in res["issues"])
