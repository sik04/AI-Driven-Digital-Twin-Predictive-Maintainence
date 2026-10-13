# High-Level Experiment Map

This document establishes the high-level mapping between the formal research questions (RQ1–RQ4) and planned experimental evaluation suites (Experiment A–D) under **ADR-018** (Protocol Version: `step06-v2`).

---

## 1. High-Level Experiment Suite Mapping

### Experiment A → RQ1: Proposed Method Evaluation

- **Associated RQ**: **RQ1** (*Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*)
- **Associated Hypotheses**: $H_{0,1}$ / $H_{1,1}$
- **Purpose**: Evaluate the proposed decision-aware, condition-adaptive conformal RUL calibration method to determine whether it improves sequential maintenance utility while preserving reliable prediction-interval coverage.
- **High-Level Comparison**:
  - Proposed method (decision-aware, condition-adaptive conformal calibration)
  - Global conformal calibration
  - Standard condition-aware calibration
- **Primary Type of Evidence Expected**:
  - **Primary Outcome**: Total simulated maintenance cost per engine contrast ($\Delta_{\text{cost}}$)
  - **Secondary / Supporting Outcomes**: Marginal, worst-regime, and worst-stage coverage errors; fleet failure rate
  - **Statistical Framework**: Paired engine-level cluster bootstrap (10,000 resamples); 98.75% percentile decision intervals; Bonferroni $\alpha = 0.05 / 4 = 0.0125$.
- **Frozen Parameters (ADR-018)**: Dataset FD002; `primary_reference` scenario ($C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$); nominal coverage 90%; threshold $\Delta_{\text{cost}} > 0.20$ SCU per engine; absolute coverage error ceiling $E < 0.05$; failure rate increase $\le 0.0$.
- **Remaining Methodological Deferrals (Step 7+)**: Exact algorithmic loss functions, nonconformity score definitions, base predictor training hyperparameters, and deployable maintenance policy optimization.

---

### Experiment B → RQ2: Conditional Reliability & Sharpness Evaluation

- **Associated RQ**: **RQ2** (*Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*)
- **Associated Hypotheses**: $H_{0,2}$ / $H_{1,2}$
- **Purpose**: Evaluate whether the proposed method improves conditional coverage and worst-group reliability across operating regimes and wear conditions without making prediction intervals excessively wide.
- **High-Level Comparison**:
  - Proposed method vs. relevant global and condition-aware calibration baselines (both GBR and LSTM; both regimes and stages required).
- **Primary Type of Evidence Expected**:
  - **Primary Outcome**: Worst-group conditional coverage error contrast ($\Delta_{\text{error}}$)
  - **Secondary / Supporting Outcomes**: Mean Prediction Interval Width contrast ($D_{\text{width}}$); Winkler interval score contrast ($D_{\text{score}}$); worst-group absolute coverage error
  - **Statistical Framework**: Engine-level cluster bootstrap (10,000 resamples); 98.75% decision intervals with conservative missing-group bound propagation.
- **Frozen Parameters (ADR-018)**: Dataset FD002; nominal coverage 90%; threshold $\Delta_{\text{error}} > 0.01$; worst-group error ceiling $E < 0.05$; sharpness noninferiority margins $D_{\text{width}} < 1.0$ cycle and $D_{\text{score}} < 1.0$ cycle.
- **Remaining Methodological Deferrals (Step 7+)**: Conformal nonconformity score functions, conditional binning algorithms, and calibrator fitting implementations.

---

### Experiment C → RQ3: Decision-Value Attribution vs. Matched-Conservatism Baselines

- **Associated RQ**: **RQ3** (*Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*)
- **Associated Hypotheses**: $H_{0,3}$ / $H_{1,3}$
- **Purpose**: Disambiguate true decision-aware calibration utility from trivial interval expansion or naive early intervention by comparing against matched-conservatism baselines.
- **High-Level Comparison**:
  - Proposed method vs. three prespecified conservative control families:
    - Matched-width / widened prediction intervals
    - Tuned point-prediction safety margins
    - Earlier-intervention conservative policies
- **Primary Type of Evidence Expected**:
  - **Primary Outcome**: Maintenance cost improvement over every prespecified matched-conservatism baseline ($\Delta_{\text{cost}}$)
  - **Secondary / Supporting Outcomes**: Wasted Remaining Useful Life ($RUL_{\text{wasted}}$); cost-inefficient early PM rate; coverage error
  - **Statistical Framework**: Paired proposed-vs-control comparisons; 98.75% engine-level cluster bootstrap decision intervals.
- **Frozen Parameters (ADR-018)**: Dataset FD002; `primary_reference` scenario; nominal coverage 90%; threshold $\Delta_{\text{cost}} > 0.20$ SCU per engine against **EVERY** prespecified control family; coverage ceiling $E < 0.05$; failure increase $\le 0.0$.
- **Remaining Methodological Deferrals (Step 7+)**: Specific control parameterization and tuning algorithms (control structure and grids prespecified; parameter selection using validation engines only; calibration engines reserved for conformal calibration; confirmatory RQ3 evaluation cannot run until that protocol is frozen).

---

### Experiment D → RQ4: Robustness & Generalization

- **Associated RQ**: **RQ4** (*Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*)
- **Associated Hypotheses**: $H_{0,4}$ / $H_{1,4}$
- **Purpose**: Evaluate whether the principal reliability and maintenance-utility benefits persist across diverse operating conditions, model families, datasets, and repeated stochastic runs.
- **High-Level Comparison**:
  - Proposed method vs. Global Conformal and Standard Condition-Aware Calibration across 6 mandatory configuration cells:
    - Cell 1: FD001 × GBR
    - Cell 2: FD001 × LSTM
    - Cell 3: FD002 × GBR
    - Cell 4: FD002 × LSTM
    - Cell 5: FD004 × GBR
    - Cell 6: FD004 × LSTM
- **Primary Type of Evidence Expected**:
  - **Primary Outcome**: Weighted aggregate contrasts and cell-level non-harm bounds across the 6 cells (weight $1/6$ each)
  - **Secondary / Supporting Outcomes**: Individual cell effect sizes; cell-level decision intervals
  - **Statistical Framework**: 98.75% engine-level cluster bootstrap decision intervals across configurations.
- **Frozen Parameters (ADR-018)**: `primary_reference` scenario; nominal coverage 90%; 5 model seeds `[2026, 2027, 2028, 2029, 2030]`; weighted aggregate thresholds $\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$; cell-level non-harm thresholds $\Delta_{\text{cost}} > -0.20$ SCU, $\Delta_{\text{error}} > -0.01$; cell-level coverage and sharpness safeguards.
- **Remaining Methodological Deferrals (Step 7+)**: Base model architecture specifications, training pipelines, and multi-dataset model deployment.

---

## 2. Experimental Boundaries and Resolved vs. Deferred Parameters

### Parameters Frozen in Step 6 (ADR-018)
- Cost scenario triples and roles (`primary_reference`, `failure_sensitive`, `waste_sensitive`)
- Numerical practical-effect thresholds for all 4 RQs ($\Delta_{\text{cost}}, \Delta_{\text{error}}, E, D_{\text{width}}, D_{\text{score}}$)
- Resampling procedure (10,000 cluster-bootstrap resamples, stratified by quartiles)
- Multiplicity control (Bonferroni $\alpha=0.0125$ across RQs, 98.75% decision intervals, intersection-union testing)
- Missing-group conservative bound propagation
- Model training seed list `[2026, 2027, 2028, 2029, 2030]`

### Resolved in Step 7 and Step 8 (ADR-020, ADR-021)
- **Step 7 Base Models**: Frozen 30-model production matrix across FD001, FD002, FD004, GBR and LSTM, seeds 2026–2030 (ADR-020).
- **Step 8 Conformal Calibration**: Engine-weighted hierarchical conformal calibration with asymmetric score scaling ($\gamma=2, \beta=-\ln(2)$), regime adaptation, and exact rational quantile thresholds across 90 bundles / 270 coverage configurations (ADR-021).
- **Benchmark Maintenance Policy**: `lower_bound_one_cycle_policy` (`lower_rul <= 1.0` during cycles $30 \le t \le T-1$).

### Remaining Deferrals Prior to Confirmatory Evaluation
- Matched-conservatism parameterization algorithms and control grid freezing (Experiment C / RQ3) using validation data only.
- Implementation and execution of the final confirmatory evaluation runner software on held-out test data.
