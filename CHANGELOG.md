# Changelog

All notable changes to the IntelliTwin research project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Research roadmap (`research/roadmap.md`) covering phases 0 through 12.
- Provisional research questions (`research/research_questions.md`) targeting RUL prediction and uncertainty quantification.
- Research governance templates: `research/decision_log.md`, `research/risk_register.md`, and `research/author_contributions.md`.
- Literature review governance: `research/literature/search_protocol.md`, `literature_matrix.csv`, and `screening_log.csv`.
- Experiment tracking framework: `experiments/templates/experiment_record.md` and `experiments/README.md`.
- Paper and thesis planning documents: `paper/outline.md`, `claims_evidence_matrix.csv`, and `references.bib`.
- Minimal modern Python package layout under `src/intellitwin/` with PEP 517/621 `pyproject.toml`.
- Continuous Integration workflow (`.github/workflows/ci.yml`) testing Python 3.10 through 3.13.
- Development tooling configuration: Ruff (lint/format), Mypy (type check), Pytest (testing), EditorConfig, and Makefile.
- Base documentation: project scope, development setup, architecture overview, and reproducibility charter.

### Changed
- Rebuilt repository foundation from a clean state into a research-first structure.
- Preserved historical codebase backup in `../intellitwin_pre_reset_backup_9b72fac.zip`.
