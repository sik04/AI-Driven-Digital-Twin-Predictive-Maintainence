# IntelliTwin Research Roadmap

This document outlines the master research and development roadmap for the IntelliTwin project, conducted jointly by Mayank Singh, Shiksha Pandey, and Ruchi Gupta. Every phase defines clear objectives, deliverables, acceptance criteria, dependencies, and research observations to log.

---

## Roadmap Overview

| Phase | Title | Status | Primary Focus |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Research Project Setup and Governance | Completed | Repository reset, governance framework, tooling, CI |
| **Phase 1** | Systematic Literature Review | In Progress | Comprehensive review of RUL, UQ, and Digital Twin literature |
| **Phase 2** | Research Gap, Questions, Hypotheses & Contributions | Completed | Formalize gaps, testable hypotheses, contribution matrix |
| **Phase 3** | Dataset Study and Experimental Protocol | In Progress — Step 5 complete; Step 6 Maintenance Simulator active | C-MAPSS dataset exploration, split protocol, metrics |
| **Phase 4** | Research Proposal and Paper Foundations | Planned | Initial manuscript draft, methodology formulation |
| **Phase 5** | Reproducible Baseline Experiments | Planned | Standard linear, tree, and baseline deep learning models |
| **Phase 6** | Proposed Model Development | Planned | Novel prognostic architecture formulation and training |
| **Phase 7** | Uncertainty and Maintenance Decision Experiments | Planned | Conformal prediction, interval calibration, DSS validation |
| **Phase 8** | Ablation, Robustness, and Statistical Analysis | Planned | Component ablations, noise stress-testing, significance tests |
| **Phase 9** | Digital Twin Software Implementation | Planned | State synchronization, telemetry streaming, user interface |
| **Phase 10** | Final Validation and Reproducibility Release | Planned | End-to-end audit, artifact release, environment pinning |
| **Phase 11** | Complete Research Paper and Thesis | Planned | Final manuscript synthesis, camera-ready preparation |
| **Phase 12** | Defense, Release, and Research Portfolio | Planned | Public dissemination, oral defense, portfolio release |

---

## Detailed Phase Specifications

### Phase 0: Research Project Setup and Governance
- **Status**: Completed (Step 1 verified and merged)
- **Objective**: Establish a clean, reproducible, research-first repository foundation with automated testing, CI, and governance documentation.
- **Expected Deliverables**:
  - `pyproject.toml` with modern packaging, formatting (`ruff`), typing (`mypy`), and testing (`pytest`).
  - Governance protocols: `roadmap.md`, `research_questions.md`, `decision_log.md`, `risk_register.md`, `author_contributions.md`.
  - Literature review templates: `search_protocol.md`, `literature_matrix.csv`, `screening_log.csv`.
  - Experiment logging templates: `experiment_record.md`.
  - Paper outline and claims-evidence matrix: `outline.md`, `claims_evidence_matrix.csv`, `references.bib`.
  - GitHub Actions CI workflow verifying lint, types, and tests.
- **Acceptance Criteria**:
  - All automated checks pass cleanly.
  - Branch workflow strictly followed; PR merged without blocking issues.
  - Clean environment installation verified.
- **Dependencies**: None.
- **Research Observations to Record**: Repository baseline state, backup integrity, toolchain compatibility.

---

### Phase 1: Systematic Literature Review
- **Status**: In Progress (Step 2 active)
- **Objective**: Conduct a thorough, evidence-based literature review of deep learning for RUL estimation, uncertainty quantification, and predictive maintenance digital twins.
- **Expected Deliverables**:
  - Fully populated `screening_log.csv` (25 records audited across seed corpus, searches, and citation tracing).
  - Complete `paper_inventory.csv` auditing all 15 local repository PDFs.
  - Expanded `literature_matrix.csv` benchmarking 23 peer-reviewed studies.
  - Stress-testing competitor matrix in `closest_work_matrix.csv`.
  - Claim-to-source mapping in `citation_map.csv`.
  - Thematic narrative literature synthesis in `literature_synthesis.md`.
  - Curated and validated BibTeX entries in `paper/references.bib` (23 verified entries).
- **Acceptance Criteria**:
  - All cited papers verified via genuine scholarly DOIs and venues.
  - Inclusion/exclusion criteria rigorously applied and documented.
  - Zero fabricated citations, hallucinated findings, or unsubstantiated novelty claims.
  - Phase 1 remains marked **In Progress** as ongoing literature surveillance continues, acknowledging institutional bulk-database access limitations.
- **Dependencies**: Phase 0.
- **Research Observations to Record**: Methodological patterns, prevailing benchmark splits, common evaluation pitfalls in literature, and confirmation that Digital Twins, RUL point estimation, and conformal prediction alone are well-established.

---

### Phase 2: Research Gap, Questions, Hypotheses, and Contributions
- **Status**: Completed (PR #5 merged and verified on main)
- **Objective**: Synthesize literature review findings into precise research gaps, refine provisional research questions into testable hypotheses, state expected scientific contributions, and establish hypothesis governance rules.
- **Expected Deliverables**:
  - Finalized central research problem / gap statement in `research/research_design/research_gap.md`.
  - Finalized RQ1–RQ4 and pre-specified hypotheses ($H_{0,1}$–$H_{1,4}$) in `research/research_questions.md` and authoritative `research/hypotheses/hypothesis_framework.yaml` / `hypothesis_framework.tex`.
  - Targeted contribution and novelty statement document in `research/research_design/contribution_statement.md` detailing targeted novelty, closest-work boundary, and explicitly rejected novelty claims.
  - Final Experiment A–D mapping across RQ1–RQ4 in `research/research_design/experiment_map.md`.
  - Success-criteria governance rule discarding arbitrary fixed thresholds (5%, 10%, 15%, 75%) until independently justified, requiring pre-specified metric, comparator, effect threshold, and statistical uncertainty rules before confirmatory testing.
  - Documented decisions in `research/decision_log.md` (ADR-006, ADR-007, ADR-008).
  - Updated claims-evidence matrix (`paper/claims_evidence_matrix.csv`).
- **Acceptance Criteria**:
  - Every research question maps to specific, measurable experiments (Experiment A → RQ1, Experiment B → RQ2, Experiment C → RQ3, Experiment D → RQ4) and target leakage constraints.
  - Gaps reflect genuine scholarly deficiencies identified in Phase 1 without unsupportable novelty claims.
  - Obsolete fixed numerical thresholds are removed from active research documentation; exact justified thresholds and statistical decision rules will be finalized before confirmatory testing.
- **Dependencies**: Phase 1.
- **Research Observations to Record**: Justifications for chosen hypotheses, pre-specified metrics, unit-of-independence constraints, and success-criteria governance rules. Step 3 research-protocol specifications have now locked: primary metrics, supporting metrics, primary comparators, statistical unit (`engine`), uncertainty framework (95% engine-level paired/cluster-bootstrap CIs, non-independent time steps, secondary p-values), Supported / Unsupported / Inconclusive decision rules, evaluation terminology, primary vs secondary outcome hierarchy, no-post-hoc-change rule, and final pre-specified RQ evaluation map. Exact numerical practical-effect thresholds remain intentionally deferred until maintenance-simulator validation and possible bounded pilot assessment.


---

### Phase 3: Dataset Study and Experimental Protocol
- **Status**: In Progress — Step 5 complete; Step 6 Maintenance Simulator active (Step 6 contract locked)
- **Objective**: Conduct exploratory analysis of benchmark degradation datasets (e.g., NASA C-MAPSS FD001–FD004), verify sensor characteristics, and establish leak-free evaluation splits.
- **Expected Deliverables**:
  - Dataset qualification specification in `research/research_design/dataset_qualification.md`.
  - Data & Evaluation Protocol specification in `research/research_design/data_evaluation_protocol.md`.
  - Sequential Maintenance Simulator specification in `research/research_design/maintenance_simulator.md`.
  - Machine-readable reproducible engine split manifest in `data/splits/fd002_engine_split_seed_2026.json`.
  - Canonical dataset organization in `data/raw/cmapss/`.
  - Strict engine-level data splitting protocol document.
  - Canonical feature preconditioning and sequence windowing pipeline.
  - Document the deferred-threshold dependency and the protocol requirements that the later maintenance-simulator stage (Step 6) must satisfy before thresholds can be frozen.
- **Acceptance Criteria**:
  - Strict train/calibration/validation/test engine isolation verified with automated assertions (130 / 52 / 26 / 52 engines).
  - Preprocessing scalers fit only on training sets.
  - Primary metrics, comparators, and statistical governance remain locked. Exact numerical practical-effect thresholds remain deferred to the later maintenance-simulator validation stage (Step 6) and must be frozen before confirmatory testing.
- **Dependencies**: Phase 2.
- **Research Observations to Record**: Sensor degradation trends, operating condition shifts, censoring points, and pre-test frozen effect thresholds. Step 4 dataset qualification established: FD002 primary (PASS), FD001 control, FD004 robustness, FD003 optional extension; strict input leakage rules; seed 2026 stratified engine-level split manifest. Step 5 Data & Evaluation Protocol COMPLETE. Step 6 Sequential Maintenance Simulator IN PROGRESS (Current locked Step 6 work: chronological replay contract, action space, information boundary, cost-function structure, per-engine outcome contract).

---

### Phase 4: Research Proposal and Paper Foundations
- **Status**: Planned
- **Objective**: Draft the research proposal, problem formulation, mathematical notations, and paper introductory sections.
- **Expected Deliverables**:
  - Formulated problem definition in `paper/outline.md` / LaTeX draft.
  - Background, notation, and system model mathematical formalisms.
- **Acceptance Criteria**:
  - Notation is consistent and mathematically rigorous.
  - Methodology directly addresses formalized research questions.
- **Dependencies**: Phase 3.
- **Research Observations to Record**: Mathematical formulation edge cases and notation trade-offs.

---

### Phase 5: Reproducible Baseline Experiments
- **Status**: Planned
- **Objective**: Implement and evaluate standard baseline models (Linear Regression, SVR, Random Forest, MLP, basic LSTM/GRU) under the identical protocol established in Phase 3.
- **Expected Deliverables**:
  - Baseline model implementations under `src/intellitwin/models/`.
  - Comprehensive experiment records in `experiments/`.
  - Baseline performance benchmark table across RMSE, Score, and compute overhead.
- **Acceptance Criteria**:
  - All baselines evaluated under exact identical engine splits and seed sets.
  - Full provenance logged (commit hash, environment, execution time).
- **Dependencies**: Phase 3, Phase 4.
- **Research Observations to Record**: Baseline convergence properties, degradation tracking limits, baseline failure modes.

---

### Phase 6: Proposed Model Development
- **Status**: Planned
- **Objective**: Design, implement, and train the proposed prognostic architecture targeting identified literature gaps.
- **Expected Deliverables**:
  - Proposed model source code with strict type hints and docstrings.
  - Training scripts with convergence monitoring and checkpointing.
  - Verified experiment records comparing proposed model with baselines.
- **Acceptance Criteria**:
  - Reproducible training pipeline with deterministic seed behavior.
  - Empirically substantiated improvements over baselines under identical test sets.
- **Dependencies**: Phase 5.
- **Research Observations to Record**: Training dynamics, loss landscape behavior, hyperparameter sensitivity.

---

### Phase 7: Uncertainty and Maintenance Decision Experiments
- **Status**: Planned
- **Objective**: Implement uncertainty quantification (e.g., conformal prediction intervals, deep ensembles, or Bayesian approximations) and evaluate uncertainty-aware maintenance decision policies.
- **Expected Deliverables**:
  - UQ implementation under `src/intellitwin/uncertainty/`.
  - Decision support module under `src/intellitwin/decision/`.
  - Coverage (PICP) and interval width (MPIW) empirical validation.
  - Decision policy comparative cost/risk analysis against static thresholds.
- **Acceptance Criteria**:
  - Conformal or Bayesian prediction intervals achieve target nominal coverage.
  - Maintenance policies demonstrate risk-bounded operational advantages.
- **Dependencies**: Phase 6.
- **Research Observations to Record**: Calibration error, width-coverage trade-offs, catastrophic failure penalty reductions.

---

### Phase 8: Ablation, Robustness, and Statistical Analysis
- **Status**: Planned
- **Objective**: Perform component ablations, sensor noise injection, operating condition perturbations, and statistical evaluation (e.g., engine-level confidence intervals and optional secondary paired tests).
- **Expected Deliverables**:
  - Systematic ablation experiment records.
  - Noise robustness stress-testing report.
  - Effect sizes and engine-level confidence intervals, with statistical hypothesis tests and p-values used only as secondary supporting evidence where appropriate.
- **Acceptance Criteria**:
  - Every proposed architectural component empirically justified by ablation.
  - Primary effects are reported with effect sizes and engine-level confidence intervals and interpreted using the pre-specified Supported / Unsupported / Inconclusive decision rules across the planned robustness evaluation.
- **Dependencies**: Phase 7.
- **Research Observations to Record**: Sensitivity to sensor dropout, noise tolerance boundaries.

---

### Phase 9: Digital Twin Software Implementation
- **Status**: Planned
- **Objective**: Implement the digital twin software layer, providing bi-directional asset state simulation, calibrated prognostic displays, and decision alerts.
- **Expected Deliverables**:
  - Digital twin service module under `src/intellitwin/twin/`.
  - Interactive demonstration interface and API endpoints.
  - Real-time simulation and telemetry synchronization tests.
- **Acceptance Criteria**:
  - Visual and state synchronization accurately reflects underlying model outputs.
  - Software operates independently from model training pipelines.
- **Dependencies**: Phase 7, Phase 8.
- **Research Observations to Record**: Real-time inference latency, synchronization fidelity, user interaction feedback.

---

### Phase 10: Final Validation and Reproducibility Release
- **Status**: Planned
- **Objective**: Conduct an independent, end-to-end reproducibility audit of all data pipelines, models, figures, and tables from clean virtual environments.
- **Expected Deliverables**:
  - Single-command reproducibility script or Makefile target.
  - Pinned lockfile / exact environment specification.
  - Full claims-evidence audit verifying all manuscript claims against experiment records.
- **Acceptance Criteria**:
  - Every table and figure in the manuscript regenerates identically from scratch.
  - All items in `paper/claims_evidence_matrix.csv` marked validated.
- **Dependencies**: Phase 9.
- **Research Observations to Record**: Execution runtimes, cross-platform reproducibility validation.

---

### Phase 11: Complete Research Paper and Thesis
- **Status**: Planned
- **Objective**: Complete the comprehensive research manuscript and academic thesis integrating all verified findings, discussions, limitations, and literature comparisons.
- **Expected Deliverables**:
  - Full LaTeX manuscript package with high-resolution figures.
  - Complete thesis document formatted according to institutional guidelines.
  - Submission-ready supplementary material.
- **Acceptance Criteria**:
  - Co-author review and approval by Mayank Singh, Shiksha Pandey, and Ruchi Gupta.
  - Complete alignment between manuscript text, code, and experiment records.
- **Dependencies**: Phase 10.
- **Research Observations to Record**: Reviewer feedback, revision notes, publication decisions.

---

### Phase 12: Defense, Release, and Research Portfolio
- **Status**: Planned
- **Objective**: Conduct oral thesis defense, publish camera-ready artifacts, and release public open-science research portfolio.
- **Expected Deliverables**:
  - Presentation slide deck and demonstration materials.
  - Zenodo / OSF open-science release package with DOI.
  - Public repository tag and release notes.
- **Acceptance Criteria**:
  - Successful academic defense.
  - Permanent open-access archival of models, code, and benchmark protocols.
- **Dependencies**: Phase 11.
- **Research Observations to Record**: Defense questions, external audience reception, future research vectors.
