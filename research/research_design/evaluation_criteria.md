# Evaluation Criteria

This document details the frozen evaluation criteria, primary metrics, supporting metrics, primary comparators, outcome hierarchy, no-post-hoc-changes rule, threshold governance policy, statistical uncertainty framework, decision rules, evaluation terminology, and final pre-specified evaluation map for Research Questions RQ1–RQ4 under **ADR-018** (Protocol Version: `step06-v2`).

---

## 1. Primary vs. Secondary Outcome Hierarchy

### Global Outcome Hierarchy Rule
The primary outcome determines the main conclusion for each research question. Secondary/supporting outcomes are used to verify constraints, characterize trade-offs, and interpret the result, but a favorable secondary outcome cannot replace failure on the primary outcome. This hierarchy is fixed before confirmatory testing and cannot be changed after confirmatory results are inspected.

### Outcome Hierarchy per Research Question

- **RQ1**:
  - **Primary Outcome**: Total simulated maintenance cost per engine contrast ($\Delta_{\text{cost}} = \overline{\text{Cost}}_B - \overline{\text{Cost}}_P$)
  - **Secondary / Supporting Outcomes**: Marginal absolute coverage error; worst-group operating regime error; worst-group lifecycle stage error; fleet failure rate
  - **Scientific Meaning**: The primary outcome determines the main maintenance-utility conclusion for RQ1. Coverage errors and fleet failure rate serve as supporting evidence and reliability constraints. A favorable secondary metric cannot compensate for failure on the primary outcome or violation of required coverage.

- **RQ2**:
  - **Primary Outcome**: Worst-group conditional coverage error contrast ($\Delta_{\text{error}} = \text{WorstErr}_B - \text{WorstErr}_P$)
  - **Secondary / Supporting Outcomes**: Mean Prediction Interval Width contrast ($D_{\text{width}} = \overline{\text{MPIW}}_P - \overline{\text{MPIW}}_B$); Winkler interval score contrast ($D_{\text{score}} = \overline{\text{IS}}_P - \overline{\text{IS}}_B$); worst-group absolute coverage error
  - **Scientific Meaning**: The primary outcome determines the main reliability conclusion for RQ2. MPIW and interval score are supporting measures used to determine whether any reliability improvement was obtained without materially degrading prediction-interval sharpness or quality.

- **RQ3**:
  - **Primary Outcome**: Maintenance cost improvement over the strongest pre-specified matched-conservatism baseline ($\Delta_{\text{cost}} = \overline{\text{Cost}}_{\text{control}} - \overline{\text{Cost}}_P$)
  - **Secondary / Supporting Outcomes**: Wasted Remaining Useful Life ($RUL_{\text{wasted}}$); cost-inefficient early PM rate; coverage error
  - **Scientific Meaning**: The primary outcome determines whether the proposed method provides genuine maintenance decision value beyond simple conservatism. Wasted RUL and early PM rate provide supporting interpretation but cannot substitute for failure on the primary outcome.

- **RQ4**:
  - **Primary Outcome**: Weighted aggregate contrasts and cell-level non-harm bounds across the 6-cell evaluation matrix
  - **Secondary / Supporting Outcomes**: Individual cell effect sizes; cell-level decision intervals
  - **Scientific Meaning**: The primary outcome determines the robustness/generalization conclusion. Equal cell weighting ($1/6$ each) prevents pooling artifacts.

---

## 2. No Post-Hoc Changes Governance Rule

After the evaluation protocol is frozen, primary metrics, comparator sets, subgroup definitions, practical-effect thresholds, statistical decision rules, and the primary/secondary outcome hierarchy must not be changed based on confirmatory results.

Any later change must be explicitly documented as a protocol deviation. Analyses affected by such a change must be labelled exploratory rather than confirmatory.

Confirmatory results must **NEVER** be used to:
1. Change the primary metric
2. Promote a secondary metric to primary
3. Remove an unfavorable comparator
4. Add a favorable comparator
5. Redefine subgroups
6. Change practical-effect thresholds
7. Redefine Supported / Unsupported / Inconclusive rules
8. Alter robustness configurations
9. Change the statistical unit
10. Change the interpretation rule after seeing results

---

## 3. Threshold-Governance Status (ADR-018 Frozen Contract)

- **Permanent Supersession**: The old arbitrary percentage-based thresholds (5%, 10%, 15%, and 75%) are permanently superseded and must not be restored.
- **Frozen Benchmark Margins**: Numerical practical-effect thresholds are frozen under `step06-v2` in `research/hypotheses/hypothesis_framework.yaml` and `ADR-018`.
- **Benchmark Rationale**:
  - $\Delta_{\text{cost}} > 0.20$ SCU per engine represents the economic cost of exactly one discarded usable operational cycle in the primary scenario ($C_{\text{WASTE}} = 0.20$).
  - $\Delta_{\text{error}} > 0.01$ represents exactly one percentage point improvement in worst-group coverage error.
  - Coverage error ceiling $E < 0.05$ creates an 85%–95% empirical acceptance band around the 90% nominal coverage target.
  - Interval noninferiority margins: $D_{\text{width}} < 1.0$ cycle for MPIW and $D_{\text{score}} < 1.0$ cycle for Winkler interval score.
  - Robustness non-harm bounds: $\Delta_{\text{cost}} > -0.20$ SCU per engine and $\Delta_{\text{error}} > -0.01$.
- **Transparent Preferences**: These thresholds are transparent benchmark acceptance preferences chosen before confirmatory results. They are not claimed to be empirically validated airline economic constants or universal engineering limits.
- **No Post-Hoc Relaxation**: Thresholds must not be relaxed or tuned after observing confirmatory results.

---

## 4. Statistical Uncertainty Framework

- **Independent Statistical Unit**: The engine unit is the independent statistical sample unit. Individual sequence time windows or time steps extracted from the same physical engine exhibit strong temporal autocorrelation and must **NEVER** be treated as independent statistical observations.
- **Comparison Structure**: When proposed and baseline methods are evaluated on the same engine units or dataset splits, comparisons are strictly paired.
- **Resampling Procedure**: Stratified cluster bootstrap ($B = 10,000$ resamples) with replacement, preserving every selected engine's trajectory, models, predictions across all 5 seeds (`[2026, 2027, 2028, 2029, 2030]`), and comparator states.
- **Decision Intervals**: Confirmatory decisions use **98.75% cluster-bootstrap percentile confidence intervals** (quantiles 0.00625 and 0.99375), providing Bonferroni family-wise error control ($\alpha = 0.05 / 4 = 0.0125$) across RQ1–RQ4. Descriptive 95% intervals (quantiles 0.025 and 0.975) provide context.
- **Intersection-Union Principle**: Each RQ requires all required component conditions to pass at the decision level.
- **Missing-Group Bound Propagation**: Replicate-level worst-group errors are recomputed across eligible groups ($\ge 10$ engines). Missing groups propagate conservative $[0, 0.90]$ bounds.
- **P-Value Policy**: No supplementary p-value hypothesis tests form part of the confirmatory protocol.
- *(Full protocol documented in [`research/research_design/statistical_inference_protocol.md`](statistical_inference_protocol.md)).*

---

## 5. Locked Definitions of Evaluation Terms

### Maintenance Improvement
Maintenance improvement means a reduction in total simulated maintenance cost per engine ($\Delta_{\text{cost}} > 0.20$ SCU) relative to the specified comparator while satisfying coverage error ceilings ($E < 0.05$) and the observed failure safeguard ($\Delta_{\text{fail}} \le 0.0$). A lower-cost result obtained by accepting increased failure rate or invalid coverage does not count as maintenance improvement.

### Required Coverage
Required coverage means the pre-specified nominal prediction-interval coverage target: primary nominal coverage is 90% ($\alpha = 0.10$). Secondary sensitivity levels are 80% and 95%.

### Worst-Group
Worst-group means the predefined eligible operating-regime ($C_1$–$C_6$) or degradation lifecycle stage (Early/Mid/Late) showing the largest absolute deviation from the 90% nominal coverage. Groups with fewer than 10 engines are ineligible.

### Matched Conservatism
Matched conservatism means a comparator deliberately adjusted to provide a comparable overall level of conservatism to the proposed method: (1) matched-width / widened intervals, (2) tuned point-prediction safety margins, and (3) earlier-intervention conservative policies. Its purpose is to verify that maintenance utility stems from decision-aware calibration rather than trivial over-conservatism.

### Premature Intervention
Premature intervention (cost-inefficient early PM) means a maintenance action where PM occurred and PM cost exceeded unmitigated failure cost under the active scenario ($W > r_{\text{equal}}$). Equality does not count. The three breakeven horizons are: `primary_reference` = 20 cycles, `failure_sensitive` = 45 cycles, `waste_sensitive` = 10 cycles.

### Wasted RUL
Wasted RUL means the uncapped remaining useful life left unused when preventive maintenance is performed ($W = T - \tau_{\text{decision}} \ge 1$ cycle). Ground-truth failure time is available offline for consequence evaluation but must **NEVER** be used as an inference-time input to the predictive model or maintenance policy.

### Robustness Configuration
A robustness configuration is one of the 6 mandatory cells: FD001 × GBR, FD001 × LSTM, FD002 × GBR, FD002 × LSTM, FD004 × GBR, FD004 × LSTM. Each cell carries an equal weight of $1/6$ in aggregate metrics.

### Practically Meaningful Improvement
Practically meaningful improvement means exceeding the frozen benchmark margins: $\Delta_{\text{cost}} > 0.20$ SCU per engine for maintenance utility; $\Delta_{\text{error}} > 0.01$ for subgroup coverage error reduction.

### Material Degradation in Sharpness
Material degradation in sharpness means an increase in MPIW ($D_{\text{width}} \ge 1.0$ cycle) or Winkler interval score ($D_{\text{score}} \ge 1.0$ cycle).

### Strongest Baseline
Strongest baseline means the best-performing relevant pre-specified comparator among the frozen comparator set under the identical evaluation protocol.

---

## 6. Final Pre-Specified Evaluation Map

### RQ1 — Sequential Maintenance Utility
- **Research Question**: *Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*
- **Primary Metric**: Total simulated maintenance cost per engine contrast ($\Delta_{\text{cost}}$)
- **Supporting Metrics**: Marginal, worst-regime, and worst-stage coverage errors; fleet failure rate
- **Primary Comparators**: Global conformal calibration; standard condition-aware calibration (both GBR and LSTM base models required)
- **Evaluation Dataset & Scenario**: FD002, `primary_reference` ($C_{\text{PM}}=1.0, C_{\text{FAIL}}=5.0, C_{\text{WASTE}}=0.20$), nominal coverage 90%
- **Frozen Thresholds**: $\Delta_{\text{cost}} > 0.20$ SCU per engine; absolute coverage error ceiling $E < 0.05$; failure increase $\le 0.0$
- **Statistical Framework**: 98.75% engine-level cluster-bootstrap percentile decision interval
- **Supported Rule**: For both GBR and LSTM, lower CI of $\Delta_{\text{cost}} > 0.20$ SCU against both baselines, upper CI of all coverage errors $< 0.05$, and observed fleet failure rate increase $\le 0.0$.
- **Unsupported Rule**: For either model, upper CI of $\Delta_{\text{cost}} < 0.20$ SCU against either baseline, lower CI of any coverage error $> 0.05$, or observed fleet failure rate increases over either baseline.
- **Inconclusive Rule**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.

### RQ2 — Conditional Reliability and Sharpness
- **Research Question**: *Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*
- **Primary Metric**: Worst-group conditional coverage error contrast ($\Delta_{\text{error}}$)
- **Supporting Metrics**: MPIW contrast ($D_{\text{width}}$); Winkler interval score contrast ($D_{\text{score}}$); worst-group coverage error
- **Primary Comparators**: Global conformal calibration; standard condition-aware calibration (both GBR and LSTM; both regimes and stages required)
- **Evaluation Dataset**: FD002, nominal coverage 90%
- **Frozen Thresholds**: $\Delta_{\text{error}} > 0.01$; worst-group error ceiling $E < 0.05$; $D_{\text{width}} < 1.0$ cycle; $D_{\text{score}} < 1.0$ cycle
- **Statistical Framework**: 98.75% engine-level cluster-bootstrap percentile decision interval with conservative missing-group bound propagation
- **Supported Rule**: For both models and both subgroup families, lower CI of $\Delta_{\text{error}} > 0.01$ against both baselines, upper CI of worst-group error $< 0.05$, upper CI of $D_{\text{width}} < 1.0$ cycle against both baselines, and upper CI of $D_{\text{score}} < 1.0$ cycle against both baselines.
- **Unsupported Rule**: Upper CI of $\Delta_{\text{error}} < 0.01$, lower CI of worst-group error $> 0.05$, lower CI of $D_{\text{width}} > 1.0$ cycle, or lower CI of $D_{\text{score}} > 1.0$ cycle against either baseline.
- **Inconclusive Rule**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.

### RQ3 — Decision Value vs. Matched Conservatism
- **Research Question**: *Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*
- **Primary Metric**: Maintenance cost improvement over matched-conservatism controls ($\Delta_{\text{cost}}$)
- **Supporting Metrics**: Wasted RUL; cost-inefficient early PM rate; coverage error
- **Primary Comparators**: All three prespecified control families (widened intervals, point safety margins, earlier-intervention policies)
- **Evaluation Dataset & Scenario**: FD002, `primary_reference`, nominal coverage 90%
- **Frozen Thresholds**: $\Delta_{\text{cost}} > 0.20$ SCU per engine against **EVERY** control family; coverage ceiling $E < 0.05$
- **Statistical Framework**: 98.75% engine-level cluster-bootstrap percentile decision interval
- **Supported Rule**: For both models, lower CI of $\Delta_{\text{cost}} > 0.20$ SCU against every control family, upper CI of coverage errors $< 0.05$, and failure increase $\le 0.0$.
- **Unsupported Rule**: Upper CI of $\Delta_{\text{cost}} < 0.20$ SCU against any control family, lower CI of coverage error $> 0.05$, or failure rate increases over any control family.
- **Inconclusive Rule**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.

### RQ4 — Robustness and Generalization
- **Research Question**: *Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*
- **Primary Metric**: Weighted aggregate contrasts and cell-level non-harm bounds across 6 cells (weight $1/6$ each)
- **Supporting Metrics**: Individual cell effect sizes; cell-level decision intervals
- **Primary Comparison**: Proposed method vs.\ Global Conformal and Standard Condition-Aware Calibration across 6 cells
- **Frozen Thresholds**:
  - Aggregate: $\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$ (regimes and stages)
  - Cell-level non-harm: $\Delta_{\text{cost}} > -0.20$ SCU, $\Delta_{\text{error}} > -0.01$ in every cell
  - Cell safeguards: coverage ceiling $E < 0.05$, $D_{\text{width}} < 1.0$ cycle, $D_{\text{score}} < 1.0$ cycle, failure increase $\le 0.0$
- **Statistical Framework**: 98.75% engine-level cluster-bootstrap percentile decision intervals
- **Supported Rule**: Lower CI of weighted aggregate $\Delta_{\text{cost}} > 0.20$ SCU, lower CI of weighted aggregate $\Delta_{\text{error}} > 0.01$ for regimes and stages, lower CI of $\Delta_{\text{cost}} > -0.20$ SCU in every cell, lower CI of $\Delta_{\text{error}} > -0.01$ in every cell, and all cell safeguards hold across all 6 cells.
- **Unsupported Rule**: Upper CI of aggregate $\Delta_{\text{cost}} < 0.20$ SCU or aggregate $\Delta_{\text{error}} < 0.01$, or upper CI of cell $\Delta_{\text{cost}} < -0.20$ SCU or $\Delta_{\text{error}} < -0.01$ in any cell, or any cell safeguard fails.
- **Inconclusive Rule**: No condition fails, but at least one decision interval covers its boundary, or inference is degenerate.
