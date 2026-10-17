# Results Table Templates and Evidence Capture Specifications

**Document Version**: `2.0 (Aligned with Protocol Freeze v4)`  
**Governing Standard**: Strict demarcation of frozen configuration evidence (T1, T2) from pending held-out confirmatory results (T3–T10). All unverified or unexecuted results are marked as `PENDING`, never zero-valued placeholders.

---

## Table T1: C-MAPSS Dataset, Operating Regime, and Partition Split Summary

*Populated from authoritative split manifests in `data/splits/` and dataset qualification under ADR-011.*

| Dataset ID | Flight Conditions | Fault Modes | Total Engines | Train Engines (50%) | Calibration Engines (20%) | Validation Engines (10%) | Held-Out Test Engines (20%) | Operational Features | Qualified Degradation Sensors | Window Length ($W$) | Split Manifest Reference |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **FD001** | 1 (Sea level) | 1 (HPC) | 100 | 50 | 20 | 10 | 20 | 3 | 14 | 30 cycles | `data/splits/fd001_engine_split_seed_2026.json` |
| **FD002** | 6 (Clusters $C_1$–$C_6$) | 1 (HPC) | 260 | 130 | 52 | 26 | 52 | 3 | 14 | 30 cycles | `data/splits/fd002_engine_split_seed_2026.json` |
| **FD004** | 6 (Clusters $C_1$–$C_6$) | 2 (HPC + Fan) | 249 | 124 | 50 | 25 | 50 | 3 | 14 | 30 cycles | `data/splits/fd004_engine_split_seed_2026.json` |
| **Total Fleet** | — | — | **609** | **304** | **122** | **61** | **122** | 3 | 14 | 30 cycles | `fd002_lifetime_quartile_provenance.json` |

---

## Table T2: Frozen Base Model Architectures and Calibration Configurations

*Populated from model registry (`experiments/base_models/model_registry.json`), Step 7 freeze (ADR-020), and calibration selection freeze (`experiments/calibration/selection/selection_freeze.json`, ADR-021). Note: Development validation uncapped RMSE values are mean ± SD across five frozen seeds (2026–2030) evaluated strictly on development validation partitions. They do not represent held-out test performance or predictive uncertainty intervals.*

| Evaluation Cell | Base Model Family | Frozen Winning Configuration | Key Hyperparameters | Development validation uncapped RMSE, mean ± SD across five frozen seeds, cycles | Training Horizon / Input Shape | Selected Calibrator Candidate | Selected Scaling $\gamma$ | Selected Asymmetry $\beta_{\text{code}}$ | Numerical $\beta$ | Selection Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **FD001 $\times$ GBR** | HistGradientBoosting | `gbr_lr010_leaf15_l2_0` | `lr=0.10, max_leaf=15, l2=0.0` | 28.42 ± 0.00 | Flattened vector $(510,)$ | `gamma2_betam1` | 2 | -1 | $-\ln(2) \approx -0.693147$ | `feasible_optimal` |
| **FD001 $\times$ LSTM** | Unidirectional LSTM | `lstm_h64_lr0010` | `H=64, lr=0.0010, drop=0.20` | 29.90 ± 0.23 | Sequential tensor $(30, 17)$ | `gamma2_betam1` | 2 | -1 | $-\ln(2) \approx -0.693147$ | `feasible_optimal` |
| **FD002 $\times$ GBR** | HistGradientBoosting | `gbr_lr010_leaf31_l2_0` | `lr=0.10, max_leaf=31, l2=0.0` | 34.66 ± 0.00 | Flattened vector $(510,)$ | `gamma2_betam1` | 2 | -1 | $-\ln(2) \approx -0.693147$ | `feasible_optimal` |
| **FD002 $\times$ LSTM** | Unidirectional LSTM | `lstm_h64_lr0010` | `H=64, lr=0.0010, drop=0.20` | 35.14 ± 0.23 | Sequential tensor $(30, 17)$ | `gamma2_betam1` | 2 | -1 | $-\ln(2) \approx -0.693147$ | `feasible_optimal` |
| **FD004 $\times$ GBR** | HistGradientBoosting | `gbr_lr010_leaf31_l2_0` | `lr=0.10, max_leaf=31, l2=0.0` | 48.83 ± 0.00 | Flattened vector $(510,)$ | `gamma2_betam1` | 2 | -1 | $-\ln(2) \approx -0.693147$ | `feasible_optimal` |
| **FD004 $\times$ LSTM** | Unidirectional LSTM | `lstm_h64_lr0010` | `H=64, lr=0.0010, drop=0.20` | 48.67 ± 0.36 | Sequential tensor $(30, 17)$ | `gamma2_betam1` | 2 | -1 | $-\ln(2) \approx -0.693147$ | `feasible_optimal` |

---

## Table T3: Point-Prediction Performance on Held-Out Test Partitions

*Target Milestone: `UPD-02`. Evaluated across 5 fixed seeds (2026–2030) on held-out test engines. Retains six point-prediction rows. Unsupported asymmetric-score and early/late error columns are excluded from this primary reporting template.*

| Dataset | Model Architecture | Evaluated Engines | Uncapped RMSE (cycles) | Uncapped MAE (cycles) | Capped RMSE ($RUL \le 125$) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **FD001** | GBR (`gbr_lr010_leaf15_l2_0`) | 20 | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | LSTM (`lstm_h64_lr0010`) | 20 | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | GBR (`gbr_lr010_leaf31_l2_0`) | 52 | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | LSTM (`lstm_h64_lr0010`) | 52 | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | GBR (`gbr_lr010_leaf31_l2_0`) | 50 | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | LSTM (`lstm_h64_lr0010`) | 50 | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |

---

## Table T4: Primary Prediction Interval Coverage, Width, and Quality by Calibration Method (90% Nominal)

*Target Milestone: `UPD-02`. Complete 18-row primary evaluation matrix across all 3 datasets, 2 model architectures, and 3 registered calibration methods on held-out test partitions. All empirical values remain PENDING.*

| Dataset | Model Architecture | Calibration Method | Marginal PICP (%) | Marginal Error $E$ | MPIW (cycles) | Winkler Interval Score | Optimistic Miss ($y < L$) | Pessimistic Miss ($y > U$) | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **FD001** | **GBR** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **GBR** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **GBR** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **LSTM** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **LSTM** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **LSTM** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **GBR** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **GBR** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **GBR** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **GBR** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **GBR** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **GBR** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **LSTM** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **LSTM** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **LSTM** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |

---

## Table T5: Operating Regime & Lifecycle Stage Subgroup Reliability Auditing (FD002 Test)

*Target Milestone: `UPD-02` / `UPD-04`. Evaluated across eligible subgroups ($\ge 10$ distinct engines). Exactly 18 subgroup rows (9 GBR, 9 LSTM: $C_1$–$C_6$ and Early/Mid/Late) plus separate worst-regime and worst-stage summaries for each model. All prefilled stage counts, eligibility, and missing-bound indicators are replaced with `PENDING` awaiting empirical verification.*

| Model Family | Subgroup Family | Subgroup Identifier | Engine Count ($N_g$) | Eligibility ($\ge 10$) | `global_hcp` Coverage | `regime_hcp` Coverage | `decision_aware_hcp` Coverage | `decision_aware` Error $E(g)$ | Missing Bounds Used | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **GBR** | Operating Regimes | Regime $C_1$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Operating Regimes | Regime $C_2$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Operating Regimes | Regime $C_3$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Operating Regimes | Regime $C_4$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Operating Regimes | Regime $C_5$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Operating Regimes | Regime $C_6$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Lifecycle Stages | Early ($t \le T/3$) | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Lifecycle Stages | Mid ($T/3 < t \le 2T/3$) | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Lifecycle Stages | Late ($t > 2T/3$) | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | Worst-Group Summary | Regime Worst Error | — | — | `PENDING` | `PENDING` | `PENDING` | — | — | `PENDING_EXPERIMENT` |
| **GBR** | Worst-Group Summary | Stage Worst Error | — | — | `PENDING` | `PENDING` | `PENDING` | — | — | `PENDING_EXPERIMENT` |
| **LSTM** | Operating Regimes | Regime $C_1$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Operating Regimes | Regime $C_2$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Operating Regimes | Regime $C_3$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Operating Regimes | Regime $C_4$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Operating Regimes | Regime $C_5$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Operating Regimes | Regime $C_6$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Lifecycle Stages | Early ($t \le T/3$) | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Lifecycle Stages | Mid ($T/3 < t \le 2T/3$) | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Lifecycle Stages | Late ($t > 2T/3$) | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | Worst-Group Summary | Regime Worst Error | — | — | `PENDING` | `PENDING` | `PENDING` | — | — | `PENDING_EXPERIMENT` |
| **LSTM** | Worst-Group Summary | Stage Worst Error | — | — | `PENDING` | `PENDING` | `PENDING` | — | — | `PENDING_EXPERIMENT` |

---

## Table T6: Primary Sequential Maintenance Simulation Outcomes (All 18 Matrix Cells)

*Target Milestone: `UPD-03`. Complete 18-row maintenance simulation outcomes evaluated under $C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$ SCU per engine. All values remain PENDING.*

| Dataset | Model Architecture | Calibration Method | Mean Cost per Engine (SCU) | Observed Failure Rate (%) | Fleet PM Rate (%) | Mean Wasted RUL ($W$, cycles) | Inefficient Early PM (Fleet) | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **FD001** | **GBR** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **GBR** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **GBR** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **LSTM** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **LSTM** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | **LSTM** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **GBR** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **GBR** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **GBR** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **GBR** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **GBR** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **GBR** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **LSTM** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **LSTM** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | **LSTM** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |

---

## Table T7: RQ3 Matched-Conservatism Control Comparisons (FD002 Test)

*Target Milestone: `UPD-03` / `UPD-04`. Evaluates decision-value attribution against four pre-specified controls across three families on FD002 test engines. Point-policy interval quantities are explicitly marked NOT_APPLICABLE. Asymmetry parameter is $\beta = -\ln(2) \approx -0.693147$. Note: $\lambda=1.00$ reflects nominal regime/global calibration without scaling, and $h=1$ represents baseline decision thresholding without lead-time advancement.*

| Base Model | Evaluated Method / Control Configuration | Control Family | Frozen Parameter | Mean Cost (SCU) | Observed Failures (%) | Mean Wasted RUL (cycles) | Cost Contrast vs Proposed ($\Delta_{\text{cost}}$) | 98.75% Decision CI $[\text{CI}_{\text{lower}}, \text{CI}_{\text{upper}}]$ | Condition Pass Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **GBR** | `decision_aware_hcp` | Proposed Reference | $\gamma=2, \beta=-\ln(2)$ | `PENDING` | `PENDING` | `PENDING` | Baseline ($0.0$) | N/A | Reference |
| **GBR** | `matched_width_interval` | Matched Width | `global_hcp`, $\lambda = 0.92$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | `widened_interval` | Widened Interval | `regime_hcp`, $\lambda = 1.00$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | `point_safety_margin` | Point Margin | $m = 5$ cycles | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | `earlier_intervention` | Early Policy | `regime_hcp`, $h = 1$ cycle | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `decision_aware_hcp` | Proposed Reference | $\gamma=2, \beta=-\ln(2)$ | `PENDING` | `PENDING` | `PENDING` | Baseline ($0.0$) | N/A | Reference |
| **LSTM** | `matched_width_interval` | Matched Width | `regime_hcp`, $\lambda = 0.90$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `widened_interval` | Widened Interval | `global_hcp`, $\lambda = 1.00$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `point_safety_margin` | Point Margin | $m = 4$ cycles | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `earlier_intervention` | Early Policy | `global_hcp`, $h = 1$ cycle | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |

---

## Table T8: Confirmatory Contrasts, 98.75% Decision Intervals, and RQ Classifications

*Target Milestone: `UPD-04`. Four-RQ summary linking to the authoritative 152-component template in [`component_reporting_template.csv`](./component_reporting_template.csv). Component criteria and identities are generated from `src/intellitwin/evaluation/decisions.py::get_rq_component_manifest` (RQ1: 14, RQ2: 20, RQ3: 22, RQ4: 96; Total: 152). All empirical fields remain PENDING; confidence intervals for observed failure gates are designated NOT_APPLICABLE.*

| Research Question | Evaluated Metric & Scope | Primary Comparators | Practical Margin / Threshold | Component Count | Authoritative Template Reference | Overall IUT Decision |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **RQ1 (Maintenance Utility)** | Cost improvement & coverage error ceilings on FD002 (GBR & LSTM) | `global_hcp`, `regime_hcp` | $\Delta_{\text{cost}} > 0.20$ SCU; $E < 0.05$; $\Delta_{\text{fail}} \le 0$ | 14 | `component_reporting_template.csv` (RQ1_*) | `PENDING` |
| **RQ2 (Subgroup Reliability)** | Worst-group coverage error on regimes ($C_1$–$C_6$) and stages on FD002 | `global_hcp`, `regime_hcp` | $\Delta_{\text{error}} > 0.01$; $E(g) < 0.05$; $D_{\text{width}}, D_{\text{score}} < 1.0$ | 20 | `component_reporting_template.csv` (RQ2_*) | `PENDING` |
| **RQ3 (Control Attribution)** | Cost improvement over four matched controls on FD002 (GBR & LSTM) | 4 matched controls | $\Delta_{\text{cost}} > 0.20$ SCU; $E < 0.05$; $\Delta_{\text{fail}} \le 0$ | 22 | `component_reporting_template.csv` (RQ3_*) | `PENDING` |
| **RQ4 (Matrix Generalization)** | Weighted aggregate ($w_k = 1/6$) and cell non-harm across all 6 cells | `global_hcp`, `regime_hcp` | Agg: $>0.20, >0.01$; Cell: $>-0.20, >-0.01$ | 96 | `component_reporting_template.csv` (RQ4_*) | `PENDING` |
| **Total Components** | Full Intersection-Union Test Specification | All frozen baselines & controls | Strictly fail-closed component logic | **152** | [`component_reporting_template.csv`](./component_reporting_template.csv) | `PENDING_EXPERIMENT` |

---

## Table T9: Descriptive Sensitivity Scenarios and Secondary Coverage Levels

*Target Milestone: `UPD-05`. Evaluated across the complete 186-key evaluation matrix in [`evaluation_matrix_template.csv`](./evaluation_matrix_template.csv) generated from `src/intellitwin/evaluation/evidence_schema.py::generate_expected_cell_summary_keys` (162 primary-method combinations + 24 control combinations). These scenarios represent descriptive sensitivity analyses, not component ablations.*

| Matrix Configuration Slice | Target Dataset(s) | Models | Calibration Methods / Controls | Nominal Coverage Levels | Cost Scenarios | Key Count | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Primary Method Evaluations** | FD001, FD002, FD004 | GBR, LSTM | `global_hcp`, `regime_hcp`, `decision_aware_hcp` | 80%, 90%, 95% | `primary_reference`, `failure_sensitive`, `waste_sensitive` | 162 | `PENDING_EXPERIMENT` |
| **Matched Control Evaluations**| FD002 | GBR, LSTM | `matched_width_interval`, `widened_interval`, `point_safety_margin`, `earlier_intervention` | 90% | `primary_reference`, `failure_sensitive`, `waste_sensitive` | 24 | `PENDING_EXPERIMENT` |
| **Complete Evaluation Matrix** | **All In-Scope Datasets** | **Both Architectures** | **All 7 Methods / Controls** | **All 3 Coverage Targets** | **All 3 Economic Scenarios** | **186** | [`evaluation_matrix_template.csv`](./evaluation_matrix_template.csv) |

---

## Table T10: Reproducibility and Verification Audit Matrix

*Tracks committed audit findings across research deliverables, separating executed verification, historical evidence, unavailable evidence, and pending experiments.*

| Evidence Category | Audit Item | Scope / Files Audited | Verification Criterion | Audit Evidence Artifact | Result Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Executed Verification** | **Base Model Checkpoints** | 30 checkpoints across 3 datasets | Checkpoint presence & SHA-256 match | `experiments/base_models/model_registry.json` | `PASS` | 30/30 checkpoints verified on CPU under ADR-020 |
| **Executed Verification** | **Base Model Reproduction** | Seed 2026 across all 6 cells | Exact numerical prediction match | `experiments/audits/step07_prediction_reproduction.json` | `PASS` | GBR max diff 0.0000; LSTM reproducible |
| **Executed Verification** | **Calibration Bundles** | 90 calibrator bundles (270 coverage sets) | POSIX path format & bundle loading | `experiments/calibration/calibration_registry.json` | `PASS` | Cross-platform Linux/Windows verified |
| **Executed Verification** | **Candidate Selection Freeze**| Validation selection across 6 cells | Leave-one-engine-out exact match | `experiments/calibration/selection/selection_freeze.json` | `PASS` | `gamma2_betam1` frozen under ADR-021 |
| **Executed Verification** | **Step 8 Reproduction Check** | 60 model/partition reproductions | Maximum prediction difference 0.0 | `experiments/pretest_verification_v4/reused_evidence.json` | `PASS` | Preserved numerical records rechecked with clean git status |
| **Executed Verification** | **Pre-Test Confirmatory Freeze**| Step 9 evaluation scripts & controls | Hash freeze & zero test artifacts | `experiments/pretest_verification_v4/pretest_audit.json` | `PASS` | Overall status: PASS; pretest readiness: PRETEST_READY |
| **Historical Evidence** | **Step 8 Full Audit v2** | Historical PR #25 verification baseline | Verification under commit `bb9e345` | `experiments/pretest_verification_v2/step08_full_audit.json` | `HISTORICAL_PASS` | Superseded by v4 reference reconstruction verification |
| **Historical Evidence** | **Protected Artifact Baseline**| Tracked Git vs local search files | 652 tracked protected artifacts | `experiments/pretest_verification_v2/baseline_manifest.json` | `HISTORICAL_PASS` | 652 git-tracked verified; 72 local-only search checkpoints |
| **Unavailable Evidence** | **Held-Out Test Trajectories** | True RUL & raw test run traces | Strictly blinded prior to test execution | `experiments/confirmatory_evaluation/` | `NOT_STARTED` | Preserves anti-leakage boundary; prevents overfitting |
| **Pending Experiments** | **Held-Out Point & Interval Outcomes** | Test engines across FD001, FD002, FD004 | Uncapped RMSE, MAE, PICP, MPIW | Pending test execution outputs | `PENDING_EXPERIMENT` | Tracked under `UPD-02` |
| **Pending Experiments** | **Sequential Simulation Outcomes** | Fleet maintenance costs & failure rates | Replay under frozen cost simulator | Pending simulation replay logs | `PENDING_EXPERIMENT` | Tracked under `UPD-03` |
| **Pending Experiments** | **Confirmatory IUT Hypothesis Decisions**| 10,000 paired engine bootstrap draws | 98.75% Bonferroni decision bounds | Pending bootstrap outputs | `PENDING_EXPERIMENT` | Tracked under `UPD-04` |
