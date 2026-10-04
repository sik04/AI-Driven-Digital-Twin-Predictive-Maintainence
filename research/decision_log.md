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
- **Follow-up Review Date / Trigger**:
  - Upon completion of Phase 3 (Dataset Study & Data Protocol Formulation) prior to model training in Phase 5.


