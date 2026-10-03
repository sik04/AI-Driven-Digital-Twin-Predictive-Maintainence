# Repository Inventory & Structural Audit
**Repository:** [AI-Driven-Digital-Twin-Predictive-Maintainence](https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence)  
**Branch:** udit/step-01-repository-baseline  
**Audit Date:** October 3, 2026  
**Auditor Role:** Senior ML Engineer & Research Reproducibility Auditor  
**Baseline Commit:** 9b72fac (feat: restructure project into IntelliTwin framework with updated documentation and frontend dashboard)

---

## 1. Executive Summary of Repository Structure

The repository contains an end-to-end cyber-physical digital twin research suite for predictive maintenance of engineering assets (primarily evaluated on the NASA C-MAPSS turbofan engine degradation dataset). It encompasses:
1. **Core ML & Prognostic Engine (intellitwin/)**: Heteroscedastic LSTM, GRU, Random Forest, and XGBoost regressors, Split Conformal Prediction calibrator, condition-normalized residual decoupling, 4-way masking discriminator, catastrophic failure lead-time evaluator, and a Flask REST API.
2. **Interactive Factory Dashboard (rontend/)**: Single-page web dashboard implementing glassmorphic dark-mode telemetry visualization, health rings, multi-machine selection, conformal uncertainty intervals, and Chart.js degradation trends.
3. **Dataset Ingestion (data/cmapss/)**: Raw NASA C-MAPSS run-to-failure subsets (complete sets for FD001 and FD002; FD003 and FD004 are absent).
4. **Academic Manuscript Deliverables (manuscript/ and root)**: IEEE double-column PDF, IEEE-formatted Word DOCX, LaTeX source, standalone HTML presentation paper, academic Markdown manuscript, and submission ZIP package.
5. **Literature Corpus (literature/)**: 15 foundational research papers in PDF format and Python extraction utilities.
6. **Verification & Test Framework (	ests/, intellitwin/verify_consistency.py)**: Unit tests covering core mathematical routines and a deliverables consistency auditor.

---

## 2. Complete Repository File Inventory

| Path | Type | Category | Purpose | Primary Dependencies | Used by Main Pipeline | Completeness Status | Stale / Duplicated Status | External Resources Required |
|---|---|---|---|---|---|---|---|---|
| .gitignore | Config | Configuration | Git ignore rules for Python bytecode, build artifacts, environments, and OS files | Git | Yes (Repo VCS) | Complete | Clean | None |
| COMMANDS_TO_RUN.txt | Text / Docs | Documentation | Comprehensive 7-step guide to run, train, evaluate, visualize, and package the project | None | Yes (Operational Reference) | Complete | Clean (Up to date with IntelliTwin) | None |
| IEEE-paper-format-template.docx | Binary DOCX | Template / Manuscript | Formatted IEEE Word template with embedded project figures and manuscript content | Word / python-docx | No (Output artifact / working template) | Complete | Superceded by manuscript/INTELLITWIN_...docx | Microsoft Word / LibreOffice |
| IEEE-paper-format-template.original.docx | Binary DOCX | Template | Clean unmodified IEEE Conference / Journal Word template | Word | No (Backup template) | Complete | Upstream pristine template | Microsoft Word |
| IntelliTwin_IEEE_Format.pdf | Binary PDF | Manuscript Reference | Official reference research paper PDF establishing project title, scope, and authors | PDF Reader | No (Reference baseline) | Complete | Upstream author reference | PDF Reader |
| Intelligent Predictive Maintenance System.pptx | Binary PPTX | Presentation | Project presentation slide deck covering digital twin concepts, architecture, and results | PowerPoint | No (Deliverable) | Complete | Clean | Microsoft PowerPoint |
| README.md | Markdown | Documentation | Main repository documentation, architecture overview, author list, benchmarks, quick start | None | Yes (Repo Entrypoint) | Complete | Clean (Aligned to IntelliTwin) | None |
| 
equirements.txt | Text / Config | Configuration | Python package dependency specification | pip | Yes (Dependency install) | Incomplete (Missing torch, xgboost, flask, python-docx) | Stale (Header still refers to UQ-DT) | PyPI |
| setup.py | Python / Config | Configuration | Standard setuptools package installer for intellitwin | setuptools | Yes (Package installation) | Partial (Missing torch in install_requires) | Clean | None |
| WhatsApp Image 2026-09-28 at 10.24.35 PM.jpeg | Binary Image | UI Reference | WhatsApp screenshot reference of the legacy/target factory overview dashboard UI | Image Viewer | No (Design specification) | Complete | Reference artifact | Image Viewer |
| WhatsApp Image 2026-09-29 at 11.40.19 PM.jpeg | Binary Image | UI Reference | WhatsApp screenshot reference of the machine detail panel and telemetry UI | Image Viewer | No (Design specification) | Complete | Reference artifact | Image Viewer |
| data/cmapss/RUL_FD001.txt | Raw Data | Dataset | True Remaining Useful Life (RUL) values for 100 test engines of subset FD001 | pandas / numpy | Yes (data_loader.py, 	rain.py) | Complete (100 rows) | Clean | None |
| data/cmapss/RUL_FD002.txt | Raw Data | Dataset | True Remaining Useful Life (RUL) values for 259 test engines of subset FD002 | pandas / numpy | Partial (data_loader.py supports, not active in 	rain.py) | Complete (259 rows) | Clean | None |
| data/cmapss/readme.txt | Text | Documentation | Official NASA C-MAPSS dataset documentation describing subsets FD001-FD004 and columns | None | No (Dataset documentation) | Complete | Pristine NASA documentation | None |
| data/cmapss/test_FD001.txt | Raw Data | Dataset | Test degradation trajectories for 100 engines in subset FD001 (13,096 cycles) | pandas / numpy | Yes (data_loader.py, 	rain.py) | Complete (13,096 rows, 26 cols) | Clean | None |
| data/cmapss/test_FD002.txt | Raw Data | Dataset | Test degradation trajectories for 259 engines in subset FD002 (33,991 cycles) | pandas / numpy | Partial (data_loader.py supports, not active in 	rain.py) | Complete (33,991 rows, 26 cols) | Clean | None |
| data/cmapss/train_FD001.txt | Raw Data | Dataset | Run-to-failure trajectories for 100 training engines in subset FD001 (20,631 cycles) | pandas / numpy | Yes (data_loader.py, 	rain.py) | Complete (20,631 rows, 26 cols) | Clean | None |
| data/cmapss/train_FD002.txt | Raw Data | Dataset | Run-to-failure trajectories for 260 training engines in subset FD002 (53,759 cycles) | pandas / numpy | Partial (data_loader.py supports, not active in 	rain.py) | Complete (53,759 rows, 26 cols) | Clean | None |
| docs/COMPREHENSIVE_RESEARCH_GAPS_AND_OPPORTUNITIES.md | Markdown | Documentation | Comprehensive research gap synthesis analyzing 15 literature papers | None | No (Research documentation) | Complete | Literature synthesis baseline | None |
| docs/REAL_WORLD_EXPLANATION.md | Markdown | Documentation | Pedagogical explanation of the research paper in accessible, real-world engineering terms | None | No (Research documentation) | Complete | Clean | None |
| docs/deep_research_gap_analysis.md | Markdown | Documentation | Deep tabular and textual gap analysis linking literature papers to framework solutions | None | No (Research documentation) | Complete | Literature synthesis baseline | None |
| docs/walkthrough.md | Markdown | Documentation | Walkthrough documentation detailing project deliverables, tests, and screenshots | None | No (Research documentation) | Complete | Clean | None |
| igures/benchmark_metrics_summary.json | JSON | Experiment Artifact | Legacy empirical evaluation metrics comparing UQ-DT against literature baselines | json / python | No (Generated by prior UQ-DT benchmarks) | Complete | Stale naming (UQ-DT keys) | None |
| igures/fig1_rul_calibrated_intervals.png | Binary Image (PNG) | Figure / Deliverable | High-resolution (300 DPI) plot of C-MAPSS RUL trajectory with 90% conformal bounds | matplotlib | Yes (Referenced in manuscript & docs) | Complete | Clean | Image Viewer |
| igures/fig2_uncertainty_decomposition.png | Binary Image (PNG) | Figure / Deliverable | 300 DPI plot of condition-normalized residuals resolving the masking problem | matplotlib | Yes (Referenced in manuscript & docs) | Complete | Stale filename (Plots masking, not decomposition) | Image Viewer |
| igures/fig3_reliability_calibration.png | Binary Image (PNG) | Figure / Deliverable | 300 DPI plot of confusion matrix (RF, 89.0%) and conformal reliability calibration curve | matplotlib / seaborn | Yes (Referenced in manuscript & docs) | Complete | Clean | Image Viewer |
| igures/fig4_pareto_coverage_width.png | Binary Image (PNG) | Figure / Deliverable | 300 DPI bar chart comparing RMSE vs NASA asymmetric score across models | matplotlib | Yes (Referenced in manuscript & docs) | Complete | Stale filename (Plots benchmark, not Pareto) | Image Viewer |
| igures/fig5_dss_cost_comparison.png | Binary Image (PNG) | Figure / Deliverable | 300 DPI distribution of catastrophic early warning lead times across 20 engines | matplotlib / seaborn | Yes (Referenced in manuscript & docs) | Complete | Stale filename (Plots lead time, not DSS cost) | Image Viewer |
| rontend/app.js | JavaScript | Frontend Source | Interactive client-side application logic, state management, Chart.js graphs, and REST client | Chart.js (CDN) | Yes (Web UI) | Complete | Clean | Web Browser / Internet (CDN) |
| rontend/assets/air_compressor.svg | SVG Vector | Frontend Asset | Industrial vector graphic icon for Air Compressor machine card | None | Yes (Web UI) | Complete | Clean | Web Browser |
| rontend/assets/cnc_machine.svg | SVG Vector | Frontend Asset | Industrial vector graphic icon for CNC Machining Center machine card | None | Yes (Web UI) | Complete | Clean | Web Browser |
| rontend/assets/conveyor_belt.svg | SVG Vector | Frontend Asset | Industrial vector graphic icon for Conveyor Belt machine card | None | Yes (Web UI) | Complete | Clean | Web Browser |
| rontend/assets/hydraulic_press.svg | SVG Vector | Frontend Asset | Industrial vector graphic icon for Hydraulic Press machine card | None | Yes (Web UI) | Complete | Clean | Web Browser |
| rontend/assets/robotic_arm.svg | SVG Vector | Frontend Asset | Industrial vector graphic icon for 6-Axis Robotic Arm machine card | None | Yes (Web UI) | Complete | Clean | Web Browser |
| rontend/generate_svgs.py | Python | Frontend Script | Utility script that generated the 5 industrial SVG assets for the dashboard | None | No (Asset generator utility) | Complete | Single-use utility | None |
| rontend/index.html | HTML | Frontend Source | Responsive single-page factory-floor dashboard UI with dark glassmorphic theme | CSS / JS | Yes (Web UI entrypoint) | Complete | Clean | Web Browser |
| rontend/styles.css | CSS | Frontend Source | Dark glassmorphic design system, CSS variables, grid layout, animations, badges | None | Yes (Web UI) | Complete | Clean | Web Browser |
| intellitwin/__init__.py | Python Source | Source Code | Package entrypoint exposing version, metadata, and core submodules | None | Yes (Core package) | Complete | Clean | None |
| intellitwin/api.py | Python Source | Source Code / API | Flask REST API backend serving factory overview, machine state, telemetry, and predictions | Flask / numpy | Yes (Web backend) | Complete | Synthetic machine data in endpoints | None |
| intellitwin/catastrophic_evaluator.py | Python Source | Source Code | Evaluates early warning lead times, critical zone detection, and missed catastrophic failures | numpy | Yes (	rain.py, tests) | Complete | Clean | None |
| intellitwin/conformal_calibrator.py | Python Source | Source Code | Implements Split Conformal Prediction for finite-sample coverage guarantees ( - lpha$) | numpy | Yes (	rain.py, tests) | Complete | Clean | None |
| intellitwin/data_loader.py | Python Source | Source Code | Loads C-MAPSS dataset, computes piecewise RUL labels, extracts rolling stats, sequences | pandas / numpy / scikit-learn | Yes (	rain.py, tests) | Complete | Clean | None |
| intellitwin/environmental_handler.py | Python Source | Source Code | Operating regime clustering (KMeans) and condition-normalized residual computation (t)$ | numpy / scikit-learn | Yes (	rain.py, tests) | Complete | Clean | None |
| intellitwin/fault_discriminator.py | Python Source | Source Code | 4-way decision matrix resolving the Environmental Masking Problem | numpy | Yes (	rain.py, tests) | Complete | Clean | None |
| intellitwin/generate_figures.py | Python Source | Script / Tool | Standalone publication script generating Figures 1-5 at 300 DPI using matplotlib/seaborn | matplotlib / seaborn / numpy | Yes (Figure generation) | Complete | Uses simulated/hardcoded values | None |
| intellitwin/metrics.py | Python Source | Source Code | Prognostic evaluation metrics: RMSE, MAE, NASA asymmetric score, PICP, MPIW, Winkler, CWC | numpy / scikit-learn | Yes (	rain.py, tests) | Complete | Clean | None |
| intellitwin/models/anomaly_detector.py | Python Source | Source Code | Unsupervised anomaly detector combining PCA dimensionality reduction & Isolation Forest | scikit-learn / numpy | Yes (	rain.py) | Complete | Weights not persisted to disk | None |
| intellitwin/models/evaluation_results.json | JSON | Experiment Artifact | Serialized empirical results from master training pipeline on NASA C-MAPSS FD001 | json | Yes (erify_consistency.py, pi.py) | Complete | Clean (Verified against paper) | None |
| intellitwin/models/fault_classifier.py | Python Source | Source Code | Multi-class health state classifier (Healthy, Degrading, Critical) using RF & XGBoost | scikit-learn / xgboost | Yes (	rain.py) | Complete | Weights not persisted to disk | None |
| intellitwin/models/gru_rul.pt | PyTorch Binary | Model Weights | Serialized PyTorch state_dict for GRURULNet baseline (54-dim input, 64 hidden, 2 layers) | torch | Yes (Baseline model) | Complete (Loads with weights_only=True) | Clean | PyTorch |
| intellitwin/models/lstm_rul.pt | PyTorch Binary | Model Weights | Serialized PyTorch state_dict for heteroscedastic LSTMRULNet (54-dim input, 64 hidden) | torch | Yes (Primary RUL model) | Complete (Loads with weights_only=True) | Clean | PyTorch |
| intellitwin/models/lstm_rul.py | Python Source | Source Code | PyTorch neural network definitions for heteroscedastic LSTM, GRU, and Gaussian NLL loss | torch / numpy | Yes (	rain.py, tests) | Complete | Clean | PyTorch |
| intellitwin/train.py | Python Source | Pipeline Script | Master pipeline training LSTM, GRU, RF, XGB, Isolation Forest, Calibrator, and Evaluator | torch / sklearn / xgboost / numpy | Yes (Master training script) | Complete | Execution takes ~10 min on CPU | None |
| intellitwin/verify_consistency.py | Python Source | Verification Tool | Comprehensive audit script verifying integrity and file sizes of all project deliverables | None | Yes (Verification gate) | Complete | Clean (100% Pass) | None |
| literature/README.md | Markdown | Documentation | Overview of the 15 foundational research papers in the literature corpus | None | No (Literature docs) | Complete | Refers to UQ-DT | None |
| literature/papers/paper 10.pdf | Binary PDF | Literature Corpus | Academic paper: AI-Driven Digital Twins for Urban Infrastructure Review | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 11.pdf | Binary PDF | Literature Corpus | Academic paper: AI-Augmented DT Architecture for Predictive Maintenance | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 12.pdf | Binary PDF | Literature Corpus | Academic paper: A New Era for Digital Twins: Progress & Industry Adoption | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 13.pdf | Binary PDF | Literature Corpus | Academic paper: Industrial IoT and edge analytics for Digital Twins | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 14.pdf | Binary PDF | Literature Corpus | Academic paper: Wang et al. (MDPI Sensors 2026) - GA-Ensemble RUL Prediction | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 15.pdf | Binary PDF | Literature Corpus | Academic paper: Federated Anomaly Detection for Industrial IoT | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 2.pdf | Binary PDF | Literature Corpus | Academic paper: Ali et al. (Digital Twin 2024) - Real-time structural updating | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 3.pdf | Binary PDF | Literature Corpus | Academic paper: Urban Digital Twins Integration & Challenges Review | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 5.pdf | Binary PDF | Literature Corpus | Academic paper: Bridge Monitoring & Sensor Integration | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 6.pdf | Binary PDF | Literature Corpus | Academic paper: Hosseinzadeh et al. (Mfg Letters 2023) - ALSTM-FCN PdM | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 7.pdf | Binary PDF | Literature Corpus | Academic paper: Multi-asset Digital Twin architectures | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 8.pdf | Binary PDF | Literature Corpus | Academic paper: Mousavi et al. (Remote Sensing 2024) - Bridge DT Scientometric Review | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper 9.pdf | Binary PDF | Literature Corpus | Academic paper: Vibration-based structural health diagnosis | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper one.pdf | Binary PDF | Literature Corpus | Academic paper: Diana et al. (CEST 2025) - Urban Infrastructure DT Review | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/papers/paper4.pdf | Binary PDF | Literature Corpus | Academic thesis: Hu Wei Doctoral Dissertation - DT & AI in Building Maintenance | PDF Reader | No (Literature baseline) | Complete (Accessible) | Clean | PDF Reader |
| literature/scripts/deep_extract.py | Python Script | Literature Tool | PDF text extractor targeting future work, limitations, and research gaps | pypdf | No (Extraction utility) | Complete | Clean | None |
| literature/scripts/extract_papers.py | Python Script | Literature Tool | Automated extraction of abstracts and discussion sections across 15 papers | pypdf | No (Extraction utility) | Complete | Clean | None |
| literature/scripts/inspect_papers.py | Python Script | Literature Tool | CLI viewer for extracted paper summaries stored in papers_summary.json | None | No (CLI tool) | Incomplete (Requires papers_summary.json) | Stale dependency | None |
| literature/scripts/show_gaps.py | Python Script | Literature Tool | Formats and displays extracted gap statements from deep_gaps_extraction.json | None | No (CLI tool) | Incomplete (Requires deep_gaps_extraction.json) | Stale dependency | None |
| literature/scripts/summarize_all.py | Python Script | Literature Tool | Compiles a full multi-paper overview from papers_summary.json | None | No (CLI tool) | Incomplete (Requires papers_summary.json) | Stale dependency | None |
| literature/scripts/summarize_extra.py | Python Script | Literature Tool | Generates synthesis summaries from extra_papers_deep.json | None | No (CLI tool) | Incomplete (Requires extra_papers_deep.json) | Stale dependency | None |
| manuscript/INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf | Binary PDF | Deliverable | Publication-grade IEEE double-column PDF compiled via headless Chrome | Chrome / PDF Viewer | Yes (Primary manuscript deliverable) | Complete (1,287,734 bytes) | Clean | PDF Reader |
| manuscript/INTELLITWIN_RESEARCH_PAPER_IEEE_FORMAT.docx | Binary DOCX | Deliverable | Official IEEE Word document populated with full paper text, styles, and tables | Word / python-docx | Yes (Primary manuscript deliverable) | Complete (2,531,198 bytes) | Clean | Microsoft Word |
| manuscript/RESEARCH_PAPER_INTELLITWIN.md | Markdown | Manuscript Source | Full academic research paper manuscript (8,000+ words, 8 sections, 5 tables) | None | Yes (Manuscript source) | Complete | Clean (Aligned to IntelliTwin) | None |
| manuscript/build_double_column_paper.py | Python Script | Build Tool | Generates self-contained HTML and compiles PDF using headless Chrome | subprocess (Chrome) | Yes (PDF compilation) | Complete | Hardcodes Chrome path on Windows | Google Chrome |
| manuscript/generate_ieee_paper_docx.py | Python Script | Build Tool | Populates IEEE-paper-format-template.docx with complete manuscript content | python-docx | Yes (Word compilation) | Complete | Clean | None |
| manuscript/intellitwin_journal_submission_package.zip | Binary ZIP | Deliverable | Pre-built complete journal submission bundle containing docx, pdf, md, bib, figs | zipfile | Yes (Submission package) | Complete (9,314,014 bytes) | Clean | Archive utility |
| manuscript/main.tex | LaTeX Source | Manuscript Source | Legacy LaTeX source code for research paper | LaTeX / pdflatex | No (Not used by current build scripts) | Complete (32,523 bytes) | Severely Stale (Contains UQ-DT and consortium authors) | TeX Live / MiKTeX |
| manuscript/package_submission.py | Python Script | Build Tool | Packages manuscript deliverables, figures, and root docs into submission ZIP | zipfile | Yes (Packaging tool) | Complete | References legacy UQ-DT zip names | None |
| manuscript/references.bib | BibTeX | Manuscript Source | Academic citations formatted in BibTeX, ordered in descending publication year | None | Yes (Citation source) | Complete (30+ references) | Clean | BibTeX parser |
| manuscript/research_paper_double_column.html | HTML | Manuscript Source | Standalone self-contained HTML publication document with base64 figures & CSS | None | Yes (Intermediate / viewable paper) | Complete (1,436,575 bytes) | Clean | Web Browser |
| setup.py | Python | Configuration | Setup package configuration | setuptools | Yes (Installation) | Complete | Clean | None |
| 	ests/test_intellitwin.py | Python Source | Test Suite | Unit test suite verifying data loader, conformal calibrator, handlers, and metrics | pytest / unittest | Yes (Verification suite) | Complete (6 test cases, 100% pass) | Clean | pytest / unittest |

