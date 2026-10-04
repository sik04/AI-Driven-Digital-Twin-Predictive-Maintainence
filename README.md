# IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance

[![CI](https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence/actions/workflows/ci.yml/badge.svg)](https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: Mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

---

## 1. Project Overview

**IntelliTwin** is a scientific research project investigating AI-driven Digital Twin architectures for the predictive maintenance (PdM) of complex engineering assets (specifically turbofan engines).

The project is conducted jointly by:
- **Mayank Singh**
- **Shiksha Pandey**
- **Ruchi Gupta**

### Research Philosophy
The project prioritizes **scientific rigor, statistical validity, and reproducibility** over superficial application development. All software deliverables—including digital twin telemetry simulation, prognostic models, and decision-support services—are implementations of systematically tested scientific hypotheses.

---

## 2. Research Questions (Provisional)

Prior to the completion of the systematic literature review (Phase 1), the following candidate research questions guide our investigation:

- **RQ1**: *How do selected RUL prediction methods compare under a consistent, leak-free engine-level evaluation protocol?*
- **RQ2**: *How reliably can uncertainty estimates quantify RUL prediction error across varying operating conditions and asset wear stages?*
- **RQ3**: *Can uncertainty-aware maintenance decisions improve warning quality relative to appropriate simple baseline heuristics?*
- **RQ4**: *Which framework components provide measurable empirical benefits, and under what operational conditions do these benefits persist?*

> *Note: These questions are provisional and will be formally refined following the Phase 1 Systematic Literature Review.*

---

## 3. Current Project Status

- **Active Milestone**: **Phase 0: Research Project Setup and Governance**
- **Current Deliverable**: Clean research foundation, modern Python packaging layout (`src/intellitwin`), strict quality toolchain (Ruff, Mypy, Pytest), CI workflow, and complete research governance framework.
- **Next Milestone**: **Phase 1: Systematic Literature Review** (PRISMA search, screening, and literature synthesis).

---

## 4. Repository Structure

```text
IntelliTwin/
├── README.md                          # Master project documentation
├── pyproject.toml                     # Modern build and toolchain configuration
├── .gitignore                         # Comprehensive Git ignore rules
├── .editorconfig                      # Universal code style settings
├── LICENSE                            # MIT License
├── CONTRIBUTING.md                    # Research ethics & contribution workflow
├── CHANGELOG.md                       # Structured release history
├── Makefile                           # Development automation commands
├── .github/
│   ├── workflows/
│   │   └── ci.yml                     # Continuous Integration workflow
│   ├── ISSUE_TEMPLATE/                # Bug report and research task templates
│   └── pull_request_template.md       # Standardized PR review template
├── docs/
│   ├── project_scope.md               # Scientific scope and boundaries
│   ├── development_setup.md           # Windows & POSIX environment guide
│   ├── architecture_overview.md       # Conceptual layers and module layout
│   └── reproducibility.md             # Reproducibility charter and protocols
├── research/
│   ├── roadmap.md                     # Phases 0 through 12 master roadmap
│   ├── research_questions.md          # Formal candidate RQs and hypotheses
│   ├── decision_log.md                # Architecture Decision Records (ADRs)
│   ├── risk_register.md               # Scientific and project risk register
│   ├── author_contributions.md        # CRediT authorship tracking
│   └── literature/
│       ├── search_protocol.md         # Systematic literature review protocol
│       ├── literature_matrix.csv      # Systematic literature extraction matrix
│       └── screening_log.csv          # PRISMA literature screening log
├── experiments/
│   ├── README.md                      # Experiment logging protocols
│   └── templates/
│       └── experiment_record.md       # Standardized experiment record template
├── paper/
│   ├── outline.md                     # Provisional manuscript/thesis outline
│   ├── claims_evidence_matrix.csv     # Paper claims and validation audit
│   └── references.bib                 # Verified scholarly bibliography
├── src/
│   └── intellitwin/
│       └── __init__.py                # Package initialization and metadata
└── tests/
    └── test_project_setup.py          # Setup, governance, and integrity tests
```

---

## 5. Development Quickstart

### Prerequisites
- Python >= 3.10 (tested on 3.10, 3.11, 3.12, 3.13)
- Git

### Installation (Windows PowerShell)

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Upgrade pip and install package with development tools
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Installation (POSIX / Linux / macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e ".[dev]"
```

---

## 6. Running Quality Verification

Before opening any pull request or committing code, run the full verification suite:

### Windows (PowerShell)

```powershell
# Format checking
ruff format --check src tests

# Linting
ruff check src tests

# Static type checking
mypy src tests

# Automated test suite
pytest
```

### POSIX (Make)

```bash
make check
```

---

## 7. Research Governance & Traceability

1. **Architecture Decisions**: Documented in [`research/decision_log.md`](research/decision_log.md).
2. **Experiment Records**: Maintained under [`experiments/`](experiments/). Every run logs seed, Git hash, and metrics.
3. **Manuscript Claims**: Audited in [`paper/claims_evidence_matrix.csv`](paper/claims_evidence_matrix.csv).
4. **Scholarly Integrity**: Literature extraction strictly requires verified DOIs in [`research/literature/`](research/literature/).
