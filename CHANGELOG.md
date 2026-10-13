# Changelog

All notable changes to the IntelliTwin research project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Completed Step 8 Decision-Aware Conformal Calibration and independent verification audit under ADR-021:
  - Designed and implemented engine-weighted hierarchical conformal calibration modules in `src/intellitwin/uncertainty/` (`scores.py`, `quantiles.py`, `calibration.py`, `metrics.py`, `selection.py`, `artifacts.py`, `schema.py`).
  - Implemented exact engine-weighted empirical and hierarchical quantiles with finite mass $F(q) = \frac{1}{m+1}\sum \frac{\text{count}}{n_i}$, mass $\frac{1}{m+1}$ at $+\infty$, and exact boundary verification via `fractions.Fraction`.
  - Implemented three conformal methods: `global_hcp`, `regime_hcp`, and proposed `decision_aware_hcp` with prespecified 9-candidate parameter grid ($\gamma \in \{0, 1, 2\}$, $\beta_{\text{code}} \in \{-1, 0, 1\}$).
  - Implemented named benchmark maintenance policy `lower_bound_one_cycle_policy` (`src/intellitwin/decision/policies.py`) operating during cycles $30 \le t \le T-1$ under `primary_reference` cost scenario.
  - Implemented strict calibration data pipeline (`src/intellitwin/data/calibration_pipeline.py`) strictly permitting only validation and calibration partitions while raising `ForbiddenPartitionAccessError` on test partitions.
  - Executed validation-only leave-one-engine-out candidate development (`scripts/run_step08_development.py`) across all 6 cells and 5 seeds, selecting `gamma2_betam1` as `feasible_optimal` across all cells with zero fallback required.
  - Created and committed authoritative selection freeze manifest in `experiments/calibration/selection/selection_freeze.json`.
  - Executed final calibration fitting (`scripts/run_step08_final_calibration.py`) on reserved calibration partition across all 30 base predictors, producing 90 calibrator bundles and 270 coverage configurations registered in `experiments/calibration/calibration_registry.json`.
  - Generated consolidated validation diagnostics in `experiments/calibration/validation_summary.csv`.
  - Implemented and executed independent audit suite (`scripts/audit_step08_calibration.py`), verifying artifact integrity, candidate selection reconstruction, threshold numerical reconstruction (max diff $2.84 \times 10^{-14}$), validation metric reconstruction, data isolation, and raw-data checkpoint prediction reproduction (recorded in `experiments/calibration/audit_report.json`).
  - Authored comprehensive Step 8 specification, freeze checklist, and completion reports in `research/research_design/step08_calibration_specification.md`, `step08_freeze_checklist.md`, and `step08_calibration_completion.md`.
  - Appended and accepted ADR-021 in `research/decision_log.md`.
  - Added scholarly citations for Lee et al. (arXiv:2306.06342v4) and Cortes-Gomez et al. (ICLR 2025) in `paper/references.bib`.

### Fixed
- Corrected Step 7 base predictor verification and documentation:
  - Extended `src/intellitwin/models/registry.py` and `scripts/audit_step07_base_models.py` with `--reproduce-predictions` to re-transform raw validation data and verify prediction reproduction across all 30 frozen models (max diff $\le 5.0 \times 10^{-7} \ll 10^{-4}$ cycles; recorded in `experiments/audits/step07_prediction_reproduction.json`).
  - Strengthened `FrozenBaseModel.predict` with strict input geometry and type assertions ($(M, 510)$ or $(M, 30, 17)$, finite floats only, preserving non-negative truncation and C-order flattening).
  - Repaired documentation in `step07_full_base_model_matrix_completion.md` where FD004 GBR capped RMSE was corrected from 22.7538 to verified 16.2977.
  - Replaced crude filename substring scans with partition role verification, permitting legitimate calibration artifacts under `experiments/calibration/`.
  - Constructed authoritative 30-model registry in `experiments/base_models/model_registry.json` tracking model IDs, file paths, SHA-256 hashes, preprocessor hashes, split manifest hashes, and git commit provenance.
  - Implemented immutable base predictor loading interface `load_frozen_base_model` and `FrozenBaseModel` wrapper with automatic runtime SHA-256 integrity verification and non-negative prediction post-processing.
  - Authored and verified independent audit suite (`scripts/audit_step07_base_models.py`) verifying all 30 models match disk artifacts, produce non-negative predictions, reproduce validation predictions, and preserve zero calibration/test data leakage.
  - Executed representative seed-2026 reproducibility audit (`scripts/run_step07_reproducibility_audit.py`) confirming numerical equivalence for GBR ($< 5.0 \times 10^{-7}$ max diff) and exact convergence for LSTM ($\Delta_{\text{RMSE}} = 0.0000 \le 0.05$).
  - Generated consolidated validation benchmark summary in `experiments/base_models/base_predictor_validation_summary.csv`.
  - Authored formal base predictor freeze document in `research/research_design/step07_base_predictor_freeze.md`.
  - Appended ADR-020 to `research/decision_log.md` formalizing the immutable 30-model freeze and downstream boundaries.
  - Created and executed test suite in `tests/test_step07_base_models.py` verifying registry completeness, loader functionality, tamper detection, and summary tables.
- Completed Step 7.4 full multi-dataset and five-seed base-model matrix:
  - Validated and froze winning configurations for FD001 (`gbr_lr010_leaf15_l2_0` and `lstm_h64_lr0010`) and FD004 (`gbr_lr010_leaf31_l2_0` and `lstm_h64_lr0010`) following frozen Step 7.1 grid on validation-only engines.
  - Trained all 30 official base models across 3 datasets (FD001, FD002, FD004), 2 model families (GBR, LSTM), and 5 seeds (2026–2030) using `scripts/run_step07_full_base_model_matrix.py`.
  - Persisted complete checkpoints, metadata, metrics, and validation prediction CSVs with zero data leakage (calibration and test engines strictly untouched).
  - Generated summary records for each dataset-model pair with exact mean and standard deviation metrics.
  - Added unit and regression test coverage in `tests/test_step07_matrix.py` verifying checkpoint reload, metadata validation, and summary schemas.
  - Authored Step 7.4 matrix completion record in `research/research_design/step07_full_base_model_matrix_completion.md`.

### Fixed
- Corrected Step 7.3 FD002 completion provenance in `research/research_design/step07_fd002_model_selection_completion.md`: FD002 has one fault mode, and the frozen engine split is 130 train / 52 calibration / 26 validation / 52 test (260 total engines).
- Added automated model-selection provenance validation (`src/intellitwin/models/provenance.py`) and split partition-count reporting helper (`src/intellitwin/data/splits.py`) to prevent model-selection reports from diverging from frozen split manifests.
- Added deterministic Step 7.3 FD002 provenance audit script (`scripts/audit_step07_fd002_provenance.py`) and regression test suite (`tests/test_step07_provenance.py`).
- Reconciled Phase 3 research observation status in `research/roadmap.md` to reflect Step 7.3 completion and Step 7.4 next up.

### Added
- HistGradientBoostingRegressor model wrapper (`src/intellitwin/models/gbr.py`) supporting 8 frozen hyperparameter configurations under ADR-019 with deterministic non-negative prediction post-processing.
- Single-layer unidirectional LSTM model (`src/intellitwin/models/lstm.py`) with lookback 30, hidden size $H \in \{32, 64\}$, dropout $p=0.20$, linear output, AdamW optimizer, gradient clipping (norm 1.0), and weighted batch MSE loss.
- Equal-engine-weighted model evaluation metrics (`src/intellitwin/models/metrics.py`) implementing uncapped-RUL RMSE ($\sqrt{\frac{1}{N}\sum \text{MSE}_i}$), uncapped MAE, and capped-target RMSE.
- Deterministic model reproducibility module (`src/intellitwin/models/reproducibility.py`) enforcing global seed synchronization across `random`, `numpy`, and PyTorch with CPU deterministic algorithms.
- Deterministic candidate ranking and 3-stage tie-breaking module (`src/intellitwin/models/selection.py`) operating on validation-only selection score.
- Model artifact and prediction persistence utilities (`src/intellitwin/models/artifacts.py`).
- Deterministic FD002 model-selection runner script (`scripts/run_step07_fd002_model_selection.py`) executing the 24-run validation selection grid with fail-fast guards against dirty worktrees and hash mismatches.
- FD002 model selection records and summary artifacts in `experiments/model_selection/FD002/` (16 GBR runs and 8 LSTM runs across seeds 2026 and 2027 with serialized checkpoints and prediction CSVs).
- Frozen winning GBR configuration `gbr_lr010_leaf31_l2_0` (learning rate 0.10, max leaf nodes 31, L2 regularization 0.0; validation uncapped RMSE 34.6613 cycles).
- Frozen winning LSTM configuration `lstm_h64_lr0010` (hidden size 64, learning rate 0.0010; mean validation uncapped RMSE 35.2523 cycles across seeds 2026 and 2027).
- Step 7.3 FD002 model selection completion record in `research/research_design/step07_fd002_model_selection_completion.md`.
- Deterministic C-MAPSS data package `src/intellitwin/data/` implementing strict raw data loading, split validation, training-only preprocessing, K-means k=6 regime modeling with canonical C1..C6 ordering, 30-cycle causal sequence windowing, and equal-engine sample weighting ($w_{i,t} = M / (N \cdot n_i)$).
- Preprocessing artifact persistence and round-trip loading in `src/intellitwin/data/artifacts.py` producing deterministic JSON artifacts in `experiments/preprocessing/{FD001,FD002,FD004}/preprocessor.json`.
- Preprocessing artifact builder script `scripts/build_step07_data_artifacts.py`.
- Comprehensive synthetic test suites in `tests/test_data_loader.py`, `tests/test_data_splits.py`, `tests/test_preprocessing.py`, `tests/test_windowing.py`, `tests/test_data_pipeline.py`, and integration tests in `tests/test_step07_data_integration.py`.
- Step 7.2 completion record in `research/research_design/step07_data_pipeline_completion.md`.
- Separate FD002 lifetime-quartile provenance artifact in `data/splits/fd002_lifetime_quartile_provenance.json` reconstructing quartile stratification from documented original rule without modifying frozen partition assignments.
- Deterministic research utility `scripts/reconstruct_fd002_quartile_provenance.py` and comprehensive test suite in `tests/test_fd002_quartile_provenance.py`.
- Step 7.1 base-predictor specification in `research/research_design/step07_base_predictor_specification.md` locking GBR and LSTM architectures, grids, data roles, and artifact provenance.
- Formal bootstrap replicate missing-group bounds unit test suite in `tests/test_statistical_inference.py`.
- Architectural decision record ADR-019 in `research/decision_log.md` formalizing Step 7.0 protocol reconciliation and Step 7.1 base-predictor specification freeze.
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
- Corrected FD002 fault mode description in `research/research_design/step07_base_predictor_specification.md` from 2 fault modes to 1 fault mode (FD002 has 6 operating regimes, 1 fault mode; HPC fault mode only).
- Removed stale bootstrap "pending" statement in `research/research_design/data_evaluation_protocol.md` and added explicit cross-reference to ADR-018/ADR-019 and statistical inference protocol $[0.0, 0.90]$ conservative bounds.
- Updated `README.md`, `research/roadmap.md`, and `step07_base_predictor_specification.md` to reflect Step 7.2 completion and Step 7.3 next up.
- Enforced strict data partition roles across `statistical_inference_protocol.md`, `research_questions.md`, `experiment_map.md`, `hypothesis_framework.yaml`, and `hypothesis_framework.tex`: training data for preprocessing/models, validation data for hyperparameter/matched-control tuning, calibration data reserved for conformal calibration, and test data untouched until confirmatory evaluation.
- Fixed bootstrap replicate missing-group bound calculation in `statistical_inference_protocol.md` to eliminate undefined $\max(\emptyset)$ and establish conservative $[0.0, 0.90]$ bounds when all eligible groups are absent.
- Reconciled `research/roadmap.md` and `README.md` to reflect GBR and LSTM base-predictor scope and remove obsolete "novel prognostic architecture" and broad baseline suite language.
- Updated `research/research_design/step06_freeze_checklist.md` to mark Step 6 completion PR #16 merged to main.
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

