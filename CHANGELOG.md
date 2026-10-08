# Changelog

All notable changes to the IntelliTwin research project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete Step 5 Data & Evaluation Protocol specifications in `research/research_design/data_evaluation_protocol.md` (17-feature schema, zero-variance ddof=0 scaling rule, 30-cycle windowing, retrospective lifecycle stages, engine-weighted worst-group coverage metrics, and 5-seed model run protocol).
- Engine split manifests `data/splits/fd001_engine_split_seed_2026.json` (50/20/10/20) and `data/splits/fd004_engine_split_seed_2026.json` (124/50/25/50) generated deterministically via `scripts/generate_engine_splits.py`. Preserved `fd002_engine_split_seed_2026.json` byte-for-byte.
- Split generator unit tests in `tests/test_split_generator.py`.
- Sequential maintenance simulator core in `src/intellitwin/simulator/` (`types.py`, `costs.py`, `engine.py`) and 14 deterministic validation unit tests in `tests/test_maintenance_simulator.py`.
- Step 6 numerical decision pilot script `scripts/run_step06_simulator_validation.py` and regenerated validation pilot summary `research/research_design/step06_validation_pilot_summary.json`.
- Architectural decision record ADR-016 in `research/decision_log.md` reconciling Step 5 protocol and correcting Step 6 governance status.

### Changed
- Reconciled Step 6 governance status across `maintenance_cost_scenarios.yaml`, `step06_numerical_freeze_decision.md`, `step06_freeze_checklist.md`, `maintenance_simulator.md`, `roadmap.md`, and `README.md` (marking simulator implementation complete while keeping numerical cost approval pending researcher decision).

- Literature source verification register (`research/literature/source_verification.csv`) tracking metadata verification, methodology status, reproduction status, and verification basis for 26 bibliographic references.
- Literature evidence corrections log (`research/literature/evidence_corrections.md`) recording exact previous assertions, replacements, supplied sources, and remaining uncertainties.
- Reinstated `yan2026audit` software artifact (Zenodo v1 deposit) and added comparators `robinson2026riskaware` (IJPHM 2026) and `benabdennour2026grouped` (Machines 2026) across bibliography and literature matrices.
- Phase 2 detailed research gap and hypotheses framework documents (`research/research_design/research_gap.md`, `research/hypotheses/hypothesis_framework.yaml`) detailing theoretical framework, metrics, target leakage constraints, unit of independence, and falsification criteria.
- Architectural decision record ADR-002 in `research/decision_log.md` formalizing the adoption of conditional RUL reliability and downstream decision consequences as the primary research direction.
- Phase 1 local paper inventory (`research/literature/paper_inventory.csv`) auditing all 15 local PDF papers with verified DOIs and venue classifications.
- Expanded literature comparison matrix (`research/literature/literature_matrix.csv`) benchmarking 23 peer-reviewed studies across 42 methodological fields.
- PRISMA literature screening log (`research/literature/screening_log.csv`) auditing 25 records with provenance tracking across seed corpus, targeted API queries, and citation tracing.
- Closest-work comparison matrix (`research/literature/closest_work_matrix.csv`) stress-testing candidate research positioning against 8 direct competitors.
- Literature citation map (`research/literature/citation_map.csv`) linking core claims to verified sources.
- Comprehensive thematic literature synthesis (`research/literature/literature_synthesis.md`) covering 11 research themes, defeated novelty claims, and candidate research gap.
- Expanded master bibliography (`paper/references.bib`) with 23 verified scholarly references with verified DOIs and correct BibTeX types.
- Updated literature search protocol (`research/literature/search_protocol.md`) documenting executed queries, APIs, and institutional database boundaries.

### Changed
- Updated `research/research_questions.md` locking Research Gap v1, RQ1 v1, and pre-specified hypotheses $H_{0,1}$ and $H_{1,1}$, while marking RQ2–RQ4 as TBD / Not Yet Formulated.
- Updated `paper/claims_evidence_matrix.csv` adding methodology claims for Research Gap v1 and Phase 1 literature grounding.
- Updated `README.md` and `research/roadmap.md` setting Phase 2 status to In Progress.
- Replaced basic literature matrix and screening log templates with fully populated, validated schemas.

