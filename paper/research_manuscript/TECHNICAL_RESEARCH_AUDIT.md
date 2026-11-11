# IntelliTwin: Technical and Scientific Research Audit

- **Document Version**: `1.0.0`
- **Audit Date**: `2026-11-11T16:20:00+05:30`
- **Governing Architecture Decision Records**: ADR-001 through ADR-029
- **Implementation Source Root**: `c:\www\AI-Driven-Digital-Twin-Predictive-Maintainence\src\intellitwin`
- **Auditors**: Antigravity Multidisciplinary Research & Engineering Team

---

## 1. Authoritative Research Problem Formulation

### 1.1 The Industrial Challenge
In mission-critical industrial rotating machinery—most notably commercial aviation gas turbine turbofans—unexpected in-service mechanical failures incur catastrophic safety risks and massive economic penalties ($5\times$ to $10\times$ the cost of scheduled depot overhaul). Conversely, excessively conservative time-based preventative maintenance discards substantial residual component life, driving up lifecycle operating costs.

### 1.2 Limitations of Conventional State of the Art
1. **Uncalibrated Point Regression**: Contemporary deep learning prognostic architectures (LSTM, CNN, Transformers) output deterministic point predictions of Remaining Useful Life ($\hat{y}_t$). These point predictions conceal predictive uncertainty, giving maintenance engineers zero insight into prediction variance or tail risk.
2. **Standard Conformal Intervals Under Non-Stationarity**: Classical inductive split conformal prediction provides aggregate marginal coverage guarantees $\mathbb{P}(y \in \widehat{C}(x)) \ge 1 - \alpha$. However, it assumes identically distributed observations and residuals. In real-world degradation trajectories, degradation rate accelerates non-linearly, and sensor noise varies across operating conditions, causing severe **conditional undercoverage** in late-life wear regimes where failure risk is most acute.
3. **Decoupling of Uncertainty and Decision Utility**: Traditional prognostics optimizes symmetric cycle error metrics (RMSE, MAE). In maintenance operations, overestimating RUL leads to catastrophic unpredicted failure, whereas underestimating RUL leads only to premature replacement waste. Fixed maintenance thresholds applied to uncalibrated or symmetrically bounded intervals fail to align with asymmetric industrial loss structures.
4. **The Core IntelliTwin Research Problem**:
   > *"Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage. Our study therefore investigates whether decision-aware, condition-adaptive conformal calibration can improve maintenance utility without sacrificing subgroup reliability or merely becoming more conservative."*

---

## 2. Formal Research Questions (RQ1–RQ4) and Preregistered Criteria

| Research Question | Scientific Objective | Primary Outcome | Primary Comparators | Acceptance / Decision Rules | Confirmatory Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RQ1** (Maintenance Utility & Coverage Reliability) | Investigate if decision-aware conformal calibration improves sequential maintenance utility while preserving prediction-interval coverage. | Paired fleet cost contrast ($\Deltacost = \overline{\Cost}_B - \overline{\Cost}_P$) in Simulated Cost Units (SCU) per engine. | Global conformal calibration (`global_hcp`) and standard regime conformal calibration (`regime_hcp`) on FD002 test engines. | Requires $\Deltacost > 0.20$ SCU (lower 98.75% CI), absolute coverage error $< 0.05$ (marginal, worst-regime, worst-stage), and failure increase $\le 0.0$ for both GBR and LSTM. | **UNSUPPORTED** (Late-stage coverage error breached 0.05 ceiling; $E_{\text{stage}} \approx 0.13$) |
| **RQ2** (Conditional Subgroup Reliability & Sharpness) | Investigate if the proposed method improves reliability across operating regimes and degradation stages without excessive interval dilation. | Worst-group conditional coverage error contrast ($\Deltaerror = \WorstErr_B - \WorstErr_P$). | `global_hcp` and `regime_hcp` across 6 operating regimes and 3 lifecycle stages. | Requires $\Deltaerror > 0.01$ (lower 98.75% CI), worst-group error $< 0.05$, MPIW increase $\Dwidth < 1.0$ cycle, and Winkler score increase $\Dscore < 1.0$ cycle. | **UNSUPPORTED** (Fails conditional regime error reduction and worst-stage coverage ceiling) |
| **RQ3** (Attribution vs. Matched Controls) | Verify whether maintenance benefits originate from decision-aware calibration rather than simple over-conservatism or premature intervention. | Maintenance cost improvement over matched-conservatism controls ($\Deltacost = \overline{\Cost}_{\text{ctrl}} - \overline{\Cost}_P$). | 4 frozen controls across 3 families: matched-width intervals, widened intervals, point safety margins, and earlier intervention. | Requires $\Deltacost > 0.20$ SCU over **every** control family, coverage error $< 0.05$, and zero fleet failure increase. | **UNSUPPORTED** (Fails point safety margin cost contrast and worst-stage coverage ceiling) |
| **RQ4** (Robustness & Generalization) | Evaluate consistency of calibration and decision utility across operating conditions, base models, datasets, and repeated runs. | Equal-weight aggregate contrasts across the 6-cell evaluation matrix with cell non-harm bounds. | 6 mandatory cells: FD001 $\times$ {GBR, LSTM}, FD002 $\times$ {GBR, LSTM}, FD004 $\times$ {GBR, LSTM}. | Requires aggregate $\Deltacost > 0.20$ SCU, aggregate $\Deltaerror > 0.01$, and non-harm bounds ($\Deltacost > -0.20$ SCU, $\Deltaerror > -0.01$) in every single cell. | **UNSUPPORTED** (Fails aggregate regime error improvement and cross-cell worst-stage ceilings) |

---

## 3. Systematic Literature Synthesis & Research Gap Matrix

| State-of-the-Art Literature | Approach & Findings | Critical Limitations Identified | IntelliTwin Research Response | Evidence in Codebase |
| :--- | :--- | :--- | :--- | :--- |
| **Saxena et al. (2008)** [10.1109/PHM.2008.4711414] | Damage propagation modeling; C-MAPSS dataset generation. | Standard benchmark, but provides no uncertainty quantification framework. | Employs C-MAPSS FD001, FD002, FD004 under engine-disjoint partitions. | `src/intellitwin/data/loader.py`, `splits.py` |
| **Huang et al. (2021)** [10.3390/s21196340] | Survey of AI-driven Digital Twins in Industry 4.0. | Conceptual focus; lacks empirical statistical calibration under dynamic operating regimes. | Realizes an interactive, causal-windowed Digital Twin replay prototype. | `apps/twin_dashboard/`, `src/intellitwin/twin/` |
| **Javanmardi & Hüllermeier (2023)** [10.36001/ijphm.2023.v14i2.3417] | Conformal prediction intervals for RUL estimation. | Evaluated only marginal coverage; ignored multi-regime conditional coverage breakdown. | Audits conditional coverage across 6 operating regimes and 3 lifecycle stages. | `src/intellitwin/uncertainty/calibration.py` |
| **Diao et al. (2026)** [10.3390/s26072249] | LSTM-based quantile regression and conformal calibration. | Relies on symmetric interval metrics without connecting uncertainty to maintenance costs. | Couples conformal bounds directly to discrete sequential maintenance policy simulation. | `src/intellitwin/simulator/engine.py` |
| **Cortes-Gomez et al. (2025)** [ICLR 2025] | Utility-directed conformal prediction for downstream decisions. | Formulated for general classification/regression; not adapted to temporal RUL degradation. | Formulates RUL-specific asymmetric shape functions ($a(p), b(p)$) with scale dilation ($\gamma$). | `src/intellitwin/uncertainty/scores.py` |
| **Lee et al. (2023)** [arXiv:2306.06342] | Distribution-free inference with hierarchical data. | Addresses clustered exchangeability mathematically. | Enforces engine-level hierarchical calibration weighting with finite sample mass $\frac{m}{m+1}$. | `src/intellitwin/uncertainty/quantiles.py` |

---

## 4. End-to-End Technical Execution Pipeline

```
[Raw C-MAPSS Sensor Telemetry]
             │
             ▼
[Engine-Disjoint Splitting (Train / Cal / Val / Test)]
             │
             ▼
[Causal Sliding Window Buffer: Length 30, Stride 1, Zero Future Leakage]
             │
             ▼
[Training-Only Z-Score Normalization & Operating Regime Clustering (k=6)]
             │
             ▼
[Base Predictor Fitting: GBR (510 flat inputs) | LSTM (30x17 sequence)]
Target: y_train = min(RUL, 125)
             │
             ▼
[Point Prediction: p(t) = max(0, y_hat)]
             │
             ▼
[Asymmetric Decision-Aware Conformal Scoring Engine]
sigma(p) = (1 + p/125)^gamma,  z(p) = exp(-p/20)
a(p) = sigma(p) * exp(beta * z(p)),  b(p) = sigma(p) * exp(-beta * z(p))
score(p, y) = max((p - y)/a(p), (y - p)/b(p), 0)
             │
             ▼
[Hierarchical Calibration on Reserved Engines]
Rational Engine Weighting: Mass m/(m+1) on finite scores, 1/(m+1) at +inf
Deterministic Regime Fallback: if m_g < max(10, ceil(1/alpha)-1) -> q_global
             │
             ▼
[Inverted Conformal Lower & Upper Bounds]
L(t) = max(0, p(t) - q* * a(p)),  U(t) = p(t) + q* * b(p)
             │
             ▼
[Sequential Maintenance Policy: a_t = MAINTAIN_NOW if L(t) <= 1.0 cycle]
Terminal Cycle T: Catastrophic Functional Failure
             │
             ▼
[Economic Cost Realization & Cluster-Bootstrap Statistical Inference]
Cost = C_PM + C_WASTE*(T-t) if t < T; Cost = C_FAIL if t = T
10,000 paired engine-cluster bootstrap draws (98.75% Bonferroni decision CIs)
```

### 4.1 Detailed Module Implementation Matrix

1. **Data Ingestion & Integrity (`src/intellitwin/data/`)**:
   - `loader.py`: Ingests NASA C-MAPSS files (space-delimited, 26 columns: engine ID, cycle, 3 operational settings, 21 sensor channels).
   - `splits.py`: Enforces strictly disjoint engine allocations:
     - **FD001** (100 engines): 50 Train / 20 Cal / 10 Val / 20 Test.
     - **FD002** (260 engines): 130 Train / 52 Cal / 26 Val / 52 Test.
     - **FD004** (249 engines): 124 Train / 50 Cal / 25 Val / 50 Test.
     - Total held-out confirmatory test engines: $20 + 52 + 50 = 122$ engines.
   - `windowing.py`: Generates causal lookback windows of fixed length $w=30$, stride 1. Cycles $1 \dots 29$ constitute a non-predictive warm-up horizon. Window bounds never cross engine boundaries.
   - `preprocessing.py`: Fits standard scalers strictly on training partition engines. Identifies 6 operational flight regimes via $k$-means on operational setting variables ($\text{setting}_1, \text{setting}_2, \text{setting}_3$).
2. **Base Prognostic Models (`src/intellitwin/models/`)**:
   - **HistGradientBoostingRegressor (GBR)**: Flattens $30 \times 17$ window into a 510-dimensional feature vector. Configured with `max_iter=300`, `learning_rate=0.05`, `max_leaf_nodes=31`, `early_stopping=True`.
   - **LSTM Regressor**: Accepts $(30, 17)$ temporal tensor. Two LSTM layers (64 and 32 units, dropout 0.1) followed by dense linear projection. Trained with Adam (`lr=1e-3`, batch size 64, early stopping patience 10).
   - Evaluated across 5 frozen model training seeds: `[2026, 2027, 2028, 2029, 2030]`.
3. **Conformal Uncertainty Quantification (`src/intellitwin/uncertainty/`)**:
   - `scores.py`: Computes asymmetric nonconformity scores using state-dependent dilation $\sigma(p) = (1 + p/125)^\gamma$ and directional asymmetry shape factors $a(p) = \sigma(p)\exp(\beta z(p))$ and $b(p) = \sigma(p)\exp(-\beta z(p))$. Validation grid search uniquely selected $\gamma = 2, \beta = -\ln 2 \approx -0.693147$.
   - `quantiles.py`: Implements finite-sample hierarchical engine weighting:
     $$F_{\text{cal}}(q) = \frac{1}{m+1} \sum_{i=1}^m \frac{1}{n_i} \sum_{t} \mathbf{1}_{\{\text{score}_{it} \le q\}}$$
     Guaranteeing exact distribution-free coverage under engine-level exchangeability.
   - `calibration.py`: Applies deterministic regime-support thresholds ($m_g \ge 10$ engines) with fallback to pooled global quantiles if support is insufficient.
4. **Maintenance Decision Simulation (`src/intellitwin/simulator/`)**:
   - `engine.py` & `costs.py`: Simulates sequential engine operation cycle-by-cycle over cycles $t \in [30, T-1]$.
   - Policy trigger: Proactive replacement executed if calibrated lower bound $L(t) = \max(0, p(t) - q^* a(p)) \le 1.0$ cycle.
   - If no intervention occurs before terminal cycle $T$, catastrophic functional failure is incurred at cycle $T$.
   - Cost accounting:
     $$\text{Cost} = \begin{cases} \CPM + \CWASTE \cdot (T - t) & \text{if proactive maintenance triggered at } t < T \\ \CFAIL & \text{if unprevented failure occurs at } t = T \end{cases}$$
5. **Digital Twin Prototype (`src/intellitwin/twin/` & `apps/twin_dashboard/`)**:
   - Strictly a **software-based historical validation-telemetry replay prototype**, providing causal lookback replay of C-MAPSS engine runs without lookahead.
   - Verified with exact numerical parity ($\text{atol} \le 10^{-4}$) against cached engine predictions across all 18 benchmark cells.
