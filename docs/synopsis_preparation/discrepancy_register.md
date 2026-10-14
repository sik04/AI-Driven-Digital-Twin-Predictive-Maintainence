# Discrepancy Register and Documentation Risk Assessment

**Pinned Source Commit**: `bb9e34579343881a831e3f052608ee15e183df76` (Historical initial draft: `224c741f5f3da19821a708e0a6da417d4810e9da`)  
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
| **DISC-08** | Step 8 Prediction Audit Status | Historical step08 report (`step08_repair_verification.json`) | `experiments/pretest_verification_v2/step08_full_audit.json` (PR #25) | Critical | Resolved by committed PR #25 artifacts (60 reproductions, max diff 0.0) |
| **DISC-09** | Pooled-Cycle vs. Engine-Weighted Metrics | Early protocol drafts | `research/research_design/data_evaluation_protocol.md` (ADR-012, ADR-018) | Critical | Drafts enforce engine-weighted aggregation exclusively |
| **DISC-10** | Four Named Controls vs. Three Families | `research_questions.md` vs. `selection.json` | `experiments/confirmatory_development/controls/` | Moderate | Clarified in drafts: 4 named controls spanning 3 distinct families |
| **DISC-11** | Unresolved Authorship & Roles | Fabricated supervisor/lead roles | `research/author_contributions.md` | High | Resolved in new drafts: 3 neutral authors, roles pending agreement |
| **DISC-12** | Preprocessing Normalization Method | Inconsistent min-max / robust scaling | `src/intellitwin/data/preprocessing.py`, ADR-013 | Critical | Resolved in new drafts: training-only z-score normalization (ddof=0) |
| **DISC-13** | Base Model Architecture Descriptions | Mentions of LightGBM, XGBoost, sub-sampling | `src/intellitwin/models/gbr.py`, `lstm.py`, ADR-020 | Critical | Resolved in new drafts: scikit-learn HistGradientBoosting & PyTorch LSTM |
| **DISC-14** | Calibration Nonconformity Equations | Erroneous sigmoid failure probability / quantile | `src/intellitwin/uncertainty/{scores, quantiles}.py`, ADR-021 | Critical | Resolved in new drafts: asymmetric score inversion, finite mass m/(m+1) |
| **DISC-15** | Maintenance Costs & Intervention Delays | Invented costs 10/100, 2-cycle lead-time delay | `src/intellitwin/simulator/{engine, costs}.py`, ADR-018 | Critical | Resolved in new drafts: SCU 1/5/0.20, immediate PM, zero lead time |
| **DISC-16** | Invented RQ3 Controls vs Pre-Registered | Unregistered 1.25 widening, margin 10 | `experiments/pretest_verification_v2/controls/`, ADR-023 | Critical | Resolved in new drafts: 4 named controls across 3 families |
| **DISC-17** | Invented Hypotheses & Margins | Arbitrary 5% cost reduction, H1 coverage alone | `research/hypotheses/hypothesis_framework.yaml`, ADR-018 | Critical | Resolved in new drafts: ADR-018 practical margins (0.20 SCU, 0.01 error) |

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

### DISC-08: Historical Step 8 Verification Report vs Committed PR #25 Full Audit
- **Exact Source**: Historical `experiments/audits/step08_repair_verification.json` recorded:
  ```json
  "checks_not_run": ["checkpoint_prediction_reproduction"],
  "results": {
    "checkpoint_prediction_reproduction": "NOT RUN"
  }
  ```
- **Conflicting Evidence & Resolution**: PR #25 merged into `main` at commit `bb9e34579343881a831e3f052608ee15e183df76`. The committed audit artifacts in `experiments/pretest_verification_v2/` establish:
  - `step08_full_audit.json`: All 6 mandatory verification checks ran; 60 base-model/partition prediction reproductions were verified across `validation` and `calibration` partitions (not training), reporting a maximum numerical prediction difference of `0.0`.
  - `pretest_audit.json`: Reports overall status `PASS` and `PRETEST_READY`.
  - `baseline_manifest.json`: 652 tracked protected artifacts verified from Git; 72 local-only search checkpoints accounted for.
  - `held_out_execution_status` remains `NOT_STARTED` and `rq_outcomes_status` remains `PENDING`.
- **Why It Matters**: Earlier documentation described prediction reproduction as pending/NOT RUN. The documentation is now updated to report the committed PR #25 audit findings directly without claiming personal re-execution.
- **Resolution Status**: Resolved by committed audit artifacts in PR #25 at commit `bb9e345`.

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
- **Exact Source**: Generic headers, fabricated supervisor titles, or unilateral lead assignments across early files.
- **Conflicting Evidence**: `research/author_contributions.md` records that contribution percentages and final author ordering are not yet finalized.
- **Why It Matters**: Hardcoding author percentages, first-author designations, supervisor names (e.g. assigning Ruchi Gupta as supervisor), or methodology leads (e.g. assigning Shiksha Pandey as lead without agreement) violates research ethics.
- **Conservative Wording in New Drafts**: The new deliverables list all three authors neutrally (alphabetical/equal formatting), explicitly mark institutional details as `PENDING_INSTITUTIONAL_SPECIFICATION`, describe IEEE styling as a provisional formatting baseline, and include a clear banner stating that drafts are working research documents awaiting confirmatory results and institutional review.
- **Owner for Eventual Correction**: All Authors (Mayank Singh, Shiksha Pandey, Ruchi Gupta).
- **Resolution Status**: Formally tracked under `UPD-08` and `UPD-09`.

---

### DISC-12: Erroneous Preprocessing Normalization Descriptions
- **Exact Source**: Legacy methodology notes and PR #26 drafts describing min-max normalization, robust min-max normalization, median/IQR normalization, or training medians as centering statistics.
- **Conflicting Evidence**: `src/intellitwin/data/preprocessing.py`, `research/research_design/data_evaluation_protocol.md` (Step 5.1), and ADR-013.
- **Why It Matters**: Min-max and median/IQR normalizations do not match the implementation. The implementation strictly fits training-only z-score normalization ($x_{\text{norm}} = (x - \mu) / s$, with $s = \sigma$ when $\sigma > 0$ and $s = 1.0$ otherwise, `ddof=0`).
- **Resolution in Corrected Package**: All active markdown drafts, LaTeX chapters, and presentation outlines now state the exact training-only z-score formula, explain dataset-specific standardization (FD001 global; FD002/FD004 K-means $k=6$ clustering on standardized settings with lexicographic centroid ordering and within-regime sensor scaling), enforce the frozen 17-feature selection order, and clarify that the 125-cycle cap is a modeling convention rather than proof that early degradation is physically absent.

---

### DISC-13: Misstated Base Model Architectures and Seed Replication
- **Exact Source**: Descriptions of GBR as LightGBM or XGBoost, invented claims of random subsampling as the cause of seed variance, or informal descriptions of LSTM architecture.
- **Conflicting Evidence**: `src/intellitwin/models/gbr.py`, `src/intellitwin/models/lstm.py`, and ADR-020.
- **Why It Matters**: GBR is strictly `sklearn.ensemble.HistGradientBoostingRegressor` over a C-order flattened 510-dimensional causal window. The LSTM is a single-layer unidirectional network (`input_size=17, hidden_size=64, num_layers=1, batch_first=True, dropout=0.0`, sequence slice, separate `nn.Dropout(p=0.20)`, `nn.Linear(64,1)`, early stopping on validation uncapped RMSE).
- **Resolution in Corrected Package**: Model descriptions are corrected across all documents. Illustrative validation RMSE numbers are removed from narrative method text and placed in designated results tables. The five seeds (2026–2030) are correctly characterized as fixed stochastic replications rather than independent experiments.

---

### DISC-14: Erroneous Calibration Equations, Nonconformity Scores, and Boundary Mass
- **Exact Source**: Legacy documents describing $p$ as a sigmoid-derived failure probability, logistic critical-threshold transformations, $a(p)=\exp(-\beta p)$, or incorrect quantile mass bounding ($1/(m n_i)$ in the final distribution).
- **Conflicting Evidence**: `src/intellitwin/uncertainty/{scores, quantiles, calibration}.py`, ADR-021, and Lee et al. (2023).
- **Why It Matters**: Mathematical errors in calibration equations invalidate theoretical and computational consistency.
- **Resolution in Corrected Package**: Use $p$ strictly for non-negative predicted RUL in cycles. Nonconformity score is $\max((p-y)/a(p), (y-p)/b(p), 0)$ with $\sigma(p)=(1+p/125)^\gamma, z(p)=\exp(-p/20), a(p)=\sigma(p)\exp(\beta z(p)), b(p)=\sigma(p)\exp(-\beta z(p))$. Final empirical CDF assigns mass $1/((m+1)n_i)$ to each finite endpoint, bounding total finite mass by $m/(m+1)$ with remaining mass $1/(m+1)$ at $+\infty$. Negative $\beta$ is accurately explained as nondecreasing lower bound and nondecreasing upper bound without claiming automatic utility improvement. Regime support threshold is $m_g \ge \max(10, \lceil 1/\alpha \rceil - 1)$.

---

### DISC-15: Erroneous Maintenance Cost Parameters and Invented Operational Delays
- **Exact Source**: Legacy drafts citing preventive replacement cost 10, failure cost 100, costs 50/200, 2-cycle intervention delays, lead-time sensitivity grids, or aircraft accident claims.
- **Conflicting Evidence**: `src/intellitwin/simulator/{engine, costs}.py`, `research/research_design/maintenance_cost_scenarios.yaml`, and ADR-018.
- **Why It Matters**: Invented costs and lead times directly contradict the frozen simulation contract and the pre-registered decision threshold.
- **Resolution in Corrected Package**: Synthetic cost scenarios are enforced as: `primary_reference` ($C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$ SCU), `failure_sensitive` ($C_{\text{FAIL}}=10.0$), and `waste_sensitive` ($C_{\text{WASTE}}=0.40$). Actions occur at cycles $30$ to $T-1$; preventive maintenance occurs immediately upon trigger with zero intervention lead time, terminating the episode. Offline interval evaluation includes all qualified cycles $30$ through $T$. The equality horizons (20, 45, 10 cycles) are clarified as economic breakeven points rather than policy thresholds.

---

### DISC-16: Invented RQ3 Controls vs. Pre-Registered Controls
- **Exact Source**: Legacy drafts describing constant half-width intervals, fixed 1.25 widening, universal safety margin 10, point threshold inflation 15, or unregistered Gaussian intervals.
- **Conflicting Evidence**: `experiments/pretest_verification_v2/controls/FD002/{GBR,LSTM}/selection.json`, `research/research_design/step09_control_selection.md`, and ADR-023.
- **Why It Matters**: Fabricating control definitions compromises the validity of RQ3 decision-value attribution.
- **Resolution in Corrected Package**: Four controls across three families are enforced: `matched_width_interval`, `widened_interval`, `point_safety_margin`, and `earlier_intervention`. Exact frozen parameters selected on FD002 validation engines across 5 seeds are recorded from the committed JSON files (GBR: matched $\lambda=0.92$, widened $\lambda=1.00$, $m=5$, $h=1$; LSTM: matched $\lambda=0.90$, widened $\lambda=1.00$, $m=4$, $h=1$).

---

### DISC-17: Invented Practical-Effect Thresholds and Hypothesis Formulations
- **Exact Source**: Result tables defining H1 as coverage $\ge 0.90$ alone, H2 as arbitrary 5% relative cost reduction, H3 allowing zero benefit, or H4 as regime-only coverage.
- **Conflicting Evidence**: `research/hypotheses/hypothesis_framework.yaml`, `research/research_design/statistical_inference_protocol.md`, and ADR-018.
- **Why It Matters**: Collapsing composite intersection-union rules into isolated arbitrary thresholds misrepresents the pre-registered scientific design.
- **Resolution in Corrected Package**: Full ADR-018 hypothesis definitions and practical-effect margins are restored for RQ1–RQ4 ($\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$, coverage error ceilings $< 0.05$, noninferiority $D_{\text{width}}, D_{\text{score}} < 1.0$, non-harm $\Delta_{\text{cost}} > -0.20, \Delta_{\text{error}} > -0.01$, observed failure rate safeguard $\Delta_{\text{fail}} \le 0.0$). The 10,000-draw cluster bootstrap percentile intervals (98.75% decision, 95% descriptive) with conservative missing-group bound propagation ($[0, 0.90]$) are enforced throughout.
