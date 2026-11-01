# Phase 6 — Proposed Methodology

**Project:** IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance  
**Institution:** Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad  
**Affiliating University:** Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow  
**Department:** Information Technology  
**Academic Session:** 2026–2027  
**Project Guide:** Dr. Ruchi Gupta  
**Project Group ID:** CSIT 4 2023-27/IT/SECTION/GID  
**Phase Status:** Phase 6 (Proposed Methodology) — **COMPLETED (AWAITING USER APPROVAL)**  
**Date:** November 1, 2026  

---

## 1. Project Team Roster (Official Order)

| S.No. | Student Name | University Roll Number | Department |
| :---: | :--- | :--- | :--- |
| 1 | **Shiksha Pandey** | 2300270110112 | Information Technology |
| 2 | **Mayank Singh** | 2300270310115 | Information Technology |

*Verification:* Automated scanning confirmed **zero occurrences** of former non-contributing members across all Phase 6 files and project records. Dr. Ruchi Gupta is strictly designated as Faculty Project Guide.

---

## 2. Deliverables Summary

The following core deliverables are provided in `synopsis/Phase_6_Proposed_Methodology/`:

| File Name | Format | Description | Page / Word Budget |
| :--- | :---: | :--- | :---: |
| [`proposed_methodology.docx`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_6_Proposed_Methodology/proposed_methodology.docx) | Word (`.docx`) | Fully editable Microsoft Word document adhering to AKGEC synopsis specifications (A4, Left: 1.5", Top/Bottom/Right: 1.0", Times New Roman, 1.5 line spacing). | 10 Pages |
| [`proposed_methodology.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_6_Proposed_Methodology/proposed_methodology.pdf) | PDF (`.pdf`) | Publication-quality high-resolution vector PDF rendered via Chrome Headless. | 10 Pages |
| [`proposed_methodology.tex`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_6_Proposed_Methodology/proposed_methodology.tex) | LaTeX (`.tex`) | Standalone, Overleaf-compatible LaTeX source conforming to AKGEC template structure and IEEE reference formatting. | 2,418 words (excluding refs) |
| [`proposed_methodology.html`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_6_Proposed_Methodology/proposed_methodology.html) | HTML/CSS | Print-optimized HTML layout matching institutional typography, margins, and print rules. | Screen / Print |
| [`generate_proposed_methodology.py`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_6_Proposed_Methodology/generate_proposed_methodology.py) | Python (`.py`) | Automation script ensuring 100% deterministic generation of `.docx` and `.pdf` artifacts. | Reproducibility script |
| [`README.md`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/synopsis/Phase_6_Proposed_Methodology/README.md) | Markdown | Phase 6 metadata, architectural structure, mathematical formulation audit, and compliance documentation. | Documentation |

---

## 3. Structural Breakdown & Mathematical Formulation Audit

The methodology section is structured into eight core subsections reflecting the complete end-to-end IntelliTwin engineering and scientific workflow:

### 6.1 Methodological Framework and Algorithmic Overview (~310 words)
- Formulates the overarching 7-stage architectural pipeline: (1) Causal telemetry ingestion; (2) Dual base prognostic estimation; (3) Engine-weighted asymmetric conformal calibration; (4) Condition-adaptive regime/wear-stage partitioning; (5) Discrete-event sequential maintenance simulation; (6) Matched-conservatism attribution auditing; and (7) Digital Twin replay synchronization.
- Directly addresses the core gap in current literature: the uncoupled silos of prognostic point estimation, marginal coverage calibration, and operational maintenance decision economics.

### 6.2 Telemetry Ingestion, Anti-Leakage Windowing and Normalization (~420 words)
- **Benchmark Corpus**: NASA C-MAPSS sub-corpora (FD002 multi-regime primary with 260 train / 259 test engines; FD001 single-condition control with 100 train / 100 test engines; FD004 multi-regime multi-fault robustness with 249 train / 248 test engines).
- **Causal Sliding Lookback Window**: Fixed horizon $W = 30$ cycles:
  $$\mathbf{X}_i(t) = [\mathbf{x}_i(t - W + 1), \dots, \mathbf{x}_i(t)]^T \in \mathbb{R}^{W \times d}$$
  strictly preventing temporal data snooping. Warm-up cycles ($1 \le t < W$) defer inference until complete historical telemetry is accumulated.
- **Sensor Pruning**: Drops six invariant channels displaying zero variance or rank-correlation across operating regimes:
  $$\mathcal{S}_{\text{dropped}} = \{ s_1 \text{ (T2)}, s_5 \text{ (P2)}, s_6 \text{ (P15)}, s_{10} \text{ (epr)}, s_{16} \text{ (farB)}, s_{19} \text{ (Nf\_dmd)} \}$$
  retaining $d = 17$ dimensions (3 flight settings + 14 degradation sensors).
- **Anti-Leakage Normalization**: Training-only Z-score standardization parameters $(\boldsymbol{\mu}_{\text{train}}, \boldsymbol{\sigma}_{\text{train}})$ applied immutably across downstream splits, with complete engine-level split isolation.

### 6.3 Base Prognostic Regression Models (~350 words)
- **Target RUL Formulation**: Piece-wise linear ground truth capped at $R_{\text{max}} = 125$ cycles:
  $$y_i^*(t) = \min(R_{\text{max}}, T_i - t)$$
- **HistGradientBoostingRegressor (GBR)**: Histogram-binned gradient-boosted decision trees over flattened 510-dimensional window vectors $\mathbf{v}_i(t) = \text{vec}(\tilde{\mathbf{X}}_i(t))$ minimizing asymmetric pinball loss:
  $$\mathcal{L}_{\rho}(y, \hat{y}) = \max(\rho(y - \hat{y}), (1 - \rho)(\hat{y} - y))$$
  for quantiles $\rho \in \{0.05, 0.50, 0.95\}$.
- **PyTorch Bidirectional LSTM**: Deep sequence model with 2 stacked bidirectional LSTM layers ($h = 64$), variational recurrent dropout ($p = 0.20$), LeakyReLU projection head, and AdamW optimization under Mean Squared Error loss.
- **Checkpoints**: Full 30-model benchmark matrix (3 datasets $\times$ 2 model architectures $\times$ 5 frozen seeds `[2026..2030]`) registered under ADR-018.

### 6.4 Condition-Adaptive Hierarchical Conformal Calibration (~480 words)
- **Asymmetric Nonconformity Scoring**: Incorporates dynamic shape factors to reflect the operational risk disparity between overestimation ($\hat{y} > y$, unscheduled failure) and underestimation ($\hat{y} < y$, premature overhaul):
  $$\sigma(\hat{p}) = \left(1 + \frac{\hat{p}}{125}\right)^\gamma, \quad z(\hat{p}) = \exp\left(-\frac{\hat{p}}{20}\right)$$
  $$a(\hat{p}) = \sigma(\hat{p}) \exp(\beta z(\hat{p})), \quad b(\hat{p}) = \sigma(\hat{p}) \exp(-\beta z(\hat{p}))$$
  $$s_i(t) = \max\left( \frac{\hat{p}_i(t) - y_i(t)}{a(\hat{p}_i(t))}, \frac{y_i(t) - \hat{p}_i(t)}{b(\hat{p}_i(t))}, 0 \right)$$
- **Engine-Weighted Hierarchical Empirical CDF**: Resolves non-exchangeability and unequal asset trajectory lengths by assigning weight $w_{i,t} = \frac{1}{m \cdot n_i}$:
  $$F_{\text{dev}}(q) = \frac{1}{m} \sum_{i=1}^m \left[ \frac{1}{n_i} \sum_{t=1}^{n_i} \mathbb{I}(s_{i,t} \le q) \right]$$
  guaranteeing finite-sample coverage validity targeting $1 - \alpha = 0.90$ under cluster exchangeability.
- **Condition-Adaptive Regime Partitioning**: Stratifies calibration scores into $K = 6$ flight condition clusters to eliminate localized undercoverage during high-stress operational modes.
- **Exact Interval Inversion**:
  $$L_i(t) = \max(0, \hat{p}_i(t) - \hat{q}_{1-\alpha} \cdot a(\hat{p}_i(t))), \quad U_i(t) = \hat{p}_i(t) + \hat{q}_{1-\alpha} \cdot b(\hat{p}_i(t))$$

### 6.5 Discrete-Event Sequential Maintenance Utility Simulation (~290 words)
- **Sequential Stopping Time**: Evaluates lower conformal bound $L_i(t)$ at each operating cycle:
  $$\tau_i = \inf \{ t \ge W : L_i(t) \le \theta \}$$
- **Standardized Cost Units (SCU)**:
  $$\text{Cost}_i(\tau_i) = \begin{cases} C_{\text{PM}} + C_{\text{WASTE}} \cdot (T_i - \tau_i), & \text{if } \tau_i < T_i \text{ (Planned PM)} \\ C_{\text{FAIL}}, & \text{if } \tau_i \ge T_i \text{ (In-Service Failure)} \end{cases}$$
  with standardized weights: $C_{\text{PM}} = 1.0$ SCU, $C_{\text{FAIL}} = 5.0$ SCU, $C_{\text{WASTE}} = 0.20$ SCU/cycle.

### 6.6 Controlled Attribution Protocol (Matched-Conservatism Baselines) (~220 words)
- Disambiguates genuine uncertainty calibration value from trivial over-conservatism across three pre-registered baseline families:
  1. *Uniformly Widened Conformal Intervals ($\delta$-Widened)*: $\hat{q}' = \hat{q} + \delta$.
  2. *Point-Prediction Safety Margins ($\Delta$-Margin)*: $\hat{p}'(t) = \hat{p}(t) - \Delta$.
  3. *Earlier Scheduled Intervention Thresholds ($\theta$-Offset)*: $\theta' = \theta + \tau_{\text{advance}}$.
- Attribution requires statistically significant cost superiority ($\Delta_{\text{cost}} > 0.20$ SCU) against *all* matched-control families.

### 6.7 Statistical Inference Protocol and Decision Rules (~160 words)
- **10,000 Engine-Level Cluster Bootstrap Draws**: Preserves intra-engine autocorrelation while estimating percentile confidence intervals.
- **Bonferroni Family-Wise Error Rate Control**: $\alpha_{\text{test}} = \frac{0.05}{4} = 0.0125$ (98.75% CI).
- **Two One-Sided Tests (TOST) Equivalence**: Confirms non-harm across all six evaluation cells:
  $$\text{Lower } 98.75\% \text{ CI of } \Delta_{\text{cost}} \ge -0.20 \text{ SCU}, \quad \text{Lower } 98.75\% \text{ CI of } \Delta_{\text{error}} \ge -0.01$$

### 6.8 Digital Twin Synchronization Replay Prototype (~190 words)
- **ISO 23247 Synchronization**: `TwinReplayEngine` streaming causal sliding windows, training Z-scores, dual inference, conformal bounds, dynamic Health Index $\text{HI}_i(t) = \min(1.0, \frac{\hat{p}_i(t)}{R_{\text{max}}})$, and multi-stage status alerts (NOMINAL, ADVISORY, CRITICAL_INTERVENTION).
- **Numerical Parity Audit**: Verified parity against offline batch computation:
  $$\max_t | \hat{p}_{\text{stream}}(t) - \hat{p}_{\text{batch}}(t) | \le 10^{-4}, \quad \max_t | L_{\text{stream}}(t) - L_{\text{batch}}(t) | \le 10^{-4}$$
  across 37 automated pytest modules, backing the FastAPI service and operator dashboard.

---

## 4. Algorithmic Traceability Matrix

| Methodological Stage | Mathematical / Algorithmic Formulation | Source Code Module | Verification Suite / Pytest | Research Question Addressed |
| :---: | :--- | :--- | :--- | :---: |
| **Stage 1** | Causal windowing ($W=30$), 17-feature selection, training Z-scores | `src/intellitwin/data/` | `tests/test_data_pipeline.py` | Foundational |
| **Stage 2** | HistGBR (pinball loss) & PyTorch BiLSTM (MSE loss), 30 models | `src/intellitwin/models/` | `tests/test_models.py` | Foundational |
| **Stage 3** | Engine-weighted hierarchical empirical CDF, asymmetric score | `src/intellitwin/calibration/` | `tests/test_calibration.py` | RQ1, RQ2 |
| **Stage 4** | K-means regime clustering ($K=6$), degradation wear bins | `src/intellitwin/calibration/` | `tests/test_regime_clustering.py` | RQ2 |
| **Stage 5** | Discrete-event sequential stopping rule $\tau_i$, SCU lifecycle cost | `src/intellitwin/simulation/` | `tests/test_simulation.py` | RQ1 |
| **Stage 6** | Matched-conservatism controls ($\delta$-widening, $\Delta$-margin, $\theta$-offset) | `src/intellitwin/evaluation/` | `tests/test_matched_controls.py` | RQ3 |
| **Stage 7** | 10k cluster bootstrap, Bonferroni $\alpha=0.0125$, TOST non-harm | `src/intellitwin/confirmatory/` | `tests/test_confirmatory.py` | RQ4 |
| **Stage 8** | Digital twin replay, state sync, parity $\le 10^{-4}$, FastAPI | `src/intellitwin/twin/`, `src/intellitwin/api/` | `tests/test_twin_replay.py` | Implementation Parity |

---

## 5. Compliance Verification Checklist

- [x] **Institutional Heading & Typography**: Main heading 14pt bold, Subheadings 12pt bold, Times New Roman body 12pt, 1.5 line spacing.
- [x] **Margin Compliance**: Left margin 1.5" (38.1 mm), Top, Bottom, and Right margins 1.0" (25.4 mm).
- [x] **IEEE Bibliographic Referencing**: 14 formal references `[1]`--`[14]` matching repository literature matrix and peer-reviewed bibliographic entries.
- [x] **Strict Roster Verification**: Exactly two student members (Shiksha Pandey & Mayank Singh). Zero mentions of former members. Dr. Ruchi Gupta properly identified as Project Guide.
- [x] **Mathematical Soundness**: All equations fully typed, numbered, and consistent with the codebase implementation in `src/intellitwin/`.
- [x] **Deterministic Reproduction**: `generate_proposed_methodology.py` produces bit-for-bit reproducible `.docx` and high-resolution vector `.pdf` files.
