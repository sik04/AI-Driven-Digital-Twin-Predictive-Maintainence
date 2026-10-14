# IntelliTwin Research Documentation Correction Report

**Repository**: `https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence`  
**Base Commit**: `bb9e34579343881a831e3f052608ee15e183df76` (PR #25 Merged Main)  
**Branch**: `fix/research-documentation-consistency`  
**Date**: October 2026  
**Scope**: Documentation correction across `docs/synopsis_preparation/` to eliminate all contradictions between documentation drafts, frozen research specifications, and committed implementation code.

---

## Executive Summary

Following the integration of PR #25 (audit artifacts and pretest verification v2), a comprehensive scientific audit of the documentation package in `docs/synopsis_preparation/` identified substantive discrepancies between drafts and authoritative project specifications. Erroneous descriptions spanned data preprocessing, base model architectures, conformal calibration mathematics, maintenance simulation parameters, comparator controls, hypothesis decision thresholds, author roles, and citation keys.

This report documents the exact resolution of all identified discrepancies across 16 categories. All modifications were restricted strictly to `docs/synopsis_preparation/`. No frozen scientific protocols, checkpoints, split manifests, or implementation files were modified. All four deliverable PDFs were recompiled and visually inspected with zero compilation errors, zero missing inputs, zero unresolved citations, and zero undefined cross-references.

---

## Category-by-Category Correction Record

### 1. Branch, Workspace, and Scope
- **Incorrect Previous Description**: Working directly on older branches (`docs/synopsis-evidence-preparation`) against outdated base commit `224c741`, or mixing documentation updates with implementation file changes.
- **Corrected Description**: Dedicated branch `fix/research-documentation-consistency` created from verified `origin/main` commit `bb9e34579343881a831e3f052608ee15e183df76`. Modifications isolated strictly to `docs/synopsis_preparation/`.
- **Affected Files**: All tracking registers, `README.md`, `discrepancy_register.md`, `completion_checklist.md`.
- **Authoritative Source & Locator**: PR #25 commit `bb9e34579343881a831e3f052608ee15e183df76`; Task Scope Section 1.
- **Validation Performed**: Verified via `git status` that zero modifications exist outside `docs/synopsis_preparation/`.
- **Remaining Limitations**: None.

### 2. Required Source Files & Audit Evidence
- **Incorrect Previous Description**: Citations of outdated or nonexistent consolidated reports (e.g., `experiments/pretest_verification_v2/audit_report.json`), and conflating historical `NOT RUN` status with the current state.
- **Corrected Description**: Updated all references to point to the actual separate audit files committed in PR #25: `step08_full_audit.json`, `pretest_audit.json`, `control_reconstruction.json`, `supersession.json`, `protocol_freeze.json`, and `baseline_manifest.json`.
- **Affected Files**: `source_manifest.csv`, `update_register.csv`, `reproducibility_draft.md`, `latex/thesis/chapters/reproducibility_appendix.tex`.
- **Authoritative Source & Locator**: `experiments/pretest_verification_v2/` files at commit `bb9e345`.
- **Validation Performed**: Automated check in `validate_documentation.py` verified every local path exists in the repository.
- **Remaining Limitations**: Held-out test evaluation remains `NOT_STARTED` and `PENDING`.

### 3. Preprocessing Everywhere
- **Incorrect Previous Description**: Mention of min–max normalization, robust min–max normalization, median/IQR normalization, and claiming all 7 excluded sensors are universally constant across all datasets and regimes.
- **Corrected Description**: "Preprocessing uses training-only z-score normalization. Means and population standard deviations are estimated with ddof=0. An exactly zero standard deviation is replaced by an effective scale of 1.0, while the mean is still subtracted."
  $$x_{\text{normalized}} = \frac{x - \mu_{\text{train}}}{s_{\text{train}}}, \quad s_{\text{train}} = \begin{cases} \sigma_{\text{train}} & \text{if } \sigma_{\text{train}} > 0 \\ 1 & \text{otherwise} \end{cases}$$
  Dataset-specific details: FD001 uses global training-fitted normalization. FD002/FD004 use standardized settings to learn 6 regimes via K-Means ($k=6, \text{random\_state}=2026, n\_init=10$) with lexicographic centroid ordering, followed by regime-specific sensor normalization. Exact 17-feature selection: `setting1, setting2, setting3, s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21`. Preprocessing occurs prior to causal window construction. The 125-cycle cap is documented as a modeling convention.
- **Affected Files**: `methodology_draft.md`, `system_description.md`, `presentation_outline.md`, `latex/paper/sections/methodology.tex`, `latex/paper/sections/experimental_setup.tex`, `latex/thesis/chapters/methodology.tex`, `latex/thesis/chapters/implementation.tex`, `latex/shared/preprocessing_models.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/data/preprocessing.py:L1-L180`, `research/research_design/data_evaluation_protocol.md`.
- **Validation Performed**: Regex scanning via `validate_documentation.py` verified zero instances of forbidden normalization terms.
- **Remaining Limitations**: None.

### 4. Base Model Descriptions
- **Incorrect Previous Description**: Base models described as LightGBM or XGBoost; random subsampling claimed as reason for repeated seeds; unpruned narrative validation RMSEs mixed into method paragraphs; bidirectional or internal LSTM dropout.
- **Corrected Description**:
  - GBR: `sklearn.ensemble.HistGradientBoostingRegressor`. Input is a C-order flattened $30 \times 17$ window (510 features). Selected configs: `gbr_lr010_leaf15_l2_0` (FD001) and `gbr_lr010_leaf31_l2_0` (FD002/FD004). Repeated seeds reflect random state initialization, not subsampling.
  - LSTM: PyTorch unidirectional recurrent layer (`input_size=17`, `hidden_size=64`, `num_layers=1`, `batch_first=True`, `bidirectional=False`, `dropout=0.0`). Output takes final sequence step, applies `nn.Dropout(p=0.20)` followed by `nn.Linear(64, 1)`. Learning rate 0.001 (`lstm_h64_lr0010`).
  - Windowing & Targets: 30-cycle causal windows, stride 1, no padding, no crossing engine boundaries. Training target is $\min(\text{rul}, 125)$; inference prediction is $p = \max(0, \hat{y})$ with no upper clipping. Selection seeds (2026, 2027) distinguished from final training seeds (2026–2030).
- **Affected Files**: `methodology_draft.md`, `presentation_outline.md`, `latex/shared/preprocessing_models.tex`, `latex/paper/sections/methodology.tex`, `latex/thesis/chapters/methodology.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/models/gbr.py`, `src/intellitwin/models/lstm.py`, `research/research_design/step07_base_predictor_specification.md`, `experiments/base_models/model_registry.json`.
- **Validation Performed**: Scanned for absence of LightGBM/XGBoost as project models; checked feature and parameter specifications.
- **Remaining Limitations**: Base model training performance numbers belong in labeled results tables, not method descriptions.

### 5. Calibration Equations
- **Incorrect Previous Description**: Predicted $p$ described as sigmoid failure probability; logistic threshold transformations; $a(p)=\exp(-\beta p), b(p)=\exp(\beta p)$; ceiling-based final quantile; finite mass described as $1/(m n_i)$; fallback claimed at 100 observations.
- **Corrected Description**: Nonnegative predicted RUL $p$ in cycles.
  $$\sigma(p) = \left(1 + \frac{p}{125}\right)^\gamma, \quad z(p) = \exp\left(-\frac{p}{20}\right)$$
  $$a(p) = \sigma(p) \exp(\beta z(p)), \quad b(p) = \sigma(p) \exp(-\beta z(p))$$
  $$\text{score}(p, y) = \max\left(\frac{p - y}{a(p)}, \frac{y - p}{b(p)}, 0\right)$$
  $$L = \max(0, p - q_g a(p)), \quad U = p + q_g b(p)$$
  Where $y$ is uncapped true RUL. Grid: $\gamma \in \{0, 1, 2\}$, $\beta \in \{-\ln 2, 0, \ln 2\}$. Selected candidate: `gamma2_betam1` across all 6 cells.
  Final calibration with $m$ engines places mass $\frac{1}{(m+1)n_i}$ on each finite endpoint, total finite mass $\frac{m}{m+1}$, and remaining mass $\frac{1}{m+1}$ at $+\infty$. Quantile $q$ is smallest score whose CDF reaches $1-\alpha$; if none reaches it, $q=+\infty$.
  Regime support requires $m_g \ge \max(10, \lceil 1/\alpha \rceil - 1)$ distinct engines (10 for 80%/90%, 19 for 95%), else fallback to global threshold for the same method and $\alpha$.
  Negative $\beta$ explanation: "At fixed $p$, $q$, and $\gamma$, negative $\beta$ decreases $a$ relative to $\beta=0$ and increases $b$. The lower bound is nondecreasing and the upper bound is nondecreasing. This does not establish improved maintenance utility or earlier intervention; thresholds are fitted separately and utility must be evaluated."
- **Affected Files**: `methodology_draft.md`, `latex/shared/calibration_equations.tex`, `latex/paper/sections/methodology.tex`, `latex/synopsis/sections/methodology.tex`, `latex/thesis/chapters/methodology.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/uncertainty/calibration.py`, `src/intellitwin/uncertainty/quantiles.py`, `src/intellitwin/uncertainty/scores.py`, `research/research_design/step08_calibration_specification.md`.
- **Validation Performed**: Verified formulas in LaTeX and Markdown; validated mathematical consistency across all drafts.
- **Remaining Limitations**: None.

### 6. Maintenance and Costs
- **Incorrect Previous Description**: Invented preventive cost 10, failure cost 100, costs 50/200; two-cycle intervention delays; lead-time sensitivity grids; logistical dispatch mechanics; claiming simulated failure represents aircraft accidents.
- **Corrected Description**: Synthetic Cost Scenarios:
  - `primary_reference`: $\CPM = 1.0, \CFAIL = 5.0, \CWASTE = 0.20$ SCU
  - `failure_sensitive`: $\CPM = 1.0, \CFAIL = 10.0, \CWASTE = 0.20$ SCU
  - `waste_sensitive`: $\CPM = 1.0, \CFAIL = 5.0, \CWASTE = 0.40$ SCU
  Policy: `MAINTAIN_NOW` iff $L(t) \le 1.0$ cycle at $t \in [30, T-1]$, else `CONTINUE`. Action occurs immediately with zero lead time. Cost is $\CPM + \CWASTE(T-t)$ if maintained at $t < T$, or $\CFAIL$ if failure occurs at $T$ without prior PM ($W=0$). Offline interval evaluation includes all cycles $30 \dots T$. Break-even waste values (20, 45, 10 cycles) clarify economic equivalence, not policy thresholds.
- **Affected Files**: `methodology_draft.md`, `system_description.md`, `results_table_templates.md`, `latex/shared/simulator_costs.tex`, `latex/paper/sections/methodology.tex`, `latex/paper/sections/results.tex`, `latex/synopsis/sections/methodology.tex`, `latex/thesis/chapters/methodology.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/simulator/costs.py`, `src/intellitwin/simulator/engine.py`, `src/intellitwin/decision/policies.py`, `research/research_design/maintenance_cost_scenarios.yaml`, `research/decision_log.md` (ADR-018).
- **Validation Performed**: Scanned for absence of $C_{\text{PM}}=10, C_{\text{FAIL}}=100$, lead-time delays, or accident claims.
- **Remaining Limitations**: Evaluated strictly on simulation replay.

### 7. RQ3 Controls
- **Incorrect Previous Description**: Constant half-width intervals; fixed widening factor 1.25; safety margin 10; threshold inflation 15; Gaussian interval baseline.
- **Corrected Description**: Four pre-registered controls across three families selected on FD002 validation engines across 5 seeds jointly at 90% coverage and `primary_reference` cost:
  1. `matched_width_interval`: $L_\lambda(t) = \max(0, p(t) - \lambda q_{\text{source}}(t)), U_\lambda(t) = p(t) + \lambda q_{\text{source}}(t)$. Grid $\lambda \in \{0.01 \dots 4.00, 5, 6, 8, 12, 16\}$, required width difference $\le 1$ cycle.
  2. `widened_interval`: same formula, grid $\lambda \in \{1.00 \dots 4.00, 5, 6, 8, 12, 16\}$.
  3. `point_safety_margin`: maintain iff $p \le 1 + m, m \in \{0 \dots 250\}$. (Conformal interval metrics designated `NOT_APPLICABLE`).
  4. `earlier_intervention`: maintain iff $L_{\text{source}} \le h, h \in \{1 \dots 251\}$.
  Committed Selections from `experiments/pretest_verification_v2/controls/`:
  - GBR: matched_width (`global_hcp`, $\lambda=0.92$), widened (`regime_hcp`, $\lambda=1.00$), point ($m=5$), earlier (`regime_hcp`, $h=1$).
  - LSTM: matched_width (`regime_hcp`, $\lambda=0.90$), widened (`global_hcp`, $\lambda=1.00$), point ($m=4$), earlier (`global_hcp`, $h=1$).
- **Affected Files**: `methodology_draft.md`, `results_table_templates.md`, `latex/shared/control_definitions.tex`, `latex/paper/sections/methodology.tex`, `latex/paper/sections/results.tex`, `latex/thesis/chapters/experimental_design.tex`.
- **Authoritative Source & Locator**: `src/intellitwin/decision/controls.py`, `experiments/pretest_verification_v2/controls/FD002/GBR/selection.json`, `experiments/pretest_verification_v2/controls/FD002/LSTM/selection.json`.
- **Validation Performed**: Verified parameter values and JSON records.
- **Remaining Limitations**: Controls frozen on validation partition; held-out evaluation pending.

### 8. Hypotheses and Statistics
- **Incorrect Previous Description**: Result-table hypotheses defined as coverage $>0.90$ alone, 5% relative cost reduction, or arbitrary single contrasts; $\delta_{\text{cost}}=0.05$ or $\delta_{\text{cov}}=0$; seed standard deviations treated as inferential uncertainty.
- **Corrected Description**: Restored exact ADR-018 definitions for RQ1–RQ4:
  - RQ1: $\Delta_{\text{cost}} > 0.20$ SCU, marginal/regime/stage coverage error $<0.05$, $\Delta_{\text{fail}} \le 0.0$ against both baselines on FD002.
  - RQ2: Worst-group error $\Delta_{\text{error}} > 0.01$, worst error $<0.05$, $D_{\text{width}} < 1.0$, $D_{\text{score}} < 1.0$ cycle for regimes and stages.
  - RQ3: $\Delta_{\text{cost}} > 0.20$ SCU over every one of the 4 controls, all coverage ceilings pass, $\Delta_{\text{fail}} \le 0.0$.
  - RQ4: Balanced 6-cell aggregate ($w_k = 1/6$) $\Delta_{\text{cost, agg}} > 0.20$, $\Delta_{\text{error, agg}} > 0.01$; Cell non-harm: $\Delta_{\text{cost}} > -0.20$, $\Delta_{\text{error}} > -0.01$, and all safeguards pass.
  - Decision Logic: Intersection-Union Testing. Benefit condition passes if lower CI $>$ margin; fails if upper CI $<$ margin; otherwise inconclusive. Ceiling passes if upper CI $<$ ceiling; fails if lower CI $>$ ceiling; otherwise inconclusive. Equality is inconclusive. Degenerate intervals are inconclusive. All-pass required for Supported; any component fail makes RQ Unsupported; else Inconclusive.
  - Bootstrap Protocol: 10,000 paired engine-cluster resamples stratified by lifetime quartiles, PCG64 `SeedSequence([2026, 6, dataset_number])`. 98.75% Bonferroni CIs ($0.00625, 0.99375$). Missing group bounds $[0, 0.90]$ at 90% coverage.
- **Affected Files**: `hypotheses_explanation.md`, `evaluation_plan.md`, `latex/shared/hypotheses.tex`, `latex/shared/decision_rules.tex`, `latex/hypotheses/main.tex`, `latex/paper/sections/results.tex`, `latex/thesis/chapters/problem_hypotheses.tex`.
- **Authoritative Source & Locator**: `research/hypotheses/hypothesis_framework.yaml`, `research/decision_log.md` (ADR-018), `src/intellitwin/evaluation/decisions.py`, `src/intellitwin/evaluation/bootstrap.py`.
- **Validation Performed**: Automated check in `validate_documentation.py` verified consistency.
- **Remaining Limitations**: Test outcome classifications remain `PENDING_EXPERIMENT`.

### 9. Coverage and Scientific Claims
- **Incorrect Previous Description**: Assertions that weighting "restores exchangeability", that empirical coverage must exceed nominal coverage in every finite test set, or that the protocol "eliminates publication bias".
- **Corrected Description**:
  "Hierarchical conformal theory provides marginal predictive coverage under its stated sampling and exchangeability assumptions. IntelliTwin uses an engine-weighted construction motivated by that theory. Applicability of those assumptions to ordered, lifetime-stratified degradation trajectories is not established merely by weighting engines equally; reliability is therefore evaluated empirically under the frozen protocol."
  Software described as a research prototype. Removed claims of production readiness, aircraft certification, or exact unconditional finite-sample FWER control.
- **Affected Files**: `methodology_draft.md`, `limitations_draft.md`, `latex/paper/sections/discussion.tex`, `latex/thesis/chapters/limitations_conclusion.tex`.
- **Authoritative Source & Locator**: Prompt Section 9; `research/decision_log.md`.
- **Validation Performed**: Scanned for absence of "restores exchangeability".
- **Remaining Limitations**: Prototype status emphasized.

### 10. Tables, Figures, and Shared Document Structure
- **Incorrect Previous Description**: Incomplete result tables omitting cells; using 0 instead of `NOT_APPLICABLE` for point policies; figure central points defined as bootstrap medians.
- **Corrected Description**:
  - Primary Interval Table: Complete $3 \times 2 \times 3 = 18$ rows across FD001, FD002, FD004, GBR/LSTM, and 3 calibration methods.
  - Primary Maintenance Table: Complete 26 rows (18 main method rows + 8 control rows on FD002).
  - Point policies explicitly assigned `NOT_APPLICABLE` for undefined interval metrics.
  - Figure F6 central point marker specified as the observed paired contrast from evaluation output.
  - Modular shared LaTeX fragments created in `latex/shared/`: `preprocessing_models.tex`, `calibration_equations.tex`, `simulator_costs.tex`, `control_definitions.tex`, `decision_rules.tex`.
  - Hypotheses appendix formatted as a derived reference rendering of the authoritative YAML.
- **Affected Files**: `results_table_templates.md`, `figure_plan.md`, `latex/shared/*.tex`, `latex/paper/sections/results.tex`, `latex/thesis/chapters/results_discussion.tex`, `latex/hypotheses/main.tex`.
- **Authoritative Source & Locator**: Prompt Section 10; `research/research_design/step09_confirmatory_protocol.md`.
- **Validation Performed**: Automated check confirmed row counts, `NOT_APPLICABLE` usage, and shared fragment inclusions.
- **Remaining Limitations**: Numerical values remain `PENDING` until held-out execution.

### 11. References and Author Information
- **Incorrect Previous Description**: Missing citation keys (`zheng2017long`, `vovk2005algorithmic`, `angelopoulos2021gentle`); invented author roles (Ruchi Gupta as supervisor, Shiksha Pandey as methodology lead).
- **Corrected Description**:
  - Removed unsupported historical sentences and unresolved citation keys.
  - Verified existing references: Javanmardi & Hüllermeier (2023) for RUL conformal prediction; Lee et al. (2023) for hierarchical conformal inference.
  - Retained all three author names (Mayank Singh, Shiksha Pandey, Ruchi Gupta) with neutral pending affiliations and contact information. Noted that final author order and contribution allocation require mutual agreement.
- **Affected Files**: `references_verified.bib`, `author_contribution_record.md`, `latex/paper/main.tex`, `latex/thesis/main.tex`, `latex/synopsis/main.tex`.
- **Authoritative Source & Locator**: Prompt Section 11; `research/author_contributions.md`.
- **Validation Performed**: Automated check in `validate_documentation.py` verified zero undefined citations and no duplicate keys.
- **Remaining Limitations**: Final author ordering pending team agreement.

### 12. Audit Status from Merged PR #25
- **Incorrect Previous Description**: Citing outdated `NOT RUN` reports from Step 8 repair verification; referencing nonexistent `audit_report.json`.
- **Corrected Description**:
  Incorporated committed findings from PR #25 (`bb9e345`):
  - `step08_full_audit.json`: all mandatory checks run; 60 model/partition reproductions on `validation` and `calibration` partitions with maximum prediction difference 0.0.
  - `pretest_audit.json`: PASS and PRETEST_READY.
  - `baseline_manifest.json`: 652 tracked protected artifacts, 72 historical local search checkpoints.
  - `held_out_execution_status`: NOT_STARTED; `rq_outcomes_status`: PENDING.
- **Affected Files**: `README.md`, `completion_checklist.md`, `discrepancy_register.md`, `claims_evidence_matrix.csv`, `update_register.csv`, `reproducibility_draft.md`, `latex/synopsis/sections/status_results.tex`, `latex/thesis/chapters/reproducibility_appendix.tex`.
- **Authoritative Source & Locator**: `experiments/pretest_verification_v2/` at commit `bb9e345`.
- **Validation Performed**: Verified existence and committed status of all audit artifacts.
- **Remaining Limitations**: Verification performed on validation/calibration partitions; test partition remains unexecuted.

### 13. Reproducibility Instructions
- **Incorrect Previous Description**: LightGBM listed as dependency; nonexistent script `scripts/audit_step07_models.py`; claims of universal Python $\ge 3.10$ testing; claims of recording CPU model, memory, or PRNG state not actually emitted.
- **Corrected Description**:
  - Declared research dependencies from `pyproject.toml`: `numpy>=1.24.0`, `pandas>=2.0.0`, `scikit-learn>=1.2.0`, `torch>=2.2`, `PyYAML>=6,<7`. Removed LightGBM.
  - Corrected script path to `scripts/audit_step07_base_models.py`.
  - Accurately described fields emitted by `src/intellitwin/provenance.py` (`ExecutionEnvironment`).
- **Affected Files**: `reproducibility_draft.md`, `latex/thesis/chapters/reproducibility_appendix.tex`.
- **Authoritative Source & Locator**: `pyproject.toml`, `src/intellitwin/provenance.py`, `scripts/audit_step07_base_models.py`.
- **Validation Performed**: Verified script path and dependency specifications.
- **Remaining Limitations**: Platform verification limited to recorded environments.

### 14. Documentation Correction and Validation Records
- **Incorrect Previous Description**: Absence of unified correction log and automated validation script.
- **Corrected Description**: Created `documentation_correction_report.md` (this file), `documentation_validation.json`, and automated validation script `validate_documentation.py`.
- **Affected Files**: `docs/synopsis_preparation/documentation_correction_report.md`, `docs/synopsis_preparation/documentation_validation.json`, `docs/synopsis_preparation/validate_documentation.py`.
- **Authoritative Source & Locator**: Prompt Section 14.
- **Validation Performed**: Executed `python docs/synopsis_preparation/validate_documentation.py` with exit code 0 (`ALL CHECKS PASSED`).
- **Remaining Limitations**: None.

### 15. Rebuild and PDF Inspection
- **Incorrect Previous Description**: Older pre-compiled PDFs in `previews/` containing outdated formulas, incorrect tables, or uninspected layouts.
- **Corrected Description**: Recompiled all four documents with Tectonic engine (exit code 0):
  - `hypotheses_appendix.pdf`: 5 pages (Standalone reference)
  - `synopsis_draft.pdf`: 4 pages (IEEE conference format)
  - `ieee_paper_draft.pdf`: 9 pages (IEEEtran two-column format, full 18-row and 26-row tables)
  - `thesis_draft.pdf`: 50 pages (Report format, complete chapters and appendices)
  Inspected text across all 68 pages: zero unresolved references (`??`), zero unresolved citations (`[?]`), zero missing glyphs.
- **Affected Files**: `docs/synopsis_preparation/previews/*.pdf`.
- **Authoritative Source & Locator**: Prompt Section 15.
- **Validation Performed**: Python PDF inspection via `pypdf` confirmed zero unresolved tokens.
- **Remaining Limitations**: Empirical test numbers remain pending held-out execution.

### 16. PR, Review, and Handoff
- **Incorrect Previous Description**: Outdated PR draft summaries with conflicting statements.
- **Corrected Description**: Prepared complete commit, pull request, and verification record.
- **Affected Files**: Git repository tracking.
- **Authoritative Source & Locator**: Prompt Section 16.
- **Validation Performed**: Pre-commit diff inspection confirmed 100% changes isolated to `docs/synopsis_preparation/`.
- **Remaining Limitations**: Final merge subject to branch protection rules.

---

## Acceptance Statement

All identified documentation defects in this correction scope were resolved and checked against the recorded sources. Final empirical conclusions remain pending held-out evaluation.
