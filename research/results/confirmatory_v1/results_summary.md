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

All four overall research question classifications are **UNSUPPORTED**. Under Intersection-Union Testing (IUT), an overall classification of UNSUPPORTED reflects the decisive failure of required reliability safeguards or benchmark noninferiority/improvement constraints; it does **not** signify that every individual component is ineffective or that cost advantages are absent. Passing cost-improvement components alone do not establish the full joint hypotheses when required reliability safeguards fail.

| Research Question | Hypothesized Focus | Number of Components | Decisive Failure Components | Overall RQ Outcome |
| :--- | :--- | :---: | :---: | :---: |
| **RQ1** | Maintenance utility with reliability safeguards | 14 | 2 | **UNSUPPORTED** |
| **RQ2** | Conditional reliability and interval sharpness | 20 | 4 | **UNSUPPORTED** |
| **RQ3** | Attribution against matched-conservatism controls | 22 | 4 | **UNSUPPORTED** |
| **RQ4** | Robustness across datasets and model families | 96 | 9 | **UNSUPPORTED** |

---

## 2. Detailed Findings by Research Question

### 2.1 Research Question 1: Maintenance Utility with Reliability Safeguards
- **Scope**: Dataset `FD002`, GBR and LSTM, 5 seeds, nominal coverage 90%, `primary_reference` scenario.
- **Outcome**: **UNSUPPORTED**
- **Primary Metrics**: Maintenance cost improvement ($\Delta_{\text{cost}} > 0.20$ SCU per engine), zero-harm failure safeguard ($\le 0$ added failures), and coverage noninferiority ceilings (marginal, worst-regime, worst-stage error $\le 0.05$).
- **Component Breakdown**: 9 PASS, 2 FAIL, 3 INDETERMINATE.
- **Synthesis & Decisive Failures**:
  - All four cost-improvement components PASS decisively: `RQ1_GBR_global_hcp_cost_improvement`, `RQ1_GBR_regime_hcp_cost_improvement`, `RQ1_LSTM_global_hcp_cost_improvement`, and `RQ1_LSTM_regime_hcp_cost_improvement` all exhibit decision interval lower bounds far exceeding $+0.20$ SCU.
  - All failure safeguards pass (0 observed failures across all configurations).
  - However, RQ1 fails the joint hypothesis because both worst-stage coverage safeguards fail:
    - `RQ1_GBR_worst_stage_coverage_ceiling` (decision interval $[0.0956, 0.1736] > 0.05$)
    - `RQ1_LSTM_worst_stage_coverage_ceiling` (decision interval $[0.0924, 0.1912] > 0.05$)
  - Indeterminate components: `RQ1_GBR_worst_regime_coverage_ceiling`, `RQ1_LSTM_marginal_coverage_ceiling`, and `RQ1_LSTM_worst_regime_coverage_ceiling` overlap the margin (under frozen rules, a lower bound below margin alone yields INDETERMINATE, not FAIL).

### 2.2 Research Question 2: Conditional Reliability and Interval Sharpness
- **Scope**: Subgroup reliability across operating regimes (C1–C6) and lifecycle stages (Early/Mid/Late).
- **Outcome**: **UNSUPPORTED**
- **Primary Metrics**: Worst-group conditional error reduction ($\Delta_{\text{error}} > 0.01$) without MPIW or interval score deterioration $\ge 1.0$ cycle.
- **Component Breakdown**: 10 PASS, 4 FAIL, 6 INDETERMINATE.
- **Decisive Failure Components**:
  - `RQ2_GBR_global_hcp_regime_error_improvement`
  - `RQ2_GBR_regime_hcp_regime_error_improvement`
  - `RQ2_GBR_worst_stage_ceiling`
  - `RQ2_LSTM_worst_stage_ceiling`

### 2.3 Research Question 3: Attribution Against Matched-Conservatism Controls
- **Scope**: Attribution against 4 prespecified controls (`matched_width_interval`, `widened_interval`, `point_safety_margin`, `earlier_intervention`).
- **Outcome**: **UNSUPPORTED**
- **Primary Metric**: Maintenance cost improvement ($\Delta_{\text{cost}} > 0.20$ SCU per engine) against every control family while satisfying coverage safeguards.
- **Component Breakdown**: 15 PASS, 4 FAIL, 3 INDETERMINATE.
- **Synthesis & Decisive Failures**:
  - RQ3 fails both point-safety-margin cost-improvement components and both worst-stage coverage safeguards:
    - `RQ3_GBR_point_safety_margin_cost_improvement` (decision interval $[-4.6058, -3.3557] < 0.20$, failing to outperform point safety margin on cost)
    - `RQ3_LSTM_point_safety_margin_cost_improvement` (decision interval $[-4.1919, -3.3485] < 0.20$)
    - `RQ3_GBR_worst_stage_coverage_ceiling` (decision interval $[0.0956, 0.1736] > 0.05$)
    - `RQ3_LSTM_worst_stage_coverage_ceiling` (decision interval $[0.0924, 0.1912] > 0.05$)
  - While outperforming matched-width, widened, and earlier-intervention controls on cost, proposed calibration fails to beat simple point safety margins on cost in FD002 and fails late-stage coverage reliability.

### 2.4 Research Question 4: Robustness Across Datasets and Model Families
- **Scope**: Equal-six-cell aggregate evaluation across FD001, FD002, FD004 x GBR, LSTM.
- **Outcome**: **UNSUPPORTED**
- **Primary Metric**: Aggregate cost improvement $> 0.20$ SCU, aggregate error improvement $> 0.01$, and no cell-level harm ($< -0.20$ SCU or $< -0.01$ error).
- **Component Breakdown**: 71 PASS, 9 FAIL, 16 INDETERMINATE.
- **Decisive Failure Components**:
  - `RQ4_aggregate_global_hcp_regime_error_improvement`
  - `RQ4_aggregate_regime_hcp_regime_error_improvement`
  - `RQ4_cell_FD001_GBR_worst_stage_ceiling`
  - `RQ4_cell_FD001_LSTM_marginal_coverage_ceiling`
  - `RQ4_cell_FD001_LSTM_worst_regime_ceiling`
  - `RQ4_cell_FD002_GBR_worst_stage_ceiling`
  - `RQ4_cell_FD002_LSTM_worst_stage_ceiling`
  - `RQ4_cell_FD004_GBR_worst_stage_ceiling`
  - `RQ4_cell_FD004_LSTM_worst_stage_ceiling`

---

## 3. Methodological Integrity & Preregistration Compliance

1. **Partition Isolation**: Test engines were strictly isolated and never accessed prior to formal confirmatory execution.
2. **Frozen Parameters**: All model checkpoints, preprocessors, calibrator bundles, and benchmark control parameters were preserved unchanged from preregistered freezes.
3. **Statistical Inference**: Evaluated via 10,000 stratified engine-cluster bootstrap replicates using PCG64 PRNG with linear quantiles and 98.75% decision intervals.
4. **Independent Reconstruction**: The independent verifier checks generated evidence through reference reconstruction without relying on production-runner internals.

