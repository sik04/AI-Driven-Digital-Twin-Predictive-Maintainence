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
  - Evidence status note added to `README.md`, `research/phase-2/research_gap_rq1_hypothesis.md`, and `research/research_questions.md`.
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





