# IntelliTwin — Synopsis Preparation Progress Tracker

**Project:** IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance  
**Institution:** Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad  
**Affiliating University:** Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow  
**Department:** Information Technology  
**Academic Session:** 2026–2027  
**Project Guide:** Dr. Ruchi Gupta  
**Current Phase:** Phase 3 (Problem Definition, Research Gap and Research Questions) — **COMPLETED**  
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
| **Phase 2** | Introduction, Industrial Domain & Rationale Formulation | `introduction.tex`, `introduction.docx`, `introduction.pdf` | **COMPLETED** |
| **Phase 3** | Problem Definition, Research Gap and Research Questions | `problem_definition.tex`, `problem_definition.docx`, `problem_definition.pdf` | **COMPLETED** |
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

### 5.4 Git Automation & Commit Verification
- **Commit Message**: `docs: add approved synopsis title page`
- **Commit Hash**: `1b78c07`
- **Remote Branch**: `main` -> `origin/main`
- **Push Status**: Verified successfully pushed (`df7c0be..1b78c07`).

---

## 6. Phase 2 Introduction Deliverables & Validation Summary

### 6.1 Deliverables in `synopsis/Phase_2_Introduction/`
- `introduction.tex`: Standalone, Overleaf-compatible LaTeX source conforming to AKGEC synopsis template structure (1,115 words excluding references).
- `introduction.docx`: Fully editable Microsoft Word document with exact margins (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing, justified, nil indentation).
- `introduction.html`: Print-optimized HTML/CSS source layout adhering to institutional circular guidelines.
- `introduction.pdf`: High-resolution publication-quality vector PDF rendered via headless Chrome engine (5 pages).
- `generate_introduction.py`: Python automation script ensuring 100% reproducible generation of `.docx` and `.pdf` artifacts.
- `README.md`: Phase 2 metadata, architectural structure, word count audit, and compliance documentation.

### 6.2 Structural Breakdown & Word Count Audit
- **Section 1.1: Background** (~285 words)
  - Cyber-physical systems (CPPS), Industry 4.0, sensor telemetry generation in rotational machinery (turbofan engines), shift from reactive to predictive maintenance, and Digital Twin foundations (Grieves, ISO 23247).
- **Section 1.2: Overview of IntelliTwin** (~295 words)
  - Continuous multi-sensor telemetry ingestion, 30-cycle causal sliding windowing, dual ML inference backends (HistGradientBoostingRegressor and PyTorch LSTM), finite-sample hierarchical split conformal prediction, sequential maintenance decision simulation, and trace-driven digital twin replay engine.
- **Section 1.3: Research Motivation** (~275 words)
  - Critical literature gaps addressed: (1) Uncalibrated point-prediction risks in safety-critical systems, (2) Disconnect between statistical loss metrics (RMSE/MAE) and operational maintenance economics (SCU penalties), and (3) Inadequate treatment of multi-regime operational drift and temporal dynamics.
- **Section 1.4: Research Significance** (~260 words)
  - Methodological rigor (distribution-free coverage bounds), economic grounding (Standardized Cost Units: PM=1, Failure=5, Inspection=0.20), and engineering realism (simulation replay parity $\le 10^{-4}$).
- **Total Core Word Count**: **1,115 words** (target: 900–1,200 words).

### 6.3 IEEE References & Citations
- **Total References**: 12 authentic, peer-reviewed foundational literature sources cited in IEEE bracketed format `[1]`–`[12]`.
- **Foundational Works**: Grieves & Vickers (Digital Twins), Tao et al. (Industry DT), Lei et al. (Machinery PHM), Saxena et al. (C-MAPSS damage propagation), Liu et al. (AI in PHM), Zheng et al. (LSTM for RUL), Ke et al. (LightGBM/GBDT), Angelopoulos & Bates (Conformal Prediction), Vovk et al. (Algorithmic Learning), Zio (PHM directions), Huynh et al. (Maintenance optimization), and ISO 23247-1:2021.

### 6.4 Verification & Compliance Audit
- **Team Roster Verification**: Strictly verified 2 members in approved order: Shiksha Pandey (`2300270110112`) and Mayank Singh (`2300270310115`). Audited with zero occurrences of former non-contributing members.
- **College Guidelines Compliance (`AKGEC/IT/CSIT/26-27/PROJ-m`)**:
  - Page Format: Standard A4 ($210 \times 297\text{ mm}$) — **PASS**
  - Margins: Left 1.5", Top/Bottom/Right 1.0" — **PASS**
  - Typography: Times New Roman (14 pt bold section headings, 12 pt bold subheadings, 12 pt regular body) — **PASS**
  - Line Spacing: 1.5, Justified Alignment, Nil Indentation — **PASS**
  - Citation Standard: IEEE numerical format `[1]`–`[12]` — **PASS**
  - Scientific Demarcation: Framed as an academic research design / pre-registered investigation avoiding premature confirmatory claims — **PASS**
- **Overall Validation Status**: **PASS (100% Compliant)**.

### 6.5 Git Automation & Commit Verification
- **Commit Message**: `docs: add synopsis introduction`
- **Commit Hash**: `9be3732`
- **Remote Branch**: `main` -> `origin/main`
- **Push Status**: Verified successfully pushed (`598a7f3..9be3732`).

---

## 7. Phase 3 Problem Definition Deliverables & Validation Summary

### 7.1 Deliverables in `synopsis/Phase_3_Problem_Definition/`
- `problem_definition.tex`: Standalone, Overleaf-compatible LaTeX source conforming to AKGEC synopsis template structure (2,024 words excluding references).
- `problem_definition.docx`: Fully editable Microsoft Word document with exact margins (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing, justified, nil indentation).
- `problem_definition.html`: Print-optimized HTML/CSS source layout adhering to institutional circular guidelines.
- `problem_definition.pdf`: High-resolution publication-quality vector PDF rendered via headless Chrome engine (9 pages).
- `generate_problem_definition.py`: Python automation script ensuring 100% reproducible generation of `.docx` and `.pdf` artifacts.
- `README.md`: Phase 3 metadata, architectural structure, word count audit, and compliance documentation.

### 7.2 Structural Breakdown & Word Count Audit
- **Section 3.1: Problem Statement** (~350 words)
  - Mathematical formalization of continuous RUL: $y_i(t) = T_i - t$.
  - Causal sliding windowing: $\mathbf{X}_i(t) \in \mathbb{R}^{W \times (d_x + d_s)}$ with fixed lookback $W=30$ cycles.
  - Requirement for distribution-free prediction intervals $\mathcal{C}_{1-\alpha}(\mathbf{X}_i(t)) = [L_i(t), U_i(t)]$ targeting nominal coverage $1 - \alpha$.
  - Sequential maintenance stopping time $\tau_i = \inf \{ t \ge W : \pi(\mathcal{C}_{1-\alpha}(\mathbf{X}_i(t))) = \text{MAINTAIN} \}$ and asymmetric lifecycle cost function $C_i(\tau_i)$ with $C_{\text{FAIL}} \gg C_{\text{PM}}$.
- **Section 3.2: Limitations of Existing Approaches** (~440 words)
  - 1. Pervasive reliance on uncalibrated point predictions (blind to operational risk asymmetry).
  - 2. Conditional miscalibration and subgroup vulnerability (global coverage masks severe undercoverage in terminal wear stages $t \to T_i$).
  - 3. Decoupling of statistical uncertainty metrics (MPIW/Winkler) from downstream replacement economics.
  - 4. Conflation of genuine decision value with trivial over-conservatism (naive early replacement squanders usable component life).
- **Section 3.3: Research Gap** (~280 words)
  - Formulates the exact pre-registered research gap: investigating whether decision-aware, condition-adaptive conformal calibration can improve sequential maintenance utility without sacrificing subgroup reliability or merely becoming more conservative.
  - Demarcates boundaries against prior art (Javanmardi & Hüllermeier 2023, Diao et al. 2026, Zhu et al. 2025, Walia & Kumar 2026, Robinson 2026, Cortes-Gomez et al. 2025).
- **Section 3.4: Proposed Research Questions** (~420 words)
  - Exact approved wording of **RQ1–RQ4** from `research/research_questions.md` mapped to Experiments A–D:
    - **RQ1**: Maintenance utility improvement ($\Delta_{\text{cost}} > 0.20$ SCU, coverage ceiling $E < 0.05$) via Experiment A on FD002.
    - **RQ2**: Subgroup conditional reliability without excessive widening ($\Delta_{\text{error}} > 0.01$, $D_{\text{width}} < 1.0$, $D_{\text{score}} < 1.0$) via Experiment B.
    - **RQ3**: Decision-value attribution vs. 3 matched-conservatism control families ($\Delta_{\text{cost}} > 0.20$ SCU against every family) via Experiment C.
    - **RQ4**: Cross-condition, cross-model robustness across 6 mandatory cells (FD001, FD002, FD004 $\times$ GBR, LSTM, 5 seeds) via Experiment D.
- **Section 3.5: Research Significance** (~260 words)
  - Methodological rigor (distribution-free finite-sample guarantees, cluster-bootstrap inference, Bonferroni $\alpha = 0.0125$).
  - Economic alignment (Standardized Cost Units: PM=1.0, Failure=5.0, Waste=0.20 per cycle).
  - Open-science governance (pre-registration under ADR-018, explicit non-harm bounds, transparent negative result reporting).
- **Section 3.6: Problem Scope and Boundaries** (~300 words)
  - NASA C-MAPSS dataset corpus (FD001, FD002, FD004).
  - 17-feature schema (14 active sensors + 3 settings; 6 invariant sensors dropped), training-only Z-score standardization.
  - Fixed 30-cycle causal sliding window ($W=30$).
  - GBR and LSTM base prognostic regressors.
  - Discrete-event sequential maintenance simulator.
  - Explicit boundaries: No live physical sensor ingestion; no physical closed-loop actuator feedback; Digital Twin implemented as an offline trace replay engine (`TwinReplayEngine` / FastAPI web dashboard at port 8000) with parity $\le 10^{-4}$.
- **Total Core Word Count**: **2,024 words** (excluding references).

### 7.3 IEEE References & Citations
- **Total References**: 14 authentic, peer-reviewed foundational literature sources cited in IEEE bracketed format `[1]`–`[14]`.
- **Sources Cited**: Saxena et al. (2008), Huang et al. (2021), Diao et al. (2026), Javanmardi & Hüllermeier (2023), Zhu et al. (2025), Chen et al. (2022), Cortes-Gomez et al. (2025), Walia & Kumar (2026), Lee et al. (2023), Robinson (2026), Gneiting & Raftery (2007), BenAbdennour (2026), Lakens (2017), and Wu et al. (2026).

### 7.4 Verification & Compliance Audit
- **Team Roster Verification**: Strictly verified 2 members in approved order: Shiksha Pandey (`2300270110112`) and Mayank Singh (`2300270310115`). Audited with zero occurrences of former non-contributing members.
- **College Guidelines Compliance (`AKGEC/IT/CSIT/26-27/PROJ-m`)**:
  - Page Format: Standard A4 ($210 \times 297\text{ mm}$) — **PASS**
  - Margins: Left 1.5", Top/Bottom/Right 1.0" — **PASS**
  - Typography: Times New Roman (14 pt bold section headings, 12 pt bold subheadings, 12 pt regular body) — **PASS**
  - Line Spacing: 1.5, Justified Alignment, Nil Indentation — **PASS**
  - Citation Standard: IEEE numerical format `[1]`–`[14]` — **PASS**
  - Scientific Demarcation: Framed as an academic research design / pre-registered investigation avoiding premature confirmatory claims — **PASS**
  - Scope Boundaries: Explicitly excludes live IoT hardware ingestion and closed-loop actuation — **PASS**
- **Overall Validation Status**: **PASS (100% Compliant)**.

### 7.5 Git Automation & Commit Verification
- **Commit Message**: `docs: add synopsis problem definition and research gap`
- **Commit Hash**: `5763192`
- **Remote Branch**: `main` -> `origin/main`
- **Push Status**: Verified successfully pushed (`78b8364..5763192`).




