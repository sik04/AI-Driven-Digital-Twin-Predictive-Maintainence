# Changelog

All notable changes to the IntelliTwin research project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Frozen Step 6 statistical inference protocol in `research/research_design/statistical_inference_protocol.md` (10,000 engine-cluster bootstrap with PCG64 `SeedSequence([2026, 6, dataset_number])`, 98.75% decision intervals with $\alpha=0.0125$ Bonferroni allocation across RQs, intersection-union testing, conservative missing-group bounds propagation $[0, 0.90]$, and cost-inefficient early PM diagnostic $W > r_{\text{equal}}$).
- Methodological references `lakens2017equivalence` (equivalence/noninferiority testing) and `gneiting2007strictly` (strictly proper scoring rules and Winkler interval scores) in `paper/references.bib`.
- Risk register entries RSK-11 through RSK-15 in `research/risk_register.md` (synthetic costs, small subgroup precision, approximate bootstrap inference, fixed-seed conditional inference, and absence of deployment/stopping-time guarantees).
- Architectural decision record ADR-018 in `research/decision_log.md` formalizing Step 6 synthetic cost and numerical evaluation freeze.
- Authoritative Step 5 protocol completion in `research/research_design/data_evaluation_protocol.md` (primary 90% nominal coverage, uncapped `rul_true` interval evaluation, engine-weighted metric equations with non-averaged RMSE, central Winkler interval score, fixed metadata subgroup governance, and K-means centroid reproducibility).
- Completed `engine_ids` metadata in `quartile_membership` for `data/splits/fd001_engine_split_seed_2026.json` and `data/splits/fd004_engine_split_seed_2026.json` derived from validated source data sorted by (lifetime, engine_id).
- Strengthened input validation in `scripts/generate_engine_splits.py` (pre-conversion integral scalar checks, consecutive ID constraints, testable `write_or_verify_manifest` helper).
- Comprehensive synthetic test suite and isolated integration tests in `tests/test_split_generator.py` and `tests/test_simulator_validation_pilot.py`.
- Strict integral scalar input validation and pre-policy checks in `src/intellitwin/simulator/engine.py` and 4 new regression tests in `tests/test_maintenance_simulator.py`.
- Verifiable provenance framework for validation pilot in `scripts/run_step06_simulator_validation.py` using `sha256-utf8-lf-v1` normalized source-code hashing.
- Architectural decision record ADR-017 in `research/decision_log.md` formalizing protocol reconciliation, validation hardening, and pilot provenance.

### Changed
- Frozen 3 synthetic maintenance cost scenarios in `research/research_design/maintenance_cost_scenarios.yaml` under v2.0 and ADR-018 (`primary_reference` [1.0, 5.0, 0.20], `failure_sensitive` [1.0, 10.0, 0.20], `waste_sensitive` [1.0, 5.0, 0.40] SCU); removed active `primary_balanced` ID.
- Locked canonical evaluation contract `step06-v2` in `research/hypotheses/hypothesis_framework.yaml` and `hypothesis_framework.tex` with numerical decision thresholds (0.20 SCU/engine cost margin, 0.01 worst-group error margin, 0.05 absolute coverage error ceiling, 1.0 cycle MPIW and Winkler interval score noninferiority margins, 0.0 observed failure rate increase allowed).
- Corrected cost formulation, break-even equality horizons ($r_{\text{equal}} \in \{20, 45, 10\}$ cycles), and theoretical oracle costs (1.20, 1.20, 1.40 SCU) in `maintenance_simulator.md` and `step06_numerical_freeze_decision.md`, clarifying that deterministic pilot fixture demonstrates trigger execution, not cost-optimal intervention.
- Corrected "30-cycle lookahead" to "30-cycle causal lookback" in `docs/reproducibility.md`.
- Synchronized experiment specifications, checklists, roadmap, and experiment record templates across `research/` and `experiments/templates/`.
- Reconciled Step 6 governance and status across `step06_freeze_checklist.md`, `step06_numerical_freeze_decision.md`, `roadmap.md`, `README.md`, `docs/reproducibility.md`, and `experiments/templates/experiment_record.md` (clarifying that numerical maintenance approval is required before confirmatory maintenance testing, not ordinary Step 7 base-predictor training).

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

