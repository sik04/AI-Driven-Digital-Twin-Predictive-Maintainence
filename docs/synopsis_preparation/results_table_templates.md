# Results Table Templates and Evidence Capture Specifications

**Document Version**: `1.0`  
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

*Populated from model registry (`experiments/base_models/model_registry.json`), Step 7 freeze (ADR-020), and calibration selection freeze (`experiments/calibration/selection/selection_freeze.json`, ADR-021).*

| Evaluation Cell | Base Model Family | Frozen Winning Configuration | Key Hyperparameters | Validation RMSE (cycles) | Training Horizon / Input Shape | Selected Calibrator Candidate | Selected Scaling $\gamma$ | Selected Asymmetry $\beta_{\text{code}}$ | Numerical $\beta$ | Selection Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **FD001 $\times$ GBR** | HistGradientBoosting | `gbr_lr010_leaf15_l2_0` | `lr=0.10, max_leaf=15, l2=0.0` | 28.42 | Flattened vector $(510,)$ | `gamma2_betam1` | 2 | -1 | $-0.693147$ | `feasible_optimal` |
| **FD001 $\times$ LSTM** | Unidirectional LSTM | `lstm_h64_lr0010` | `H=64, lr=0.0010, drop=0.20` | 30.08 | Sequential tensor $(30, 17)$ | `gamma2_betam1` | 2 | -1 | $-0.693147$ | `feasible_optimal` |
| **FD002 $\times$ GBR** | HistGradientBoosting | `gbr_lr010_leaf31_l2_0` | `lr=0.10, max_leaf=31, l2=0.0` | 34.66 | Flattened vector $(510,)$ | `gamma2_betam1` | 2 | -1 | $-0.693147$ | `feasible_optimal` |
| **FD002 $\times$ LSTM** | Unidirectional LSTM | `lstm_h64_lr0010` | `H=64, lr=0.0010, drop=0.20` | 35.25 | Sequential tensor $(30, 17)$ | `gamma2_betam1` | 2 | -1 | $-0.693147$ | `feasible_optimal` |
| **FD004 $\times$ GBR** | HistGradientBoosting | `gbr_lr010_leaf31_l2_0` | `lr=0.10, max_leaf=31, l2=0.0` | 48.83 | Flattened vector $(510,)$ | `gamma2_betam1` | 2 | -1 | $-0.693147$ | `feasible_optimal` |
| **FD004 $\times$ LSTM** | Unidirectional LSTM | `lstm_h64_lr0010` | `H=64, lr=0.0010, drop=0.20` | 48.25 | Sequential tensor $(30, 17)$ | `gamma2_betam1` | 2 | -1 | $-0.693147$ | `feasible_optimal` |

---

## Table T3: Point-Prediction Performance on Held-Out Test Partitions

*Target Milestone: `UPD-02`. Evaluated across 5 fixed seeds (2026–2030) on held-out test engines.*

| Dataset | Model Architecture | Evaluated Engines | Uncapped RMSE (cycles) | Uncapped MAE (cycles) | Capped RMSE ($RUL \le 125$) | C-MAPSS Asymmetric Score | Early Error Rate ($d < 0$) | Late Error Rate ($d > 0$) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **FD001** | GBR (`gbr_lr010_leaf15_l2_0`) | 20 | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD001** | LSTM (`lstm_h64_lr0010`) | 20 | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | GBR (`gbr_lr010_leaf31_l2_0`) | 52 | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | LSTM (`lstm_h64_lr0010`) | 52 | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | GBR (`gbr_lr010_leaf31_l2_0`) | 50 | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD004** | LSTM (`lstm_h64_lr0010`) | 50 | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |

---

## Table T4: Coverage, Width, and Interval Score by Calibration Method (90% Nominal)

*Target Milestone: `UPD-02`. Evaluated at 90% nominal coverage on held-out test engines across 5 seeds.*

| Dataset | Model | Calibration Method | Marginal PICP (%) | Marginal Error $E$ | MPIW (cycles) | Winkler Interval Score | Optimistic Miss Rate ($y < L$) | Pessimistic Miss Rate ($y > U$) | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **FD002** | **GBR** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **GBR** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **GBR** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **FD002** | **LSTM** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |

---

## Table T5: Operating Regime & Lifecycle Stage Subgroup Reliability Auditing (FD002 Test)

*Target Milestone: `UPD-02` / `UPD-04`. Evaluated across eligible subgroups ($\ge 10$ engines).*

| Subgroup Family | Subgroup Identifier | Engine Count ($N_g$) | Eligibility ($\ge 10$) | `global_hcp` Coverage | `regime_hcp` Coverage | `decision_aware_hcp` Coverage | `decision_aware` Error $E(g)$ | Missing Bounds Used | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Operating Regimes** | Regime $C_1$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **Operating Regimes** | Regime $C_2$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **Operating Regimes** | Regime $C_3$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **Operating Regimes** | Regime $C_4$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **Operating Regimes** | Regime $C_5$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **Operating Regimes** | Regime $C_6$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **Lifecycle Stages** | Early ($t \le T/3$) | 52 | Eligible | `PENDING` | `PENDING` | `PENDING` | `PENDING` | No | `PENDING_EXPERIMENT` |
| **Lifecycle Stages** | Mid ($T/3 < t \le 2T/3$) | 52 | Eligible | `PENDING` | `PENDING` | `PENDING` | `PENDING` | No | `PENDING_EXPERIMENT` |
| **Lifecycle Stages** | Late ($t > 2T/3$) | 52 | Eligible | `PENDING` | `PENDING` | `PENDING` | `PENDING` | No | `PENDING_EXPERIMENT` |
| **Worst-Group Summary** | Regime Worst Error | — | — | `PENDING` | `PENDING` | `PENDING` | — | — | `PENDING_EXPERIMENT` |
| **Worst-Group Summary** | Stage Worst Error | — | — | `PENDING` | `PENDING` | `PENDING` | — | — | `PENDING_EXPERIMENT` |

---

## Table T6: Sequential Maintenance Simulation Outcomes (FD002 Primary Reference)

*Target Milestone: `UPD-03`. Evaluated under $C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$ SCU per engine.*

| Model | Calibration Method | Mean Cost per Engine (SCU) | Observed Failure Rate (%) | Fleet PM Rate (%) | Mean Wasted RUL ($W$, cycles) | Inefficient Early PM Rate (Fleet) | Inefficient Early PM Rate (PM-Only) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **GBR** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `global_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `regime_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `decision_aware_hcp` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |

---

## Table T7: RQ3 Matched-Conservatism Control Comparisons (FD002 Test)

*Target Milestone: `UPD-03` / `UPD-04`. Evaluates decision-value attribution against four pre-specified controls.*

| Base Model | Evaluated Method / Control Configuration | Control Family | Frozen Parameter | Mean Cost (SCU) | Observed Failures (%) | Mean Wasted RUL (cycles) | Cost Contrast vs Proposed ($\Delta_{\text{cost}}$) | 98.75% Decision CI $[\text{CI}_{\text{lower}}, \text{CI}_{\text{upper}}]$ | Condition Pass Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **GBR** | `decision_aware_hcp` | Proposed | $\gamma=2, \beta=-1$ | `PENDING` | `PENDING` | `PENDING` | Baseline ($0.0$) | N/A | Reference |
| **GBR** | `matched_width_interval` | Widened Interval | $\lambda = 0.92$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | `widened_interval` | Widened Interval | $\lambda = 1.00$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | `point_safety_margin` | Point Margin | $m = 5$ cycles | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **GBR** | `earlier_intervention` | Early Policy | $h = 1$ cycle | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `decision_aware_hcp` | Proposed | $\gamma=2, \beta=-1$ | `PENDING` | `PENDING` | `PENDING` | Baseline ($0.0$) | N/A | Reference |
| **LSTM** | `matched_width_interval` | Widened Interval | $\lambda = 0.90$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `widened_interval` | Widened Interval | $\lambda = 1.00$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `point_safety_margin` | Point Margin | $m = 4$ cycles | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **LSTM** | `earlier_intervention` | Early Policy | $h = 1$ cycle | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |

---

## Table T8: Confirmatory Contrasts, 98.75% Decision Intervals, and RQ Classifications

*Target Milestone: `UPD-04`. Evaluated via 10,000 stratified cluster-bootstrap resamples under Bonferroni FWER control ($\alpha = 0.0125$).*

| Research Question | Evaluated Metric & Contrast Direction | Baseline / Comparator | Practical Margin | 95% Descriptive CI | 98.75% Decision CI | Failure Safeguard ($\Delta_{\text{fail}} \le 0$) | Coverage Safeguard ($E < 0.05$) | Final IUT Decision Classification |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **RQ1 (GBR)** | Cost Contrast $\Delta_{\text{cost}}$ (SCU) | `global_hcp` | $> 0.20$ SCU | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **RQ1 (GBR)** | Cost Contrast $\Delta_{\text{cost}}$ (SCU) | `regime_hcp` | $> 0.20$ SCU | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **RQ1 (LSTM)** | Cost Contrast $\Delta_{\text{cost}}$ (SCU) | `global_hcp` | $> 0.20$ SCU | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **RQ1 (LSTM)** | Cost Contrast $\Delta_{\text{cost}}$ (SCU) | `regime_hcp` | $> 0.20$ SCU | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING_EXPERIMENT` |
| **RQ2 (GBR)** | Regime Error $\Delta_{\text{error}}$ | `global_hcp` | $> 0.01$ | `PENDING` | `PENDING` | N/A | $D_{\text{width}}, D_{\text{score}} < 1.0$ | `PENDING_EXPERIMENT` |
| **RQ2 (GBR)** | Stage Error $\Delta_{\text{error}}$ | `regime_hcp` | $> 0.01$ | `PENDING` | `PENDING` | N/A | $D_{\text{width}}, D_{\text{score}} < 1.0$ | `PENDING_EXPERIMENT` |
| **RQ2 (LSTM)** | Regime Error $\Delta_{\text{error}}$ | `global_hcp` | $> 0.01$ | `PENDING` | `PENDING` | N/A | $D_{\text{width}}, D_{\text{score}} < 1.0$ | `PENDING_EXPERIMENT` |
| **RQ2 (LSTM)** | Stage Error $\Delta_{\text{error}}$ | `regime_hcp` | $> 0.01$ | `PENDING` | `PENDING` | N/A | $D_{\text{width}}, D_{\text{score}} < 1.0$ | `PENDING_EXPERIMENT` |
| **RQ3 (GBR)** | Cost Contrast vs All 4 Controls | Matched Controls | $> 0.20$ SCU | `PENDING` | `PENDING` | `PENDING` | All ceilings pass | `PENDING_EXPERIMENT` |
| **RQ3 (LSTM)** | Cost Contrast vs All 4 Controls | Matched Controls | $> 0.20$ SCU | `PENDING` | `PENDING` | `PENDING` | All ceilings pass | `PENDING_EXPERIMENT` |
| **RQ4 (Agg)** | Weighted Aggregate $\Delta_{\text{cost, agg}}$ | Calibration Baselines | $> 0.20$ SCU | `PENDING` | `PENDING` | `PENDING` | All ceilings pass | `PENDING_EXPERIMENT` |
| **RQ4 (Agg)** | Weighted Aggregate $\Delta_{\text{error, agg}}$ | Calibration Baselines | $> 0.01$ | `PENDING` | `PENDING` | `PENDING` | All ceilings pass | `PENDING_EXPERIMENT` |
| **RQ4 (Cells)**| Cell Non-Harm Bounds (6 cells) | Calibration Baselines | $> -0.20, > -0.01$ | `PENDING` | `PENDING` | `PENDING` | All ceilings pass | `PENDING_EXPERIMENT` |

---

## Table T9: Sensitivity Scenarios and Secondary Coverage Levels

*Target Milestone: `UPD-05`. Evaluated on FD002 test engines across secondary configurations.*

| Scenario / Coverage Condition | Parameter Specification | `global_hcp` Cost (SCU) | `regime_hcp` Cost (SCU) | `decision_aware` Cost (SCU) | Contrast $\Delta_{\text{cost}}$ | Observed Failures | Analysis Designation | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **Failure-Sensitive Cost** | $C_{\text{FAIL}}=10.0, C_{\text{PM}}=1.0, C_{\text{WASTE}}=0.20$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | Secondary Sensitivity | `PENDING_EXPERIMENT` |
| **Waste-Sensitive Cost** | $C_{\text{FAIL}}=5.0, C_{\text{PM}}=1.0, C_{\text{WASTE}}=0.40$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | Secondary Sensitivity | `PENDING_EXPERIMENT` |
| **80% Nominal Coverage** | Target: $1 - \alpha = 0.80$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | Secondary Sensitivity | `PENDING_EXPERIMENT` |
| **95% Nominal Coverage** | Target: $1 - \alpha = 0.95$ | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | Secondary Sensitivity | `PENDING_EXPERIMENT` |

---

## Table T10: Reproducibility and Verification Audit Matrix

*Tracks verification status across research deliverables against commit `224c741`.*

| Audit Item | Scope / Files Audited | Verification Criterion | Audit Evidence Artifact | Result Status | Notes |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Base Model Registry** | 30 checkpoints across 3 datasets | Checkpoint presence & SHA-256 match | `experiments/base_models/model_registry.json` | `PASS` | 30/30 checkpoints verified on CPU |
| **Base Model Reproduction** | Seed 2026 across all 6 cells | Exact numerical prediction match | `experiments/audits/step07_prediction_reproduction.json` | `PASS` | GBR 0.0000; LSTM reproducible |
| **Calibration Registry** | 90 calibrator bundles (270 coverage sets) | POSIX path format & bundle loading | `experiments/calibration/calibration_registry.json` | `PASS` | Cross-platform Linux/Windows verified |
| **Candidate Selection Freeze**| Validation selection across 6 cells | Leave-one-engine-out exact match | `experiments/calibration/selection/selection_freeze.json` | `PASS` | `gamma2_betam1` frozen under ADR-021 |
| **Step 8 Deep Verification** | 724 protected calibration files | Byte-for-byte SHA-256 match | `experiments/audits/step08_repair_verification.json` | `PASS` | Checkpoint reproduction: NOT RUN |
| **Pre-Test Confirmatory Freeze**| Step 9 evaluation scripts & controls | Hash freeze & zero test artifacts | `experiments/confirmatory_development/pretest_audit.json` | `PASS` | Confirmatory test execution: NOT STARTED |
| **Corrected Pretest Audit v2**| Checkpoint prediction reproduction | Clean working tree execution | `experiments/pretest_verification_v2/` | `PENDING` | Tracked under `UPD-01` |
