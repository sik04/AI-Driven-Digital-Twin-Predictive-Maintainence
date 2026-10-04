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
