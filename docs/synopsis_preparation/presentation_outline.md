# Academic Seminar and Defense Presentation Outline

**Document Version**: `1.0`  
**Topic**: IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Calibration for Predictive Maintenance  
**Target Duration**: 25–30 minutes (12 Slides)  
**Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta  
**Status**: Authoritative 12-Slide Master Structure (Slides 10–12 Results-Dependent)

---

## Slide 1: Title and Core Research Direction
* **Header**: IntelliTwin: Decision-Aware Conformal Uncertainty Calibration for Predictive Maintenance
* **Subtitle**: Bridging Conditional Prognostic Reliability and Downstream Sequential Maintenance Economics
* **Research Team**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
* **Core Research Question**: *Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*
* **Governance Notice**: Pre-registered confirmatory research framework frozen under ADR-018.

---

## Slide 2: Practical Industrial Problem: The Cost of Prognostic Asymmetry
* **The Operational Conflict**:
  - In-service engine failures cause catastrophic safety hazards, unscheduled flight cancellations, and severe financial penalties ($C_{\text{FAIL}}$).
  - Time-based preventive replacement scraps healthy turbofan components with dozens or hundreds of usable flight cycles remaining ($C_{\text{WASTE}} \cdot W$).
* **The Limitations of Point Predictors**:
  - Point-prediction RUL models ($\hat{y}$) emit deterministic cycle numbers without uncertainty bounds.
  - Symmetric training loss functions (MSE) fail to reflect industrial reality: overestimating RUL leads to failure; underestimating RUL causes economic waste.
* **The Operational Requirement**: Decision-makers require mathematically calibrated prediction intervals where lower bounds ($L$) provide verifiable safety guarantees against in-service failure without triggering excessively early replacement.

---

## Slide 3: Relevant Prior Work: The Conformal Prediction & PHM Frontier
* **Evolution of Prognostic Uncertainty**:
  - *Heuristic / Parametric UQ*: Gaussian Process Regression, Bayesian Neural Networks, Monte Carlo dropout ensembles (e.g., Zhu et al., 2025). Vulnerable to violated Gaussianity assumptions.
  - *Conformal Prediction in RUL*: Inductive split conformal prediction (Javanmardi & Hüllermeier, 2023) and Conformalized Quantile Regression (Diao et al., 2026; Robinson, 2026) provide distribution-free finite-sample marginal coverage guarantees.
* **Key Literature Limitations**:
  - Existing conformal RUL methods pool cycles, violating intra-engine temporal exchangeability (Lee et al., 2023).
  - Prior studies evaluate statistical metrics (PICP, MPIW) without evaluating sequential replacement policies or maintenance economics.
  - Subgroup reliability across operating flight envelopes (Yang et al., 2026; BenAbdennour, 2026) is rarely integrated with decision-aware interval construction.

---

## Slide 4: Research Gap and Pre-registered Objectives
* **The Identified Research Gap**:
  > *Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage.*
* **Four Confirmatory Research Questions (RQ1–RQ4)**:
  - **RQ1**: Maintenance utility improvement ($\Delta_{\text{cost}} > 0.20$ SCU) and coverage error ceiling ($E < 0.05$).
  - **RQ2**: Conditional reliability across operating regimes and wear stages ($\Delta_{\text{error}} > 0.01$, $\Delta \text{MPIW} < 1.0$).
  - **RQ3**: Decision-value attribution vs. four prespecified matched-conservatism controls.
  - **RQ4**: Cross-cell generalization without material harm across 6 mandatory evaluation cells.

---

## 5. Slide 5: Data Curation, Partition Isolation, and Leakage Controls
* **Dataset Qualification (ADR-011)**:
  - NASA C-MAPSS: FD001 (single regime control), FD002 (6 operating regimes, primary), FD004 (6 regimes, 2 fault modes).
  - Total Fleet: 609 engines (304 train, 122 calibration, 61 validation, 122 held-out test).
* **Strict Anti-Leakage Protocol**:
  - *Engine-Level Splits*: Entire run-to-failure trajectories allocated to a single partition; zero cross-engine leakage.
  - *Training-Only Preprocessing*: Scaling medians, interquartile ranges, and K-Means centroids fit exclusively on training data.
  - *Causal Temporal Windowing*: Window length $W=30$ cycles, stride 1; **zero padding prohibited** (first inference at $t=30$).
  - *Dual-Horizon Target Construction*: Base models trained on capped RUL ($y \le 125$); calibration and evaluation performed strictly against uncapped $y_{\text{true}} = T - t$.

---

## Slide 6: Frozen Base Predictor Matrix
* **Two Complementary Model Families (ADR-019, ADR-020)**:
  - *Histogram Gradient Boosting Regressor (GBR)*: Flattened 510-dimensional causal vectors ($30 \text{ cycles} \times 17 \text{ features}$). Fast, high-capacity non-neural baseline. Deterministic execution ($\sigma_{\text{RMSE}} = 0.0000$).
  - *Unidirectional LSTM Network*: Sequential input tensors of shape $(30, 17)$, hidden dimension $H=64$, dropout $0.20$, early stopping on validation RMSE.
* **Validation-Only Configuration Freeze**:
  - Winning configurations selected on validation data across seeds 2026–2027.
  - Full 30-model matrix trained across five official seeds (`2026, 2027, 2028, 2029, 2030`). Checkpoints cryptographically verified and frozen in `experiments/base_models/model_registry.json`.

---

## Slide 7: Proposed Decision-Aware Conformal Calibration
* **Exact Engine-Weighted Quantiles (Lee et al., 2023)**:
  - Eliminates survivor bias: individual endpoint weight $w_{it} = \frac{1}{m \cdot n_i}$.
  - Finite-score probability mass bounded by $\frac{m}{m+1}$; remaining mass $\frac{1}{m+1}$ placed at $+\infty$.
* **Proposed Asymmetric Score Inversion**:
  $$\sigma(p) = \left(1 + \frac{p}{125}\right)^\gamma, \quad z(p) = \exp\left(-\frac{p}{20}\right)$$
  $$a(p) = \sigma(p)\exp(\beta z(p)), \quad b(p) = \sigma(p)\exp(-\beta z(p))$$
  $$\text{score}(p, y) = \max\left(\frac{p - y}{a(p)}, \; \frac{y - p}{b(p)}, \; 0\right)$$
  $$L = \max(0, \; p - q_g \cdot a(p)), \quad U = p + q_g \cdot b(p)$$
* **Mechanics of Negative Beta ($\beta = -\ln 2$)**:
  - As $p \to 0$, $a(p)$ decreases by half and $b(p)$ doubles.
  - At fixed $p, q, \gamma$, negative beta raises the unclipped lower bound (narrowing lower-side margin).
  - Validation selection froze `gamma2_betam1` across all 6 cells under ADR-021.

---

## Slide 8: Sequential Maintenance Simulator and Economic Costing
* **Discrete-Event Simulation Replay Engine (ADR-014, ADR-015)**:
  - Replays engine operational cycles sequentially from $t=30$ to $T-1$.
  - Evaluates operational policy: `MAINTAIN_NOW` iff $L(t) \le 1.0$.
  - Immediate episode termination upon maintenance trigger; in-service failure recorded at cycle $T$ if unmaintained.
* **Normalized Simulated Cost Units (SCU) under ADR-018**:
  - Planned replacement base cost: $C_{\text{PM}} = 1.0$ SCU.
  - Unplanned in-service failure penalty: $C_{\text{FAIL}} = 5.0$ SCU.
  - Wasted life cost per discarded usable cycle: $C_{\text{WASTE}} = 0.20$ SCU.
  - Economic Equivalence Horizon: $r_{\text{equal}} = \frac{5.0 - 1.0}{0.20} = 20$ cycles.
  - Evaluates secondary sensitivity scenarios: `failure_sensitive` ($C_{\text{FAIL}}=10.0$) and `waste_sensitive` ($C_{\text{WASTE}}=0.40$).

---

## Slide 9: Statistical Inference Protocol and Matched Controls
* **10,000-Draw Stratified Cluster Bootstrap (ADR-018, ADR-023)**:
  - Resamples engines intact with replacement, stratified by lifetime quartiles ($Q_1$–$Q_4$).
  - Multiplicity control: Bonferroni family-wise error control ($\alpha = 0.05/4 = 0.0125$) yielding **98.75% decision intervals**.
  - Conservative missing-group bound propagation ($[0.0, 0.90]$ per absent group).
  - Intersection-Union Testing (IUT): All component conditions must pass.
* **Four Matched-Conservatism Controls (RQ3)**:
  - `matched_width_interval`: Width matched to proposed validation MPIW within $\le 1.0$ cycle.
  - `widened_interval`: Parameterized interval expansion ($\lambda \ge 1.0$).
  - `point_safety_margin`: Point prediction offset ($p \le 1 + m$).
  - `earlier_intervention`: Elevated threshold policy ($L \le h$).
  - Selected strictly on validation engines; test data untouched.

---

## Slide 10: Experimental Results — Held-Out Evaluation Strictly Pending
* **Current Implementation & Audit Status**:
  - Base Model Registry: 30/30 checkpoints verified (`experiments/base_models/model_registry.json`).
  - Calibration Registry: 90/90 bundles verified (`experiments/calibration/calibration_registry.json`).
  - Pre-Test Audit: Zero held-out test data processed (`experiments/confirmatory_development/pretest_audit.json`).
* **Pending Held-Out Verification Gates (UPD-01 to UPD-04)**:
  - *Milestone UPD-01*: Corrected pretest verification audit (`experiments/pretest_verification_v2/`).
  - *Milestone UPD-02*: Held-out predictive accuracy and interval coverage metrics (Tables T3, T4, T5).
  - *Milestone UPD-03*: Sequential maintenance simulation event logs and cost accounting (Table T6).
  - *Milestone UPD-04*: 10,000-draw bootstrap decision intervals and three-way RQ classifications (Table T8).
* **Demarcation Statement**: No preliminary or validation numbers are presented as confirmatory test findings.

---

## Slide 11: Software Demonstrator Architecture (Phase 9 Milestone)
* **Interactive Decision-Support Demonstrator (UPD-06)**:
  - Python-based simulation replay interface designed for fleet maintenance operators.
  - *Live Trajectory Playback*: Visualizes cycle-by-cycle sensor telemetry for any selected C-MAPSS engine.
  - *Uncertainty Visualization*: Renders point predictions alongside global, condition-aware, and decision-aware prediction intervals.
  - *Decision Dashboard*: Displays maintenance trigger alerts ($L \le 1.0$), remaining useful life, wasted life, and accumulated maintenance costs.
* **Demonstrator Scope Notice**: The demonstrator is a post-processing visualization tool for presenting verified research outputs. It does not perform physical engine telemetry ingestion.

---

## Slide 12: Threats to Validity, Methodological Limitations, and Conclusion
* **Key Research Limitations**:
  - *Benchmark Dynamics*: Physics-based synthetic degradation (C-MAPSS) with monotonic failure; absence of real-world corrective actions.
  - *Synthetic Cost Preferences*: SCU parameters are pre-registered benchmark criteria, not airline financial accounting data.
  - *Conformal Theory Boundaries*: Guarantees marginal exchangeable coverage; does not prove exact conditional or sequential stopping-time coverage.
  - *Sample Scale*: Small subgroup clusters require conservative bound propagation; single-asset maintenance scope.
* **Scientific Conclusion**:
  - IntelliTwin establishes an end-to-end, reproducible research framework uniting deep prognostics, hierarchical conformal calibration, and sequential maintenance economics.
  - The methodology, code, and documentation package are completely prepared, frozen, and ready to incorporate verified experimental findings upon execution of the confirmatory protocol.
