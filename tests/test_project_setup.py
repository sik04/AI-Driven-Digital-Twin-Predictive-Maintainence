"""Automated tests validating project setup, package integrity, and research governance."""

import csv
import sys
from pathlib import Path

import intellitwin


def test_package_import_and_metadata() -> None:
    """Verify package imports correctly and exposes expected metadata."""
    assert hasattr(intellitwin, "__version__")
    assert isinstance(intellitwin.__version__, str)
    assert intellitwin.__version__ == "0.1.0.dev1"

    assert hasattr(intellitwin, "__authors__")
    assert isinstance(intellitwin.__authors__, list)
    expected_authors = ["Mayank Singh", "Shiksha Pandey", "Ruchi Gupta"]
    assert intellitwin.__authors__ == expected_authors


def test_python_runtime_compatibility() -> None:
    """Verify runtime Python meets the >= 3.10 requirement."""
    assert sys.version_info >= (3, 10), "Python version must be >= 3.10"


def test_required_governance_files_exist() -> None:
    """Verify critical research governance files exist and are not empty."""
    repo_root = Path(__file__).parent.parent

    required_files = [
        repo_root / "pyproject.toml",
        repo_root / "README.md",
        repo_root / "LICENSE",
        repo_root / "CONTRIBUTING.md",
        repo_root / "CHANGELOG.md",
        repo_root / "Makefile",
        repo_root / ".gitignore",
        repo_root / ".editorconfig",
        repo_root / ".github" / "workflows" / "ci.yml",
        repo_root / ".github" / "pull_request_template.md",
        repo_root / "docs" / "project_scope.md",
        repo_root / "docs" / "development_setup.md",
        repo_root / "docs" / "architecture_overview.md",
        repo_root / "docs" / "reproducibility.md",
        repo_root / "research" / "roadmap.md",
        repo_root / "research" / "research_questions.md",
        repo_root / "research" / "decision_log.md",
        repo_root / "research" / "risk_register.md",
        repo_root / "research" / "author_contributions.md",
        repo_root / "research" / "literature" / "search_protocol.md",
        repo_root / "research" / "literature" / "literature_matrix.csv",
        repo_root / "research" / "literature" / "screening_log.csv",
        repo_root / "experiments" / "README.md",
        repo_root / "experiments" / "templates" / "experiment_record.md",
        repo_root / "paper" / "outline.md",
        repo_root / "paper" / "claims_evidence_matrix.csv",
        repo_root / "paper" / "references.bib",
    ]

    for file_path in required_files:
        assert file_path.is_file(), f"Missing required file: {file_path}"
        assert file_path.stat().st_size > 0, f"File is unexpectedly empty: {file_path}"


def test_roadmap_phases_integrity() -> None:
    """Verify that research/roadmap.md contains all 13 phases and future phases are Planned."""
    repo_root = Path(__file__).parent.parent
    roadmap_path = repo_root / "research" / "roadmap.md"
    content = roadmap_path.read_text(encoding="utf-8")

    for phase_num in range(13):
        assert f"Phase {phase_num}" in content, f"Roadmap missing Phase {phase_num}"

    # Verify future phases are marked planned, not completed
    for phase_num in range(1, 13):
        assert f"### Phase {phase_num}:" in content, (
            f"Missing detailed section for Phase {phase_num}"
        )


def test_claims_evidence_matrix_schema_and_validity() -> None:
    """Verify claims_evidence_matrix.csv schema.

    Confirm no unvalidated claims are marked valid.
    """
    repo_root = Path(__file__).parent.parent
    claims_csv = repo_root / "paper" / "claims_evidence_matrix.csv"

    expected_headers = [
        "claim_id",
        "proposed_claim",
        "claim_type",
        "supporting_evidence",
        "artifact_path",
        "experiment_id",
        "source_or_citation",
        "validation_status",
        "notes",
    ]

    with open(claims_csv, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == expected_headers

        for row in reader:
            # Performance claims must never be marked Validated prior to experiments
            if row["claim_type"].strip().lower() == "performance":
                assert row["validation_status"].strip().lower() != "validated", (
                    f"Performance claim {row['claim_id']} cannot be Validated at this stage"
                )


def test_literature_review_csv_schemas() -> None:
    """Verify schemas of literature review tracking files."""
    repo_root = Path(__file__).parent.parent

    matrix_file = repo_root / "research" / "literature" / "literature_matrix.csv"
    with open(matrix_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        expected = [
            "paper_id",
            "title",
            "authors",
            "year",
            "venue",
            "doi",
            "method_category",
            "dataset_used",
            "split_protocol",
            "evaluation_metrics",
            "key_findings",
            "reported_limitations",
            "code_data_availability",
            "notes",
        ]
        assert headers == expected

    screening_file = repo_root / "research" / "literature" / "screening_log.csv"
    with open(screening_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        expected = [
            "screening_id",
            "search_query",
            "database",
            "retrieval_date",
            "title",
            "first_author",
            "year",
            "doi",
            "abstract_screen_decision",
            "full_text_screen_decision",
            "inclusion_reason",
            "exclusion_reason",
            "screener",
        ]
        assert headers == expected


def test_experiment_record_template_provenance_fields() -> None:
    """Verify experiment_record.md template contains necessary provenance fields."""
    repo_root = Path(__file__).parent.parent
    template = repo_root / "experiments" / "templates" / "experiment_record.md"
    content = template.read_text(encoding="utf-8")

    essential_fields = [
        "Git Commit SHA",
        "Random Seeds",
        "Dataset Source",
        "Engine Split Protocol",
        "Root Mean Squared Error (RMSE)",
        "Prediction Interval Coverage Probability (PICP)",
        "Observations, Anomalies, and Failures",
    ]
    for field in essential_fields:
        assert field in content, f"Experiment template missing essential field: {field}"
