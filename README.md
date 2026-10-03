# IntelliTwin: An AI-Driven Digital Twin Framework for Predictive Maintenance of Engineering Assets

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Dataset: NASA C-MAPSS](https://img.shields.io/badge/Dataset-NASA%20C--MAPSS%20FD001-orange.svg)](data/cmapss/)
[![Conformal Coverage](https://img.shields.io/badge/Conformal%20Coverage-95.00%25-brightgreen.svg)](#empirical-performance-on-nasa-c-mapss)
[![Catastrophic Prevention](https://img.shields.io/badge/Catastrophic%20Prevention-100%25-emerald.svg)](#catastrophic-failure-prevention)

An end-to-end, publication-grade research framework and industrial cyber-physical software suite for predictive maintenance of engineering assets. IntelliTwin synchronizes multi-modal physical sensor telemetry with a dynamic virtual representation that decouples operational variations from structural wear, provides finite-sample calibrated uncertainty bounds for Remaining Useful Life (RUL), and triggers automated maintenance actions via a factory-floor dashboard.

---

## 👥 Authors & Affiliations
* **Mayank Singh** — *Department of Electronics and Communication Engineering (ECE)*, Ajay Kumar Garg Engineering College, Ghaziabad, India (`mayanksingh2745@gmail.com`)
* **Shiksha Pandey** — *Department of Information Technology (IT)*, Ajay Kumar Garg Engineering College, Ghaziabad, India (`shikshapandey2004@gmail.com`)
* **Ruchi Gupta** — *Department of Information Technology (IT)*, Ajay Kumar Garg Engineering College, Ghaziabad, India (`ruchigupta@akgec.ac.in`)

---

## 📖 Research Paper Manuscripts & Deliverables

The complete, submission-ready academic research manuscripts and packages:
* **IEEE Word Document (DOCX):** [`manuscript/INTELLITWIN_RESEARCH_PAPER_IEEE_FORMAT.docx`](manuscript/INTELLITWIN_RESEARCH_PAPER_IEEE_FORMAT.docx)
* **IEEE Double-Column PDF:** [`manuscript/INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf`](manuscript/INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf)
* **Interactive HTML Publication Paper:** [`manuscript/research_paper_double_column.html`](manuscript/research_paper_double_column.html)
* **Academic Markdown Source (8,000+ words):** [`manuscript/RESEARCH_PAPER_INTELLITWIN.md`](manuscript/RESEARCH_PAPER_INTELLITWIN.md)
* **BibTeX References (Descending Publication Year):** [`manuscript/references.bib`](manuscript/references.bib)
* **Complete Journal Submission Package (ZIP):** [`manuscript/intellitwin_journal_submission_package.zip`](manuscript/intellitwin_journal_submission_package.zip)
* **Step-by-Step Execution Guide:** [`COMMANDS_TO_RUN.txt`](COMMANDS_TO_RUN.txt)

---

## 🎯 The Four Industrial Prognostic Challenges Solved by IntelliTwin

1. **Deterministic Overconfidence:** Conventional neural networks generate scalar point predictions of RUL with no confidence intervals. IntelliTwin introduces **Split Conformal Prediction** to guarantee finite-sample coverage: $P(y \in C(x)) \ge 1 - \alpha$.
2. **The Environmental Masking Problem:** Operational adjustments (throttle, load, speed) create sensor shifts that imitate or conceal physical degradation. IntelliTwin computes **condition-normalized residuals** $r(t) = S(t) - \hat{S}_{\text{nominal}}(u(t))$ to isolate mechanical wear.
3. **Catastrophic Failure Vulnerability:** Wear accelerates non-linearly near end-of-life. IntelliTwin optimizes a **heteroscedastic Gaussian NLL loss** and severe-risk alert thresholds, achieving **100% catastrophic failure prevention**.
4. **Architectural Disconnect:** Connects physical sensors, digital twin state vectors $\mathbf{\Psi}(t)$, deep learning inference, and an interactive **cyber-physical factory dashboard**.

---

## 📊 Empirical Performance on NASA C-MAPSS (FD001)

Evaluated across 100 training engines, 100 test engines, 20,631 cycles, and 20 complete run-to-failure fleets:

### 1. Remaining Useful Life (RUL) Prognostics
| Model Architecture | Input Representation | RMSE (cycles) | MAE (cycles) | NASA Score $S$ |
|---|---|---|---|---|
| Random Forest Regressor | Tabular (54-dim) | 18.12 | 13.39 | 884.0 |
| XGBoost Regressor | Tabular (54-dim) | 16.99 | 12.49 | 715.7 |
| GRU Baseline Network | Sequence ($30 \times 54$) | 16.78 | 12.25 | 665.0 |
| **IntelliTwin Heteroscedastic LSTM** | **Sequence ($30 \times 54$)** | **16.00** | **12.33** | **542.1** |

### 2. Multi-Class Health State Classification
* **Overall Accuracy:** **89.00%** (Macro F1: 0.8579)
* **Healthy State F1:** **0.9431** (Precision: 93.55%, Recall: 95.08%)
* **Critical State F1:** **0.8750** (Precision: 87.50%, Recall: 87.50%)
* **False Alarm Rate:** **2.38%** (0 healthy units misclassified as critical)

### 3. Uncertainty Quantification & Conformal Calibration
* **Nominal Target Coverage:** $90.00\%$ ($\alpha = 0.10$)
* **Empirical Coverage (PICP):** **95.00%** (Rigorously satisfied)
* **Mean Prediction Interval Width (MPIW):** 62.54 cycles (Winkler Score: 70.91)

### 4. Catastrophic Failure Prevention
* **Catastrophic Failure Prevention Rate:** **100.00%** (**0 missed critical failures**)
* **Mean Early Warning Lead Time:** **41.1 cycles** prior to physical destruction
* **False Alarm Rate During Healthy State:** **0.00%**

---

## 🖥️ Cyber-Physical Factory Dashboard

The dashboard provides a real-time, responsive dark-mode monitoring environment:
* **Fleet Overview:** Circular health gauges, active machine tallies (8/10 operational), and aggregate facility status.
* **Multi-Machine Switching:** CNC Machine (94%), Robotic Arm (72%), Conveyor Belt (38% Critical), Air Compressor (89%), Hydraulic Press (65%).
* **Conformal Uncertainty Display:** Visualizes 90% confidence bounds `[28 - 44 hrs]` alongside point predictions.
* **Degradation Trends:** Interactive Chart.js line charts tracking health score decay and vibration spikes.
* **Actionable AI Checklists:** Prescriptive mechanical maintenance actions with automated PDF report generation.
* **REST API:** Powered by Flask (`intellitwin/api.py`).

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
```

### 2. Start the Interactive Factory Dashboard
```bash
python intellitwin/api.py
```
Open your browser to `http://localhost:5000` or open `frontend/index.html` directly.

### 3. Run Master Training & Benchmark Pipeline
```bash
python -m intellitwin.train
```

### 4. Generate 300-DPI Publication Figures
```bash
python intellitwin/generate_figures.py
```

### 5. Recompile IEEE Research Paper
```bash
python manuscript/generate_ieee_paper_docx.py
python manuscript/build_double_column_paper.py
```

### 6. Verify Integrity & Deliverables
```bash
python intellitwin/verify_consistency.py
```

---

## 📂 Repository Structure

```text
├── data/                                  # Public Benchmark Data
│   └── cmapss/                            # NASA C-MAPSS dataset (FD001, FD002)
├── figures/                               # 300-DPI publication figures
│   ├── fig1_rul_calibrated_intervals.png  # Conformal prediction intervals
│   ├── fig2_uncertainty_decomposition.png # Masking problem residual decoupling
│   ├── fig3_reliability_calibration.png   # Confusion matrix & reliability curve
│   ├── fig4_pareto_coverage_width.png     # Prognostic benchmark comparison
│   └── fig5_dss_cost_comparison.png       # Catastrophic warning lead time
├── frontend/                              # Cyber-Physical Web Dashboard
│   ├── index.html                         # Factory dashboard single-page app
│   ├── styles.css                         # Dark glassmorphic design system
│   ├── app.js                             # Interactive state logic & Chart.js
│   ├── generate_svgs.py                   # Industrial SVG generator
│   └── assets/                            # Machine vector assets (CNC, Arm, Belt...)
├── intellitwin/                           # Core Python Package
│   ├── __init__.py                        # Package initialization
│   ├── api.py                             # Flask REST API backend
│   ├── data_loader.py                     # NASA C-MAPSS loader & preprocessor
│   ├── conformal_calibrator.py            # Split Conformal Prediction engine
│   ├── environmental_handler.py           # Condition-normalized residual engine
│   ├── fault_discriminator.py             # 4-way masking problem discriminator
│   ├── catastrophic_evaluator.py          # Early warning & lead-time evaluator
│   ├── metrics.py                         # PICP, MPIW, Winkler, NASA score
│   ├── train.py                           # Master training & evaluation pipeline
│   ├── generate_figures.py                # Publication figure generation script
│   ├── verify_consistency.py              # Deliverables integrity audit script
│   └── models/                            # Model architectures & weights
│       ├── lstm_rul.py                    # Heteroscedastic LSTM & GRU
│       ├── fault_classifier.py            # Random Forest & XGBoost classifiers
│       ├── anomaly_detector.py            # Isolation Forest + PCA detector
│       ├── evaluation_results.json        # Verified empirical metrics
│       └── lstm_rul.pt                    # Trained PyTorch model weights
├── manuscript/                            # Publication Submission Package
│   ├── RESEARCH_PAPER_INTELLITWIN.md      # Full academic research paper (8,000+ words)
│   ├── INTELLITWIN_RESEARCH_PAPER_IEEE_FORMAT.docx # Official IEEE Word Document
│   ├── INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf # Publication double-column PDF
│   ├── research_paper_double_column.html  # Standalone HTML research paper
│   ├── references.bib                     # IEEE BibTeX citations (descending year)
│   ├── generate_ieee_paper_docx.py        # Word generator script
│   ├── build_double_column_paper.py       # PDF compiler script
│   ├── package_submission.py              # Journal zip packager
│   └── intellitwin_journal_submission_package.zip # Pre-built journal bundle
├── COMMANDS_TO_RUN.txt                    # Step-by-step execution guide
├── requirements.txt                       # Python dependencies
└── README.md                              # This documentation file
```

---

## 📜 Citation
```bibtex
@article{singh2026intellitwin,
  author    = {Singh, Mayank and Pandey, Shiksha and Gupta, Ruchi},
  title     = {IntelliTwin: An {AI}-Driven Digital Twin Framework for Predictive Maintenance of Engineering Assets},
  journal   = {IEEE Transactions on Industrial Informatics / IEEE Access},
  year      = {2026},
  note      = {Ajay Kumar Garg Engineering College, Ghaziabad, India}
}
```
