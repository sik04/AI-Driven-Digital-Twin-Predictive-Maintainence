# IntelliTwin Research Documentation Correction Report

**Repository**: `https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence`  
**Baseline Commit**: `c163bb279e7427b8f1b6e75955af4969ff9370fd` (PR #27 Merged Main)  
**Committed Readiness Evidence**: `experiments/pretest_verification_v4/` (Audit Execution Commit: `550a7994d5746d3bcbfa28c26e7ed4f1a26a6153`, `git_dirty: false`, readiness: `PRETEST_READY`, held-out execution: `NOT_STARTED`, RQ outcomes: `PENDING`)  
**Branch**: `fix/research-docs-v4-alignment`  
**Date**: October 2026  
**Scope**: Documentation correction across `docs/synopsis_preparation/` to eliminate all contradictions between documentation drafts, frozen research specifications, committed implementation code, and v4 audit evidence.

> **Status Statement**: Base predictors and conformal calibrators are implemented and frozen. The committed v4 pre-test audit reports PASS and PRETEST_READY. Held-out execution has not started, and RQ1–RQ4 outcomes remain pending. Development validation and audit results do not establish confirmatory maintenance benefit, subgroup reliability, or robustness.

---

## Executive Summary

Following the integration of PR #27 and the v4 pre-test verification audit, a comprehensive audit of the documentation package in `docs/synopsis_preparation/` identified remaining discrepancies between drafts, authoritative project specifications, and v4 audit artifacts. Discrepancies spanned data preprocessing, base model training parameters, conformal calibration mathematics, maintenance simulation parameters, comparator controls, hypothesis decision thresholds, author roles, table templates, and citation keys.

This report documents the exact resolution of all identified discrepancies across 16 categories. All modifications were restricted strictly to `docs/synopsis_preparation/`. No frozen scientific protocols, checkpoints, split manifests, or implementation files outside `docs/synopsis_preparation/` were modified. All four deliverable PDFs were recompiled and visually inspected with zero compilation errors, zero missing inputs, zero unresolved citations, and zero undefined cross-references.

---

## Category-by-Category Correction Record

### 1. Branch, Workspace, and Scope
- **Incorrect Previous Description**: Working directly on older branches (`docs/synopsis-evidence-preparation`, `fix/research-documentation-consistency`) against outdated base commits (`224c741`, `bb9e345`), or mixing documentation updates with implementation file changes.
- **Corrected Description**: Dedicated branch `fix/research-docs-v4-alignment` created from verified `origin/main` commit `c163bb279e7427b8f1b6e75955af4969ff9370fd`. Modifications isolated strictly to `docs/synopsis_preparation/`.
- **Affected Files**: All tracking registers, `README.md`, `discrepancy_register.md`, `completion_checklist.md`.
- **Authoritative Source & Locator**: PR #27 commit `c163bb279e7427b8f1b6e75955af4969ff9370fd`.
- **Validation Performed**: Verified via `git status` that zero modifications exist outside `docs/synopsis_preparation/`.
- **Remaining Limitations**: None.

### 2. Required Source Files & Audit Evidence
- **Incorrect Previous Description**: Citations of outdated or superseded v2 audit artifacts in `experiments/pretest_verification_v2/`, or conflating historical `NOT RUN` status with the current state.
- **Corrected Description**: Updated all references to point to the actual v4 pre-test audit files committed in `experiments/pretest_verification_v4/`: `pretest_audit.json`, `content_verification.json`, `input_manifest.json`, `reused_evidence.json`, `protocol_freeze.json`, `supersession.json`, and `regression_test_report.json`.
- **Audit Details**:
  - `pretest_audit.json`: Reports overall status `PASS` and `PRETEST_READY`.
  - `input_manifest.json`: 652 tracked protected artifacts verified from Git; 72 historical/unavailable entries accounted for.
  - `reused_evidence.json`: 60 validation and calibration prediction reproduction records with maximum difference 0.0 preserved with original provenance; raw inference was not rerun during documentation repair.
  - Validation-smoke evidence: 930 configurations (810 primary + 120 controls), 19,590 engine-seed outcomes, 186 cell-summary rows, 152 hypothesis-component rows, 10,000 bootstrap draws (validation-smoke counts, not observed held-out results).
  - `held_out_execution_status` remains strictly `NOT_STARTED` and `rq_outcomes_status` remains `PENDING`.
- **Affected Files**: `source_manifest.csv`, `update_register.csv`, `claims_evidence_matrix.csv`, `reproducibility_draft.md`, `latex/thesis/chapters/reproducibility_appendix.tex`.
- **Authoritative Source & Locator**: `experiments/pretest_verification_v4/` artifacts.
- **Validation Performed**: Automated check in `validate_documentation.py` verified every local path exists in the repository.
- **Remaining Limitations**: Held-out test evaluation remains `NOT_STARTED` and `PENDING`.

### 3. Preprocessing Everywhere
- **Incorrect Previous Description**: Mention of min–max normalization, robust min–max normalization, median/IQR normalization, and claiming all 7 excluded sensors are universally constant across all datasets and regimes.
- **Corrected Description**: "Preprocessing uses training-only z-score normalization. Means and population standard deviations are estimated with ddof=0. An exactly zero standard deviation is replaced by an effective scale of 1.0, while the mean is still subtracted."
  $$x_{\text{normalized}} = \frac{x - \mu_{\text{train}}}{s_{\text{train}}}, \quad s_{\text{train}} = \begin{cases} \sigma_{\text{train}} & \text{if } \sigma_{\text{train}} > 0 \\ 1 & \text{otherwise} \end{cases}$$
  Dataset-specific details: FD001 uses global training-fitted normalization. FD002/FD004 use standardized settings to learn 6 regimes via K-Means ($k=6, \text{random\_state}=2026, \text{n\_init}=10$) with lexicographic centroid ordering, followed by regime-specific sensor normalization. Exact 17-feature selection: `setting1, setting2, setting3, s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21`. Preprocessing occurs prior to causal window construction. The 125-cycle cap is documented as a modeling convention.
- **Affected Files**: `methodology_draft.md`, `system_description.md`, `presentation_outline.md`, `latex/paper/sections/methodology.tex`, `latex/paper/sections/experimental_setup.tex`, `latex/thesis/chapters/methodology.tex`, `latex/thesis/chapters/implementation.tex`, `latex/shared/preprocessing_models.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/data/preprocessing.py`, `research/research_design/data_evaluation_protocol.md`.
- **Validation Performed**: Regex scanning via `validate_documentation.py` verified zero instances of forbidden normalization terms.
- **Remaining Limitations**: None.

### 4. Base Model Descriptions
- **Incorrect Previous Description**: Base models described as LightGBM or XGBoost; random subsampling claimed as reason for repeated seeds; unpruned narrative validation RMSEs mixed into method paragraphs; Adam optimizer with batch size 128 for LSTM.
- **Corrected Description**:
  - GBR: `sklearn.ensemble.HistGradientBoostingRegressor`. Input is a C-order flattened $30 \times 17$ window (510 features). Selected configs: `gbr_lr010_leaf15_l2_0` (FD001) and `gbr_lr010_leaf31_l2_0` (FD002/FD004).
  - LSTM: PyTorch unidirectional recurrent layer (`input_size=17`, `hidden_size=64`, `num_layers=1`, `batch_first=True`, `bidirectional=False`, `dropout=0.0`). Output takes final sequence step, applies `nn.Dropout(p=0.20)` followed by `nn.Linear(64, 1)`. Optimizer is **AdamW** with learning rate $\eta = 0.001$, weight decay $0.0001$, batch size 256 (not 128), betas $(0.9, 0.999)$, and epsilon $10^{-8}$. Selected configuration: `lstm_h64_lr0010`.
  - Windowing & Targets: 30-cycle causal windows, stride 1, no padding, no crossing engine boundaries. Training target is $\min(\text{rul}, 125)$; inference prediction is $p = \max(0, \hat{y})$ with no upper clipping. Prespecified training seeds: `[2026, 2027, 2028, 2029, 2030]`.
  - Point-prediction RMSE definition: For each seed, average within-engine squared errors, average those engine MSEs equally, then take square root.
- **Affected Files**: `methodology_draft.md`, `presentation_outline.md`, `latex/shared/preprocessing_models.tex`, `latex/paper/sections/methodology.tex`, `latex/thesis/chapters/methodology.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/models/gbr.py`, `src/intellitwin/models/lstm.py`, `research/research_design/step07_base_predictor_specification.md`, `experiments/base_models/model_registry.json`.
- **Validation Performed**: Scanned for absence of LightGBM/XGBoost as project models; checked AdamW feature and parameter specifications.
- **Remaining Limitations**: Base model training performance numbers belong in labeled results tables, not method descriptions.

### 5. Calibration Equations
- **Incorrect Previous Description**: Predicted $p$ described as sigmoid failure probability; logistic threshold transformations; $a(p)=\exp(-\beta p), b(p)=\exp(\beta p)$; mathematical $\beta = -1$; global interval displayed width claimed to be universally constant.
- **Corrected Description**: Nonnegative predicted RUL $p = \max(0, \text{raw\_prediction})$.
  $$\sigma(p) = \left(1 + \frac{p}{125}\right)^\gamma, \quad z(p) = \exp\left(-\frac{p}{20}\right)$$
  $$a(p) = \sigma(p) \exp(\beta z(p)), \quad b(p) = \sigma(p) \exp(-\beta z(p))$$
  $$\text{score}(p, y) = \max\left(\frac{p - y}{a(p)}, \frac{y - p}{b(p)}, 0\right)$$
  $$L = \max(0, p - q_g a(p)), \quad U = p + q_g b(p)$$
  Where $y$ is uncapped true RUL. Selected candidate: `gamma2_betam1` ($\gamma = 2, \beta_{\text{code}} = -1, \beta = -\ln(2) \approx -0.693147$).
  Displayed baseline interval width is $p + q - \max(0, p-q)$, which equals $2q$ only when $p \ge q$.
  Negative $\beta$ interpretation: "At fixed $p$, $q$ and $\gamma$, negative $\beta$ decreases $a(p)$ and increases $b(p)$. The lower and upper endpoints are therefore nondecreasing relative to $\beta=0$. This does not establish earlier intervention or better maintenance utility because calibration thresholds are refitted and policy outcomes depend on the resulting trajectories."
  Final calibration with $m$ engines places mass $\frac{1}{(m+1)n_i}$ on each finite endpoint, total finite mass $\frac{m}{m+1}$, and remaining mass $\frac{1}{m+1}$ at $+\infty$. Quantile $q$ is smallest score whose CDF reaches $1-\alpha$; if none reaches it, $q=+\infty$.
  Regime support requires $m_g \ge \max(10, \lceil 1/\alpha \rceil - 1)$ distinct engines (10 for 80%/90%, 19 for 95%), else fallback to global threshold for the same method and $\alpha$. Calibration support thresholds are distinguished from the separate evaluation-subgroup eligibility threshold of 10 engines.
- **Affected Files**: `methodology_draft.md`, `latex/shared/calibration_equations.tex`, `latex/paper/sections/methodology.tex`, `latex/synopsis/sections/methodology.tex`, `latex/thesis/chapters/methodology.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/uncertainty/calibration.py`, `src/intellitwin/uncertainty/quantiles.py`, `src/intellitwin/uncertainty/scores.py`, `research/research_design/step08_calibration_specification.md`.
- **Validation Performed**: Verified formulas in LaTeX and Markdown; validated mathematical consistency across all drafts.
- **Remaining Limitations**: None.

### 6. Maintenance and Costs
- **Incorrect Previous Description**: Invented preventive cost 10, failure cost 100, costs 50/200; two-cycle intervention delays; lead-time sensitivity grids; logistical dispatch mechanics; claiming simulated failure represents aircraft accidents; SCU described as validated airline economics.
- **Corrected Description**: Synthetic Cost Scenarios (SCU values represent synthetic benchmark preferences):
  - `primary_reference`: $\CPM = 1.0, \CFAIL = 5.0, \CWASTE = 0.20$ SCU
  - `failure_sensitive`: $\CPM = 1.0, \CFAIL = 10.0, \CWASTE = 0.20$ SCU
  - `waste_sensitive`: $\CPM = 1.0, \CFAIL = 5.0, \CWASTE = 0.40$ SCU
  Policy: `MAINTAIN_NOW` iff $L(t) \le 1.0$ cycle at $t \in [30, T-1]$, else `CONTINUE`. Action occurs immediately with zero lead time. Cost is $\CPM + \CWASTE(T-t)$ if maintained at $t < T$, or $\CFAIL$ if failure occurs at $T$ without prior PM ($W=0$). Offline interval evaluation includes all cycles $30 \dots T$. Break-even waste values (20, 45, 10 cycles) clarify economic equivalence, not policy thresholds.
- **Affected Files**: `methodology_draft.md`, `system_description.md`, `results_table_templates.md`, `latex/shared/simulator_costs.tex`, `latex/paper/sections/methodology.tex`, `latex/paper/sections/results.tex`, `latex/synopsis/sections/methodology.tex`, `latex/thesis/chapters/methodology.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/simulator/costs.py`, `src/intellitwin/simulator/engine.py`, `src/intellitwin/decision/policies.py`, `research/research_design/maintenance_cost_scenarios.yaml`, `research/decision_log.md` (ADR-018).
- **Validation Performed**: Scanned for absence of $C_{\text{PM}}=10, C_{\text{FAIL}}=100$, lead-time delays, or accident claims.
- **Remaining Limitations**: Evaluated strictly on simulation replay.

### 7. RQ3 Controls
- **Incorrect Previous Description**: Constant half-width intervals; fixed widening factor 1.25; safety margin 10; threshold inflation 15; Gaussian interval baseline; $\lambda=1.00$ described as actual widening; $h=1$ described as earlier intervention.
- **Corrected Description**: Four prespecified controls across three families selected on FD002 validation engines across 5 seeds jointly at 90% coverage and `primary_reference` cost:
  1. `matched_width_interval`: $L_\lambda(t) = \max(0, p(t) - \lambda q_{\text{source}}(t)), U_\lambda(t) = p(t) + \lambda q_{\text{source}}(t)$. Grid $\lambda \in \{0.01 \dots 4.00, 5, 6, 8, 12, 16\}$, required width difference $\le 1$ cycle.
  2. `widened_interval`: same formula, grid $\lambda \in \{1.00 \dots 4.00, 5, 6, 8, 12, 16\}$. Note that $\lambda=1.00$ corresponds to unscaled baseline width, not actual expansion beyond baseline.
  3. `point_safety_margin`: maintain iff $p \le 1 + m, m \in \{0 \dots 250\}$. (Conformal interval metrics designated `NOT_APPLICABLE`).
  4. `earlier_intervention`: maintain iff $L_{\text{source}} \le h, h \in \{1 \dots 251\}$. Note that $h=1$ matches the baseline threshold, not an empirically earlier intervention.
  Committed Selections from `experiments/pretest_verification_v4/control_selection.json`:
  - GBR: matched_width (`global_hcp`, $\lambda=0.92$), widened (`regime_hcp`, $\lambda=1.00$), point ($m=5$), earlier (`regime_hcp`, $h=1$).
  - LSTM: matched_width (`regime_hcp`, $\lambda=0.90$), widened (`global_hcp`, $\lambda=1.00$), point ($m=4$), earlier (`global_hcp`, $h=1$).
- **Affected Files**: `methodology_draft.md`, `results_table_templates.md`, `latex/shared/control_definitions.tex`, `latex/paper/sections/methodology.tex`, `latex/paper/sections/results.tex`, `latex/thesis/chapters/experimental_design.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/decision/controls.py`, `experiments/pretest_verification_v4/control_selection.json`.
- **Validation Performed**: Verified parameter values and JSON records.
- **Remaining Limitations**: Controls frozen on validation partition; held-out evaluation pending.

### 8. Hypotheses and Statistics
- **Incorrect Previous Description**: Result-table hypotheses defined as coverage $>0.90$ alone, 5% relative cost reduction, or arbitrary single contrasts; "at least 0.20 SCU"; coverage ceiling written as "coverage < 0.05"; observed failure safeguard described as a confidence-interval proof of population safety.
- **Corrected Description**: Restored exact ADR-018 definitions with strict inequalities:
  - RQ1: Both models on FD002, `primary_reference`, 90% coverage: $\Delta_{\text{cost}} > 0.20$ SCU, marginal, worst-regime, and worst-stage absolute coverage error ceilings $<0.05$, $\Delta_{\text{fail}} \le 0.0$ against both baselines.
  - RQ2: Both models, both baselines, both subgroup families (regimes & stages): worst-group error $\Delta_{\text{error}} > 0.01$, worst error ceiling $<0.05$, noninferiority $D_{\text{width}} < 1.0$, $D_{\text{score}} < 1.0$ cycle.
  - RQ3: Both models against all four named controls: $\Delta_{\text{cost}} > 0.20$ SCU, proposed-method coverage error ceilings $<0.05$, $\Delta_{\text{fail}} \le 0.0$ against every control.
  - RQ4: Equal weighting of 6 mandatory cells ($w_k = 1/6$): aggregate cost $\Delta_{\text{cost, agg}} > 0.20$, aggregate error $\Delta_{\text{error, agg}} > 0.01$; every-cell non-harm: $\Delta_{\text{cost}} > -0.20$, $\Delta_{\text{error}} > -0.01$, and all safeguards pass.
  - Decision Logic: Intersection-Union Testing. Benefit condition passes if lower CI $>$ margin; fails if upper CI $<$ margin; otherwise inconclusive. Ceiling passes if upper CI $<$ ceiling; fails if lower CI $>$ ceiling; otherwise inconclusive. Equality and degenerate intervals are inconclusive. All-pass required for Supported; any component fail makes RQ Unsupported; else Inconclusive.
  - Observed failure safeguard is an empirical gate ($\Delta_{\text{fail}} \le 0.0$), not a confidence-interval proof of population safety.
  - Bootstrap Protocol: 10,000 paired engine-cluster resamples stratified by lifetime quartiles, PCG64 `SeedSequence([2026, 6, dataset_number])`. 98.75% Bonferroni CIs ($0.00625, 0.99375$). Nominal familywise Bonferroni control; percentile bootstrap inference is approximate. Worst eligible group is recomputed within each bootstrap replicate. Missing group bounds $[0, 0.90]$ at 90% coverage.
- **Affected Files**: `hypotheses_explanation.md`, `evaluation_plan.md`, `latex/shared/hypotheses.tex`, `latex/shared/decision_rules.tex`, `latex/hypotheses/main.tex`, `latex/paper/sections/problem_formulation.tex`, `latex/paper/sections/results.tex`, `latex/thesis/chapters/problem_hypotheses.tex`.
- **Authoritative Source & Locator**: `research/hypotheses/hypothesis_framework.yaml`, `research/decision_log.md` (ADR-018), `src/intellitwin/evaluation/decisions.py`, `src/intellitwin/evaluation/bootstrap.py`.
- **Validation Performed**: Automated check in `validate_documentation.py` verified consistency.
- **Remaining Limitations**: Test outcome classifications remain `PENDING_EXPERIMENT`.

### 9. Coverage and Scientific Claims
- **Incorrect Previous Description**: Assertions that weighting "restores exchangeability", that empirical coverage must exceed nominal coverage, or that conformal intervals guarantee safe maintenance decisions.
- **Corrected Description**: Applied standard hierarchical conformal paragraph:
  "IntelliTwin uses an engine-weighted conformal construction motivated by hierarchical conformal prediction. Formal coverage results require the hierarchical sampling and exchangeability assumptions stated in the underlying theory. Equal engine weighting does not establish these assumptions for ordered, lifetime-stratified degradation trajectories. This study therefore evaluates marginal and subgroup coverage empirically. It does not claim guaranteed coverage for each engine, lifecycle stage, operating regime, complete trajectory, or adaptively selected maintenance time. Nominal 90% coverage is a target, not a guaranteed realized coverage proportion. Maintenance outcomes are evaluated separately under the frozen simulator."
  Software described as an offline, trace-driven prognostic decision-support research prototype. Replaced broad Bayesian criticism with common protocol evaluation statement.
- **Affected Files**: `introduction_draft.md`, `methodology_draft.md`, `limitations_draft.md`, `latex/paper/sections/introduction.tex`, `latex/paper/sections/related_work.tex`, `latex/paper/sections/methodology.tex`, `latex/paper/sections/discussion.tex`, `latex/synopsis/sections/introduction.tex`, `latex/synopsis/sections/related_work.tex`, `latex/thesis/chapters/introduction.tex`, `latex/thesis/chapters/literature_review.tex`, `latex/thesis/chapters/methodology.tex`, `latex/thesis/chapters/limitations_conclusion.tex`.
- **Authoritative Source & Locator**: Authoritative prompt instructions.
- **Validation Performed**: Scanned for absence of "restores exchangeability".
- **Remaining Limitations**: Prototype status emphasized.

### 10. Tables, Reporting Manifests, and Figures
- **Incorrect Previous Description**: Broken table boundaries in `results_table_templates.md` (T3 running into T4); malformed T10 column separators; aggregate FD counts used to check tables; incomplete component templates.
- **Corrected Description**:
  - Rewrote `results_table_templates.md` repairing all tables T1–T10.
  - T2 labeled as "Development validation uncapped RMSE, mean ± SD across five frozen seeds, cycles" with committed values: FD001 GBR 28.42 ± 0.00, LSTM 29.90 ± 0.23; FD002 GBR 34.66 ± 0.00, LSTM 35.14 ± 0.23; FD004 GBR 48.83 ± 0.00, LSTM 48.67 ± 0.36.
  - Created `component_reporting_template.csv` with exactly 152 rows generated from `decisions.py` (RQ1: 14, RQ2: 20, RQ3: 22, RQ4: 96).
  - Created `evaluation_matrix_template.csv` with exactly 186 keys generated from `evidence_schema.py` (162 primary + 24 controls).
  - Created native TikZ architecture diagram (`latex/shared/figures/architecture.tex`) and causal window diagram (`latex/shared/figures/causal_window.tex`) with exact split counts (FD001 50/20/10/20, FD002 130/52/26/52, FD004 124/50/25/50).
- **Affected Files**: `results_table_templates.md`, `component_reporting_template.csv`, `evaluation_matrix_template.csv`, `figure_plan.md`, `latex/shared/figures/architecture.tex`, `latex/shared/figures/causal_window.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/evaluation/decisions.py`, `src/intellitwin/evaluation/evidence_schema.py`.
- **Validation Performed**: Verified 152 rows and 186 keys in templates; compiled TikZ figures in paper and thesis.
- **Remaining Limitations**: Numerical evaluation results remain `PENDING` until held-out execution.

### 11. References and Author Information
- **Incorrect Previous Description**: Incorrect Utility-Directed Conformal Prediction URL; identifier 7hJ2l0FwNu; missing Lee et al. revision details; blanket assignment of all contribution roles to all three authors; master's/doctoral thesis descriptions.
- **Corrected Description**:
  - Cortes-Gomez 2025: URL updated to `https://openreview.net/forum?id=iOMnn1hSBO` and proceedings URL. Removed identifier 7hJ2l0FwNu.
  - Lee 2023: Original submission year 2023 preserved; revision v4 (August 2025) identified; URL `https://arxiv.org/abs/2306.06342v4`; primaryClass `math.ST`.
  - Author contributions: Mayank Singh assigned lead developer role; individual partner attributions pending team agreement.
  - Thesis described as "Research Project Report / Thesis Draft".
- **Affected Files**: `references_verified.bib`, `reference_audit.csv`, `related_work_matrix.csv`, `author_contribution_record.md`, `latex/paper/main.tex`, `latex/thesis/main.tex`, `latex/synopsis/main.tex`.
- **Authoritative Source & Locator**: Publisher records and arXiv APIs.
- **Validation Performed**: Zero undefined citations or duplicate keys.
- **Remaining Limitations**: Final author ordering pending team agreement.

### 12. Audit Limitations and Development Handoff
- **Incorrect Previous Description**: Stating that all repository issues are resolved without recording identified audit and environment limitations.
- **Corrected Description**: Added clearly labeled Developer-Owned Audit Limitations section to `discrepancy_register.md` and `update_register.csv`:
  - `DEV-01`: `scripts/audit_step09_freeze.py::build_regression_test_report` constructs a fixed mutation-summary record. Generating that JSON is not itself execution of the mutation tests. Documentation distinguishes stored regression metadata from actual pytest execution evidence.
  - `DEV-02`: `tests/test_pretest_reference_verification.py::test_mutation_bootstrap_stat_with_consistent_contrast_fails_closed` uses 5th/95th percentiles for decision intervals. The frozen decision quantiles are 0.00625 and 0.99375. The developer correction is to construct consistent summaries using the frozen quantiles.
  - `DEV-03`: `experiments/pretest_verification_v4/supersession.json` contains a local staging path. Documentation links use committed repository paths while preserving the historical artifact.
  - `DEV-04`: Scikit-learn 1.9.1 checkpoints loaded with 1.8.0 emitted compatibility warnings in review environment. Dependency-compatible reproduction is recorded as a developer-owned release task.
- **Affected Files**: `discrepancy_register.md`, `update_register.csv`, `reproducibility_draft.md`.
- **Authoritative Source & Locator**: Pretest audit inspection and review environment logs.
- **Validation Performed**: Recorded with explicit owners and pending statuses.
- **Remaining Limitations**: Awaits developer release handoff.

---

## Acceptance Statement

Documentation corrections completed and verified; confirmatory results and final submission readiness remain dependent on the explicitly listed outstanding work.
