# Step 8 Conformal Uncertainty Calibration — Completion and Audit Report

- **Protocol Version**: `step08-v1`
- **Schema Version**: `step08-completion-v1`
- **Date**: 2026-10-12 / 2026-10-13
- **Branch**: `feat/step08-decision-aware-calibration`
- **Baseline Git SHA**: `e4b32ac3dd6a168984e47ab7714867be189e2064`
- **Selection Freeze Commit**: `1ba34208b442e9824b653a67eff1046535c7859c`
- **Status**: Complete — Executed and Independently Audited (Held-out confirmatory evaluation pending)

---

## 1. Executive Summary and Scope

Step 8 establishes the complete uncertainty quantification architecture for the IntelliTwin research initiative. Operating strictly on top of the 30 frozen base predictors from Step 7 (3 datasets × 2 model families × 5 seeds), Step 8 implements engine-weighted hierarchical conformal calibration across three distinct methods:
1. `global_hcp`: Global engine-weighted hierarchical conformal baseline using absolute residuals $s = |y - p|$.
2. `regime_hcp`: Operating-regime condition-aware hierarchical conformal baseline fitting separate thresholds per regime with global fallback.
3. `decision_aware_hcp`: Proposed asymmetric decision-aware method modulating scale $\sigma(p) = (1 + p/125)^\gamma$ and asymmetry $z(p) = \exp(-p/20)$, $a(p) = \sigma(p)\exp(\beta z(p))$, $b(p) = \sigma(p)\exp(-\beta z(p))$.

A prespecified 9-candidate parameter grid ($\gamma \in \{0, 1, 2\}$, $\beta_{\text{code}} \in \{-1, 0, 1\}$, $\beta = \beta_{\text{code}} \ln(2)$) was evaluated using validation engines only under the prespecified `lower_bound_one_cycle_policy` and `primary_reference` cost scenario. All six dataset/model-family cells were frozen under a mandatory commit gate before final calibration was fitted on reserved calibration engines.

**Total Calibrated Configurations**:
- **90 Calibrator Bundles** (3 datasets × 2 model families × 5 seeds × 3 methods).
- **270 Coverage Configurations** (each bundle contains exact hierarchical thresholds for 80%, 90%, and 95% nominal coverage).

---

## 2. Step 7 Corrections and Prediction-Reproduction Audit

Before Step 8 execution, Step 7 base predictor verification and documentation were corrected:
- **Numerical Prediction Reproduction**: Extended `scripts/audit_step07_base_models.py` with `--reproduce-predictions` to re-transform raw validation data and execute inference for all 30 frozen models. All 30 models matched saved predictions within $\Delta \le 5.0 \times 10^{-7} \ll 10^{-4}$ cycles, and recomputed engine-weighted uncapped RMSE, uncapped MAE, and capped RMSE matched saved metadata within $1.0 \times 10^{-4}$.
- **Evidence Record**: Recorded in `experiments/audits/step07_prediction_reproduction.json`.
- **Capped-RMSE Table Correction**: Repaired documentation error in `step07_full_base_model_matrix_completion.md` where FD004 GBR capped RMSE was corrected from 22.7538 to the true verified value of 16.2977 (uncapped RMSE: 48.8283).
- **Strict Input Geometry Enforcement**: `FrozenBaseModel.predict` now strictly rejects incorrect shapes, non-float inputs, NaN, and Inf, and preserves C-order flattening and non-negative truncation.
- **Data Isolation Fix**: Replaced naive filename substring checks with rigorous partition membership and manifest verification, permitting legitimate Step 8 calibration artifacts under `experiments/calibration/`.

---

## 3. Step 8 Selection Freeze Results (Validation Partition Only)

Candidate selection evaluated all 9 candidates plus baselines across all 5 seeds using leave-one-engine-out cross-validation on validation engines exclusively. No calibration or test engines were accessed.

### 3.1 Selected Winning Configurations

*(Aggregation: five-seed average within engine, then equal engine mean across validation partition)*

| Dataset | Family | Selected Candidate | $\gamma$ | $\beta_{\text{code}}$ | $\beta$ | Selection Status | Mean Cost (SCU) | Marg. PICP | MPIW | Failed Constraints |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **FD001** | **GBR** | `gamma2_betam1` | 2 | -1 | $-\ln(2)$ | `feasible_optimal` | 3.4400 | 0.8975 | 75.06 | None |
| **FD001** | **LSTM** | `gamma2_betam1` | 2 | -1 | $-\ln(2)$ | `feasible_optimal` | 3.6840 | 0.8968 | 79.10 | None |
| **FD002** | **GBR** | `gamma2_betam1` | 2 | -1 | $-\ln(2)$ | `feasible_optimal` | 5.0000 | 0.8984 | 91.79 | None |
| **FD002** | **LSTM** | `gamma2_betam1` | 2 | -1 | $-\ln(2)$ | `feasible_optimal` | 4.5846 | 0.8983 | 93.84 | None |
| **FD004** | **GBR** | `gamma2_betam1` | 2 | -1 | $-\ln(2)$ | `feasible_optimal` | 8.1600 | 0.8964 | 133.13 | None |
| **FD004** | **LSTM** | `gamma2_betam1` | 2 | -1 | $-\ln(2)$ | `feasible_optimal` | 8.3488 | 0.8965 | 132.99 | None |

### 3.2 Key Selection Observations
- All 6 cells selected **`gamma2_betam1`** as `feasible_optimal`. Zero cells required identity fallback (`gamma0_beta0`).
- **Asymmetry Mechanics**:
  $$a(p) = \sigma(p)\exp(\beta z(p)), \quad b(p) = \sigma(p)\exp(-\beta z(p))$$
  $$L = \max(0, p - q a(p)), \quad U = p + q b(p)$$
  For $\beta < 0$, holding $p$, $q$, and $\gamma$ fixed:
  - $a(p)$ decreases, so the lower subtraction distance $q a(p)$ decreases.
  - $b(p)$ increases, so the upper addition distance $q b(p)$ increases.
  - The lower bound $L$ rises or remains at zero after clipping.
  - The upper bound $U$ rises.
  Holding fixed parameters, this shifts interval mass upward; it does not by itself justify claiming earlier preventive maintenance or protection against late failure. In practice, refitted conformal quantiles $q$ interact with empirical residual distributions to determine final boundary locations and observed maintenance decisions.
- Quadratic scale expansion ($\gamma = 2$) narrows intervals for low RUL while permitting broader intervals for distant, high-RUL regimes.
- The selection records and freeze manifest are preserved at Git commit `1ba34208b442e9824b653a67eff1046535c7859c` (`experiments/calibration/selection/selection_freeze.json`).

---

## 4. Final Calibration Matrix and Support Audit

Final hierarchical conformal thresholds were fitted on the reserved calibration partition for all 90 bundles (3 datasets × 2 families × 5 seeds × 3 methods).

### 4.1 Calibration Engine Counts and Finite Mass Boundary
- Global finite support requires $m / (m + 1) \ge \text{nominal coverage}$.
- Minimum global calibration engine counts are:
  - 80% coverage: $m \ge 4$ engines ($4/5 = 0.80$).
  - 90% coverage: $m \ge 9$ engines ($9/10 = 0.90$).
  - 95% coverage: $m \ge 19$ engines ($19/20 = 0.95$).
- Regime routing additionally requires a frozen minimum support threshold of $m_g \ge 10$ distinct contributing calibration engines before fitting regime-specific quantiles (at 95%, $m_g \ge 19$ is required). These are counts of contributing calibration engines with valid endpoints, not counts of fully covered engines.
- Actual calibration partition engine counts:
  - **FD001**: 20 calibration engines, 1 operating regime. Fully supported at 80%, 90%, 95%.
  - **FD002**: 52 calibration engines, 6 operating regimes. All 6 regimes contain 52 contributing calibration engines ($m_g = 52 \ge 19$). Fully supported.
  - **FD004**: 50 calibration engines, 6 operating regimes. All 6 regimes contain 50 contributing calibration engines ($m_g = 50 \ge 19$). Fully supported.

### 4.2 Fallback Routing Counts
- **Total Bundles**: 90.
- **Fallback Invocations in Final Calibrators**: 0 (all regimes meet $m_g \ge 19$ support criteria).
- **Fallback Implementation**: Fully verified and tested via unit tests (`test_regime_minimum_support_fallback`).

---

## 5. Post-Selection Validation Diagnostics (Summary Table)

The following metrics are development diagnostics evaluated on validation engines using final calibrators. They are **not** independent confirmatory test results.

*(Table below presents Seed 2026 validation diagnostics as an illustrative individual seed; full 270-row consolidated five-seed metrics are preserved in `experiments/calibration/validation_summary.csv`)*

| Dataset | Family | Method | Nominal Cov | Marg. PICP | MPIW (cycles) | Interval Score | Lower Miss | Upper Miss | Fallback Frac |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FD001** | **GBR** | `decision_aware_hcp` | 0.80 | 0.8971 | 74.39 | 92.36 | 0.0089 | 0.0940 | 0.0 |
| **FD001** | **GBR** | `decision_aware_hcp` | 0.90 | 0.9854 | 130.80 | 136.64 | 0.0000 | 0.0146 | 0.0 |
| **FD001** | **GBR** | `decision_aware_hcp` | 0.95 | 1.0000 | 217.11 | 217.11 | 0.0000 | 0.0000 | 0.0 |
| **FD001** | **GBR** | `regime_hcp` | 0.80 | 0.8879 | 81.17 | 104.00 | 0.0022 | 0.1099 | 0.0 |
| **FD001** | **GBR** | `regime_hcp` | 0.90 | 0.9838 | 150.54 | 157.68 | 0.0000 | 0.0162 | 0.0 |
| **FD001** | **GBR** | `regime_hcp` | 0.95 | 1.0000 | 237.63 | 237.63 | 0.0000 | 0.0000 | 0.0 |
| **FD001** | **GBR** | `global_hcp` | 0.80 | 0.8879 | 81.17 | 104.00 | 0.0022 | 0.1099 | 0.0 |
| **FD001** | **GBR** | `global_hcp` | 0.90 | 0.9838 | 150.54 | 157.68 | 0.0000 | 0.0162 | 0.0 |
| **FD001** | **GBR** | `global_hcp` | 0.95 | 1.0000 | 237.63 | 237.63 | 0.0000 | 0.0000 | 0.0 |
| **FD002** | **GBR** | `decision_aware_hcp` | 0.80 | 0.8973 | 86.81 | 106.66 | 0.0090 | 0.0937 | 0.0 |
| **FD002** | **GBR** | `decision_aware_hcp` | 0.90 | 0.9866 | 152.01 | 157.94 | 0.0000 | 0.0134 | 0.0 |
| **FD002** | **GBR** | `decision_aware_hcp` | 0.95 | 1.0000 | 253.30 | 253.30 | 0.0000 | 0.0000 | 0.0 |
| **FD002** | **GBR** | `regime_hcp` | 0.80 | 0.8931 | 93.30 | 114.99 | 0.0034 | 0.1035 | 0.0 |
| **FD002** | **GBR** | `regime_hcp` | 0.90 | 0.9861 | 170.82 | 176.53 | 0.0000 | 0.0139 | 0.0 |
| **FD002** | **GBR** | `regime_hcp` | 0.95 | 1.0000 | 269.45 | 269.45 | 0.0000 | 0.0000 | 0.0 |
| **FD004** | **GBR** | `decision_aware_hcp` | 0.80 | 0.8943 | 96.65 | 120.35 | 0.0099 | 0.0958 | 0.0 |
| **FD004** | **GBR** | `decision_aware_hcp` | 0.90 | 0.9877 | 169.31 | 175.40 | 0.0000 | 0.0123 | 0.0 |
| **FD004** | **GBR** | `decision_aware_hcp` | 0.95 | 1.0000 | 280.95 | 280.95 | 0.0000 | 0.0000 | 0.0 |
| **FD004** | **GBR** | `regime_hcp` | 0.80 | 0.8872 | 102.81 | 128.53 | 0.0040 | 0.1088 | 0.0 |
| **FD004** | **GBR** | `regime_hcp` | 0.90 | 0.9845 | 187.90 | 194.50 | 0.0000 | 0.0155 | 0.0 |
| **FD004** | **GBR** | `regime_hcp` | 0.95 | 1.0000 | 296.72 | 296.72 | 0.0000 | 0.0000 | 0.0 |

**Validation Overcoverage Diagnostic**:
Validation coverage exceeds 95% due to finite-sample hierarchical quantile conservatism (the remaining $1/(m+1)$ mass is placed at $+\infty$). In accordance with research integrity decisions, the selected calibrators are preserved without post-hoc retuning. Development-set overcoverage will be tested against unobserved held-out data during confirmatory evaluation.

*(Full 270-row consolidated table recorded in `experiments/calibration/validation_summary.csv`.)*

---

## 6. Verification and Provenance Audit Results

The updated Step 8 audit (`scripts/audit_step08_calibration.py`) executed clean reconstruction and verification:
1. **Artifact Integrity**: PASS (all 90 calibrator JSON files load and match registered SHA-256 hashes).
2. **Selection Reconstruction**: PASS (exact match of selected winner `gamma2_betam1` and full candidate evidence for all 6 cells from cached validation predictions).
3. **Threshold Numerical Reconstruction**: PASS (re-fitted thresholds from calibration prediction caches matched saved artifacts within strict numerical tolerance $\Delta \le 1.0 \times 10^{-10}$).
4. **Validation Metric Reconstruction**: PASS (recomputed validation interval metrics matched saved `metrics.json` within $\Delta \le 1.0 \times 10^{-10}$).
5. **Scoped Data Isolation**: PASS (verified zero train or test engines appear in any Step 8 artifact; verified split partition disjointness scoped to Step 7/8).
6. **Prediction Reproduction**: PASS (re-executed inference of all 30 frozen models on raw calibration and validation partitions; matched caches within $\Delta \le 5.0 \times 10^{-7} \le 1.0 \times 10^{-4}$).
7. **Provenance & Baseline Preservation**: Recorded under ADR-022. Baseline manifest: `experiments/audits/step08_repair_baseline.json`. Clean verification report: `experiments/audits/step08_repair_verification.json`.

*(Note: Automated verification confirms numerical reproducibility and code correctness against specified schemas; it is an automated verification suite, not an independent human review).*

---

## 7. Scientific Boundaries and Novelty Positioning

### 7.1 Formal Theoretical Limitations
1. **Exchangeability Assumption**: Hierarchical exchangeability is a mathematical modeling assumption, not an established physical property of turbofan degradation or the C-MAPSS engine sampling process.
2. **No Pointwise or Trajectory Guarantees**: Conformal coverage bounds apply to the hierarchical marginal distribution. No pointwise, trajectory-wide, stopping-time, deployment-safety, or universal regime-conditional coverage guarantee is established.
3. **Stopping Times and Decision Utility**: Maintenance decisions are empirical operational policies evaluated on observable prediction bounds; they carry no formal safety or risk-elimination guarantee.
4. **Development vs. Confirmatory Status**: Validation selection and post-selection validation metrics are development-set observations. Confirmatory research conclusions remain strictly pending held-out evaluation.
5. **Automated CI Scope**: Passing automated CI and unit tests demonstrates implementation correctness and contract satisfaction; it does not prove scientific hypotheses or deployment safety.
6. **Zero Observed Failures**: Observing zero unmitigated failures in simulated episodes does not prove zero risk in out-of-distribution deployments.

### 7.2 Methodological Citations and Novelty Scope
- **Hierarchical Conformal Method**: Lee, Foygel Barber, & Willett (2023), *"Distribution-Free Inference with Hierarchical Data"*, arXiv:2306.06342v4. This project uses their hierarchical conformal formulation, not an invention thereof.
- **Decision-Aware Conformal Prediction**: Cortes-Gomez et al. (ICLR 2025), *"Utility-Directed Conformal Prediction: A Decision-Aware Framework for Actionable Uncertainty Quantification"*.
- **Risk-Aware Turbofan Conformal RUL**: Robinson (IJPHM 2026), *"Remaining Useful Life Estimation for Aircraft Engines with Risk-Aware Prediction Intervals via Conformalized Quantile Regression"*.
- **IntelliTwin Contribution**: The specific prespecified combination of engine-weighted hierarchical calibration, regime-specific thresholding, prediction-dependent asymmetric score scaling, and validation-selected sequential maintenance utility under controlled comparison against frozen baselines. No claim of inventing decision-aware conformal prediction is made.

---

## 8. Next Research Step

In accordance with Phase 6 acceptance and the Step 8 freeze checklist:
1. **Confirmatory Experiment Freeze**: Freeze the complete confirmatory evaluation plan and matched-conservatism control parameter grids (RQ3) prior to inspecting any held-out test data.
2. **Phase 7 Execution**: Execute confirmatory maintenance simulations on the strictly held-out test partition only after the control protocols are formally locked.
