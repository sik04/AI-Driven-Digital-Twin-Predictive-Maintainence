# IntelliTwin — Synopsis Preparation Progress Tracker

**Project:** IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance  
**Institution:** Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad  
**Affiliating University:** Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow  
**Department:** Information Technology  
**Academic Session:** 2026–2027  
**Project Guide:** Dr. Ruchi Gupta  
**Current Phase:** Phase 6 (Proposed Methodology) — **COMPLETED (AWAITING USER APPROVAL)**  
**Last Updated:** November 1, 2026  

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
| **Phase 4** | Literature Survey (Thematic Review, Comparison Table & Gap) | `literature_survey.tex`, `literature_survey.docx`, `literature_survey.pdf` | **APPROVED** |
| **Phase 5** | Objectives and Scope | `objectives_and_scope.tex`, `objectives_and_scope.docx`, `objectives_and_scope.pdf` | **APPROVED** |
| **Phase 6** | Proposed Methodology & Algorithmic Formulation | `proposed_methodology.tex`, `proposed_methodology.docx`, `proposed_methodology.pdf` | **COMPLETED (AWAITING APPROVAL)** |
| **Phase 7** | System Architecture & Workflow Diagrams | Architecture Diagrams & Pipeline Specs | Scheduled |
| **Phase 8** | Implementation Status and Results / Expected Results | Experimental Artifacts & Status Reports | Scheduled |
| **Phase 9** | Tools, Technologies and System Requirements | Requirements & Technology Stack | Scheduled |
| **Phase 10** | Conclusion and Future Work | Conclusion & Roadmap | Scheduled |
| **Final Phase** | Overleaf LaTeX Synchronization & Final Page-Budget Audit (6–8 pages) | Clean Compilable LaTeX Zip & PDF | Scheduled |

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

---

## 8. Phase 4 Literature Survey Deliverables & Validation Summary

### 8.1 Deliverables in `synopsis/Phase_4_Literature_Survey/`
- `literature_survey.tex`: Standalone, Overleaf-compatible LaTeX source conforming to AKGEC synopsis template structure (2,355 words excluding references).
- `literature_survey.docx`: Fully editable Microsoft Word document with exact margins (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing, justified, nil indentation, including Table 1).
- `literature_survey.html`: Print-optimized HTML/CSS source layout adhering to institutional circular guidelines.
- `literature_survey.pdf`: High-resolution publication-quality vector PDF rendered via headless Chrome engine (11 pages).
- `generate_literature_survey.py`: Python automation script ensuring 100% reproducible generation of `.docx` and `.pdf` artifacts.
- `README.md`: Phase 4 metadata, architectural structure, word count audit, and compliance documentation.

### 8.2 Structural Breakdown & Word Count Audit
- **Section 4.1: Thematic Overview and Survey Taxonomy** (~310 words)
  - Methodological taxonomy across 25 verified scholarly works in `research/literature/literature_matrix.csv` and 5 foundational papers.
  - Dual corpus classification: 15 local repository works (`LOC-01` to `LOC-15`) and 10 supplemental closest works (`SUP-01` to `SUP-10`).
  - Four core themes: Cyber-Physical Digital Twins, Data-Driven RUL Estimation, Distribution-Free Conformal Prediction, and Decision-Aware Maintenance Optimization.
- **Section 4.2: Critical Thematic Review of Prior Art** (~1,300 words)
  - *Theme 1: Cyber-Physical Digital Twins*: Surveys by Huang et al. (2021), Hasan & Crawford (2025), Pathri & Ganduri (2025); implementations by Wei (2024), Diana et al. (2025), Mazzetto (2024), Mousavi et al. (2024), Mahmud et al. (2025), Bello et al. (2024), Shehadeh (2024), Belay et al. (2026); DT RUL platform by Wu et al. (2026) battery platform, identifying UQ as critical future work.
  - *Theme 2: Data-Driven RUL Estimation*: Run-to-failure benchmark by Saxena et al. (2008) (NASA C-MAPSS dataset and asymmetric scoring); deep learning models by Hosseinzadeh et al. (2023), Zheng et al. (2017), Ma & Mao (2021). Point estimators optimize symmetric loss, unable to quantify tail risk or reflect in-service breakdown penalties.
  - *Theme 3: Distribution-Free Conformal Prediction*: Split conformal prediction on C-MAPSS by Javanmardi & Hüllermeier (2023); conformalized quantile regression (CQR) with LSTM by Diao et al. (2026); asymmetric CQR and risk-aware intervals by Robinson (2026); grouped validation by BenAbdennour (2026); regime-shift diagnostics by Yang et al. (2026), Hong Yan (2026) software audit; hierarchical conformal prediction by Lee, Barber, and Willett (2023).
  - *Theme 4: Decision-Aware Maintenance Optimization*: Maintenance optimization under RUL uncertainty by Chen et al. (2022), Zhu et al. (2025), Walia & Kumar (2026); structural reliability decision support by Brighenti et al. (2024), Hisamuddin et al. (2026); utility-directed conformal prediction by Cortes-Gomez et al. (2025); proper scoring rules by Gneiting & Raftery (2007); equivalence testing by Lakens (2017).
- **Section 4.3: Comparative Synthesis and Closest-Work Comparison Matrix** (~150 words + Table 1)
  - Detailed multi-dimensional comparative synthesis table contrasting 10 verified closest works across 8 key dimensions.
- **Section 4.4: Critical Methodological Observations and Research Gap Formulation** (~595 words)
  - Synthesis of four literature gaps: (1) Fragmentation between conformal calibration and operational economics ($C_{\text{FAIL}} \gg C_{\text{PM}}$); (2) Vulnerability of marginal conformal guarantees under operational shifts (localized terminal wear undercoverage); (3) Absence of matched-conservatism attribution controls (disambiguating true decision value from naive early overhaul); (4) Disconnection between ML models and Digital Twin platforms.
  - Restates the exact pre-registered research gap (ADR-018) and defines IntelliTwin's scientific positioning as a method-level integration.
- **Total Core Word Count**: **2,355 words** (excluding references and table captions).

### 8.3 IEEE References & Citations
- **Total References**: 30 authentic, peer-reviewed foundational literature sources cited in IEEE bracketed format `[1]`–`[30]`.
- **Sources Cited**: Saxena et al. (2008), Diana et al. (2025), Huang et al. (2021), Mazzetto (2024), Wei (2024), Bello et al. (2024), Hosseinzadeh et al. (2023), Shehadeh (2024), Mousavi et al. (2024), Brighenti et al. (2024), Hisamuddin et al. (2026), Mahmud et al. (2025), Hasan & Crawford (2025), Pathri & Ganduri (2025), Wu et al. (2026), Belay et al. (2026), Chen et al. (2022), Zhu et al. (2025), Diao et al. (2026), Walia & Kumar (2026), Xu et al. (2026), Yang et al. (2026), Javanmardi & Hüllermeier (2023), Yan (2026), Robinson (2026), BenAbdennour (2026), Lakens (2017), Gneiting & Raftery (2007), Lee et al. (2023), and Cortes-Gomez et al. (2025).

### 8.4 Verification & Compliance Audit
- **Team Roster Verification**: Strictly verified 2 members in approved order: Shiksha Pandey (`2300270110112`) and Mayank Singh (`2300270310115`). Audited with zero occurrences of former non-contributing members.
- **College Guidelines Compliance (`AKGEC/IT/CSIT/26-27/PROJ-m`)**:
  - Page Format: Standard A4 ($210 \times 297\text{ mm}$) — **PASS**
  - Margins: Left 1.5", Top/Bottom/Right 1.0" — **PASS**
  - Typography: Times New Roman (14 pt bold section headings, 12 pt bold subheadings, 12 pt regular body) — **PASS**
  - Line Spacing: 1.5, Justified Alignment, Nil Indentation — **PASS**
  - Comparative Table: Formatted multi-dimensional comparison matrix (Table 1) — **PASS**
  - Citation Standard: IEEE numerical format `[1]`–`[30]` — **PASS**
  - Scientific Demarcation: Framed as an academic research design / pre-registered investigation avoiding premature confirmatory claims — **PASS**
- **Overall Validation Status**: **PASS (100% Compliant)**.

### 8.5 Git Automation & Commit Verification
- **Commit Message**: `docs: add synopsis literature survey`
- **Commit Hash**: `85d160a`
- **Remote Branch**: `main` -> `origin/main`
- **Push Status**: Verified successfully pushed (`c487f90..85d160a`).

### 8.6 Phase 4 Forensic Audit & Reconciliation Summary
- **Audit Date**: November 1, 2026
- **Duplicate Directory & File Scan**: Completed repository-wide. Confirmed zero duplicate directories (no `Phase_4_Final`, `Phase_4_New`, etc.) and zero orphan copies of deliverables.
- **Uploaded Package Verification**: User-uploaded `literature_survey.zip` was verified to be 100% byte-identical to repository deliverables across `.docx`, `.pdf`, `.tex`, and `.html`.
- **Content Duplication**: AST and XML parsing confirmed zero duplicate paragraphs, zero duplicate headings, zero duplicate table rows, and zero duplicate references.
- **Deterministic Packaging Fix**: Modified `generate_literature_survey.py` to embed fixed zip entry timestamps `(2026, 11, 1, 0, 0, 0)` in `build_docx()`, guaranteeing bit-for-bit reproducible SHA-256 hashes across runs.
- **Literature Count Reconciliation**:
  - `paper/references.bib`: 30 verified entries (26 domain works + 4 foundational methodological papers).
  - `research/literature/source_verification.csv`: 26 domain works (23 Crossref DOI + 3 pending publication/institutional).
  - `research/literature/literature_matrix.csv`: 25 comparative studies (15 local `LOC-01`..`LOC-15` + 10 supplemental `SUP-01`..`SUP-10`).
  - `research/literature/screening_log.csv`: 27 records (26 domain works + 1 documented excluded lead).
  - `research/literature/paper_inventory.csv`: 15 local repository PDFs.
  - `research/literature/closest_work_matrix.csv`: 11 entries (10 primary + 1 candidate comparator).
  - Root `README.md` and `research/roadmap.md` synchronized with audited counts.
- **Detailed Forensic Audit Document**: Recorded in [`synopsis/Phase_4_Literature_Survey/PHASE_4_FORENSIC_AUDIT.md`](Phase_4_Literature_Survey/PHASE_4_FORENSIC_AUDIT.md).
- **Formal Phase 4 Status**: **APPROVED** (Formally reviewed and approved by user).

---

## 9. Phase 5 Objectives and Scope Deliverables & Validation Summary

### 9.1 Deliverables in `synopsis/Phase_5_Objectives_and_Scope/`
- `objectives_and_scope.docx`: Fully editable Microsoft Word document adhering strictly to AKGEC specifications (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing, 8 pages).
- `objectives_and_scope.pdf`: High-resolution vector PDF rendered via headless Chrome engine (8 pages, zero orphan lines).
- `objectives_and_scope.tex`: Standalone, Overleaf-compatible LaTeX source conforming to AKGEC synopsis template structure (1,421 words excluding references).
- `objectives_and_scope.html`: Print-optimized HTML/CSS source layout adhering to institutional circular guidelines.
- `generate_objectives_and_scope.py`: Python automation script ensuring 100% deterministic, reproducible generation of `.docx` and `.pdf` artifacts.
- `README.md`: Phase 5 metadata, architectural structure, traceability matrix, and compliance documentation.

### 9.2 Structural Breakdown & Word Count Audit
- **Section 5.1: Aim of the Project** (~280 words)
  - Cyber-physical reliability engineering; bridging continuous multivariate sensor RUL prediction, finite-sample distribution-free uncertainty calibration, and sequential operational maintenance decision-making.
  - Highlights the operational hazards of deterministic point estimates in asymmetric cost environments ($C_{\text{FAIL}} \gg C_{\text{PM}}$).
- **Section 5.2: Primary Objective** (~140 words)
  - States the central research objective: designing and validating an engine-weighted, condition-adaptive conformal calibration method that achieves significant lifecycle cost reductions ($\Delta_{\text{cost}} > 0.20$ SCU per engine) while strictly preserving finite-sample coverage reliability across operational regimes.
  - Aligned with pre-registered research gap (ADR-018) and RQ1.
- **Section 5.3: Specific Objectives** (~530 words)
  - Eight measurable, traceable objectives:
    1. *Telemetry Ingestion & Anti-Leakage Preprocessing*: C-MAPSS FD002 primary multi-regime, FD001 control, FD004 robustness; 30-cycle causal sliding lookback $W=30$; 17-feature schema; training-only Z-score normalization; engine-level split isolation.
    2. *Base Predictor Development & Checkpoint Freezing*: HistGBR and PyTorch LSTM; 30-model benchmark matrix across 5 official seeds `[2026..2030]`.
    3. *Engine-Weighted Hierarchical Conformal Calibration*: Asymmetric nonconformity score inversion targeting 90% nominal coverage ($1-\alpha=0.90$); engine weighting; flight regime and degradation stage bins.
    4. *Prediction Interval Validity & Sharpness Evaluation*: Marginal coverage, MPIW, Winkler scores, worst-subgroup conditional coverage error ($\Delta_{\text{error}} > 0.01$, $D_{\text{width}} < 1.0$ cycle, addressing RQ2).
    5. *Discrete-Event Sequential Maintenance Utility Simulation*: Retirement stopping time $\tau_i$ governed by lower bound $L_i(t)$; Standardized Cost Units: $C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$ per cycle.
    6. *Decision-Value Attribution Against Matched-Conservatism Controls*: Attribution testing against 3 matched-control baseline families (widened intervals, safety margins, earlier overhaul heuristics, addressing RQ3).
    7. *Cross-Condition Robustness and Non-Harm Verification*: 6 mandatory evaluation cells (FD001, FD002, FD004 $\times$ GBR, LSTM across 5 seeds); weighted aggregate utility contrasts and non-harm bounds under Bonferroni $\alpha=0.0125$, addressing RQ4.
    8. *Digital Twin Synchronization Replay Prototype*: `TwinReplayEngine` streaming telemetry with validation parity $\le 10^{-4}$; FastAPI REST service; HTML5/JS operator dashboard.
- **Section 5.4: Scope of the Project** (~310 words)
  - Clearly specifies research domain, C-MAPSS dataset roles (FD002 primary, FD001 control, FD004 robustness), continuous RUL regression task ($y_i(t) = T_i - t$), 17-feature schema, GBR and LSTM base models, split conformal calibration, sequential threshold policy, SCU economic parameters, and Python software ecosystem (37 pytest modules).
- **Section 5.5: Scope Boundaries and Limitations** (~220 words)
  - Explicit boundaries: Offline trace-driven replay (`TwinReplayEngine`); advisory decision support without autonomous closed-loop actuator control; evaluated on NASA simulation without FAA/EASA flight certification; pre-registered hypotheses under test rather than premature confirmatory claims.
- **Section 5.6: Expected Scientific and Practical Contributions** (~140 words)
  - Methodological integration, matched-conservatism benchmark protocol, and reproducible open-source digital twin prototype.
- **Total Core Word Count**: **1,421 words** (Excluding references and titles).

### 9.3 IEEE References & Citations
- **Total References**: 14 authentic, peer-reviewed foundational literature sources cited in IEEE bracketed format `[1]`–`[14]`.
- **Sources Cited**: Saxena et al. (2008), Huang et al. (2021), Diao et al. (2026), Javanmardi & Hüllermeier (2023), Zhu et al. (2025), Chen et al. (2022), Cortes-Gomez et al. (2025), Walia & Kumar (2026), Lee et al. (2023), Robinson (2026), Gneiting & Raftery (2007), Lakens (2017), Wu et al. (2026), and ISO 23247-1:2021.

### 9.4 Verification & Compliance Audit
- **Team Roster Verification**: Strictly verified 2 members in approved order: Shiksha Pandey (`2300270110112`) and Mayank Singh (`2300270310115`). Audited with zero occurrences of former non-contributing members.
- **College Guidelines Compliance (`AKGEC/IT/CSIT/26-27/PROJ-m`)**:
  - Page Format: Standard A4 ($210 \times 297\text{ mm}$) — **PASS**
  - Margins: Left 1.5", Top/Bottom/Right 1.0" — **PASS**
  - Typography: Times New Roman (14 pt bold section headings, 12 pt bold subheadings, 12 pt regular body) — **PASS**
  - Line Spacing: 1.5, Justified Alignment, Nil Indentation — **PASS**
  - Citation Standard: IEEE numerical format `[1]`–`[14]` — **PASS**
  - Scientific Demarcation: Framed as pre-registered research design (ADR-018) avoiding premature confirmatory claims — **PASS**
  - Scope Boundaries: Explicit exclusion of physical IoT and closed-loop actuation — **PASS**
- **Overall Validation Status**: **PASS (100% Compliant)**.
- **Formal Phase 5 Status**: **APPROVED** (Formally reviewed and approved by user).

### 9.5 Git Automation & Commit Verification
- **Commit Message**: `docs: add synopsis objectives and scope`
- **Commit Hash**: `576d033`
- **Remote Branch**: `main` -> `origin/main`
- **Push Status**: Verified successfully pushed (`24783ea..576d033`).

---

## 10. Phase 6 Proposed Methodology Deliverables & Validation Summary

### 10.1 Deliverables in `synopsis/Phase_6_Proposed_Methodology/`
- `proposed_methodology.docx`: Fully editable Microsoft Word document adhering strictly to AKGEC specifications (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing, 10 pages).
- `proposed_methodology.pdf`: High-resolution vector PDF rendered via headless Chrome engine (10 pages, zero orphan lines).
- `proposed_methodology.tex`: Standalone, Overleaf-compatible LaTeX source conforming to AKGEC synopsis template structure (2,418 words excluding references).
- `proposed_methodology.html`: Print-optimized HTML/CSS source layout adhering to institutional circular guidelines.
- `generate_proposed_methodology.py`: Python automation script ensuring 100% deterministic, reproducible generation of `.docx` and `.pdf` artifacts.
- `README.md`: Phase 6 metadata, architectural structure, mathematical formulation audit, traceability matrix, and compliance documentation.

### 10.2 Structural Breakdown & Mathematical Formulation Audit
- **Section 6.1: Methodological Framework and Algorithmic Overview** (~310 words)
  - End-to-end 7-stage architectural pipeline: (1) Causal telemetry ingestion; (2) Dual base prognostic estimation; (3) Engine-weighted asymmetric conformal calibration; (4) Condition-adaptive regime/wear-stage partitioning; (5) Discrete-event sequential maintenance simulation; (6) Matched-conservatism attribution auditing; (7) Digital Twin replay synchronization.
  - Resolves methodological fragmentation between statistical point estimation and operational maintenance utility.
- **Section 6.2: Telemetry Ingestion, Anti-Leakage Windowing and Normalization** (~420 words)
  - *Benchmark Corpus*: NASA C-MAPSS sub-corpora (FD002 primary multi-regime, FD001 single-condition control, FD004 multi-regime/multi-fault robustness).
  - *Causal Sliding Window*: Fixed lookback horizon $W = 30$ cycles ($\mathbf{X}_i(t) \in \mathbb{R}^{30 \times 17}$) eliminating temporal lookahead leakage.
  - *Sensor Pruning*: Automated drop of six invariant or uninformative channels ($\mathcal{S}_{\text{dropped}} = \{ s_1, s_5, s_6, s_{10}, s_{16}, s_{19} \}$) yielding $d = 17$ features (3 settings + 14 degradation sensors).
  - *Anti-Leakage Normalization*: Training-only Z-scores $(\boldsymbol{\mu}_{\text{train}}, \boldsymbol{\sigma}_{\text{train}})$ with strict engine-level split isolation.
- **Section 6.3: Base Prognostic Regression Models** (~350 words)
  - *Target RUL*: Piece-wise linear ground truth capped at $R_{\text{max}} = 125$ cycles.
  - *HistGradientBoostingRegressor (GBR)*: Multi-quantile boosting over flattened 510-dim vectors minimizing asymmetric pinball loss $\mathcal{L}_{\rho}$ across $\rho \in \{0.05, 0.50, 0.95\}$.
  - *PyTorch BiLSTM*: 2 stacked bidirectional LSTM layers ($h = 64$), variational recurrent dropout ($p = 0.20$), LeakyReLU projection head, AdamW optimization under MSE loss.
  - *Checkpoints*: Full 30-model benchmark matrix (3 datasets $\times$ 2 architectures $\times$ 5 seeds `[2026..2030]`) registered under ADR-018.
- **Section 6.4: Condition-Adaptive Hierarchical Conformal Calibration** (~480 words)
  - *Asymmetric Nonconformity Scoring*: Parameterized shape factors $\sigma(\hat{p}) = (1+\hat{p}/125)^\gamma$, $z(\hat{p}) = \exp(-\hat{p}/20)$, $a(\hat{p}) = \sigma(\hat{p})\exp(\beta z(\hat{p}))$, $b(\hat{p}) = \sigma(\hat{p})\exp(-\beta z(\hat{p}))$ penalizing hazardous overestimation ($\hat{y} > y$) more heavily than premature underestimation ($\hat{y} < y$).
  - *Engine-Weighted Hierarchical Empirical CDF*: Assigns weights $w_{i,t} = \frac{1}{m \cdot n_i}$ to resolve non-exchangeability across engines with variable trajectory lengths, targeting nominal $1-\alpha = 0.90$ coverage.
  - *Condition-Adaptive Partitioning*: K-means clustering ($K = 6$) on flight settings $(z_1, z_2, z_3)$ for regime-stratified conformal thresholds $\hat{q}_{1-\alpha}^{(k)}$.
  - *Interval Inversion*: Exact closed-form bounds $L_i(t) = \max(0, \hat{p}_i(t) - \hat{q}_{1-\alpha} a(\hat{p}_i(t)))$ and $U_i(t) = \hat{p}_i(t) + \hat{q}_{1-\alpha} b(\hat{p}_i(t))$.
- **Section 6.5: Discrete-Event Sequential Maintenance Utility Simulation** (~290 words)
  - *Stopping Time*: Maintenance dispatched when lower conformal bound breaches threshold: $\tau_i = \inf \{ t \ge W : L_i(t) \le \theta \}$.
  - *Standardized Cost Units (SCU)*: Planned overhaul $C_{\text{PM}} = 1.0$ SCU, in-service failure $C_{\text{FAIL}} = 5.0$ SCU, usable life waste $C_{\text{WASTE}} = 0.20$ SCU/cycle.
- **Section 6.6: Controlled Attribution Protocol (Matched-Conservatism Baselines)** (~220 words)
  - Disambiguates genuine uncertainty value from trivial over-conservatism across three pre-registered baseline families: (1) $\delta$-widened conformal intervals; (2) $\Delta$-margin deterministic safety offsets; (3) $\theta$-offset earlier intervention thresholds.
- **Section 6.7: Statistical Inference Protocol and Decision Rules** (~160 words)
  - 10,000 engine-level cluster bootstrap resamples; Bonferroni family-wise error rate control $\alpha_{\text{test}} = 0.0125$ (98.75% CI); Two One-Sided Tests (TOST) non-harm equivalence bounds ($\Delta_{\text{cost}} \ge -0.20$ SCU, $\Delta_{\text{error}} \ge -0.01$).
- **Section 6.8: Digital Twin Synchronization Replay Prototype** (~190 words)
  - ISO 23247-aligned `TwinReplayEngine` streaming sliding buffers, training Z-scores, dual inference, conformal bounds, dynamic Health Index $\text{HI}_i(t)$, and status alerts.
  - Verified numerical parity against offline batch execution: $\max_t | \hat{p}_{\text{stream}}(t) - \hat{p}_{\text{batch}}(t) | \le 10^{-4}$ and $\max_t | L_{\text{stream}}(t) - L_{\text{batch}}(t) | \le 10^{-4}$ across 37 automated pytest modules, backing FastAPI service and operator dashboard.
- **Total Core Word Count**: **2,418 words** (Excluding references and preamble).

### 10.3 IEEE References & Citations
- **Total References**: 14 authentic, peer-reviewed foundational literature sources cited in IEEE bracketed format `[1]`–`[14]`.
- **Sources Cited**: Saxena et al. (2008), Huang et al. (2021), Diao et al. (2026), Javanmardi & Hüllermeier (2023), Zhu et al. (2025), Chen et al. (2022), Cortes-Gomez et al. (2025), Walia & Kumar (2026), Lee et al. (2023), Robinson (2026), Gneiting & Raftery (2007), Lakens (2017), Wu et al. (2026), and ISO 23247-1:2021.

### 10.4 Verification & Compliance Audit
- **Team Roster Verification**: Strictly verified 2 members in approved order: Shiksha Pandey (`2300270110112`) and Mayank Singh (`2300270310115`). Audited with zero occurrences of former non-contributing members.
- **College Guidelines Compliance (`AKGEC/IT/CSIT/26-27/PROJ-m`)**:
  - Page Format: Standard A4 ($210 \times 297\text{ mm}$) — **PASS**
  - Margins: Left 1.5", Top/Bottom/Right 1.0" — **PASS**
  - Typography: Times New Roman (14 pt bold section headings, 12 pt bold subheadings, 12 pt regular body) — **PASS**
  - Line Spacing: 1.5, Justified Alignment, Nil Indentation — **PASS**
  - Citation Standard: IEEE numerical format `[1]`–`[14]` — **PASS**
  - Mathematical Formulations: Numbered LaTeX equations fully consistent with implementation in `src/intellitwin/` — **PASS**
  - Scope Boundaries: Explicit exclusion of physical IoT and closed-loop actuation — **PASS**
- **Overall Validation Status**: **PASS (100% Compliant)**.
- **Current Phase 6 Status**: **COMPLETED — AWAITING USER APPROVAL**.




