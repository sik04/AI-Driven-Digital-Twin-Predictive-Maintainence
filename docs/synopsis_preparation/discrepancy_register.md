# Discrepancy Register and Documentation Risk Assessment

**Pinned Source Commit**: `224c741f5f3da19821a708e0a6da417d4810e9da`  
**Governing Principle**: Identify contradictions between legacy documents, protocol specifications, implementation code, and audit records. Do not alter underlying historical files outside `docs/synopsis_preparation/`. Instead, record discrepancies and enforce strictly conservative wording in all new documentation deliverables.

---

## 1. Summary of Identified Discrepancies

| ID | Topic | Primary Conflicted Source | Opposing Evidence / Implementation | Severity / Risk | Resolution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DISC-01** | Outdated Phase-0 Scope | `docs/project_scope.md`, `docs/architecture_overview.md` | `README.md`, `research/decision_log.md` (ADR-001, ADR-002) | Moderate | Documented; scoped in new drafts |
| **DISC-02** | Legacy Paper Outline Baselines | `paper/outline.md` (Section 7) | `research/research_design/step07_base_predictor_specification.md` (ADR-019, ADR-020) | High | Resolved in new drafts; frozen baselines restricted to GBR & LSTM |
| **DISC-03** | Epistemic/Aleatoric Decomposition | `paper/outline.md`, early notes | `src/intellitwin/uncertainty/conformal.py`, ADR-021 | High | Prohibited claim; drafts evaluate total predictive nonconformity |
| **DISC-04** | Physical Asset / Bidirectional Twin | `docs/project_scope.md`, early drafts | Codebase inspection (`src/intellitwin/`) | Critical | Prohibited claim; drafts describe simulation replay on C-MAPSS |
| **DISC-05** | Inherited Literature Status Labels | `research/literature/source_verification.csv` | Independent source checking of unindexed DOIs/theses | Moderate | Documented; unverified sources flagged in `reference_audit.csv` |
| **DISC-06** | Blanket "Verified Bibliography" Claim | `paper/references.bib` header | Several entries lack formal peer review or assigned DOIs | Moderate | Replaced with verified subset in `references_verified.bib` |
| **DISC-07** | Unqualified Conditional Coverage | Early methodology notes | `statistical_inference_protocol.md` (Section 8) | High | Drafts explicitly state conformal guarantees are marginal exchangeable |
| **DISC-08** | Completion Report Overstating Audit | `research/research_design/step09_pretest_completion.md` | `experiments/audits/step08_repair_verification.json` | High | Tracked under UPD-01; drafts report checkpoint reproduction as NOT RUN |
| **DISC-09** | Pooled-Cycle vs. Engine-Weighted Metrics | Early protocol drafts | `research/research_design/data_evaluation_protocol.md` (ADR-012, ADR-018) | Critical | Drafts enforce engine-weighted aggregation exclusively |
| **DISC-10** | Four Named Controls vs. Three Families | `research_questions.md` vs. `selection.json` | `experiments/confirmatory_development/controls/` | Moderate | Clarified in drafts: 4 named controls spanning 3 distinct families |
| **DISC-11** | Unresolved Authorship & Institution | Default university placeholders | `research/author_contributions.md` | Low | Drafts omit fabricated names; marked explicitly as pending |

---

## 2. Detailed Discrepancy Audits

### DISC-01: Outdated Phase-0 Scope and Architecture Descriptions
- **Exact Source**: `docs/project_scope.md` and `docs/architecture_overview.md`.
- **Conflicting Evidence**: `README.md` (Sections 1–3), `research/roadmap.md`, and `research/decision_log.md` (ADR-001, ADR-002, ADR-018).
- **Why It Matters**: The early scope and architecture documents contain broad, historical aspirations (e.g., broad multi-tier cloud architectures, live vibration streaming, fleet-wide orchestration) that were superseded when the project reset to establish a rigorous, hypothesis-driven econometric and prognostic study on turbofan C-MAPSS degradation.
- **Conservative Wording in New Drafts**: All new drafts frame IntelliTwin strictly around its locked scientific scope: an offline, replay-based research framework evaluating decision-aware, condition-adaptive conformal calibration on C-MAPSS run-to-failure benchmarks. Legacy descriptions are noted as historical context only.
- **Owner for Eventual Correction**: Project Team / Mayank Singh.
- **Resolution Status**: Recorded in documentation; active drafts reflect locked ADR scope.

---

### DISC-02: Legacy Baselines in Paper Outline Not Included in Frozen Matrix
- **Exact Source**: `paper/outline.md` (Section 7: Experimental Setup).
- **Conflicting Evidence**: `paper/outline.md` lists `Linear, SVR, Random Forest, MLP, LSTM, GRU`. However, the formal frozen study under ADR-019 and ADR-020 strictly specifies exactly two base point-predictor families: Histogram Gradient Boosting Regressor (GBR) and unidirectional Long Short-Term Memory (LSTM) networks.
- **Why It Matters**: Promising six baseline architectures in the methodology or outline creates an unfulfillable expectation and contradicts the frozen 30-model production matrix and statistical inference contracts.
- **Conservative Wording in New Drafts**: The new synopsis, IEEE paper, and thesis drafts explicitly limit the point-prediction baselines to the two frozen families (GBR and LSTM), explaining that GBR provides a high-capacity non-neural tabular gradient-boosted benchmark over flattened 510-dimensional causal windows, while LSTM provides a sequential recurrent representation over 30×17 causal tensors.
- **Owner for Eventual Correction**: Research Partner (Writing Lead).
- **Resolution Status**: Corrected in new drafts.

---

### DISC-03: Unsupported Claims of Epistemic vs. Aleatoric Uncertainty Decomposition
- **Exact Source**: `paper/outline.md` (Section 3 & 6), and informal research notes mentioning Bayesian neural networks and epistemic/aleatoric separation.
- **Conflicting Evidence**: The implemented uncertainty subsystem (`src/intellitwin/uncertainty/conformal.py`) implements nonconformity score inversion via hierarchical conformal calibration (`score(p, y) = max((p-y)/a(p), (y-p)/b(p), 0)`). Conformal prediction constructs distribution-free prediction intervals covering total predictive error; it does not decompose residuals into aleatoric (data noise) and epistemic (model parameter uncertainty) components.
- **Why It Matters**: Claiming epistemic/aleatoric decomposition when using conformal prediction intervals is a severe scientific and methodological mischaracterization.
- **Conservative Wording in New Drafts**: All new drafts strictly describe the uncertainty mechanism as *marginal and condition-adaptive total predictive uncertainty quantification via distribution-free conformal calibration*. Any claim of separating epistemic from aleatoric variance is strictly avoided.
- **Owner for Eventual Correction**: Research Partner (Theory Lead).
- **Resolution Status**: Enforced in all new documentation deliverables.

---

### DISC-04: Unsupported Claims of Physical Asset or Live Bidirectional Digital Twin Integration
- **Exact Source**: `docs/project_scope.md`, `docs/architecture_overview.md`, and title phrases mentioning "Digital Twin Framework".
- **Conflicting Evidence**: Inspection of `src/intellitwin/` confirms there are no IoT protocols (MQTT, OPC UA), no hardware sensor interfaces, and no bidirectional telemetry back-coupling into an operational engine. The implementation consists of an offline, discrete-event maintenance simulation engine replaying recorded C-MAPSS run-to-failure cycles.
- **Why It Matters**: Claiming an operational industrial deployment or physical twin synchronization when the evaluation is an offline empirical simulation on synthetic NASA benchmark data constitutes scientific misrepresentation.
- **Conservative Wording in New Drafts**: The framework is accurately characterized as an *AI-driven digital twin decision-support prototype evaluated via trace-driven sequential simulation replay on the NASA C-MAPSS benchmark*. All claims of physical engine coupling, bidirectional actuation, or factory-floor deployment are explicitly disclaimed.
- **Owner for Eventual Correction**: Lead Developer & Writing Partner.
- **Resolution Status**: Enforced in all new documentation deliverables.

---

### DISC-05: Inherited Literature Status Labels from Earlier Supplied Audits
- **Exact Source**: `research/literature/source_verification.csv` (lines 2–27).
- **Conflicting Evidence**: In `source_verification.csv`, column `verification_basis` states: *"Independent source audit supplied in the correction instruction; not independently reverified by the implementing agent"*. Certain sources (e.g., `wei2024digital`, `hisamuddin2026ai`, `belay2026digital`) have pending DOIs or unindexed institutional handles.
- **Why It Matters**: Relying on second-hand audit labels without verifying what was actually accessible risks propagating phantom citations or unverified methodological assertions.
- **Conservative Wording in New Drafts**: In `reference_audit.csv`, each reference is audited with clear access levels: `full_text_inspected`, `abstract_inspected`, `metadata_only`, or `unresolved`. Claims in `related_work_synthesis.md` are bounded strictly by the inspected source content.
- **Owner for Eventual Correction**: Research Partner (Writing Lead).
- **Resolution Status**: Fully audited in `reference_audit.csv` and `related_work_matrix.csv`.

---

### DISC-06: Blanket "Verified Bibliography" Statement Despite Unresolved Entries
- **Exact Source**: `paper/references.bib` header comment: *"Every entry has been audited against publisher records, Crossref API, or arXiv. Unverified leads are strictly omitted from this file."*
- **Conflicting Evidence**: Three entries in `paper/references.bib` (`wei2024digital`, `hisamuddin2026ai`, `belay2026digital`) remain unassigned DOIs, unindexed preprints, or unverified institutional handles.
- **Why It Matters**: Making an absolute blanket claim of complete verification undermines academic credibility when unindexed or preprint entries remain present.
- **Conservative Wording in New Drafts**: `references_verified.bib` contains strictly the independently verified bibliographic entries needed by the research drafts. Entries with pending verification are explicitly segregated and annotated.
- **Owner for Eventual Correction**: Research Partner (Writing Lead).
- **Resolution Status**: Created clean, verified subset `references_verified.bib`.

---

### DISC-07: Unqualified Conditional and Finite-Sample Coverage Claims
- **Exact Source**: Informal summaries suggesting conformal prediction guarantees valid coverage for every operational cycle, wear stage, or stopping time.
- **Conflicting Evidence**: `research/research_design/statistical_inference_protocol.md` (Section 8) and foundational conformal theory (Vovk et al., Lee et al. 2023). Conformal prediction guarantees finite-sample marginal coverage under exchangeability. Because degradation trajectories are non-exchangeable time series, and stopping times are state-dependent, conformal inference does not theoretically guarantee exact pointwise conditional coverage or sequential stopping-time coverage.
- **Why It Matters**: Promising exact conditional coverage or stopping-time validity when the underlying mathematics only guarantees exchangeable marginal coverage is a fatal statistical error.
- **Conservative Wording in New Drafts**: All drafts explicitly emphasize that conditional and subgroup validity is an *empirical diagnostic evaluated across operating regimes and lifecycle stages*, and that stopping-time coverage under sequential replacement policies remains an empirical research question rather than a proven mathematical guarantee.
- **Owner for Eventual Correction**: Research Partner (Theory Lead).
- **Resolution Status**: Enforced in all theoretical and methodology drafts.

---

### DISC-08: Pretest Completion Report Overstating Verification Audit Evidence
- **Exact Source**: `research/research_design/step09_pretest_completion.md` (Section 1, item 2): *"Re-executed raw prediction reproduction on validation and calibration partitions with zero discrepancies."*
- **Conflicting Evidence**: `experiments/audits/step08_repair_verification.json` records:
  ```json
  "checks_not_run": ["checkpoint_prediction_reproduction"],
  "results": {
    "checkpoint_prediction_reproduction": "NOT RUN"
  }
  ```
- **Why It Matters**: A narrative markdown completion report claims a verification check succeeded when the formal JSON audit report in the repository explicitly records that check as `NOT RUN`.
- **Conservative Wording in New Drafts**: The new drafts document that while structural registry completeness, cache integrity, and rational quantiles passed, official checkpoint prediction reproduction was recorded as `NOT RUN` in the Step 8 verification report. Full re-verification is pending Mayank's clean execution under `experiments/pretest_verification_v2/` (tracked in `update_register.csv` as `UPD-01`).
- **Owner for Eventual Correction**: Lead Developer (Mayank Singh).
- **Resolution Status**: Formally logged as an active discrepancy pending merge of `pretest_verification_v2`.

---

### DISC-09: Historical Pooled-Cycle Metrics vs. Frozen Engine-Weighted Evaluation
- **Exact Source**: Early evaluation discussions calculating PICP, RMSE, or maintenance cost by pooling all operational cycles into a single aggregate denominator.
- **Conflicting Evidence**: `research/research_design/data_evaluation_protocol.md` (ADR-012, ADR-016), `statistical_inference_protocol.md` (ADR-018), and Lee et al. (2023). Trajectories vary in run-to-failure length; pooling raw cycles biases metrics toward longer-lived engines and violates independence. ADR-018 freezes the engine as the independent statistical unit.
- **Why It Matters**: Evaluating metrics by pooling cycles creates survivor bias and invalidates statistical confidence intervals.
- **Conservative Wording in New Drafts**: All mathematical formulations and narrative descriptions in the drafts enforce *equal-engine-weighted metric aggregation*: metrics are computed within engine across qualified cycles ($t \ge 30$), averaged across the 5 fixed seeds within each engine, and then averaged equally across the $N$ evaluated engines in the split.
- **Owner for Eventual Correction**: Research Partner (Theory Lead).
- **Resolution Status**: Enforced in all methodology drafts and LaTeX equations.

---

### DISC-10: Distinguishing Four Named RQ3 Controls from Three Control Families
- **Exact Source**: `research/research_questions.md` (RQ3) states: *"Evaluate decision-value attribution by comparing the proposed method against three prespecified matched-conservatism control families: widened intervals, point-prediction safety margins, and earlier-intervention conservative policies."*
- **Conflicting Evidence**: `experiments/confirmatory_development/controls/FD002/{GBR,LSTM}/selection.json` contains four named controls:
  1. `earlier_intervention`
  2. `matched_width_interval`
  3. `point_safety_margin`
  4. `widened_interval`
- **Why It Matters**: A reader might be confused by whether there are three or four comparators in Experiment C / RQ3.
- **Conservative Wording in New Drafts**: The drafts explicitly explain the hierarchical taxonomy: there are **three general control families** (widened intervals, point-prediction safety margins, and earlier-intervention policies), instantiated by **four named operational control configurations** (because the widened-interval family evaluates both a target-matched width control and a boundary-expanded widened interval control).
- **Owner for Eventual Correction**: Research Partner (Theory Lead).
- **Resolution Status**: Explicitly clarified in methodology, evaluation plan, and thesis chapters.

---

### DISC-11: Unresolved Author Contributions, Institutional Details, and Venue Specifications
- **Exact Source**: Generic headers or placeholders across early files.
- **Conflicting Evidence**: `research/author_contributions.md` records that contribution percentages and final author ordering are not yet finalized. Institutional guidelines and target IEEE conference CFP are pending selection.
- **Why It Matters**: Hardcoding author percentages, first-author designations, supervisor names, or venue acceptance statements without evidence violates research ethics.
- **Conservative Wording in New Drafts**: The new deliverables list all three authors neutrally (alphabetical/equal formatting), explicitly mark institutional details as `PENDING_INSTITUTIONAL_SPECIFICATION`, describe IEEE styling as a provisional formatting baseline, and include a clear banner stating that drafts are working research documents awaiting confirmatory results and institutional review.
- **Owner for Eventual Correction**: All Authors (Mayank Singh, Shiksha Pandey, Ruchi Gupta).
- **Resolution Status**: Formally tracked under `UPD-08` and `UPD-09`.
