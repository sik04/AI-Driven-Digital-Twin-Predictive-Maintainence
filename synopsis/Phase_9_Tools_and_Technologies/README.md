# Phase 9 — Tools, Technologies and System Requirements

**Project:** IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance  
**Institution:** Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad  
**Affiliating University:** Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow  
**Department:** Information Technology  
**Academic Session:** 2026–2027  
**Project Guide:** Dr. Ruchi Gupta  
**Project Group ID:** CSIT 4 2023-27/IT/SECTION/GID  
**Phase Status:** Phase 9 (Tools, Technologies and System Requirements) — **COMPLETED (AWAITING USER APPROVAL)**  
**Date:** November 3, 2026  

---

## 1. Project Team Roster (Official Order)

| S.No. | Student Name | University Roll Number | Department |
| :---: | :--- | :--- | :--- |
| 1 | **Shiksha Pandey** | 2300270110112 | Information Technology |
| 2 | **Mayank Singh** | 2300270310115 | Information Technology |

*Verification:* Automated scanning confirmed **zero occurrences** of former non-contributing members across all Phase 9 files and project records. Dr. Ruchi Gupta is strictly designated as Faculty Project Guide.

---

## 2. Deliverables Summary

The following core deliverables are provided in `synopsis/Phase_9_Tools_and_Technologies/`:

| File Name | Format | Description | Page / Word Budget |
| :--- | :---: | :--- | :---: |
| [`tools_and_technologies.docx`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_9_Tools_and_Technologies/tools_and_technologies.docx) | Word (`.docx`) | Fully editable Microsoft Word document adhering to AKGEC synopsis specifications (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing, 2 formatted tables). | 7 Pages (8.9 KB) |
| [`tools_and_technologies.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_9_Tools_and_Technologies/tools_and_technologies.pdf) | PDF (`.pdf`) | Publication-quality high-resolution vector PDF rendered via Chrome Headless containing 2 styled academic tables. | 7 Pages (259.2 KB) |
| [`tools_and_technologies.tex`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_9_Tools_and_Technologies/tools_and_technologies.tex) | LaTeX (`.tex`) | Standalone, Overleaf-compatible LaTeX source conforming to AKGEC template structure, IEEE reference formatting, and formal LaTeX tabular environments. | 949 words (prose excluding tables/refs) |
| [`tools_and_technologies.html`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_9_Tools_and_Technologies/tools_and_technologies.html) | HTML/CSS | Print-optimized HTML layout matching institutional typography, margins, and styled academic tables. | Screen / Print |
| [`generate_tools_and_technologies.py`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_9_Tools_and_Technologies/generate_tools_and_technologies.py) | Python (`.py`) | Automation script ensuring 100% deterministic, bit-for-bit reproducible generation of `.docx` and `.pdf` artifacts. | Reproducibility script |
| [`README.md`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_9_Tools_and_Technologies/README.md) | Markdown | Phase 9 metadata, software toolchain breakdown, hardware specifications, traceability matrix, and compliance documentation. | Documentation |

---

## 3. Structural Breakdown & Technology Stack Audit

The chapter provides a comprehensive specification of runtime environments, libraries, simulation and API infrastructure, quality toolchains, and hardware requirements across six subsections:

### 9.1 Programming Language and Runtime Environment (~220 words)
- Formulates Python 3.10–3.13 as the core computing language and execution runtime.
- Documents dependency management under PEP 517/518/621 (`pyproject.toml`) using `setuptools` (≥ 61.0) and editable source packaging (`src/intellitwin/`).
- Details cross-platform validation across Windows 11 (PowerShell), Ubuntu Linux (20.04/22.04 LTS), and macOS.
- Establishes cryptographic source line-ending normalization (`sha256-utf8-lf-v1`) guaranteeing reproducible hashes across CRLF and LF checkouts (ADR-022).

### 9.2 Core Frameworks and Scientific Computing Libraries (~260 words + Table 9.1)
- **Deep Learning**: PyTorch (≥ 2.2) powering the bidirectional LSTM prognostic sequence model, variational dropout ($p = 0.20$), LeakyReLU projection, AdamW optimizer, with CUDA acceleration and deterministic CPU reproduction.
- **Machine Learning**: Scikit-Learn (≥ 1.2.0) implementing `HistGradientBoostingRegressor` multi-quantile regressors (pinball loss) and K-means operational regime clustering ($K = 6$).
- **Numerical & Data Processing**: NumPy (≥ 1.24.0) for causal array buffering ($W = 30$) and C-order flattening (510-dim); Pandas (≥ 2.0.0) for C-MAPSS dataset ingestion; SciPy (≥ 1.10.0) for statistical bootstrapping; `fractions.Fraction` for exact rational quantile solving under cluster exchangeability.
- Summarizes the complete scientific computing toolchain in Table 9.1.

### 9.3 Digital Twin Simulation, API, and Visualization Stack (~190 words)
- **Backend Service**: FastAPI (≥ 0.110.0) providing asynchronous REST endpoints (`/api/sessions`, `/advance`, `/reset`, `/trace.csv`) with Pydantic schema validation.
- **ASGI Server**: Uvicorn (≥ 0.28.0) hosting the local API service at port 8000.
- **Thread Safety**: Python `threading.Lock` primitives enforcing mutually exclusive cycle-by-cycle replay advances.
- **Operator Dashboard**: Lightweight HTML5, CSS3, vanilla JavaScript (ES6+) interface in `apps/twin_dashboard/` with dynamic SVG/Canvas sensor charts, conformal interval bands, Health Index dials, and alert banners.

### 9.4 Development Toolchain, Quality Assurance, and Testing Framework (~160 words)
- **Code Quality**: `ruff` (≥ 0.1.0) enforcing PEP 8 compliance, `isort` imports, and 100-character line length limits.
- **Static Typing**: `mypy` (≥ 1.5.0) under strict type analysis (`strict = true`) across `src/intellitwin/`.
- **Automated Testing**: 37 automated pytest modules validating data pipelines, model determinism, calibration quantiles, maintenance simulation, and twin replay parity ($\text{atol} \le 10^{-4}$).
- **Provenance Engine**: `src/intellitwin/provenance.py` recording machine environment, dependencies, random seeds, and Git dirty checks.

### 9.5 Hardware and Operational System Requirements (~150 words + Table 9.2)
- Quantifies minimum development workstations (quad-core CPU, 8 GB RAM, 10 GB SSD) and recommended cluster environments (8+ cores, 16–32 GB RAM, NVIDIA GPU with CUDA, 25 GB NVMe SSD).
- **Physical Boundary Demarcation**: Explicitly clarifies that no physical aircraft engine hardware, avionics buses (ARINC 429), or physical microcontrollers are required for this software-based, trace-driven research prototype.

### 9.6 Institutional Software Compliance and Authoring Standards (~90 words)
- Documents alignment with AKGEC Department of Information Technology Circular `AKGEC/IT/CSIT/26-27/PROJ-m`: Overleaf (LaTeX) authoring, A4 geometry, 1.5" left margin, 1.0" top/bottom/right margins, Times New Roman, 1.5 line spacing, and IEEE numerical referencing `[1]`–`[14]`.

---

## 4. Traceability Matrix

| Tool / Technology | Minimum Version | Codebase / Project Scope | Verification Suite | Primary Responsibility |
| :---: | :---: | :--- | :--- | :--- |
| **Python** | 3.10–3.13 | Repository-wide | `python -V` | Core runtime execution environment |
| **PyTorch** | $\ge 2.2.0$ | `src/intellitwin/models/lstm.py` | `tests/test_models.py` | Deep bidirectional LSTM sequence modeling |
| **Scikit-Learn** | $\ge 1.2.0$ | `src/intellitwin/models/gbr.py`, `data/` | `tests/test_models.py` | HistGBR quantile trees, K-means regime clustering |
| **NumPy** | $\ge 1.24.0$ | `src/intellitwin/data/windowing.py` | `tests/test_data_pipeline.py` | Causal sliding-window array buffers ($W=30$) |
| **Pandas** | $\ge 2.0.0$ | `src/intellitwin/data/loader.py` | `tests/test_data_pipeline.py` | Tabular C-MAPSS ingestion and split manifests |
| **SciPy** | $\ge 1.10.0$ | `src/intellitwin/evaluation/bootstrap.py` | `tests/test_confirmatory.py` | 10k cluster bootstrap hypothesis testing |
| **FastAPI** | $\ge 0.110.0$ | `src/intellitwin/twin/api.py` | `tests/test_twin_replay.py` | RESTful Digital Twin replay endpoints (:8000) |
| **Uvicorn** | $\ge 0.28.0$ | `src/intellitwin/twin/api.py` | `tests/test_twin_replay.py` | High-concurrency ASGI server hosting |
| **Pytest** | $\ge 7.4.0$ | `tests/` (37 modules) | `pytest -v` | Comprehensive unit and integration test suite |
| **Ruff** | $\ge 0.1.0$ | `pyproject.toml` | `ruff check src tests` | High-speed PEP 8 linting and formatting |
| **Mypy** | $\ge 1.5.0$ | `pyproject.toml` | `mypy src tests` | Strict static type checking (`strict = true`) |

---

## 5. Compliance Verification Checklist

- [x] **Institutional Heading & Typography**: Main heading 14pt bold, Subheadings 12pt bold, Times New Roman body 12pt, 1.5 line spacing.
- [x] **Margin Compliance**: Left margin 1.5" (38.1 mm), Top, Bottom, and Right margins 1.0" (25.4 mm).
- [x] **IEEE Bibliographic Referencing**: 14 formal references `[1]`–`[14]` matching repository literature matrix and peer-reviewed bibliographic entries.
- [x] **Strict Roster Verification**: Exactly two student members (Shiksha Pandey & Mayank Singh). Zero mentions of former members. Dr. Ruchi Gupta properly identified as Project Guide.
- [x] **Academic Tables**: Formal styled tables for software toolchains (Table 9.1) and system hardware requirements (Table 9.2).
- [x] **Deterministic Reproduction**: `generate_tools_and_technologies.py` produces bit-for-bit reproducible `.docx` and high-resolution vector `.pdf` files.
