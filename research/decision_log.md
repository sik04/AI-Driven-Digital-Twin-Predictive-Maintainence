# Architectural and Research Decision Log

This log documents formal architectural, methodological, and research governance decisions made throughout the IntelliTwin project. Every significant decision must be recorded with its context, alternatives, rationale, and implications.

---

## Decision Record Template

```markdown
### ADR-XXX: [Title of Decision]
- **Date**: YYYY-MM-DD
- **Status**: [Proposed | Accepted | Superseded | Deprecated]
- **Authors Responsible**: [Mayank Singh / Shiksha Pandey / Ruchi Gupta]
- **Context and Motivation**:
  - What problem or challenge is being addressed?
  - Why is a decision required at this point?
- **Alternatives Considered**:
  1. *Alternative A*: Description, pros, and cons.
  2. *Alternative B*: Description, pros, and cons.
- **Evidence Reviewed**:
  - Citations, benchmark data, or empirical findings examined.
- **Decision Rationale**:
  - Why was the chosen approach selected over alternatives?
- **Expected Implications**:
  - Impact on architecture, experimental protocol, dependencies, and timeline.
- **Follow-up Review Date / Trigger**:
  - When or under what condition should this decision be re-evaluated?
```

---

## Logged Decisions

### ADR-001: Clean Repository Reset to Establish Research-First Foundation
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - The repository previously contained unverified model artifacts, ad-hoc scripts, and mixed frontend code without a standardized experimental evaluation protocol, formal test suites, or research governance documentation.
  - Scientific validity and peer-reviewed publication standards require that all experimental claims be built from a clean, verifiable, and reproducible foundation.
- **Alternatives Considered**:
  1. *Incremental refactoring of existing codebase*: Would preserve legacy uncalibrated weights and untracked scripts, introducing risk of unverified assumptions lingering into experimental phases.
  2. *Clean reset from scratch within the existing Git repository with full historical backup*: Preserves complete repository history, protects all prior commits and PDFs, but establishes a clean working directory and standardized Python packaging layout.
- **Evidence Reviewed**:
  - Guidelines from ACM/IEEE reproducibility standards, ICML/NeurIPS reproducibility checklists, and PEP 517/621 packaging guidelines.
- **Decision Rationale**:
  - Starting from a clean working directory with modern packaging (`pyproject.toml`), comprehensive testing (`pytest`), strict typing (`mypy`), and linter enforcement (`ruff`) eliminates legacy technical debt and guarantees that all subsequent research findings are fully traceable.
  - Prior work was fully archived into `../intellitwin_pre_reset_backup_9b72fac.zip` and remains accessible via Git history.
- **Expected Implications**:
  - All subsequent models, preprocessing scripts, and tests will be developed incrementally on feature branches following the roadmap.
  - Literature review will proceed systematically in Phase 1 before any model training code is written.
- **Follow-up Review Date / Trigger**:
  - At the completion of Phase 0 / commencement of Phase 1.

---

### ADR-002: Adoption of Conditional RUL Reliability and Downstream Decision Consequences as Primary Research Direction
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Phase 1 literature review revealed that broad research topics such as general AI + Digital Twin + predictive maintenance, baseline C-MAPSS RUL point prediction, and aggregate split conformal prediction intervals are already well-established.
  - Asserting novelty on broad claims would be scientifically unsupportable and easily rejected during peer review.
  - A refined, evidence-backed candidate research gap was needed to ground Phase 2 hypothesis testing.
- **Alternatives Considered**:
  1. *Broad Novelty Claim (AI + Digital Twin + RUL)*: Rejected. Extensive prior literature (e.g., Huang et al. 2021, Wu et al. 2026, Hasan & Crawford 2025) fully covers point-prediction RUL in Digital Twin architectures.
  2. *Standard Conformal Prediction Interval Claim*: Rejected. Diao et al. (2026) and Javanmardi & Hüllermeier (2023) have already applied split conformal prediction to C-MAPSS.
  3. *Conditional Reliability & Downstream Maintenance Impact (Selected Approach)*: Adopted. Investigating whether nominally calibrated prediction intervals fail conditionally across degradation stages and operating regimes, and quantifying how such failures impact downstream maintenance decisions (e.g., late failure penalties vs. premature maintenance waste).
- **Evidence Reviewed**:
  - Phase 1 evidence matrix (`research/literature/literature_matrix.csv`), closest work matrix (`research/literature/closest_work_matrix.csv`), and literature synthesis (`research/literature/literature_synthesis.md`).
- **Decision Rationale**:
  - This targeted direction addresses a genuine, underexplored scientific limitation without making sweeping, unsupported novelty claims.
  - It establishes a rigorous framework for pre-specifying hypotheses ($H_{0,1}$ / $H_{1,1}$), metrics ($PICP_g$, $CE_g$, $WGC$, $MCG$), target leakage constraints, and falsification criteria before conducting experiments.
- **Expected Implications**:
  - Experimental design in Phase 3–7 will focus on auditing conditional coverage gaps ($PICP_g$) across degradation stages and operating regimes, and quantifying operational decision costs.
  - Models and calibration modules must satisfy strict target leakage constraints (no true RUL used at inference time).
- **Follow-up Review Date / Trigger**:
  - Completion of Phase 7 (Uncertainty and Maintenance Decision Experiments) or if Outcome C (no meaningful conditional failure) is observed in Phase 7.

---

### ADR-003: Experiment A Protocol Specification — Datasets, Model Families, and High-Level Calibration Strategy
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - RQ1 requires a concrete, pre-specified experimental protocol (Experiment A) to test whether nominally calibrated RUL prediction intervals conceal conditional reliability failures.
  - Pre-defining dataset scope, model families, and audit axes prevents post-hoc selection bias.
- **Alternatives Considered**:
  1. *Single Dataset Audit (FD001 only)*: Rejected. FD001 lacks operating-regime shifts, making it incapable of auditing regime-conditional undercoverage.
  2. *Full 4-Dataset Benchmark in Experiment A*: Rejected. Combining all 4 datasets in Experiment A increases protocol complexity unnecessarily. FD003/FD004 are better suited for downstream robustness testing in Experiment D.
  3. *Single Neural Model Family*: Rejected. Evaluating only a single model architecture leaves findings vulnerable to criticisms of architecture-specific bias.
- **Decisions**:
  - **Datasets**: C-MAPSS FD002 selected as the **primary dataset** (multi-regime); C-MAPSS FD001 selected as the **control dataset** (single-condition). FD003 and FD004 are deferred to Experiment D.
  - **Base Models**: Gradient Boosting Regressor (**GBR**) and Long Short-Term Memory Network (**LSTM**) selected as base predictor families.
  - **High-Level Calibration**: **Global conformal calibration** selected at a high conceptual level.
  - **Audit Axes**: **Operating regime** selected as the primary audit axis (derived from setting variables); **degradation stage** selected as a secondary post-hoc scientific audit.
- **Decision Rationale**:
  - FD002 directly exposes multi-regime operational shifts; FD001 provides a clean single-condition baseline.
  - Combining GBR (tree-based) and LSTM (recurrent temporal) ensures findings are not artifacts of a single model type.
  - Global calibration must be established first to test whether aggregate validity hides local subgroup failure.
- **Deferred Decisions**:
  - Exact conformal prediction variant (standard split vs. normalized vs. CQR)
  - Exact nonconformity score definition
  - Calibration split fraction
  - Exact degradation-stage boundary cutoffs
  - Exact operating-regime identification algorithm
  - Exact statistical test package
---

### ADR-005: Systematic Reassessment of Research Gap and Literature Evidence Base Following Source Audit
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - A thorough source audit of external literature entries revealed inaccuracies in bibliographic metadata, unverified methodological details, and omitted closest-work comparators in earlier tracking files.
  - Correcting these entries against verified publisher records, arXiv, Zenodo, IJPHM, and MDPI established that prior literature already includes conformal RUL prediction, life-stage and operating-regime diagnostics, and maintenance-related evaluation.
- **Alternatives Considered**:
  1. *Proceeding with pre-specified gap and novelty claims unchanged*: Rejected. Maintaining claims of novelty after discovering prior art would violate scientific integrity.
  2. *Reassessing evidence status while preserving locked v1 research questions*: Accepted. Setting evidence status to "Under reassessment", updating source verification registers, and preserving v1 hypothesis structures ensures systematic, honest evaluation without prematurely jumping to v2 before experiment execution.
- **Evidence Reviewed**:
  - Verified source audit of 26 bibliographic references in `paper/references.bib`, `research/literature/source_verification.csv`, `research/literature/evidence_corrections.md`, and updated `closest_work_matrix.csv`.
- **Decision Rationale**:
  - Source corrections invalidate the prior claim that conditional calibration plus maintenance decisions is a novel, unstudied gap. Reassessing the gap before conducting experiments preserves scientific integrity.
- **Expected Implications**:
  - `CLM-05` status changed to "Under reassessment" in `paper/claims_evidence_matrix.csv`.
  - Evidence status note added to `README.md`, `research/research_design/research_gap.md`, and `research/research_questions.md`.
  - Literature tracking files, metric interpretations, and source verification registers updated to exact verified facts.
- **Follow-up Review Date / Trigger**:
  - Prior to initiating Phase 5/6 model development or Phase 7 experiments.

---

### ADR-006: Final Research Problem Formulation — Measuring Decision Value of Condition-Aware Calibration
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Following the literature source corrections and closest-work audit, the research direction was refined to focus on evaluating whether condition-aware calibration provides measurable maintenance-decision value beyond global calibration and simple conservative point-prediction policies under identical experimental controls.
- **Alternatives Considered**:
  1. *Framing novelty on detecting conditional miscalibration alone*: Rejected. Literature shows conditional calibration has been audited in bearings and turbofans.
  2. *Refining research problem to decision-value comparison*: Adopted. Centers the research problem on whether condition-aware calibration provides measurable maintenance-decision value beyond global calibration and simple conservative point-prediction policies, when compared under the same predictor, data protocol, and sequential maintenance setting.
- **Evidence Reviewed**:
  - Synthesized evidence across closest works in `research/literature/closest_work_matrix.csv` and `research/literature/literature_synthesis.md`.
- **Decision Rationale**:
  - Establishes a clear, controlled comparative scientific framework evaluating decision utility across point, global, and condition-aware calibration baselines under identical predictor and data protocol controls.
- **Expected Implications**:
  - Research problem statement updated consistently across `research/research_design/research_gap.md`, `research/research_questions.md`, `README.md`, and `paper/claims_evidence_matrix.csv`.
  - Hypotheses, RQs, and experimental protocols remain locked.
- **Follow-up Review Date / Trigger**:
  - At the conclusion of Phase 2 final synthesis.

---

### ADR-007: Shift of Primary Contribution to Decision-Aware Condition-Adaptive Conformal Calibration Method
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - A systematic audit of closest-work literature demonstrated that conditional RUL reliability analysis, regime/condition-aware conformal calibration, and uncertainty-aware maintenance decision support already exist separately or in partial combinations.
  - Asserting novelty solely on detecting conditional miscalibration or showing marginal coverage masks subgroup failure is scientifically unsupportable.
  - The strongest remaining research opportunity is the controlled method-level integration of condition-aware conformal calibration with downstream sequential maintenance utility while preserving subgroup coverage reliability.
- **Alternatives Considered**:
  1. *Claiming novelty on conditional-miscalibration detection alone*: Rejected. Subgroup coverage diagnostics have been studied in bearing prognostics (Yang et al. 2026) and turbofan life stages (Diao et al. 2026).
  2. *Shifting primary contribution to method-level integration (Selected Approach)*: Adopted. Target a decision-aware, condition-adaptive conformal calibration method for RUL prediction that explicitly incorporates sequential maintenance utility while preserving reliable conditional uncertainty coverage.
- **Evidence Reviewed**:
  - Closest-work comparison matrix (`research/literature/closest_work_matrix.csv`), contribution statement (`research/research_design/contribution_statement.md`), and updated literature synthesis.
- **Governance Declarations**:
  - Previous research questions and hypotheses were revised prior to confirmatory model development, training, or experiments.
  - No final experimental results were used to choose the new research direction.
  - The change resulted strictly from systematic closest-work and literature reassessment.
  - Novelty is treated as a cautious, evidence-based claim dependent on closest-work audit completeness, rather than an absolute fact.
- **Expected Implications**:
  - Research questions RQ1–RQ4 and hypotheses $H_{0,1}$–$H_{1,4}$ updated to reflect proposed method evaluation, subgroup reliability, decision-value attribution against matched-conservatism baselines, and multi-setting robustness.
  - Hypothesis framework registry updated in `research/hypotheses/hypothesis_framework.yaml` and `research/hypotheses/hypothesis_framework.tex`.
  - Contribution statement created in `research/research_design/contribution_statement.md`.
- **Follow-up Review Date / Trigger**:
  - At Phase 2 completion milestone.

---

### ADR-008: Establishment of Governance Rule for Hypothesis Success Criteria and Removal of Arbitrary Fixed Thresholds
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Earlier provisional hypothesis formulations included fixed numerical thresholds (e.g., 5%, 10%, 15%, 75%) as practical effect criteria.
  - Pre-specification alone does not make an arbitrary threshold scientifically valid. Fixed numerical thresholds without empirical or operational grounding introduce arbitrary bias into hypothesis evaluation.
- **Alternatives Considered**:
  1. *Retaining fixed numerical thresholds (5%, 10%, 15%, 75%)*: Rejected. Lacks engineering, operational, or statistical justification for turbofan sequential maintenance utility.
  2. *Establishing a Success-Criteria Governance Rule (Selected Approach)*: Adopted. Discard fixed numerical thresholds until independently justified, and establish a governance rule requiring pre-specified primary metrics, comparators, practical effect thresholds, and statistical uncertainty rules for each RQ prior to confirmatory testing.
- **Evidence Reviewed**:
  - Governance standards on pre-specified hypothesis testing, effect-size justification in industrial PHM, and statistical decision theory.
- **Decision Rationale**:
  - Pre-specifying a rule structure (primary metric, comparator, practical effect threshold, statistical uncertainty rule, supported/unsupported/inconclusive outcomes) ensures scientific rigor while preventing arbitrary threshold selection.
- **Governance Declarations**:
  - No final experimental results have been inspected.
  - Replacement criteria and numerical thresholds will be fixed prior to confirmatory experiments during Phase 3–4 protocol definition.
  - Each RQ must ultimately have:
    1. Primary metric
    2. Comparator
    3. Practical effect threshold
    4. Uncertainty / statistical rule
    5. Supported outcome rule
    6. Unsupported outcome rule
    7. Inconclusive outcome rule
- **Expected Implications**:
  - Obsolete fixed thresholds removed from active research documentation (`hypothesis_framework.yaml`, `hypothesis_framework.tex`, `research_questions.md`, `experiment_map.md`, `experiment_a_design.md`).
  - Success criteria sections created in `hypothesis_framework.yaml` with TBD placeholders to be populated in Phase 3–4.
- **Follow-up Review Date / Trigger**:
  - Phase 3–4 experimental protocol finalization prior to model training.

---

### ADR-009: Locking Primary Metrics and Comparators for RQ1–RQ4 and Formalizing Practical-Effect Threshold Deferral Policy
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - ADR-008 established a governance rule requiring pre-specified primary metrics, comparators, and effect thresholds for each RQ.
  - Step 3 requires locking the primary decision metrics and planned comparators for RQ1–RQ4, while explicitly formalizing the governance policy for numerical practical-effect thresholds.
- **Decision**:
  - **Locked Primary Metrics**:
    - **RQ1**: Total simulated maintenance cost per engine (supporting: late/failure intervention rate, required coverage).
    - **RQ2**: Worst-group conditional coverage error (supporting: MPIW, interval score).
    - **RQ3**: Maintenance cost/utility improvement over the matched-conservatism baseline (supporting: wasted RUL, premature intervention rate).
    - **RQ4**: Cross-configuration consistency of the observed effect (supporting: effect size, engine-level confidence intervals).
  - **Locked Comparators**:
    - **RQ1**: Proposed method vs. global conformal calibration and standard condition-aware calibration under identical predictors and data protocols.
    - **RQ2**: Proposed method vs. global conformal calibration and standard condition-aware calibration on conditional coverage, worst-group reliability, width, and quality.
    - **RQ3**: Proposed method vs. matched-conservatism controls (widened prediction intervals, tuned point-prediction safety margins, earlier-intervention policies).
    - **RQ4**: Proposed-vs-baseline performance consistency across predefined datasets/operating conditions, base RUL model families, and random seeds.
  - **Threshold Deferral Policy**: Numerical practical-effect thresholds remain deliberately deferred until after maintenance simulator implementation and validation.
- **Rationale for Threshold Deferral**:
  - "Numerical effect thresholds cannot yet be defensibly tied to operational significance because the maintenance simulator and its cost/risk scale have not been validated. Choosing percentages now would be arbitrary."
- **Governance Declarations**:
  - Maintenance simulator validation must occur before numerical thresholds are finalized.
  - Bounded pilot evidence may be used to estimate realistic variability or operational effect scales.
  - All final numerical thresholds must be justified and frozen prior to confirmatory testing.
  - Final confirmatory test results cannot be used post-hoc to revise thresholds.
- **Expected Implications**:
  - Primary metrics and comparators locked in `hypothesis_framework.yaml`, `hypothesis_framework.tex`, `research_questions.md`, `experiment_map.md`, and `evaluation_criteria.md`.
  - Future methodology and experimental protocol phases will freeze exact numerical effect thresholds following maintenance simulator implementation and validation in the later simulator stage of the governing research workflow (Step 6), with bounded pilot evidence used if needed, prior to confirmatory model training.
- **Follow-up Review Date / Trigger**:
  - Maintenance simulator validation milestone in Step 6.

---

### ADR-010: Final Step 3 Evaluation Hierarchy and Confirmatory Governance
- **Date**: 2026-10-04
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Following the locking of primary metrics, comparators, and threshold deferral policy (ADR-009), the remaining Step 3 evaluation governance rules must be formalized to prevent post-hoc changes and bias during confirmatory testing.
- **Decision**:
  - Locked the primary vs. secondary outcome hierarchy for RQ1–RQ4: primary outcome determines main RQ conclusion; supporting outcomes provide reliability/constraint evidence and trade-off characterization. A favorable secondary outcome cannot replace failure on the primary outcome.
  - Locked the No Post-Hoc Criteria Changes rule: after protocol freezing, primary metrics, comparators, subgroup definitions, effect thresholds, decision rules, and outcome hierarchy must not be changed based on confirmatory results. Any later change must be explicitly documented as a protocol deviation and affected analyses labelled exploratory.
  - Locked threshold-governance status: non-restoration of legacy 5%, 10%, 15%, and 75% values as default success thresholds; exact numerical practical-effect thresholds remain intentionally deferred until maintenance-simulator validation and (if needed) bounded pilot evidence, and must be frozen before confirmatory testing.
  - Established the Final Pre-Specified Evaluation Map for RQ1–RQ4 mapping RQ $\rightarrow$ primary metric $\rightarrow$ supporting metrics $\rightarrow$ comparators $\rightarrow$ threshold status $\rightarrow$ statistical unit (`engine`) $\rightarrow$ statistical framework $\rightarrow$ Supported / Unsupported / Inconclusive decision rules.
- **Decision Rationale**:
  - Pre-specifying the complete evaluation hierarchy before confirmatory testing prevents outcome switching, comparator cherry-picking, subgroup redefinition, and threshold adjustment after results are observed.
  - Numerical practical-effect thresholds remain deliberately deferred because meaningful operational scales depend on the validated maintenance simulator and, if required, bounded pilot evidence.
  - Once those numerical values are finalized, they must be frozen before confirmatory experiments.
- **Expected Implications**:
  - Complete evaluation governance and final pre-specified evaluation map documented across `research/research_design/evaluation_criteria.md`, `research/hypotheses/hypothesis_framework.yaml`, `research/hypotheses/hypothesis_framework.tex`, `research/research_questions.md`, and `research/research_design/experiment_map.md`.
  - The later simulator stage of the governing research workflow (Step 6) will implement and validate the maintenance simulator and freeze final numerical practical-effect thresholds prior to confirmatory testing.
- **Follow-up Review Date / Trigger**:
  - Completion of maintenance simulator validation in Step 6 prior to confirmatory model training.

---

### ADR-011: Step 4 Dataset Qualification, Dataset Roles, Input Leakage Rules, and Engine-Level Split Governance
- **Date**: 2026-10-05
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Following the locking of evaluation criteria in Step 3, Step 4 requires formal qualification of the benchmark datasets, definition of dataset roles, strict input and target leakage governance, standardized regime clustering rules, RQ2 subgroup scope definitions, and establishment of a reproducible engine-level partition split.
- **Decisions**:
  - **Dataset Roles Locked**:
    - **FD002**: Primary dataset (6 operating regimes, 1 fault mode; multi-regime condition adaptation testbed; Qualification = **PASS**).
    - **FD001**: Control dataset (1 operating condition, 1 fault mode; single-condition baseline; Qualification = **PASS**).
    - **FD004**: Required robustness dataset (6 operating regimes, 2 fault modes; reserved for RQ4 robustness evaluation; Qualification = **PASS**).
    - **FD003**: Optional exploratory extension (1 operating condition, 2 fault modes; secondary exploratory dataset; Qualification = **PASS**).
  - **FD002 Regime Identification Rule**: Operating conditions must be derived ONLY from operating settings (`setting1`–`setting3`) using a training-engine-only scaler and K-means with $k=6$. Scaler parameters and cluster centers are frozen after training fit; non-training cycles are assigned to nearest frozen centers without refitting. True RUL, sensors, degradation stages, and maintenance outcomes must NEVER be used to define regimes.
  - **RQ2 Subgroup Scope & Worst-Group Analysis**: RQ2 evaluates conditional reliability across two primary subgroup families: (1) Operating-condition groups (C1–C6) and (2) Degradation-stage groups (boundaries deferred to Step 5). True RUL is used for degradation stages post-hoc only. Worst-group reliability considers predefined eligible groups from these families. Regime $\times$ degradation stage intersections are secondary diagnostic analysis only.
  - **Input & Target Leakage Rules**: Predictive features restricted to operating settings (`setting1`–`setting3`) and sensors (`s1`–`s21`). `unit` (engine ID) is an identifier only. Preprocessing parameters must be fit on train engines ONLY. Ground-truth RUL is strictly prohibited as an inference feature, calibrator condition variable, or maintenance policy input.
  - **Engine-Level Partition Breakdown**: The unit of independence is the **ENGINE**. 260 FD002 engines split 50%/20%/10%/20%: Train = 130 engines, Calibration = 52 engines, Validation = 26 engines, Held-out Test = 52 engines.
  - **Reproducible Split**: Generated using seed `2026` via engine-lifetime quartile stratification to prevent lifetime bias. 100% disjoint engine isolation and 6/6 regime representation verified across all partitions. Split manifest saved to `data/splits/fd002_engine_split_seed_2026.json`.
  - **FD004 Fault-Mode Claim Boundary**: FD004 evaluates robustness under a complex mixed-fault setting. Fault-mode-specific claims are strictly prohibited without defensible per-cycle labels. Actual parsed file counts (249 train / 248 test engines) are documented as executable source of truth over README metadata.
  - **Sequential Maintenance Boundary**: NASA official test trajectories are truncated prior to failure; sequential maintenance evaluation uses held-out run-to-failure training engines. Claims refer to simulated sequential maintenance utility under a cost model. Step 6 maintenance simulator was not implemented in Step 4.
  - **Step 4 Completion Status**: **COMPLETE** (Passed full 26-item dataset and split completion audit).
- **Expected Implications**:
  - All subsequent data pipelines, model training, and conformal calibration will consume the reproducible manifest `data/splits/fd002_engine_split_seed_2026.json`.
  - Detailed dataset specification documented in `research/research_design/dataset_qualification.md`.
- **Follow-up Review Date / Trigger**:
  - Step 5 Data & Evaluation Protocol definition.

---

### ADR-012: Step 5 RUL Target Construction
- **Date**: 2026-10-06
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Following the dataset qualification and engine-level split governance established in Step 4 (ADR-011), Step 5.1 requires locking the mathematical formulation and usage governance for Remaining Useful Life (RUL) prediction targets.
  - Standardizing the RUL target is essential for supervised model training while preventing target leakage and ensuring that downstream scientific evaluation uses true, uncapped remaining operational lifetimes.
- **Decisions**:
  - **Capped Piecewise-Linear Training Target**: For supervised training of base RUL predictors, the target is defined as $\text{RUL}_{\text{target}}(i, t) = \min(\text{RUL}_{\text{true}}(i, t), 125)$, enforcing a fixed upper cap of 125 cycles.
  - **Fixed Cap Rule**: The RUL cap value of 125 cycles is strictly locked. It must NOT be tuned, optimized, or made configurable based on validation or test set performance.
  - **Uncapped Ground-Truth Retention**: The uncapped actual remaining cycles until failure, $\text{RUL}_{\text{true}}(i, t) = T_{\text{failure}}(i) - t$, is retained separately. `rul_true` must be used for final scientific evaluation, post-hoc error metrics, degradation-stage labeling, wasted RUL calculations, and downstream maintenance simulator consequence evaluation.
  - **Target Non-Interchangeability**: `rul_target` and `rul_true` are strictly non-interchangeable. Model training consumes `rul_target`, whereas evaluation and maintenance decision consequences consume `rul_true`.
  - **Model Output Interpretation**: Early-life predictions may saturate near the 125-cycle cap. `rul_target` must never be reported as an engine's actual remaining life, and wasted useful life must never be calculated from `rul_target`.
  - **Inference-Time Input Leakage Restrictions**: Neither `rul_true`, `rul_target`, final failure cycle $T_{\text{failure}}(i)$, nor future-cycle data may be used as predictive model inputs, calibrator condition variables, operating condition features, or maintenance policy inputs at inference time.
  - **Scope Limitation**: No other Step 5 preprocessing decisions (sensor selection, normalization, sequence windowing, degradation stage boundaries, subgroup eligibility thresholds, conformal coverage levels, or model architectures) are locked by this ADR; all remain unresolved for subsequent Step 5 sub-steps.
- **Expected Implications**:
  - Data preprocessing specifications documented in `research/research_design/data_evaluation_protocol.md`.
  - All future RUL predictor training pipelines will generate `rul_target` as the training label while retaining `rul_true` for post-hoc evaluation.
- **Follow-up Review Date / Trigger**:
  - Step 5.2 Sensor and Input Policy definition.

---

### ADR-013: Final Predictive Input Schema and Training-Only Normalization Protocol
- **Date**: 2026-10-06
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Following the locked RUL target construction (ADR-012) and the training-only FD002 sensor diagnostic (`research/research_design/fd002_training_sensor_diagnostic.csv`), Step 5.2B and Step 5.3 require locking the final predictive input feature schema, sensor exclusion policies, and strict training-only feature normalization rules across all benchmark datasets.
  - Locking feature definitions and normalization protocols prior to sequence windowing and model training is essential to prevent feature cherry-picking, target leakage, and test-set data contamination.
- **Decisions**:
  1. **Engine ID Excluded**: `unit` is an identifier for partition assignment, trajectory grouping, and unit-of-independence statistical evaluation; it is strictly excluded from predictive model inputs.
  2. **Cycle Excluded**: `cycle` is used for temporal ordering, window construction, label calculation, and trajectory indexing; it is strictly excluded from predictive model inputs to force predictors to learn health status from sensor telemetry rather than operational age shortcuts.
  3. **Operating Settings Retained**: All three operating settings (`setting1`, `setting2`, `setting3`) are retained as predictive model inputs and remain the ONLY variables used for operating regime identification.
  4. **Final Retained Sensor Set**: Exactly 14 sensors are locked as predictive inputs: `s2`, `s3`, `s4`, `s7`, `s8`, `s9`, `s11`, `s12`, `s13`, `s14`, `s15`, `s17`, `s20`, `s21`.
  5. **Final Excluded Sensor Set**: Exactly 7 sensors are locked as excluded: `s1`, `s5`, `s6`, `s10`, `s16`, `s18`, `s19`. Exclusion is supported by empirical evidence in `fd002_training_sensor_diagnostic.csv` showing zero (`s1`, `s5`, `s18`, `s19`), near-zero (`s6`, `s10`), or near-constant (`s16`) within-regime variation.
  6. **Common Sensor Schema**: The identical 14-sensor schema is enforced across FD001 (control), FD002 (primary), and FD004 (robustness) to prevent dataset-specific feature selection bias.
  7. **Canonical Per-Cycle Predictive Vector**: Each operational cycle is represented by a 17-dimensional feature vector ($3 \text{ settings} + 14 \text{ sensors}$) in canonical order: `["setting1", "setting2", "setting3", "s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]`.
  8. **FD002 Setting Normalization**: `setting1`–`setting3` are globally standardized using a single `StandardScaler` fit on the 130 FD002 training engines only.
  9. **Unified Setting Scaler**: The same frozen training-derived setting scaler is used for both K-means operating regime identification ($k=6$) and predictor setting inputs.
  10. **FD002 Sensor Normalization**: Retained sensors are normalized using regime-aware z-score normalization ($x_{\text{normalized}} = (x - \mu_{\text{train}}[g, j]) / \sigma_{\text{train}}[g, j]$) using means and standard deviations computed strictly from the 130 FD002 training engines within each of the 6 frozen regimes.
  11. **FD001 Normalization Protocol**: FD001 uses global training-only z-score normalization for settings and retained sensors without regime clustering because it is the single-condition control dataset.
  12. **FD004 Normalization Protocol**: FD004 will use dataset-specific training-only regime-aware normalization after its engine split is frozen in later Step 5 sub-steps.
  13. **Missing-Value Policy**: Silent imputation (mean, median, forward/backward fill, interpolation) is strictly prohibited. Missing values must trigger an explicit data validation error.
  14. **Zero Standard Deviation Rule**: If a training-derived standard deviation is zero, pipelines must trigger a validation failure rather than silently replacing std with 1.0 or adding epsilon.
  15. **Prohibited Transformations**: PCA, ICA, polynomial expansion, temporal smoothing (moving average, Savitzky-Golay), clipping, winsorization, learned feature selection, and target encoding are explicitly prohibited.
  16. **Training-Only Learning Rule**: All preprocessing parameters MUST be fit strictly on training engines. Calibration, validation, and test partitions MUST be transformed using frozen parameters and must never influence parameter fitting.
- **Evidence Reviewed**:
  - Training-only sensor diagnostic results in `research/research_design/fd002_training_sensor_diagnostic.csv` and executable script `scripts/audit_fd002_sensors.py`.
- **Expected Implications**:
  - Input schema and preprocessing specifications documented in `research/research_design/data_evaluation_protocol.md`.
  - Future data pipeline modules will implement the 17-feature input vector and training-only normalization rules.
- **Follow-up Review Date / Trigger**:
  - Step 5.4 Sequence / Window Construction definition.

---

### ADR-014: Sequential Maintenance Simulator Contract and Cost Structure
- **Date**: 2026-10-08
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Following the finalization of the Step 5 Data & Evaluation Protocol (ADR-012, ADR-013), Step 6 requires formalizing the sequential maintenance simulator contract, event ordering, action space, information boundaries, and cost model structure.
  - Standardizing the simulator contract prior to policy development and model training is necessary to prevent lookahead leakage, target contamination, custom cost functions, or unequal comparison conditions.
- **Decisions**:
  1. **Chronological Replay**: Engine trajectories are replayed independently in strict chronological order ($t = 1, 2, \dots$).
  2. **Strict Information Boundary**: Only observations available through decision cycle $t$ ($\mathcal{H}(i, t)$) may influence the policy decision at cycle $t$.
  3. **Action Space**: Restrict the action space strictly to two discrete choices: $\mathcal{A} = \{\text{CONTINUE}, \text{MAINTAIN\_NOW}\}$. No inspection, partial repair, or fleet optimization actions are approved.
  4. **Episode Termination**: Selecting $\text{MAINTAIN\_NOW}$ terminates the engine episode immediately and permanently.
  5. **No Post-Maintenance Trajectory**: Post-maintenance trajectories, sensor resets, or engine overhauls are NOT simulated on C-MAPSS data.
  6. **Final Preventive Opportunity**: The final preventive decision opportunity occurs at cycle $t = T_{\text{failure}}(i) - 1$ ($\text{RUL}_{\text{true}} = 1$).
  7. **Failure Event Boundary**: Selecting $\text{CONTINUE}$ at cycle $T_{\text{failure}}(i) - 1$ transitions the engine to functional failure at $T_{\text{failure}}(i)$ ($\text{RUL}_{\text{true}} = 0$) and terminates the replay without further decision opportunities.
  8. **Hidden Ground Truth**: True remaining life $\text{RUL}_{\text{true}}$, target $\text{RUL}_{\text{target}}$, failure cycle $T_{\text{failure}}$, and future telemetry are strictly hidden from the online decision policy.
  9. **Uniform Interface**: All baselines (point-prediction, global conformal, condition-aware conformal, proposed decision-aware, matched-conservatism controls) interact with the exact same simulator interface, event ordering, and cost function.
  10. **Cost Structure**: Maintenance cost contains exactly three components: $C_{\text{PM}}$ (fixed PM cost), $C_{\text{FAIL}}$ (unmitigated failure cost), and $C_{\text{WASTE}}$ (cost per wasted RUL cycle).
  11. **Preventive Cost**: Preventive maintenance cost at cycle $\tau_i$ is $C_i = C_{\text{PM}} + C_{\text{WASTE}} \cdot W_i$, where $W_i = T_{\text{failure}}(i) - \tau_i = \text{RUL}_{\text{true}}(i, \tau_i)$.
  12. **Failure Cost**: Failure cost is $C_i = C_{\text{FAIL}}$.
  13. **Deferred Parameter Values**: Numerical parameter values for $C_{\text{PM}}$, $C_{\text{FAIL}}$, and $C_{\text{WASTE}}$ remain intentionally deferred to pre-specified validation scenarios in Step 6.
  14. **Simulated Cost Units**: All costs are expressed in Simulated Cost Units under the constraint $C_{\text{PM}} > 0, C_{\text{FAIL}} > C_{\text{PM}}, C_{\text{WASTE}} \ge 0$.
  15. **Independent Unit**: The engine ($N$) is the fundamental independent unit of evaluation and statistical analysis.
  16. **Primary Outcome**: Mean simulated maintenance cost per engine ($\bar{C} = \frac{1}{N} \sum_{i=1}^N C_i$) remains the primary outcome for RQ1.
- **Expected Implications**:
  - Detailed simulator contract documented in `research/research_design/maintenance_simulator.md`.
  - Future simulator software implementation will strictly execute this chronological contract.
- **Follow-up Review Date / Trigger**:
  - Step 6 simulator implementation and validation scenario freezing.

---

### ADR-015: Step 6 Simulator Core Implementation, Deterministic Validation, and Cost-Scenario Infrastructure
- **Date**: 2026-10-08
- **Status**: Accepted
- **Authors Responsible**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
- **Context and Motivation**:
  - Following the locked sequential maintenance simulator contract (ADR-014), Step 6 requires implementing the core Python replay engine (`src/intellitwin/simulator/`), establishing a deterministic validation suite (`tests/test_maintenance_simulator.py`), defining cost-scenario family structures (`research_design/maintenance_cost_scenarios.yaml`), and executing a validation-only decision pilot (`scripts/run_step06_simulator_validation.py`).
- **Decisions**:
  1. **Simulator Implementation Semantics**: Simulator codebase implemented in `src/intellitwin/simulator/` (`types.py`, `costs.py`, `engine.py`). Replay is strictly chronological, enforcing $t < T_{\text{failure}}$ and isolating policy execution from ground-truth failure cycles and true RUL.
  2. **Common Policy Interface**: `MaintenancePolicy` protocol defined in `types.py`. Any policy receives only `PredictionState` containing `engine_id`, `cycle`, `point_rul`, `lower_rul`, `upper_rul`, and optional `regime`. Ground-truth RUL, failure cycles, and future records are strictly prohibited.
  3. **Deterministic Validation Suite**: 11 unit tests locked in `tests/test_maintenance_simulator.py` validating perfect timing, never maintain, early maintenance, final opportunity, continue at final opportunity, optimistic prediction stream, pessimistic prediction stream, cost arithmetic, policy information isolation, invalid input handling, and fleet aggregation.
  4. **Cost Scenario Families**: Locked three scenario family structures in `research_design/maintenance_cost_scenarios.yaml`: `primary_balanced`, `failure_sensitive`, and `waste_sensitive`.
  5. **Validation-Only Numerical Freeze Procedure**: Numerical cost parameters ($C_{\text{PM}}=10.0, C_{\text{FAIL}}=100.0, C_{\text{WASTE}}=1.0$ for `primary_balanced`) and practical-effect thresholds (5% cost reduction, 5% max worst-group coverage error) are officially frozen following researcher approval of the decision packet (`step06_numerical_freeze_decision.md`).
  6. **Strict Leakage Prohibition**: Held-out test set evaluation results must NEVER be used to choose, tune, or optimize cost scenario values or practical-effect thresholds.
  7. **Step 6 Status**: Step 6 Sequential Maintenance Simulator is officially marked **COMPLETE** and frozen for downstream confirmatory model development in Step 7.
- **Expected Implications**:
  - The simulator software stack, deterministic validation protocol, cost scenario parameters, and practical-effect thresholds are frozen.
  - Step 7 model development can proceed under locked evaluation controls.
- **Follow-up Review Date / Trigger**:
  - Step 7 baseline model training.













