# IntelliTwin — Synopsis Preparation Progress Tracker

**Project:** IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance  
**Institution:** Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad  
**Affiliating University:** Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow  
**Department:** Information Technology  
**Academic Session:** 2026–2027  
**Project Guide:** Dr. Ruchi Gupta  
**Current Phase:** Phase 1 (Official Project Synopsis Title Page) — **COMPLETED**  
**Last Updated:** October 31, 2026  

---

## 1. Project Team Roster (Official Order)

| S.No. | Student Name | University Roll Number | Department |
| :---: | :--- | :--- | :--- |
| 1 | **Shiksha Pandey** | 2300270110112 | Information Technology |
| 2 | **Mayank Singh** | 2300270310115 | Information Technology |

---

## 2. Phase-by-Phase Roadmap

| Phase | Phase Description | Target Deliverable | Status |
| :---: | :--- | :--- | :---: |
| **Phase 0** | **Discovery, PDF Identification & Repository Audit** | `PROJECT_IMPLEMENTATION_AUDIT.md`, `RESEARCH_PAPER_INVENTORY.md` | **COMPLETED** |
| **Phase 1** | Project Title Page, Departmental Header & Metadata Alignment | Title page source (.tex, .docx), PDF, validation | **COMPLETED** |
| **Phase 2** | Introduction, Industrial Domain & Rationale Formulation | Section 2 & 4 Drafts | Scheduled |
| **Phase 3** | Problem Statement, Research Questions & Objective Bullet Points | Section 3 & 5 Drafts | Scheduled |
| **Phase 4** | Methodology, System Architecture Diagrams & Calibration Equations | Section 6 Drafts & Diagrams | Scheduled |
| **Phase 5** | Expected Outcomes, Tools/Technologies & Gantt Project Schedule | Section 7, 8 & 9 Drafts | Scheduled |
| **Phase 6** | Conclusion, Novelty Summary & IEEE Formatted References | Section 10 & 11 Drafts | Scheduled |
| **Phase 7** | Viva / Review Defense Answers (100-word Q1, Q2, Q3) | Synopsis Review Defense Guide | Scheduled |
| **Phase 8** | Overleaf LaTeX Synchronization & Final Page-Budget Audit (6–8 pages) | Clean Compilable LaTeX Zip & PDF | Scheduled |

---

## 3. Phase 0 Audit Summary

### 3.1 Document Identification
1. **Official College Synopsis Format PDF**:
   - **Path**: [`PROJECT SYNOPSIS.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/PROJECT%20SYNOPSIS.pdf)
   - **Readability**: Fully readable (2 scanned image pages containing high-resolution circular text).
   - **Issuing Authority**: Department of Information Technology, AKGEC (File No: `AKGEC/IT/CSIT/26-27/PROJ-m`, Date: 25-08-2026), signed by Project Coordinator Dr. Aditya Pratap Singh and HoD Prof. (Dr.) Rahul Sharma.
   - **Key Formatting Rules**:
     - Main body: strictly **6–8 pages** excluding title/cover and references.
     - Page size: A4; Margins: Top 1.0", Bottom 1.0", Left 1.5", Right 1.0".
     - Font: Times New Roman; Title: 18 pt Bold Center; Main Headings: 14 pt Bold; Sub-headings: 12 pt Bold; Content: 12 pt Regular.
     - Line Spacing: 1.5; Alignment: Justified; Indentation: Nil.
     - Citations: Strictly IEEE format.
     - Authoring requirement: Exclusively in Overleaf (LaTeX) via template `https://www.overleaf.com/read/ccvkzmsccqfs#84c5d4`.
     - Evaluation review preparation: Three mandatory 100-word defense questions.

2. **Previous / Old Project Synopsis PDF**:
   - **Path**: [`Synopsis1.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/Synopsis1.pdf)
   - **Readability**: Fully readable (9-page native vector PDF dated October 11, 2026).
   - **Purpose**: Historical baseline reference.
   - **Key Discrepancies vs. Current Project**:
     - *Team Roster*: Listed only 4 students (Mayank Singh was missing; Shiksha Pandey was listed 3rd instead of 1st).
     - *Technical Scope*: Old synopsis described a simple software simulation of a CNC milling machine using random walks with drift, Logistic Regression, Random Forest classification, and a Streamlit dashboard.
     - *Current Codebase Reality*: The actual implementation operates on real-world turbofan aircraft engine degradation data (NASA C-MAPSS FD001–FD004), predicting continuous Remaining Useful Life (RUL) using `HistGradientBoostingRegressor` and PyTorch `LSTM`, calibrated with engine-weighted hierarchical split conformal prediction, evaluated under a discrete-event sequential maintenance cost simulator, and rendered in a FastAPI + HTML5/JS Digital Twin replay dashboard.

### 3.2 Research Paper Inventory Summary
- **Complete Research Papers in Repo**: **1 paper** physically present:
  - [`data/raw/cmapss/Damage Propagation Modeling.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/data/raw/cmapss/Damage%20Propagation%20Modeling.pdf): Abhinav Saxena, Kai Goebel, Donald Simon, Neil Eklund, *"Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation"*, PHM 2008 (IEEE).
- **Tracked External Scholarly Literature**: 23 verified scholarly sources in `paper/references.bib` and 15 audited references in `research/literature/paper_inventory.csv`.
- **Recommended Literature Pillars**: 10 authentic papers with official DOIs cataloged in `synopsis/RESEARCH_PAPER_INVENTORY.md` spanning Digital Twins, RUL deep learning, Conformal Prediction, and Utility-directed maintenance policies.

### 3.3 Project Implementation Classification Summary
- **Implemented and Experimentally Evaluated**:
  - NASA C-MAPSS dataset loader, split manifests, and validation pipeline.
  - Training-only Z-score preprocessing, invariant sensor removal, and K-means regime clustering ($k=6$).
  - 30-cycle causal sliding window feature engineering ($W=30$).
  - 30 frozen base model checkpoints across 5 seeds (2026–2030) for GBR and LSTM architectures.
  - Conformal calibration subsystem (asymmetric score inversion, engine weighting, finite-sample bounds).
  - Sequential maintenance decision simulator (Standardized Cost Units: PM=1, Failure=5, Inspection=0.20).
  - Confirmatory held-out test evaluation on 122 engines across 930 matrix configurations (39,180 rows).
  - Factorial component ablation ($2 \times 2 \times 2$) and stress robustness testing across 1,620 evaluations under 18 stream conditions.
  - Digital Twin trace-driven replay engine with $\le 10^{-4}$ validation parity.
  - Automated quality assurance test suite (37 pytest modules).
- **Implemented**:
  - FastAPI Digital Twin REST API service and local HTML5/JS operator dashboard.
- **Not Found (Deprecated / Superseded)**:
  - Synthetic CNC random-walk telemetry generator (superseded by C-MAPSS).
  - Logistic regression and Random Forest binary classifiers (superseded by RUL regressors).
  - Interactive Jupyter Notebooks (`.ipynb`) (code is organized as pure modular Python packages).
- **Planned Future Work**:
  - Physical IoT edge sensor deployment and bidirectional closed-loop actuation.

---

## 4. Git Automation & Tracking

- **Branch**: `main`
- **Configured Remote**: `origin` -> `https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence.git`
- **Pre-existing Working Directory Status**:
  - `modified: experiments/phase08_exploratory_v3/stress_interval_predictions.csv.gz` (Preserved intact; not staged)
  - `untracked: PROJECT SYNOPSIS.pdf` (Preserved intact in root; not staged to avoid repository bloat)
  - `untracked: Synopsis1.pdf` (Preserved intact in root; not staged)
- **Staged Files for Phase 0**:
  - `synopsis/README.md`
  - `synopsis/SYNOPSIS_PROGRESS.md`
  - `synopsis/PROJECT_IMPLEMENTATION_AUDIT.md`
  - `synopsis/RESEARCH_PAPER_INVENTORY.md`
  - `synopsis/references/.gitkeep`
- **Commit Details**:
  - Commit Message: `docs: add synopsis discovery and repository audit`
  - Commit Hash: `1a5a16f`
- **Push Access Status**: Verified successfully pushed to `origin/main` (`https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence.git`).

---

## 5. Phase 1 Title Page Deliverables & Validation Summary

### 5.1 Deliverables in `synopsis/Phase_1_Title_Page/`
- `title_page.pdf`: High-resolution vector PDF rendered according to A4 dimensions and exact margins.
- `title_page.docx`: Fully editable Microsoft Word source document (A4, Left: 1.5", Right: 1.0", Top: 1.0", Bottom: 1.0").
- `title_page.tex`: Overleaf LaTeX source file matching AKGEC IT Department guidelines.
- `title_page.html`: Print-optimized HTML/CSS source layout.
- `akgec_logo.png`: Official college emblem graphic asset.
- `generate_title_page.py`: Python automation script regenerating PDF and DOCX artifacts.
- `README.md`: Phase 1 documentation and validation audit log.

### 5.2 Verification & Validation Results
- **Approved Title**: Matches `IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance` (18 pt Bold Centered).
- **Institutional Headings**: Verified AKGEC, AKTU Lucknow, and Department of Information Technology.
- **Project Team Roster**: Strictly verified 2 members in approved order:
  1. Shiksha Pandey (`2300270110112`)
  2. Mayank Singh (`2300270310115`)
- **Exclusion of Non-Contributing Members**: Programmatically audited with zero occurrences of `Prateek Gangwar`, `Rishikesh Chaurasia`, or `Surya Ranjha`.
- **Layout Fidelity**: Visually inspected with no clipping, correct line breaks, and centered emblem.
- **Overall Validation Status**: **PASS (100% Compliant)**.

### 5.3 Administrative Confirmation Items
1. Formal confirmation of Project Group ID `CSIT 4 2023-27/IT/SECTION/GID` with the 2-member group structure.
2. Departmental milestone calendar dates for Gantt chart preparation in Phase 5.

