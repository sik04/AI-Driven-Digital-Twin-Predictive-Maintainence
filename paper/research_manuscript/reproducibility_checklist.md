# IntelliTwin: Research Reproducibility Checklist

- **Repository**: `https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence`
- **Target Manuscript**: *IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance*
- **Audit Date**: `2026-11-11T16:35:00+05:30`
- **Standard**: Follows IEEE, ACM, and NeurIPS Reproducibility Guidelines

---

## 1. Mathematical and Algorithmic Specifications

- [x] **Complete Model Descriptions**: Both prognostic architectures are fully specified:
  - **HistGradientBoostingRegressor (GBR)**: 510-dimensional input vector (flattened $30 \times 17$ window), `max_iter=300`, `learning_rate=0.05`, `max_leaf_nodes=31`, `early_stopping=True`.
  - **LSTM Regressor**: Input tensor shape $(30, 17)$, 2 LSTM layers (hidden dimensions 64 and 32, dropout 0.1), dense linear output projection. Adam optimizer, `lr=1e-3`, batch size 64.
- [x] **Target Construction**: Linear piecewise RUL clipping at cycle 125 during training ($y_{\text{train}} = \min(\text{RUL}, 125)$) and uncapped true remaining cycles ($y_{\text{eval}} = \text{RUL}$) during evaluation.
- [x] **Conformal Prediction Nonconformity Score**:
  $$\text{score}(p, y) = \max\left(\frac{p - y}{a(p)}, \frac{y - p}{b(p)}, 0\right)$$
  where $\sigma(p) = (1 + p/125)^\gamma$, $z(p) = \exp(-p/20)$, $a(p) = \sigma(p)\exp(\beta z(p))$, and $b(p) = \sigma(p)\exp(-\beta z(p))$. Frozen hyperparameters: $\gamma = 2, \beta = -\ln 2$.
- [x] **Hierarchical Engine Weighting**:
  $$F_{\text{final}}(q) = \frac{1}{m+1} \sum_{i=1}^m \frac{1}{n_i} \sum_{t} \mathbf{1}_{\{\text{score}_{it} \le q\}}$$
  with finite mass $\frac{m}{m+1}$ and point mass $\frac{1}{m+1}$ placed at $+\infty$.
- [x] **Deterministic Fallback Rule**: Regime clusters must satisfy $m_g \ge \max(10, \lceil 1/\alpha \rceil - 1)$ distinct calibration engines; otherwise deterministically falls back to the pooled global threshold $q^*_{\text{global}}$.
- [x] **Sequential Maintenance Policy**: Discrete-cycle trigger $a_t = \text{MAINTAIN\_NOW}$ if $L(t) \le 1.0$ cycle over $t \in [30, T-1]$. Terminal cycle $T$ incurs catastrophic failure cost $\CFAIL$. Cost realized via:
  $$\text{Cost} = \begin{cases} \CPM + \CWASTE \cdot (T - t) & \text{if proactive maintenance triggered at } t < T \\ \CFAIL & \text{if unprevented failure occurs at } t = T \end{cases}$$

---

## 2. Dataset and Partition Protocols

- [x] **Data Source**: NASA C-MAPSS benchmark turbofan degradation datasets (FD001, FD002, FD004).
- [x] **Partition Integrity**: Engine-level disjoint splits guaranteed across all sub-corpora:
  - **FD001** (100 engines): 50 Train / 20 Cal / 10 Val / 20 Test.
  - **FD002** (260 engines): 130 Train / 52 Cal / 26 Val / 52 Test.
  - **FD004** (249 engines): 124 Train / 50 Cal / 25 Val / 50 Test.
  - Total held-out confirmatory test engines: $20 + 52 + 50 = 122$ engines.
- [x] **Leakage Protection**:
  - Z-score normalization parameters fitted strictly on training partition engines.
  - Causal sliding window buffers (length $w=30$, stride 1) terminate at current cycle $t$; zero future lookahead.
  - Cycles $1 \dots 29$ constitute a non-predictive warm-up horizon.
  - Test partition engines were blinded and never used for feature selection, hyperparameter tuning, or matched-control selection.

---

## 3. Statistical Resampling and Multiplicity Controls

- [x] **Resampling Unit**: Physical engine units ($i \in \{1, \dots, N\}$). Individual operational cycles are never resampled independently.
- [x] **Stratification**: Frozen lifetime quartiles ($Q_1, Q_2, Q_3, Q_4$).
- [x] **PRNG & Seeding**: `numpy.random.Generator` backed by `PCG64` initialized with `SeedSequence([2026, 6, dataset_number])`.
- [x] **Replication**: $B = 10{,}000$ paired cluster-bootstrap resamples per dataset.
- [x] **Decision Confidence Level**: Bonferroni family-wise corrected 98.75% percentile decision intervals (quantiles 0.00625 and 0.99375) across the four primary research questions ($\alpha = 0.05 / 4 = 0.0125$).
- [x] **Decision Logic**: Intersection-Union Testing (IUT). An RQ is Supported if and only if every single required component passes.

---

## 4. Software Environment & Execution Commands

- [x] **Python Environment**: Python 3.14.0 (`.venv_confirmatory`).
- [x] **Key Packages**: `torch 2.14.1+cpu`, `scikit-learn 1.9.1`, `pandas 3.0.6`, `scipy 1.18.1`, `narwhals 2.27.1`, `PyYAML 6.0.3`.
- [x] **Execution Reproduction Commands**:
  ```bash
  # Step 1: Pre-test verification audit
  python -m intellitwin.confirmatory.verification

  # Step 2: Confirmatory test evaluation (Step 9)
  python -m intellitwin.confirmatory.runner

  # Step 3: Phase 8 independent reference audit
  python -m intellitwin.robustness.verification

  # Step 4: Phase 8 reporting synthesis
  python -m intellitwin.robustness.reporting
  ```
- [x] **Open Verification Receipts**: All raw prediction arrays, interval predictions, and independent audit receipts are preserved with SHA-256 integrity manifests in `experiments/confirmatory_v1/` and `experiments/phase08_exploratory_v3/`.
