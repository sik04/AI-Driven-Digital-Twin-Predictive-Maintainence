# Changelog

All notable changes to the IntelliTwin research project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Authoritative machine-readable hypothesis framework registry (`research/hypotheses/hypothesis_framework.yaml`) locking RQ1–RQ4 v1, $H_0$/$H_1$ definitions, pre-specified practical effect-size thresholds, primary metrics, decision rules, and falsification rules.
- Restructured research design folder (`research/research_design/`) containing `research_gap.md`, `experiment_map.md`, and `experiment_a_design.md`.
- Architectural decision records ADR-002, ADR-003, and ADR-004 in `research/decision_log.md` formalizing conditional RUL reliability research direction, Experiment A protocol, and machine-readable hypothesis specification.
- Phase 1 local paper inventory (`research/literature/paper_inventory.csv`) auditing all 15 local PDF papers with verified DOIs and venue classifications.
- Expanded literature comparison matrix (`research/literature/literature_matrix.csv`) benchmarking 23 peer-reviewed studies across 42 methodological fields.
- PRISMA literature screening log (`research/literature/screening_log.csv`) auditing 25 records with provenance tracking across seed corpus, targeted API queries, and citation tracing.
- Closest-work comparison matrix (`research/literature/closest_work_matrix.csv`) stress-testing candidate research positioning against 8 direct competitors.
- Literature citation map (`research/literature/citation_map.csv`) linking core claims to verified sources.
- Comprehensive thematic literature synthesis (`research/literature/literature_synthesis.md`) covering 11 research themes, defeated novelty claims, and candidate research gap.
- Expanded master bibliography (`paper/references.bib`) with 23 verified scholarly references with verified DOIs and correct BibTeX types.
- Updated literature search protocol (`research/literature/search_protocol.md`) documenting executed queries, APIs, and institutional database boundaries.

### Changed
- Restructured research directory by removing roadmap-indexed `research/phase-2/` and separating narrative research design (`research/research_design/`) from formal machine-readable hypotheses (`research/hypotheses/hypothesis_framework.yaml`).
- Updated `research/research_questions.md` referencing `research_gap.md` and `hypothesis_framework.yaml` without duplicating full YAML text.
- Updated `paper/claims_evidence_matrix.csv` adding methodology claims for Research Gap v1 and Phase 1 literature grounding.
- Updated `README.md` and `research/roadmap.md` reflecting restructured research design deliverables.
- Replaced basic literature matrix and screening log templates with fully populated, validated schemas.


