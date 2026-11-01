# Phase 5 — Objectives and Scope

**Project:** IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance  
**Institution:** Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad  
**Affiliating University:** Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow  
**Department:** Information Technology  
**Academic Session:** 2026–2027  
**Project Guide:** Dr. Ruchi Gupta  
**Project Group ID:** CSIT 4 2023-27/IT/SECTION/GID  
**Phase Status:** Phase 5 (Objectives and Scope) — **COMPLETED (AWAITING USER APPROVAL)**  
**Date:** November 1, 2026  

---

## 1. Project Team Roster (Official Order)

| S.No. | Student Name | University Roll Number | Department |
| :---: | :--- | :--- | :--- |
| 1 | **Shiksha Pandey** | 2300270110112 | Information Technology |
| 2 | **Mayank Singh** | 2300270310115 | Information Technology |

*Verification:* Automated scans confirmed **zero occurrences** of former non-contributing members across all Phase 5 files and project records.

---

## 2. Deliverables Summary

The following core deliverables are provided in `synopsis/Phase_5_Objectives_and_Scope/`:

| File Name | Format | Description | Page / Word Budget |
| :--- | :---: | :--- | :---: |
| [`objectives_and_scope.docx`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_5_Objectives_and_Scope/objectives_and_scope.docx) | Word (`.docx`) | Fully editable Microsoft Word document adhering to AKGEC synopsis specifications (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing). | 8 Pages |
| [`objectives_and_scope.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_5_Objectives_and_Scope/objectives_and_scope.pdf) | PDF (`.pdf`) | Publication-quality high-resolution vector PDF rendered via Chrome Headless. | 8 Pages |
| [`objectives_and_scope.tex`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_5_Objectives_and_Scope/objectives_and_scope.tex) | LaTeX (`.tex`) | Standalone, Overleaf-compatible LaTeX source conforming to AKGEC template structure. | 1,421 words (excluding refs) |
| [`objectives_and_scope.html`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_5_Objectives_and_Scope/objectives_and_scope.html) | HTML/CSS | Print-optimized HTML layout matching institutional typography, margins, and print rules. | Screen / Print |
| [`generate_objectives_and_scope.py`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_5_Objectives_and_Scope/generate_objectives_and_scope.py) | Python (`.py`) | Automation script ensuring 100% deterministic generation of `.docx` and `.pdf` artifacts. | Reproducibility script |
| [`README.md`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_5_Objectives_and_Scope/README.md) | Markdown | Phase 5 metadata, architectural structure, traceability matrix, and compliance documentation. | Documentation |

---

## 3. Structural Breakdown & Word Count Audit

The section is organized into six core subsections following departmental requirements:

### 5.1 Aim of the Project (~280 words)
- Formulates the overarching purpose of IntelliTwin: bridging data-driven RUL prognostic regression, finite-sample distribution-free uncertainty calibration, and sequential operational maintenance decision-making for safety-critical industrial rotational assets.
- Contextualizes this aim within cyber-physical systems and aerospace safety standards, explaining why uncalibrated point predictions fail in asymmetric operational risk environments ($C_{\text{FAIL}} \gg C_{\text{PM}}$).

### 5.2 Primary Objective (~140 words)
- States the central research objective:
  > *"To formulate, implement, and empirically validate an engine-weighted, condition-adaptive conformal calibration methodology for Remaining Useful Life (RUL) estimation that explicitly incorporates downstream sequential maintenance utility, achieving a statistically significant reduction in total lifecycle maintenance cost (exceeding 0.20 Standardized Cost Units per engine) while strictly preserving finite-sample prediction-interval coverage reliability across heterogeneous operating regimes without inducing trivial over-conservatism."*
- Directly operationalizes the pre-registered research gap (ADR-018) and provides an empirical evaluation mechanism for Research Question 1 (RQ1).

### 5.3 Specific Objectives (~530 words)
Eight concrete, measurable, and technically verifiable objectives traceable to the research design and implementation:
1. *Systematic Telemetry Ingestion and Anti-Leakage Preprocessing* (NASA C-MAPSS FD002 primary, FD001 control, FD004 robustness; 30-cycle causal sliding window $W=30$; 17-feature schema; training-only Z-score normalization; strict engine-level isolation).
2. *Development and Checkpoint Freezing of Base Prognostic Predictors* (`HistGradientBoostingRegressor` and PyTorch `LSTM`; 30-model benchmark matrix across 5 official seeds `[2026..2030]`).
3. *Formulation of Engine-Weighted Hierarchical Conformal Calibration* (asymmetric score inversion targeting 90% nominal coverage $1-\alpha=0.90$; engine-level weighting; condition-adaptive flight regime and degradation stage bins).
4. *Comprehensive Evaluation of Prediction Interval Validity and Sharpness* (empirical marginal coverage, MPIW, Winkler interval scores, worst-subgroup conditional coverage error $\Delta_{\text{error}} > 0.01$ without excessive width deterioration $D_{\text{width}} < 1.0$ cycle, addressing RQ2).
5. *Discrete-Event Sequential Maintenance Utility Simulation* (cycle-by-cycle stopping time $\tau_i$ triggered by lower conformal bounds $L_i(t)$; Standardized Cost Units: $C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$ per cycle).
6. *Decision-Value Attribution Analysis Against Matched-Conservatism Controls* (attribution testing against 3 matched-control baseline families: widened intervals, point-prediction safety margins, earlier scheduled overhaul heuristics, addressing RQ3).
7. *Cross-Condition, Multi-Model Robustness and Non-Harm Verification* (evaluating 6 mandatory cells: FD001, FD002, FD004 $\times$ GBR, LSTM across 5 seeds; weighted aggregate contrasts and non-harm bounds $\Delta_{\text{cost}} \ge -0.20$ SCU, $\Delta_{\text{error}} \ge -0.01$ under Bonferroni $\alpha=0.0125$, addressing RQ4).
8. *Development and Validation of Digital Twin Synchronization Replay Prototype* (`TwinReplayEngine` streaming telemetry with validation parity $\le 10^{-4}$ against batch execution; FastAPI REST API; HTML5/JS operator dashboard).

### 5.4 Scope of the Project (~310 words)
- *Research Domain*: Cyber-physical reliability engineering and digital twin operational decision support.
- *Asset & Dataset Domain*: NASA C-MAPSS turbofan corpus (FD002 primary multi-regime, FD001 single-condition control, FD004 cross-regime/cross-fault robustness).
- *Prognostic Task & Features*: Continuous RUL regression $y_i(t) = T_i - t$ for $t \ge 30$; 17-feature schema (14 sensors + 3 settings; 6 invariant sensors dropped).
- *Base Predictors & Calibration*: HistGBR and PyTorch LSTM; engine-weighted split conformal prediction ($1-\alpha=0.90$).
- *Decision Simulation*: Sequential threshold policy evaluated under SCU economic metrics.
- *Software Environment*: Python 3.12/3.13, PyTorch, scikit-learn, FastAPI, 37 pytest modules.

### 5.5 Scope Boundaries and Limitations (~220 words)
- Four explicit operational boundaries:
  1. *Trace-Driven Simulation vs. Live Hardware Ingestion*: Offline trace-driven replay engine (`TwinReplayEngine`); excludes physical IoT edge microcontrollers and live telemetry buses.
  2. *Advisory Decision Support vs. Closed-Loop Actuation*: Predictive recommendations and risk alerts for fleet managers; excludes autonomous physical closed-loop actuator control.
  3. *Benchmark Data vs. In-Flight Avionics Certification*: Evaluated on NASA C-MAPSS simulation; not certified under FAA/EASA DO-178C avionics standards.
  4. *Pre-Registered Evaluation vs. Confirmatory Outcome Claims*: Framed strictly as pre-registered hypotheses under test (ADR-018); avoids premature confirmatory outcome assertions.

### 5.6 Expected Scientific and Practical Contributions (~140 words)
- Methodological integration of condition-adaptive conformal prediction with sequential maintenance economics.
- Formal matched-conservatism attribution benchmark protocol.
- Modular, reproducible open-source digital twin replay architecture.

**Total Core Word Count:** **1,421 words** (Excluding references and titles).

---

## 4. Traceability Matrix (Objectives vs. Research Protocol)

| Specific Objective | Target Milestone / Capability | Research Questions | Experimental Mapping | Software / Codebase Module |
| :---: | :--- | :---: | :---: | :--- |
| **Obj 1** | Data ingestion, causal windowing ($W=30$), 17 features, anti-leakage splits | Foundations | Phase 3 Protocol | `src/intellitwin/data/` |
| **Obj 2** | Frozen base GBR and LSTM regressors (30 checkpoints across 5 seeds) | Foundations | Step 7 Matrix | `src/intellitwin/models/` |
| **Obj 3** | Engine-weighted hierarchical split conformal calibration ($1-\alpha=0.90$) | RQ1, RQ2 | Step 8 Calibration | `src/intellitwin/calibration/` |
| **Obj 4** | Prediction interval validity, sharpness, and conditional reliability diagnostics | RQ2 | Experiment B | `src/intellitwin/evaluation/` |
| **Obj 5** | Sequential discrete-event maintenance cost simulation (SCU metrics) | RQ1 | Experiment A | `src/intellitwin/simulation/` |
| **Obj 6** | Attribution analysis against 3 matched-conservatism control families | RQ3 | Experiment C | `src/intellitwin/evaluation/matched_controls/` |
| **Obj 7** | Multi-condition robustness and non-harm evaluation across 6 cells (Bonferroni $\alpha=0.0125$) | RQ4 | Experiment D | `src/intellitwin/confirmatory/` |
| **Obj 8** | Digital twin telemetry replay engine (parity $\le 10^{-4}$), FastAPI & dashboard | System Integration | Step 11 Prototype | `src/intellitwin/twin/`, `src/intellitwin/api/` |

---

## 5. Compliance Checklist (AKGEC Department Circular `AKGEC/IT/CSIT/26-27/PROJ-m`)

| Requirement | Prescribed Specification | Implemented Value | Compliance |
| :--- | :--- | :--- | :---: |
| **Page Format** | Standard A4 ($210 \times 297\text{ mm}$) | Standard A4 | **PASS** |
| **Margins** | Left: 1.5 in (38.1 mm); Top, Bottom, Right: 1.0 in (25.4 mm) | Left: 1.5 in; Top/Bottom/Right: 1.0 in | **PASS** |
| **Typography** | Times New Roman throughout | Times New Roman | **PASS** |
| **Heading Sizes** | Title: 18 pt Bold; Section: 14 pt Bold; Sub-section: 12 pt Bold | 18 pt / 14 pt / 12 pt | **PASS** |
| **Body Text** | 12 pt Regular, Justified, Nil Indentation, 1.5 Line Spacing | 12 pt, Justified, 0 Indent, 1.5 Spacing | **PASS** |
| **Team Membership** | Strictly Shiksha Pandey & Mayank Singh | 2 members verified; 0 former members | **PASS** |
| **Project Guide** | Dr. Ruchi Gupta (Faculty Guide) | Correctly designated as Guide | **PASS** |
| **Citation Standard** | IEEE Citation Format with bracketed numbering | IEEE format [1]–[14] | **PASS** |
| **Scientific Demarcation**| Framed as academic research design / pre-registered investigation | No premature confirmatory claims | **PASS** |
| **Scope Boundaries** | Explicit exclusion of physical IoT and closed-loop actuation | Stated clearly in Section 5.5 | **PASS** |

---

## 6. IEEE References Cited

1. **[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund**, "Damage propagation modeling for aircraft engine run-to-failure simulation," in *Proc. 2008 Int. Conf. Prognostics and Health Management (PHM)*, IEEE, 2008, pp. 1–9.
2. **[2] Z. Huang, Y. Shen, J. Li, M. Fey, and C. Brecher**, "A survey on AI-driven digital twins in Industry 4.0: Smart manufacturing and advanced robotics," *Sensors*, vol. 21, no. 19, p. 6340, 2021.
3. **[3] R. Diao, M. Zhou, G. Meng, and S. Wang**, "Turbofan engine remaining useful life prediction with reliable prediction intervals via LSTM-based quantile regression and conformal calibration," *Sensors*, vol. 26, no. 7, p. 2249, 2026.
4. **[4] A. Javanmardi and E. Hüllermeier**, "Conformal prediction intervals for remaining useful lifetime estimation," *Int. J. Progn. Health Manag.*, vol. 14, no. 2, pp. 1–14, 2023.
5. **[5] Z. Zhu, L. Wang, M. Chen, and X. Zhao**, "Predictive maintenance strategies for aero-engines considering remaining useful life prediction interval," *Qual. Reliab. Eng. Int.*, 2025.
6. **[6] C. Chen, J. Shi, N. Lu, Z. H. Zhu, and B. Jiang**, "Data-driven predictive maintenance strategy considering the uncertainty in remaining useful life prediction," *Neurocomputing*, vol. 494, pp. 79–88, 2022.
7. **[7] S. Cortes-Gomez, C. M. Patiño, Y. Byun, S. Wu, E. Horvitz, and B. Wilder**, "Utility-directed conformal prediction: A decision-aware framework for actionable uncertainty quantification," in *Int. Conf. Learn. Represent. (ICLR)*, 2025.
8. **[8] G. K. Walia and M. Kumar**, "Uncertainty-aware remaining useful life prediction and PPO based optimal maintenance scheduling in industrial IoT," *Reliab. Eng. Syst. Saf.*, p. 112356, 2026.
9. **[9] Y. Lee, R. F. Barber, and R. Willett**, "Distribution-free inference with hierarchical data," *arXiv preprint arXiv:2306.06342*, 2023.
10. **[10] C. D. Robinson**, "Remaining useful life estimation for aircraft engines with risk-aware prediction intervals via conformalized quantile regression," *Int. J. Progn. Health Manag.*, vol. 17, no. 1, p. 4724, 2026.
11. **[11] T. Gneiting and A. E. Raftery**, "Strictly proper scoring rules, prediction, and estimation," *J. Am. Stat. Assoc.*, vol. 102, no. 477, pp. 359–378, 2007.
12. **[12] D. Lakens**, "Equivalence tests: A practical primer for t tests, correlations, and meta-analyses," *Soc. Psychol. Personal. Sci.*, vol. 8, no. 4, pp. 355–362, 2017.
13. **[13] J. Wu, Y. Zhou, X. Wang, C. Chen, Y. Ma, and C. Zhang**, "Research on remaining useful life prediction of equipment based on digital twins," *Sensors*, vol. 26, no. 4, p. 1240, 2026.
14. **[14] ISO 23247-1:2021**, "Automation systems and integration — Digital twin framework for manufacturing — Part 1: Overview and general principles," International Organization for Standardization, Geneva, Switzerland, 2021.
