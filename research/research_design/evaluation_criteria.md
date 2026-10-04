# Evaluation Criteria

This document details the locked evaluation criteria, primary metrics, supporting metrics, primary comparators, outcome hierarchy, no-post-hoc-changes rule, threshold governance policy, statistical uncertainty framework, decision rules, evaluation terminology, and final pre-specified evaluation map for Research Questions RQ1–RQ4.

---

## 1. Primary vs. Secondary Outcome Hierarchy

### Global Outcome Hierarchy Rule
The primary outcome determines the main conclusion for each research question. Secondary/supporting outcomes are used to verify constraints, characterize trade-offs, and interpret the result, but a favorable secondary outcome cannot replace failure on the primary outcome. This hierarchy must be fixed before confirmatory testing and cannot be changed after confirmatory results are inspected.

### Outcome Hierarchy per Research Question

- **RQ1**:
  - **Primary Outcome**: Total simulated maintenance cost per engine
  - **Secondary / Supporting Outcomes**: Late/failure intervention rate; required prediction-interval coverage
  - **Scientific Meaning**: The primary outcome determines the main maintenance-utility conclusion for RQ1. Late/failure intervention rate and prediction-interval coverage serve as supporting evidence and reliability constraints. A favorable secondary metric cannot compensate for failure on the primary outcome or violation of required coverage.

- **RQ2**:
  - **Primary Outcome**: Worst-group conditional coverage error
  - **Secondary / Supporting Outcomes**: Mean Prediction Interval Width (MPIW); interval score
  - **Scientific Meaning**: The primary outcome determines the main reliability conclusion for RQ2. MPIW and interval score are supporting measures used to determine whether any reliability improvement was obtained without materially degrading prediction-interval sharpness or quality.

- **RQ3**:
  - **Primary Outcome**: Maintenance cost/utility improvement over the strongest pre-specified matched-conservatism baseline
  - **Secondary / Supporting Outcomes**: Wasted Remaining Useful Life ($RUL_{\text{wasted}}$); premature intervention rate
  - **Scientific Meaning**: The primary outcome determines whether the proposed method provides genuine maintenance decision value beyond simple conservatism. Wasted RUL and premature intervention rate provide supporting interpretation but cannot substitute for failure on the primary outcome.

- **RQ4**:
  - **Primary Outcome**: Cross-configuration consistency of the proposed method's effect
  - **Secondary / Supporting Outcomes**: Effect size; engine-level confidence intervals
  - **Scientific Meaning**: The primary outcome determines the robustness/generalization conclusion. Effect sizes and engine-level confidence intervals provide supporting statistical evidence used to interpret the consistency and uncertainty of the observed effect.

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

## 3. Threshold-Governance Status

- **Non-Restoration of Default Thresholds**: The previously used 5%, 10%, 15%, and 75% values are not part of the final active evaluation criteria and must not be restored as default success thresholds.
- **Simulator Validation Prerequisite**: Exact numerical practical-effect thresholds remain intentionally deferred until after maintenance-simulator implementation and validation in the later simulator stage of the governing research workflow (Step 6).
- **Role of Bounded Pilots**: If necessary, bounded pilot evidence may then be used to estimate realistic operational effect and variability scales.
- **Pre-Test Freezing**: After simulator validation and any bounded pilot assessment, the final thresholds must be scientifically and operationally justified and frozen before confirmatory testing.
- **No Post-Hoc Threshold Tuning**: Confirmatory results cannot be used to select, tune, relax, or redefine these thresholds.

---

## 4. Statistical Uncertainty Framework

- **Independent Statistical Unit**: The engine unit is the independent statistical sample unit. Individual sequence time windows or time steps extracted from the same physical engine exhibit strong temporal autocorrelation and must **NEVER** be treated as independent statistical observations.
- **Comparison Structure**: When proposed and baseline methods are evaluated on the same engine units or dataset splits, comparisons must be paired.
- **Uncertainty Quantification**: For each primary metric, statistical uncertainty will be quantified using a **95% engine-level paired/cluster bootstrap confidence interval** (resampling engine units intact).
- **Effect Reporting**: Effect sizes and their corresponding 95% engine-level confidence intervals must always be reported together.
- **P-Value Policy**: P-values or statistical hypothesis tests, if reported, represent secondary supporting evidence and cannot independently determine whether a research question is supported.
- **Deferred Statistical Parameters**: The exact bootstrap resample count, exact CI construction variant (e.g., percentile vs. BCa), secondary significance tests, and multiplicity correction procedures remain deferred to the detailed experimental protocol.

---

## 5. Locked Definitions of Evaluation Terms

### Maintenance Improvement
Maintenance improvement means a reduction in total simulated maintenance cost per engine relative to the specified comparator while satisfying the required coverage/reliability constraints. A lower-cost result obtained by accepting unacceptable failure risk or invalid coverage does not count as maintenance improvement.

### Required Coverage
Required coverage means the pre-specified nominal prediction-interval coverage requirement used by the experiment. The exact nominal coverage level and allowable tolerance will be fixed in the detailed experimental protocol before confirmatory testing.

### Worst-Group
Worst-group means the predefined eligible operating-condition or degradation subgroup showing the largest deviation from the required nominal coverage. For RQ2, worst-group conditional coverage error therefore represents the maximum subgroup coverage error across the predefined eligible groups. The worst group must not be selected through post-hoc subgroup creation.

### Matched Conservatism
Matched conservatism means a comparator deliberately adjusted to provide a comparable overall level of conservatism to the proposed method, such as comparable interval width, safety margin, or intervention tendency. Its purpose is to determine whether maintenance improvement comes from useful decision-aware uncertainty information rather than merely being more cautious. The exact matching procedure will be fixed before confirmatory testing.

### Premature Intervention
Premature intervention means a maintenance action triggered substantially earlier than operationally necessary according to the finalized maintenance-simulator policy, resulting in avoidable loss of usable component life. The exact numerical boundary will be defined after maintenance-simulator validation.

### Wasted RUL
Wasted RUL means the amount of true remaining useful life left unused when maintenance is performed. Ground-truth RUL may be used for post-hoc evaluation of this metric but must **NEVER** be used as an inference-time input to the proposed method or deployable maintenance policy. *(Target-leakage safeguard).*

### Robustness Configuration
A robustness configuration is a predefined experimental setting formed from the relevant dataset or dataset subset, operating-condition setting, base RUL predictor/model family, and repeated run/seed specification. Robustness configurations must be defined before confirmatory analysis and cannot be created afterward to favor the observed results.

### Practically Meaningful Improvement
Practically meaningful improvement means an effect large enough to exceed the pre-specified minimum operational or scientific importance threshold. The exact numerical threshold remains deferred until after maintenance-simulator validation and bounded pilot evidence, after which it must be frozen before confirmatory testing.

### Material Degradation in Sharpness
Material degradation in sharpness means a worsening of MPIW or interval score large enough to exceed the future pre-specified acceptable degradation threshold. Differences within the finalized acceptable tolerance will not automatically invalidate an RQ2 reliability improvement.

### Strongest Baseline
Strongest baseline means the best-performing relevant pre-specified comparator for the primary outcome of the corresponding RQ under the same evaluation protocol. Comparator membership must be finalized before confirmatory analysis; baselines cannot be added or removed after confirmatory results are inspected.

---

## 6. Final Pre-Specified Evaluation Map

### RQ1 — Sequential Maintenance Utility

- **Research Question**: *Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*
- **Primary Metric**: Total simulated maintenance cost per engine
- **Supporting Metrics**: Late/failure intervention rate; required prediction-interval coverage
- **Primary Comparators**: Global conformal calibration; standard condition-aware calibration
- **Comparison Conditions**: The proposed and baseline methods must be evaluated under the same predictor, data protocol, engine splits, and sequential maintenance environment.
- **Practical-Effect Threshold**: Deferred until after maintenance-simulator validation and, if needed, bounded pilot evidence.
- **Statistical Unit**: Engine
- **Statistical Framework**: Paired comparison when the same engines/splits are used; 95% engine-level paired/cluster-bootstrap confidence interval; effect size reported with confidence interval; windows/time steps are not independent samples; p-values, if reported, are secondary evidence.
- **Supported Rule**: The proposed method achieves a practically meaningful reduction in total simulated maintenance cost per engine relative to both global conformal calibration and standard condition-aware calibration, the 95% engine-level confidence interval supports that improvement, and the required prediction-interval coverage is maintained.
- **Unsupported Rule**: Evidence shows no practically meaningful maintenance-cost improvement over the strongest relevant baseline, a relevant baseline performs better, or the proposed method achieves lower maintenance cost only by violating the required coverage/reliability constraint.
- **Inconclusive Rule**: The estimated maintenance improvement is favorable but its 95% confidence interval overlaps the future practical-effect threshold, or results across the primary comparators do not permit a clear conclusion.

### RQ2 — Conditional Reliability and Sharpness

- **Research Question**: *Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*
- **Primary Metric**: Worst-group conditional coverage error
- **Supporting Metrics**: Mean Prediction Interval Width (MPIW); interval score
- **Primary Comparators**: Global conformal calibration; standard condition-aware calibration
- **Practical-Effect Threshold**: Deferred until after maintenance-simulator validation and, if needed, bounded pilot evidence.
- **Statistical Unit**: Engine
- **Statistical Framework**: Engine-level uncertainty; 95% confidence interval; effect size reported with uncertainty; no window-level pseudo-replication.
- **Supported Rule**: The proposed method produces a practically meaningful improvement in worst-group conditional coverage error, supported by its 95% engine-level confidence interval, without materially degrading prediction-interval sharpness or quality as measured by MPIW and interval score.
- **Unsupported Rule**: There is no practically meaningful improvement in worst-group reliability, worst-group reliability becomes worse, or the apparent coverage improvement is achieved primarily through materially wider or poorer-quality prediction intervals.
- **Inconclusive Rule**: Worst-group reliability appears to improve, but the confidence interval overlaps the future meaningful-effect boundary, or the reliability-versus-sharpness trade-off cannot clearly be classified as beneficial.

### RQ3 — Decision Value vs. Matched Conservatism

- **Research Question**: *Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*
- **Primary Metric**: Maintenance cost/utility improvement over the strongest pre-specified matched-conservatism baseline
- **Supporting Metrics**: Wasted RUL; premature intervention rate
- **Primary Comparators**: Widened / matched-width prediction intervals; tuned point-prediction safety margins; earlier-intervention conservative policies. *(Exact implementation/tuning remains deferred until the detailed protocol).*
- **Practical-Effect Threshold**: Deferred until after maintenance-simulator validation and, if needed, bounded pilot evidence.
- **Statistical Unit**: Engine
- **Statistical Framework**: Paired proposed-vs-baseline comparisons; 95% engine-level paired/cluster-bootstrap confidence interval; effect size reported with uncertainty.
- **Supported Rule**: The proposed method achieves a practically meaningful improvement in maintenance cost/utility over the strongest pre-specified matched-conservatism baseline, supported by its 95% engine-level confidence interval, demonstrating maintenance benefit beyond that obtainable by simple interval widening, point-prediction safety margins, or earlier intervention.
- **Unsupported Rule**: One or more appropriately matched conservative baselines reproduce or outperform the proposed method's maintenance benefit, indicating that the observed gain does not require decision-aware calibration.
- **Inconclusive Rule**: The proposed method appears better than the matched-conservatism controls, but the confidence interval overlaps the future meaningful-effect boundary or the different conservative controls provide mixed evidence.

### RQ4 — Robustness and Generalization

- **Research Question**: *Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*
- **Primary Metric**: Cross-configuration consistency of the proposed method's effect
- **Supporting Metrics**: Effect size; engine-level confidence intervals
- **Primary Comparison**: The same proposed-versus-baseline comparisons will be repeated across predefined datasets/dataset subsets, operating conditions, base RUL model families, and random seeds/runs. *(Exact datasets, model families, configurations, and seed count remain deferred until the detailed protocol).*
- **Practical/Consistency Threshold**: Deferred until after maintenance-simulator validation and, if needed, bounded pilot evidence.
- **Statistical Unit**: Engine
- **Statistical Framework**: Effect sizes across predefined configurations; engine-level confidence intervals; repeated seeds/configurations must not be treated as justification for window-level independence.
- **Supported Rule**: The proposed method shows a consistently favorable and practically meaningful effect across the predefined robustness evaluation, with no systematic reversal across datasets, operating conditions, base RUL model families, or repeated seeds/runs. Engine-level uncertainty estimates support the conclusion that the effect is not limited to a particular experimental configuration. *(Support does NOT require improvement in broad terms in literally every individual configuration, but requires consistent overall benefit without systematic failure).*
- **Unsupported Rule**: The proposed method's benefit disappears, systematically reverses, or is clearly restricted to particular datasets, operating conditions, model families, or stochastic runs.
- **Inconclusive Rule**: Results are mixed across predefined robustness configurations or the statistical uncertainty is too large to determine whether the observed benefit is genuinely robust.
