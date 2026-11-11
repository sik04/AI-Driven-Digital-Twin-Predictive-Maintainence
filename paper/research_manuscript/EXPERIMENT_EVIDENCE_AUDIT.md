# IntelliTwin: Experimental Evidence and Results Audit

- **Document Version**: `1.0.0`
- **Audit Date**: `2026-11-11T16:25:00+05:30`
- **Governing Architecture Decision Records**: ADR-026, ADR-027, ADR-028, ADR-029
- **Primary Evidence Repositories**:
  - Confirmatory Test Evidence: `c:\www\AI-Driven-Digital-Twin-Predictive-Maintainence\experiments\confirmatory_v1\`
  - Exploratory Factorial & Stress Evidence: `c:\www\AI-Driven-Digital-Twin-Predictive-Maintainence\experiments\phase08_exploratory_v3\`
  - Publication Bundle: `c:\www\AI-Driven-Digital-Twin-Predictive-Maintainence\research\results\phase08_submission_v1\`
- **Auditors**: Antigravity Multidisciplinary Research & Engineering Team

---

## 1. Comprehensive Experiment Inventory

| Experiment Stage | Scope & Configurations | Resampling & Seeds | Evaluation Partition | Audit Verification Receipt | Scientific Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Step 7 Base Model Production** | 30 trained models (3 datasets $\times$ 2 architectures $\times$ 5 seeds) | Seeds: `[2026, 2027, 2028, 2029, 2030]` | Training splits | `experiments/audits/step07_prediction_reproduction.json` (Error $\le 10^{-4}$) | **Authoritative / Frozen** |
| **Step 8 Conformal Calibrators** | 90 fitted bundles (3 datasets $\times$ 2 models $\times$ 5 seeds $\times$ 3 methods) | Reserved calibration partition engines | Calibration splits | `experiments/audits/step08_repair_verification.json` (LOEO reconstruction PASS) | **Authoritative / Frozen** |
| **Step 9 Confirmatory Evaluation** | 930 configurations (810 primary + 120 controls), 39,180 engine outcome records | 10,000 paired cluster bootstrap draws; PCG64 seed `[2026, 6, dataset_id]` | 122 held-out test engines (FD001: 20, FD002: 52, FD004: 50) | `experiments/confirmatory_v1/independent_audit.json` (`overall_status: PASS`, 0 failing reasons) | **Authoritative / Frozen** |
| **Phase 8 Factorial Ablation** | 240 cells ($2 \times 2 \times 2$ factorial: $\gamma \in \{0, 2\}$, $\beta \in \{-\ln 2, 0\}$, routing $\in \{\text{global}, \text{regime}\}$) | 10,000 paired engine bootstrap draws; 1,176 non-trivial paired contrasts | 122 held-out test engines | `experiments/phase08_submission_verification_v1/independent_audit.json` (10/10 checks PASS) | **Approved / Exploratory** |
| **Phase 8 Engineering Stress Battery** | 1,620 stress evaluations across 18 stream conditions (noise, dropout, bias) | Gaussian noise ($\sigma \in \{0.05, 0.10, 0.20\}$); dropout ($p \in \{0.05, 0.10\}$); bias ($\pm 0.20$) | 122 held-out test engines | `research/results/phase08_submission_v1/final_receipt.json` (Discrepancy $\le 4.55 \times 10^{-13}$) | **Approved / Exploratory** |

---

## 2. Confirmatory Held-Out Test Results (Step 9 / ADR-027)

All confirmatory results were evaluated on the **122 held-out test engines** under preregistered Bonferroni-corrected 98.75% paired cluster-bootstrap confidence intervals and Intersection-Union Testing (IUT).

### 2.1 Research Question 1 (RQ1) Evaluation Matrix

- **Target Benchmark**: NASA C-MAPSS FD002 test engines ($N=52$), `primary_reference` scenario ($\CPM=1.0, \CFAIL=5.0, \CWASTE=0.20$ SCU), nominal 90% coverage.
- **Decision Rule**: Lower 98.75% CI of $\Deltacost > 0.20$ SCU, upper 98.75% CI of all coverage errors $< 0.05$, and fleet failure rate increase $\le 0.0$.

| Component ID | Model | Comparator | Metric Evaluated | Observed Point Est. | 95% Bootstrap CI | 98.75% Decision CI | Threshold / Margin | Component Decision |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `RQ1_GBR_global_hcp_cost_improvement` | GBR | `global_hcp` | $\Deltacost$ (SCU/eng) | **+7.6231** | [6.8692, 8.4269] | [6.6442, 8.6538] | $> +0.20$ | **PASS** |
| `RQ1_GBR_global_hcp_failure_safeguard` | GBR | `global_hcp` | $\Deltafail$ (failures) | **0.0000** | [0.0, 0.0] | [0.0, 0.0] | $\le 0.0$ | **PASS** |
| `RQ1_GBR_regime_hcp_cost_improvement` | GBR | `regime_hcp` | $\Deltacost$ (SCU/eng) | **+7.5038** | [6.8192, 8.2078] | [6.6269, 8.3923] | $> +0.20$ | **PASS** |
| `RQ1_GBR_regime_hcp_failure_safeguard` | GBR | `regime_hcp` | $\Deltafail$ (failures) | **0.0000** | [0.0, 0.0] | [0.0, 0.0] | $\le 0.0$ | **PASS** |
| `RQ1_GBR_marginal_coverage_ceiling` | GBR | Nominal 90% | $|Coverage - 0.90|$ | **0.0287** | [0.0086, 0.0453] | [0.0037, 0.0488] | $< 0.05$ | **PASS** |
| `RQ1_GBR_worst_regime_coverage_ceiling`| GBR | Nominal 90% | Worst Regime Error | **0.0443** | [0.0240, 0.0636] | [0.0192, 0.0682] | $< 0.05$ | **INDETERMINATE** |
| `RQ1_GBR_worst_stage_coverage_ceiling` | GBR | Nominal 90% | Worst Stage Error | **0.1320** | [0.0999, 0.1650] | [0.0956, 0.1736] | $< 0.05$ | **FAIL** |
| `RQ1_LSTM_global_hcp_cost_improvement`| LSTM | `global_hcp` | $\Deltacost$ (SCU/eng) | **+10.9938** | [10.0069, 12.0531] | [9.7684, 12.3739] | $> +0.20$ | **PASS** |
| `RQ1_LSTM_global_hcp_failure_safeguard`| LSTM | `global_hcp` | $\Deltafail$ (failures) | **0.0000** | [0.0, 0.0] | [0.0, 0.0] | $\le 0.0$ | **PASS** |
| `RQ1_LSTM_regime_hcp_cost_improvement`| LSTM | `regime_hcp` | $\Deltacost$ (SCU/eng) | **+11.3215** | [10.3354, 12.4324] | [10.1000, 12.7442] | $> +0.20$ | **PASS** |
| `RQ1_LSTM_regime_hcp_failure_safeguard`| LSTM | `regime_hcp` | $\Deltafail$ (failures) | **0.0000** | [0.0, 0.0] | [0.0, 0.0] | $\le 0.0$ | **PASS** |
| `RQ1_LSTM_marginal_coverage_ceiling` | LSTM | Nominal 90% | $|Coverage - 0.90|$ | **0.0288** | [0.0076, 0.0465] | [0.0025, 0.0507] | $< 0.05$ | **INDETERMINATE** |
| `RQ1_LSTM_worst_regime_coverage_ceiling`| LSTM | Nominal 90% | Worst Regime Error | **0.0388** | [0.0190, 0.0583] | [0.0145, 0.0621] | $< 0.05$ | **INDETERMINATE** |
| `RQ1_LSTM_worst_stage_coverage_ceiling` | LSTM | Nominal 90% | Worst Stage Error | **0.1281** | [0.0951, 0.1770] | [0.0924, 0.1912] | $< 0.05$ | **FAIL** |

**RQ1 Summary**:
- **Component Breakdown**: 9 PASS, 2 FAIL, 3 INDETERMINATE (Total: 14 components).
- **Formal IUT Classification**: **UNSUPPORTED**.
- **Scientific Audit Insight**: The proposed framework delivered massive, statistically decisive maintenance cost reductions ($+7.50$ to $+11.32$ SCU per engine) with zero fleet failures. However, under the preregistered intersection-union test, the joint hypothesis required *all* components to pass. Because empirical coverage in the late degradation lifecycle stage fell to $\sim 77\%$ (breaching the $E < 0.05$ error ceiling with lower CI bound $> 0.092$), RQ1 was formally decided as UNSUPPORTED.

### 2.2 Research Question 2 (RQ2) Evaluation Matrix
- **Component Breakdown**: 10 PASS, 4 FAIL, 6 INDETERMINATE (Total: 20 components).
- **Failing Components**:
  - `RQ2_GBR_global_hcp_regime_error_improvement` (observed: $-0.0098$, CI: $[-0.0199, 0.0091]$ vs margin $> 0.01$)
  - `RQ2_GBR_regime_hcp_regime_error_improvement` (observed: $-0.0126$, CI: $[-0.0214, 0.0062]$ vs margin $> 0.01$)
  - `RQ2_GBR_worst_stage_ceiling` (lower CI bound: $0.0956 > 0.05$)
  - `RQ2_LSTM_worst_stage_ceiling` (lower CI bound: $0.0924 > 0.05$)
- **Formal IUT Classification**: **UNSUPPORTED**.

### 2.3 Research Question 3 (RQ3) Evaluation Matrix
- **Component Breakdown**: 15 PASS, 4 FAIL, 3 INDETERMINATE (Total: 22 components).
- **Failing Components**:
  - `RQ3_GBR_point_safety_margin_cost_improvement` (observed: $+0.1200$ vs margin $> 0.20$ SCU)
  - `RQ3_LSTM_point_safety_margin_cost_improvement` (observed: $+0.0800$ vs margin $> 0.20$ SCU)
  - `RQ3_GBR_worst_stage_coverage_ceiling` (lower CI bound $> 0.05$)
  - `RQ3_LSTM_worst_stage_coverage_ceiling` (lower CI bound $> 0.05$)
- **Formal IUT Classification**: **UNSUPPORTED**.

### 2.4 Research Question 4 (RQ4) Evaluation Matrix
- **Component Breakdown**: 71 PASS, 9 FAIL, 16 INDETERMINATE (Total: 96 components).
- **Failing Components**: Aggregate regime error improvements, FD001 LSTM marginal/regime errors, and worst-stage coverage ceilings across FD001, FD002, and FD004.
- **Formal IUT Classification**: **UNSUPPORTED**.

---

## 3. Verified Phase 8 Exploratory Findings (ADR-028 / ADR-029)

To diagnose the underlying mechanisms behind the confirmatory outcomes without modifying frozen baselines, Phase 8 executed a $2 \times 2 \times 2$ factorial component ablation and an engineering stress battery.

### 3.1 Factorial Component Main Effects on Maintenance Cost

Paired differences ($On - Off$) with 10,000 stratified engine bootstrap draws:

| Dataset | Model | Factor | Effect ($On - Off$) | 95% Bootstrap CI | Observed Direction |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **FD001** | GBR | `gamma_scale` ($\gamma=2$ vs $0$) | **-10.1800 SCU** | [-11.8600, -8.4550] | Cost reduction |
| **FD001** | GBR | `beta_asymmetry` ($\beta=-\ln 2$ vs $0$) | **-1.4000 SCU** | [-2.1050, -0.8700] | Cost reduction |
| **FD001** | GBR | `regime_routing` (regime vs global) | **+0.0000 SCU** | [+0.0000, +0.0000] | Null (Identical by definition) |
| **FD001** | LSTM | `gamma_scale` | **-11.1600 SCU** | [-12.9481, -9.2660] | Cost reduction |
| **FD001** | LSTM | `beta_asymmetry` | **-1.2960 SCU** | [-1.6710, -0.9710] | Cost reduction |
| **FD001** | LSTM | `regime_routing` | **+0.0000 SCU** | [+0.0000, +0.0000] | Null (Identical by definition) |
| **FD002** | GBR | `gamma_scale` | **-6.5365 SCU** | [-7.0798, -6.0038] | Cost reduction |
| **FD002** | GBR | `beta_asymmetry` | **-1.1558 SCU** | [-1.4038, -0.9250] | Cost reduction |
| **FD002** | GBR | `regime_routing` | **+0.0615 SCU** | [-0.0683, +0.1740] | Inconclusive / Near-zero |
| **FD002** | LSTM | `gamma_scale` | **-9.8438 SCU** | [-10.8002, -8.9510] | Cost reduction |
| **FD002** | LSTM | `beta_asymmetry` | **-1.4435 SCU** | [-1.6548, -1.2479] | Cost reduction |
| **FD002** | LSTM | `regime_routing` | **+0.2704 SCU** | [+0.1796, +0.3683] | Cost increase |
| **FD004** | GBR | `gamma_scale` | **-17.1560 SCU** | [-19.0670, -15.2970] | Cost reduction |
| **FD004** | GBR | `beta_asymmetry` | **-0.8700 SCU** | [-1.1040, -0.6590] | Cost reduction |
| **FD004** | GBR | `regime_routing` | **+0.7200 SCU** | [+0.3360, +1.1420] | Cost increase |
| **FD004** | LSTM | `gamma_scale` | **-8.0174 SCU** | [-9.4986, -6.6020] | Cost reduction |
| **FD004** | LSTM | `beta_asymmetry` | **-1.1198 SCU** | [-1.3170, -0.9292] | Cost reduction |
| **FD004** | LSTM | `regime_routing` | **+2.3046 SCU** | [+2.0252, +2.5806] | Cost increase |

**Descriptive Unweighted Aggregate Means Across 6 Cells**:
- **Scale Dilation ($\gamma$)**: **-10.4823 SCU** (Substantial cost savings across all cells)
- **Directional Asymmetry ($\beta$)**: **-1.2142 SCU** (Consistent secondary cost reduction)
- **Regime Routing**: **+0.5594 SCU** (Null on single-regime; slight penalty on multi-regime fleets due to partition sample dispersion)

### 3.2 Engineering Stress Robustness Battery (1,620 Evaluations)
- **Gaussian Sensor Noise**: Across 54 noise contrast combinations ($\sigma \in \{0.05, 0.10, 0.20\}$), mean paired cost increase relative to clean telemetry was **+0.5633 SCU**.
- **Sensor Dropout**: Across 36 causal forward-fill dropout conditions ($p \in \{0.05, 0.10\}$), mean paired coverage delta was **-0.0007** ($-0.07$ percentage points).
- **Operating Setting Bias**: Setting bias of $\pm 0.20$ shifted cluster assignments but did not trigger catastrophic policy failure.
