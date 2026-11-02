# Phase 7 — System Architecture and Workflow

**Project:** IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance  
**Institution:** Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad  
**Affiliating University:** Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow  
**Department:** Information Technology  
**Academic Session:** 2026–2027  
**Project Guide:** Dr. Ruchi Gupta  
**Project Group ID:** CSIT 4 2023-27/IT/SECTION/GID  
**Phase Status:** Phase 7 (System Architecture and Workflow) — **COMPLETED (AWAITING USER APPROVAL)**  
**Date:** November 2, 2026  

---

## 1. Project Team Roster (Official Order)

| S.No. | Student Name | University Roll Number | Department |
| :---: | :--- | :--- | :--- |
| 1 | **Shiksha Pandey** | 2300270110112 | Information Technology |
| 2 | **Mayank Singh** | 2300270310115 | Information Technology |

*Verification:* Automated scanning confirmed **zero occurrences** of former non-contributing members across all Phase 7 files and project records. Dr. Ruchi Gupta is strictly designated as Faculty Project Guide.

---

## 2. Deliverables Summary

The following core deliverables are provided in `synopsis/Phase_7_System_Architecture/`:

| File Name | Format | Description | Page / Word Budget |
| :--- | :---: | :--- | :---: |
| [`system_architecture.docx`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_7_System_Architecture/system_architecture.docx) | Word (`.docx`) | Fully editable Microsoft Word document adhering to AKGEC synopsis specifications (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing). | 10 Pages (13.0 KB) |
| [`system_architecture.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_7_System_Architecture/system_architecture.pdf) | PDF (`.pdf`) | Publication-quality high-resolution vector PDF rendered via Chrome Headless containing crisp embedded vector figures. | 10 Pages (509.4 KB) |
| [`system_architecture.tex`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_7_System_Architecture/system_architecture.tex) | LaTeX (`.tex`) | Standalone, Overleaf-compatible LaTeX source conforming to AKGEC template structure, IEEE reference formatting, and native TikZ diagrams. | 2,112 words (excluding refs/TikZ) |
| [`system_architecture.html`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_7_System_Architecture/system_architecture.html) | HTML/CSS | Print-optimized HTML layout matching institutional typography, margins, and inline high-resolution SVG diagrams. | Screen / Print |
| [`generate_system_architecture.py`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_7_System_Architecture/generate_system_architecture.py) | Python (`.py`) | Automation script ensuring 100% deterministic, bit-for-bit reproducible generation of `.docx` and `.pdf` artifacts. | Reproducibility script |
| [`README.md`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_7_System_Architecture/README.md) | Markdown | Phase 7 metadata, architectural tier breakdown, diagram specifications, traceability matrix, and compliance documentation. | Documentation |

---

## 3. Structural Breakdown & Architectural Tier Audit

The architecture section covers the end-to-end IntelliTwin engineering pipeline across seven comprehensive subsections:

### 7.1 Architectural Overview and Multi-Tier Decomposition (~360 words)
- Formulates the overarching 5-tier decoupled cyber-physical architecture:
  1. *Tier 1: Data Ingestion & Anti-Leakage Preprocessing Tier*
  2. *Tier 2: Prognostic Base Inference Tier*
  3. *Tier 3: Hierarchical Conformal Calibration Tier*
  4. *Tier 4: Sequential Decision & Maintenance Simulation Tier*
  5. *Tier 5: Digital Twin Synchronization & Presentation Tier*
- **Physical Integration Demarcation**: Explicitly establishes that the architecture operates on offline trace-driven replay of NASA C-MAPSS run-to-failure telemetry. Excludes live physical aircraft/engine hardware, live IoT bus protocols (MQTT, OPC UA), and autonomous closed-loop physical actuation.
- **Strict Anti-Leakage Boundary**: Enforces an impermeable boundary around held-out test engines; oracle failure times and true RUL are private to offline post-hoc scoring routines.

### 7.2 Data Ingestion, Normalization, and Causal Windowing Pipeline (~430 words)
- **C-MAPSS Data Schema**: 26 raw columns (engine ID, cycle index, 3 settings, 21 sensors).
- **Invariant Sensor Pruning**: Dropping six invariant or uninformative channels:
  $$\mathcal{S}_{\text{dropped}} = \{ s_1 \text{ (T2)}, s_5 \text{ (P2)}, s_6 \text{ (P15)}, s_{10} \text{ (epr)}, s_{16} \text{ (farB)}, s_{19} \text{ (Nf\_dmd)} \}$$
  retaining $d = 17$ informative channels (3 flight settings + 14 thermo-mechanical sensors).
- **Strict Engine-Level Split Partitioning**:
  - FD001 (Single-regime control): 50 Train / 20 Cal / 10 Val / 20 Test.
  - FD002 (Multi-regime primary): 130 Train / 52 Cal / 26 Val / 52 Test.
  - FD004 (Multi-regime multi-fault): 124 Train / 50 Cal / 25 Val / 50 Test.
- **Training-Only Normalization & Regime Clustering**: Z-scores $(\boldsymbol{\mu}_{\text{train}}, \boldsymbol{\sigma}_{\text{train}})$ with `ddof=0`; K-means clustering ($K = 6$) on standardized operating settings $(z_1, z_2, z_3)$.
- **Causal Sliding Lookback Window**: Fixed horizon $W = 30$ cycles with stride 1:
  $$\mathbf{X}_i(t) \in \mathbb{R}^{30 \times 17}$$
  Warm-up cycles ($1 \le t < 30$) defer inference without zero-padding. Dual representations: $30 \times 17$ 2D sequential tensor (LSTM) and 510-dim 1D C-order vector (GBR).

### 7.3 Prognostic Base Inference Tier (~320 words)
- **Dual Target Formulations**: Piecewise-linear capped training targets $y_{\text{train}, i}(t) = \min(R_{\text{max}}, T_i - t)$ with $R_{\text{max}} = 125$ cycles vs. uncapped evaluation targets $y_{\text{eval}, i}(t) = T_i - t$.
- **HistGradientBoostingRegressor (GBR)**: Histogram-binned quantile regression trees over flattened 510-dim vectors minimizing asymmetric pinball loss for $\rho \in \{0.05, 0.50, 0.95\}$.
- **PyTorch Bidirectional LSTM**: Two stacked bidirectional LSTM recurrent layers ($h = 64$), variational recurrent dropout ($p = 0.20$), LeakyReLU projection head, AdamW optimizer.
- **Registry**: 30 frozen model checkpoints (3 datasets $\times$ 2 architectures $\times$ 5 seeds `[2026..2030]`) under ADR-018.

### 7.4 Hierarchical Conformal Calibration and Interval Inversion Workflow (~440 words)
- **Asymmetric Nonconformity Scoring**: Parameterized shape factors:
  $$\sigma(\hat{p}) = \left(1 + \frac{\hat{p}}{125}\right)^\gamma, \quad z(\hat{p}) = \exp\left(-\frac{\hat{p}}{20}\right)$$
  $$a(\hat{p}) = \sigma(\hat{p}) \exp(\beta z(\hat{p})), \quad b(\hat{p}) = \sigma(\hat{p}) \exp(-\beta z(\hat{p}))$$
  $$s_i(t) = \max\left( \frac{\hat{p}_i(t) - y_i(t)}{a(\hat{p}_i(t))}, \frac{y_i(t) - \hat{p}_i(t)}{b(\hat{p}_i(t))}, 0 \right)$$
  with candidate parameters $\gamma = 2, \beta = -\ln 2 \approx -0.693147$.
- **Exact Engine-Weighted Quantile Solver**: Resolves cluster non-exchangeability by assigning weights $w_{i,t} = \frac{1}{(m+1)n_i}$:
  $$F_{\text{dev}}(q) = \frac{1}{m+1} \sum_{i=1}^m \left[ \frac{1}{n_i} \sum_{t=1}^{n_i} \mathbb{I}(s_{i,t} \le q) \right]$$
  Finite mass equals $\frac{m}{m+1}$ with point-at-infinity $\frac{1}{m+1}$, targeting nominal $1-\alpha = 0.90$.
- **Closed-Form Interval Inversion**:
  $$L_i(t) = \max(0, \hat{p}_i(t) - \hat{q}_{1-\alpha} a(\hat{p}_i(t))), \quad U_i(t) = \hat{p}_i(t) + \hat{q}_{1-\alpha} b(\hat{p}_i(t))$$

### 7.5 Discrete-Event Sequential Maintenance Utility Simulation Workflow (~290 words)
- **Stopping Rule**: $\tau_i = \inf \{ t \ge W : L_i(t) \le 1.0 \text{ cycle} \}$.
- **Standardized Cost Units (SCU)**: Planned overhaul $C_{\text{PM}} = 1.0$ SCU, in-service failure $C_{\text{FAIL}} = 5.0$ SCU, discarded useful life $C_{\text{WASTE}} = 0.20$ SCU/cycle.
- **Controlled Attribution Protocol**: Benchmark against three matched-conservatism control families ($\delta$-widened intervals, $\Delta$-safety margins, $\theta$-earlier intervention thresholds).
- **Inference**: 10,000 engine-level cluster bootstrap resamples, Bonferroni $\alpha = 0.0125$, and TOST non-harm bounds.

### 7.6 Digital Twin State Synchronization and Replay Engine (~280 words)
- **Thread-Safe Replay State Machine**: Four-state lifecycle (`WARMING_UP`, `ACTIVE`, `MAINTAINED`, `FAILED`) managed under mutual exclusion locks.
- **Numerical Parity Guarantee**: $\max_t | \hat{p}_{\text{stream}}(t) - \hat{p}_{\text{batch}}(t) | \le 10^{-4}$ and $\max_t | L_{\text{stream}}(t) - L_{\text{batch}}(t) | \le 10^{-4}$ verified by 37 automated pytest modules.
- **FastAPI Service & Operator Dashboard**: Endpoints (`/api/health`, `/api/catalog`, `/api/sessions`, `/advance`, `/reset`, `/trace.csv`) linked to an interactive HTML5/JS dashboard with real-time sensor charts, conformal bands, Health Index dials, and status indicators.

### 7.7 Architectural Schematics and Workflow Diagrams
- **Figure 7.1**: Multi-Tier System Architecture & Offline Evaluation Boundary (Data partition, training, calibration, frozen policy, simulation replay, and digital twin engine).
- **Figure 7.2**: Causal Sliding-Window Formulation ($W=30$), Dual Tensor/Vector Representation Mappings, and Target Ground Truth Assignment.
- **Figure 7.3**: Cycle-by-Cycle Digital Twin Replay Engine and Sequential Maintenance Decision Workflow (Decision tree from ingestion, warm-up check, feature extraction, dual forward pass, conformal calibration, PM dispatch at $L(t) \le 1.0$, terminal failure check, to live telemetry streaming).

---

## 4. Architectural Traceability Matrix

| Architectural Tier | Function / Responsibility | Primary Code Module | Test Suite / Pytest | Research Question Addressed |
| :---: | :--- | :--- | :--- | :---: |
| **Tier 1** | C-MAPSS ingestion, 17-feature selection, training Z-scores, $W=30$ windowing | `src/intellitwin/data/` | `tests/test_data_pipeline.py` | Foundational |
| **Tier 2** | HistGBR (pinball loss) & PyTorch BiLSTM (MSE loss), 30 frozen checkpoints | `src/intellitwin/models/` | `tests/test_models.py` | Foundational |
| **Tier 3** | Asymmetric score $s_i(t)$, engine-weighted empirical CDF, interval inversion | `src/intellitwin/uncertainty/` | `tests/test_calibration.py` | RQ1, RQ2 |
| **Tier 4** | Sequential stopping rule $\tau_i$, SCU lifecycle cost accounting, matched controls | `src/intellitwin/simulator/`, `decision/` | `tests/test_simulation.py` | RQ1, RQ3 |
| **Tier 5** | 10k cluster bootstrap, Bonferroni $\alpha=0.0125$, TOST non-harm verification | `src/intellitwin/evaluation/` | `tests/test_confirmatory.py` | RQ4 |
| **Tier 6** | `TwinReplayEngine`, thread-safe state machine, parity $\le 10^{-4}$, FastAPI API | `src/intellitwin/twin/`, `apps/twin_dashboard/` | `tests/test_twin_replay.py` | Implementation Parity |

---

## 5. Compliance Verification Checklist

- [x] **Institutional Heading & Typography**: Main heading 14pt bold, Subheadings 12pt bold, Times New Roman body 12pt, 1.5 line spacing.
- [x] **Margin Compliance**: Left margin 1.5" (38.1 mm), Top, Bottom, and Right margins 1.0" (25.4 mm).
- [x] **IEEE Bibliographic Referencing**: 14 formal references `[1]`–`[14]` matching repository literature matrix and peer-reviewed bibliographic entries.
- [x] **Strict Roster Verification**: Exactly two student members (Shiksha Pandey & Mayank Singh). Zero mentions of former members. Dr. Ruchi Gupta properly identified as Project Guide.
- [x] **Visual Evidence & Diagrams**: Three high-resolution visual diagrams (Figures 7.1, 7.2, and 7.3) rendered natively in LaTeX TikZ, HTML/CSS inline SVG, and formatted OpenXML callouts.
- [x] **Deterministic Reproduction**: `generate_system_architecture.py` produces bit-for-bit reproducible `.docx` and high-resolution vector `.pdf` files.
