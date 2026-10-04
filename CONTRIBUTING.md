# Contributing to IntelliTwin

Welcome to the IntelliTwin research project. This repository is dedicated to scientific research on AI-driven Digital Twin architectures and predictive maintenance, conducted jointly by Mayank Singh, Shiksha Pandey, and Ruchi Gupta.

The project prioritizes scientific validity, reproducibility, and rigorous empirical methodology over rapid application development.

---

## 1. Core Principles

1. **Evidence First**: No claim, model metric, or literature assertion may be made without verifiable, documented evidence.
2. **Reproducibility**: Every experiment must record configuration, random seeds, software environment, and Git commit hash.
3. **Traceability**: All code, configurations, and manuscript drafts must link back to formal decisions recorded in `research/decision_log.md`.
4. **Honesty and Integrity**: Negative and null results must be reported alongside positive results. Never cherry-pick or fabricate metrics.

---

## 2. Git Feature-Branch Workflow

All modifications must adhere to a strict feature-branch lifecycle:

1. **Branching**:
   - Never commit directly to `main`.
   - Create a descriptive branch from up-to-date `main`:
     - `feat/<feature-name>` for new functionality or research capabilities.
     - `research/<phase-name>` for research deliverables and documentation.
     - `fix/<bug-name>` for bug fixes.
     - `docs/<doc-name>` for documentation updates.
2. **Commits**:
   - Use Conventional Commits formatting:
     - `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `test: ...`, `chore: ...`.
   - Keep commits small, atomic, and focused.
3. **Quality Verification**:
   - Before opening a pull request, run all checks locally:
     ```powershell
     ruff format --check src tests
     ruff check src tests
     mypy src tests
     pytest
     ```
4. **Pull Requests**:
   - Open a PR targeting `main` using `.github/pull_request_template.md`.
   - Provide an evidence-based summary of changes, test outcomes, and limitations.
   - Wait for CI checks to pass and conduct a thorough diff review before merging.
5. **Branch Cleanup**:
   - Once merged to `main`, delete the feature branch remotely and locally.

---

## 3. Author Contributions and Authorship

Authorship contributions are recorded neutrally in [`research/author_contributions.md`](research/author_contributions.md) following the CRediT (Contributor Roles Taxonomy) guidelines:
- Conceptualization
- Literature Review
- Methodology
- Software
- Validation & Experiments
- Formal Analysis
- Investigation
- Data Curation
- Writing - Original Draft
- Writing - Review & Editing

All decisions regarding author order and contribution percentages require mutual agreement among all authors (Mayank Singh, Shiksha Pandey, and Ruchi Gupta).

---

## 4. Coding & Tooling Standards

- **Language**: Python >= 3.10
- **Linter & Formatter**: `ruff`
- **Type Checker**: `mypy` (strict mode enabled)
- **Testing**: `pytest`
- **Dependencies**: Keep runtime dependencies minimal. Heavy libraries (PyTorch, XGBoost, etc.) are introduced only as justified by formal research milestones.
