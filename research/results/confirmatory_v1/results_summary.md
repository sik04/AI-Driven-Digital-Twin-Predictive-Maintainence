# Step 9 Held-Out Confirmatory Evaluation: Empirical Results & Scientific Synthesis

- **Protocol Version**: `step09-v1`
- **Status**: Verified Confirmatory Test Evidence
- **Source Commit**: `67b96453bfc9b2786ce39bd5c6b510acea10c3d7`
- **Execution Timestamp (UTC)**: `2026-10-23T17:20:41.476812+00:00`
- **Total Matrix Configurations**: `930`
- **Total Evaluated Outcome Rows**: `39180`
- **Independent Audit Status**: `PASS`

---

## 1. Executive Summary & Authoritative RQ Decisions

Under the immutable preregistered protocol (ADR-018, ADR-026), the four central research questions evaluate whether asymmetric, condition-adaptive conformal calibration (`decision_aware_hcp`) improves sequential maintenance decision-making without compromising reliability constraints.

| Research Question | Hypothesized Focus | Number of Components | Decisive Failure Components | Overall RQ Outcome |
| :--- | :--- | :---: | :---: | :---: |
| **RQ1** | Maintenance Utility & Coverage | 14 | 2 | **UNSUPPORTED** |
| **RQ2** | Conditional Subgroup Reliability & Sharpness | 20 | 4 | **UNSUPPORTED** |
| **RQ3** | Decision Attribution vs Matched Controls | 22 | 4 | **UNSUPPORTED** |
| **RQ4** | Robustness & Multi-Cell Generalization | 96 | 9 | **UNSUPPORTED** |

---

## 2. Detailed Findings by Research Question

### 2.1 Research Question 1: Sequential Maintenance Utility and Coverage Reliability
- **Scope**: Dataset `FD002`, GBR and LSTM, 5 seeds, nominal coverage 90%, `primary_reference` scenario.
- **Outcome**: **UNSUPPORTED**
- **Primary Metric**: Maintenance cost improvement ($\Delta_{\text{cost}} > 0.20$ SCU per engine).
- **Component Breakdown**: 9 PASS, 2 FAIL, 3 INDETERMINATE.

### 2.2 Research Question 2: Conditional Reliability and Interval Sharpness
- **Scope**: Subgroup reliability across operating regimes (C1–C6) and lifecycle stages (Early/Mid/Late).
- **Outcome**: **UNSUPPORTED**
- **Primary Metric**: Worst-group conditional error reduction ($\Delta_{\text{error}} > 0.01$) without MPIW or interval score deterioration $\ge 1.0$ cycle.
- **Component Breakdown**: 10 PASS, 4 FAIL, 6 INDETERMINATE.

### 2.3 Research Question 3: Decision-Value Attribution vs. Matched-Conservatism Controls
- **Scope**: Attribution against 4 prespecified controls (`matched_width_interval`, `widened_interval`, `point_safety_margin`, `earlier_intervention`).
- **Outcome**: **UNSUPPORTED**
- **Primary Metric**: Maintenance cost improvement ($\Delta_{\text{cost}} > 0.20$ SCU per engine) against every control family.
- **Component Breakdown**: 15 PASS, 4 FAIL, 3 INDETERMINATE.

### 2.4 Research Question 4: Robustness and Multi-Cell Generalization
- **Scope**: Equal-six-cell aggregate evaluation across FD001, FD002, FD004 x GBR, LSTM.
- **Outcome**: **UNSUPPORTED**
- **Primary Metric**: Aggregate cost improvement $> 0.20$ SCU, aggregate error improvement $> 0.01$, and no cell-level harm ($< -0.20$ SCU or $< -0.01$ error).
- **Component Breakdown**: 71 PASS, 9 FAIL, 16 INDETERMINATE.

---

## 3. Methodological Integrity & Preregistration Compliance

1. **Partition Isolation**: Test engines were strictly isolated and never accessed prior to formal confirmatory execution.
2. **Frozen Parameters**: All model checkpoints, preprocessors, calibrator bundles, and benchmark control parameters were preserved unchanged from preregistered freezes.
3. **Statistical Inference**: Evaluated via 10,000 stratified engine-cluster bootstrap replicates using PCG64 PRNG with linear quantiles and 98.75% decision intervals.
4. **Independent Reconstruction**: All numerical outputs, intervals, and component decisions were independently reconstructed with zero reliance on runner outputs.
