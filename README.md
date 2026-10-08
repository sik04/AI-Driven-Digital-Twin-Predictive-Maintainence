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

## 2. Research Questions and Direction

The core research problem and questions guide the IntelliTwin evaluation framework:

- **Research Direction**: The project investigates decision-aware, condition-adaptive conformal calibration for RUL prediction, designed to connect conditional uncertainty reliability with downstream sequential maintenance utility.
- **RQ1**: *Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*
- **RQ2**: *Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*
- **RQ3**: *Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*
- **RQ4**: *Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*

> *For detailed research design, scientific positioning, hypothesis framework, and experiment mapping, see:*
> - [`research/research_design/contribution_statement.md`](research/research_design/contribution_statement.md)
> - [`research/research_design/research_gap.md`](research/research_design/research_gap.md)
> - [`research/research_questions.md`](research/research_questions.md)
> - [`research/hypotheses/hypothesis_framework.yaml`](research/hypotheses/hypothesis_framework.yaml)
> - [`research/research_design/experiment_map.md`](research/research_design/experiment_map.md)

---

## 3. Current Project Status

- **Phase 0: Research Project Setup and Governance**: **Completed** (Repository reset, baseline backup, CI workflow, packaging, and governance framework verified).
- **Phase 1: Systematic Literature Review**: **Completed** (26 verified scholarly works synthesized in [`research/literature/literature_synthesis.md`](research/literature/literature_synthesis.md), [`paper/references.bib`](paper/references.bib), and [`research/literature/source_verification.csv`](research/literature/source_verification.csv)).
- **Phase 2: Research Gap, Questions, Hypotheses & Contributions**: **Completed** (Final Research Problem, RQ1–RQ4, and pre-specified hypotheses locked in [`research/research_questions.md`](research/research_questions.md)).
- **Phase 3: Dataset Study and Experimental Protocol**: **In Progress**:
  - Step 4 Dataset Qualification: **Completed** (FD002 primary, FD001 control, FD004 robustness).
  - Step 5 Data & Evaluation Protocol: **Completed** (Locked 17-feature schema, zero-variance scaling rule, 30-cycle windowing, retrospective stages, and split manifests in `data/splits/`).
  - Step 6 Sequential Maintenance Simulator: **In Progress** (Simulator contract, Python replay engine, 14-case deterministic validation suite, cost scenario infrastructure, and validation pilot complete. Numerical cost approval pending researcher decision).



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
│   ├── research_questions.md          # Finalized research questions and hypotheses
│   ├── decision_log.md                # Architecture Decision Records (ADRs)
│   ├── risk_register.md               # Scientific and project risk register
│   ├── author_contributions.md        # CRediT authorship tracking
│   └── literature/
│       ├── paper_inventory.csv        # Inventory of 15 local PDF papers
│       ├── literature_matrix.csv      # Expanded 23-study literature comparison matrix
│       ├── screening_log.csv          # PRISMA literature screening log (25 entries)
│       ├── closest_work_matrix.csv    # Direct closest-work comparison matrix
│       ├── citation_map.csv           # Claim-to-source mapping matrix
│       ├── literature_synthesis.md    # Thematic literature synthesis and gap analysis
│       └── search_protocol.md         # Multi-source search protocol and limitations
├── experiments/
│   ├── README.md                      # Experiment logging protocols
│   └── templates/
│       └── experiment_record.md       # Standardized experiment record template
├── paper/
│   ├── outline.md                     # Provisional manuscript/thesis outline
│   ├── claims_evidence_matrix.csv     # Paper claims and validation audit
│   └── references.bib                 # Verified scholarly bibliography (23 verified entries)
├── src/
│   └── intellitwin/
│       └── __init__.py                # Package initialization and metadata
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
