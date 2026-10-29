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
- **Phase 3: Dataset Study and Experimental Protocol**: **Completed**:
  - Step 4 Dataset Qualification: **Completed** (FD002 primary, FD001 control, FD004 robustness).
  - Step 5 Data & Evaluation Protocol: **Completed** (Authoritative protocol with primary 90% nominal coverage, uncapped `rul_true` interval calibration and evaluation, engine-weighted metric aggregation, locked 17-feature schema, zero-variance scaling rule, 30-cycle windowing, retrospective stages, completed quartile membership metadata, and verified split manifests in `data/splits/`).
  - Step 6 Sequential Maintenance Simulator: **Completed** (Simulator contract, Python replay engine, 18-case deterministic validation suite, cost scenario infrastructure, verifiable validation pilot, frozen synthetic maintenance cost scenarios [ADR-018], and complete statistical inference protocol in [`research/research_design/statistical_inference_protocol.md`](research/research_design/statistical_inference_protocol.md)).
  - Step 7.0 Protocol Reconciliation: **COMPLETE** (FD002 lifetime-quartile provenance reconstructed, strict train/validation/calibration/test roles enforced, missing-group bounds logic formalized, and Step 7.1 base-predictor specification locked under ADR-019).
  - Step 7.1 Specification: **LOCKED** (HistGradientBoostingRegressor and LSTM base predictor architectures, search grids, and validation-only selection criteria frozen in [`research/research_design/step07_base_predictor_specification.md`](research/research_design/step07_base_predictor_specification.md)).
  - Step 7.2 Data/Preprocessing/Window Pipeline: **COMPLETE** (Strict C-MAPSS data loader, frozen split validation, training-only preprocessors, K-means k=6 regime models, 30-cycle causal windows, equal-engine weights, and deterministic artifact persistence).
  - Step 7.3 FD002 Base-Model Implementation and Selection: **COMPLETE** (Implemented GBR and LSTM model architectures under ADR-019, executed frozen 24-run configuration-selection procedure on FD002 validation partition across seeds 2026 and 2027, froze winning configurations `gbr_lr010_leaf31_l2_0` and `lstm_h64_lr0010` with zero calibration/test data leakage).
  - Step 7.4 Multi-Dataset/Five-Seed Final Base-Model Matrix: **COMPLETE** (Executed 24-run validation selection for FD001 and FD004 freezing dataset winners; trained complete 30-model matrix across official seeds 2026–2030; all 30 checkpoints verified on CPU; zero calibration/test data leakage).
  - Step 7.5 Independent Audit, Registry, and Formal Freeze: **COMPLETE** (Executed independent 30-model audit, constructed authoritative model registry [`experiments/base_models/model_registry.json`](experiments/base_models/model_registry.json), verified seed-2026 reproducibility across all 6 cells, authored formal freeze record [`research/research_design/step07_base_predictor_freeze.md`](research/research_design/step07_base_predictor_freeze.md), and accepted ADR-020).
- **Phase 5 (Step 7 Base Predictors)**: **COMPLETE** (All 30 base predictors immutably frozen under ADR-020).
- **Phase 6 (Step 8 Conformal Calibration & Corrective Audit)**: **COMPLETE & REVERIFIED** (Engine-weighted hierarchical conformal calibration across 90 bundles / 270 coverage configurations; candidate selection froze `gamma2_betam1` across all 6 cells under ADR-021; Step 8 corrective verification and full raw CPU reproduction audit passed [ADR-022, ADR-024] in `experiments/pretest_verification_v2/step08_full_audit.json` with 60/60 raw reproduction checks passing at 0.0 error, cross-platform POSIX registry paths verified on Linux and Windows, and baseline artifacts immutably preserved in `experiments/pretest_verification_v2/baseline_manifest.json` separating 652 tracked protected artifacts from 72 local-only tuning checkpoints).
- **Phase 7 (Step 9 Confirmatory Evaluation & Independent Audit)**: **COMPLETED & AUDIT PASSED** (Implemented separate confirmatory execution architecture in `src/intellitwin/confirmatory/`, executed official held-out test evaluation on 122 test engines across 930 matrix configurations [39,180 outcome rows, 186 cell summaries, 152 hypothesis components] with 10,000 stratified bootstrap draws under ADR-018 and ADR-026. Official independent audit in `experiments/confirmatory_v1/independent_audit.json` passed with zero failing reasons. Decisive confirmatory research question outcomes: RQ1 UNSUPPORTED, RQ2 UNSUPPORTED, RQ3 UNSUPPORTED, RQ4 UNSUPPORTED. Complete evidence and reports committed in `experiments/confirmatory_v1/` and `research/results/confirmatory_v1/`). Historical pre-test verification bundles (`experiments/pretest_verification_v5/` and `v6/`) and their historical `NOT_STARTED` pre-exposure readiness statements remain preserved unchanged.
- **Phase 8 (Ablation, Robustness, and Statistical Analysis)**: **COMPLETED & AUDIT PASSED** (Exploratory post-confirmatory $2 \times 2 \times 2$ factorial component ablation across 240 cells, engineering stress testing across 1,620 evaluations under 18 stream conditions, and paired lifetime-stratified bootstrap with 10,000 draws. Authoritative successor bundle in [`experiments/phase08_exploratory_v3/`](experiments/phase08_exploratory_v3/) with full independent reference audit in [`experiments/phase08_exploratory_v3/independent_audit.json`](experiments/phase08_exploratory_v3/independent_audit.json) [PASS, 0 failing reasons] and dynamic verified reports in [`research/results/phase08_exploratory_v3/`](research/results/phase08_exploratory_v3/). Historic v1 and v2 bundles preserved as superseded).
- **Phase 9 (Digital Twin Replay Prototype)**: **TESTED & VERIFIED** (Telemetry-replay digital-twin prototype replaying C-MAPSS validation engines under frozen 30-cycle causal lookback windows, tested across all 18 benchmark cells with $\text{atol} \le 10^{-4}$ validation parity, serving interactive local web dashboard at http://127.0.0.1:8000).



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

---

## 8. Digital Twin Validation-Replay Dashboard Prototype

To launch the local validation telemetry-replay prototype:

```bash
python -m uvicorn intellitwin.twin.api:app --host 127.0.0.1 --port 8000
```

Once running, navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) in a web browser.

For complete architectural details, API reference, and verification guides, see [`docs/development/twin_demo.md`](docs/development/twin_demo.md) and [`docs/development/twin_verification.md`](docs/development/twin_verification.md).
