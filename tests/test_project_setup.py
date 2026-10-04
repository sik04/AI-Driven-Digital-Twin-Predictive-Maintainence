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
        repo_root / "research" / "literature" / "paper_inventory.csv",
        repo_root / "research" / "literature" / "search_protocol.md",
        repo_root / "research" / "literature" / "literature_matrix.csv",
        repo_root / "research" / "literature" / "screening_log.csv",
        repo_root / "research" / "literature" / "closest_work_matrix.csv",
        repo_root / "research" / "literature" / "citation_map.csv",
        repo_root / "research" / "literature" / "source_verification.csv",
        repo_root / "research" / "literature" / "evidence_corrections.md",
        repo_root / "research" / "literature" / "literature_synthesis.md",
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
            if row["claim_type"].strip().lower() == "performance":
                assert row["validation_status"].strip().lower() != "validated", (
                    f"Performance claim {row['claim_id']} cannot be Validated at this stage"
                )


def test_literature_review_csv_schemas() -> None:
    """Verify schemas of all literature review tracking files."""
    repo_root = Path(__file__).parent.parent

    matrix_file = repo_root / "research" / "literature" / "literature_matrix.csv"
    with open(matrix_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert len(headers) == 42, (
            f"Expected 42 headers in literature_matrix.csv, got {len(headers)}"
        )
        assert headers[0] == "paper_id"
        assert headers[1] == "bibtex_key"
        assert headers[-1] == "closest_work_flag"

    screening_file = repo_root / "research" / "literature" / "screening_log.csv"
    with open(screening_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert len(headers) == 14, f"Expected 14 headers in screening_log.csv, got {len(headers)}"
        assert headers[0] == "screening_id"
        assert headers[-1] == "screener"

    inventory_file = repo_root / "research" / "literature" / "paper_inventory.csv"
    with open(inventory_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert len(headers) == 12, f"Expected 12 headers in paper_inventory.csv, got {len(headers)}"
        assert headers[0] == "filename"
        assert headers[-1] == "notes"

    closest_file = repo_root / "research" / "literature" / "closest_work_matrix.csv"
    with open(closest_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert len(headers) == 21, (
            f"Expected 21 headers in closest_work_matrix.csv, got {len(headers)}"
        )

    citation_file = repo_root / "research" / "literature" / "citation_map.csv"
    with open(citation_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert len(headers) == 9, f"Expected 9 headers in citation_map.csv, got {len(headers)}"

    source_ver_file = repo_root / "research" / "literature" / "source_verification.csv"
    with open(source_ver_file, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        expected_source_ver = [
            "bibtex_key",
            "source_url",
            "source_locator",
            "metadata_status",
            "methodology_status",
            "reproduction_status",
            "verification_basis",
            "unresolved_items",
        ]
        assert headers == expected_source_ver, (
            f"Expected headers {expected_source_ver} in source_verification.csv, got {headers}"
        )


def test_paper_inventory_exactness() -> None:
    """Verify paper_inventory.csv exists, has 15 records, and satisfies schema rules."""
    repo_root = Path(__file__).parent.parent
    inventory_file = repo_root / "research" / "literature" / "paper_inventory.csv"

    assert inventory_file.exists(), f"Missing paper_inventory.csv at {inventory_file}"

    with open(inventory_file, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 15, f"Expected 15 inventoried seed paper records, got {len(rows)}"

    required_fields = {
        "filename",
        "title",
        "authors",
        "year",
        "publication_type",
        "venue",
        "doi",
        "doi_verification_status",
        "peer_review_status",
        "primary_research_topic",
        "relevance_to_intellitwin",
    }
    assert reader.fieldnames is not None
    missing = required_fields - set(reader.fieldnames)
    assert required_fields.issubset(set(reader.fieldnames)), (
        f"Missing required fields in paper_inventory.csv: {missing}"
    )

    titles = [r["title"].strip() for r in rows if r["title"].strip()]
    filenames = [r["filename"].strip() for r in rows if r["filename"].strip()]
    assert len(titles) == 15, "Each inventory row must contain a non-empty title"
    assert len(filenames) == 15, "Each inventory row must contain a non-empty filename identifier"
    assert len(set(titles)) == 15, "Duplicate paper titles found in paper_inventory.csv"
    assert len(set(filenames)) == 15, "Duplicate filenames found in paper_inventory.csv"


def test_literature_matrices_record_counts() -> None:
    """Verify required fields, unique IDs, and valid status values in tracking files."""
    repo_root = Path(__file__).parent.parent

    matrix_file = repo_root / "research" / "literature" / "literature_matrix.csv"
    with open(matrix_file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) >= 20, (
            f"Expected at least 20 rows in literature_matrix.csv, got {len(rows)}"
        )
        paper_ids = [r["paper_id"] for r in rows]
        assert len(paper_ids) == len(set(paper_ids)), (
            "Duplicate paper_id found in literature_matrix.csv"
        )

    closest_file = repo_root / "research" / "literature" / "closest_work_matrix.csv"
    with open(closest_file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) >= 10, (
            f"Expected at least 10 rows in closest_work_matrix.csv, got {len(rows)}"
        )
        keys = [r["citation_key"] for r in rows]
        assert len(keys) == len(set(keys)), (
            "Duplicate citation_key found in closest_work_matrix.csv"
        )

    screening_file = repo_root / "research" / "literature" / "screening_log.csv"
    with open(screening_file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) >= 25, f"Expected at least 25 rows in screening_log.csv, got {len(rows)}"
        screening_ids = [r["screening_id"] for r in rows]
        assert len(screening_ids) == len(set(screening_ids)), (
            "Duplicate screening_id in screening_log.csv"
        )

    citation_file = repo_root / "research" / "literature" / "citation_map.csv"
    with open(citation_file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) >= 9, f"Expected at least 9 rows in citation_map.csv, got {len(rows)}"
        claim_ids = [r["claim_id"] for r in rows]
        assert len(claim_ids) == len(set(claim_ids)), "Duplicate claim_id in citation_map.csv"

    source_ver_file = repo_root / "research" / "literature" / "source_verification.csv"
    with open(source_ver_file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) >= 20, (
            f"Expected at least 20 rows in source_verification.csv, got {len(rows)}"
        )
        bib_keys = [r["bibtex_key"] for r in rows]
        assert len(bib_keys) == len(set(bib_keys)), (
            "Duplicate bibtex_key in source_verification.csv"
        )
        valid_meta_statuses = {"verified", "pending"}
        valid_method_statuses = {
            "full_text_checked",
            "abstract_checked",
            "indexed_primary_text_checked",
            "artifact_code_checked",
            "not_verified",
        }
        for r in rows:
            assert r["metadata_status"] in valid_meta_statuses, (
                f"Invalid metadata_status: {r['metadata_status']}"
            )
            assert r["methodology_status"] in valid_method_statuses, (
                f"Invalid methodology_status: {r['methodology_status']}"
            )
            assert r["reproduction_status"] == "not_reproduced"


def test_references_bib_integrity() -> None:
    """Verify paper/references.bib contains valid BibTeX entries."""
    repo_root = Path(__file__).parent.parent
    bib_file = repo_root / "paper" / "references.bib"
    content = bib_file.read_text(encoding="utf-8")

    expected_keys = [
        "saxena2008damage",
        "diana2025ai",
        "huang2021survey",
        "mazzetto2024review",
        "wei2024digital",
        "bello2024ai",
        "hosseinzadeh2023predictive",
        "shehadeh2024evaluating",
        "mousavi2024evolution",
        "brighenti2024forecasting",
        "hisamuddin2026ai",
        "mahmud2025ai",
        "hasan2025new",
        "pathri2025smart",
        "wu2026research",
        "belay2026digital",
        "chen2022data",
        "zhu2025predictive",
        "diao2026turbofan",
        "walia2026uncertainty",
        "xu2026novel",
        "yang2026empirical",
        "javanmardi2023conformal",
        "yan2026audit",
        "robinson2026riskaware",
        "benabdennour2026grouped",
    ]
    for key in expected_keys:
        assert f"{{{key}," in content, f"Missing BibTeX key: {key}"


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
