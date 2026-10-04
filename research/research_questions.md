# Phase 2 Formal Research Questions and Hypotheses (Version 1)

> **Important Notice on Scientific Status**:
> Following the Phase 1 Literature Review, Research Gap v1 and RQ1–RQ4 have been formally formulated and locked for the current research iteration.
> 
> **Governance Status Policy**: **Locked for the current research iteration, but subject to revision if later evidence or methodological constraints invalidate the formulation.**
> 
> "Locked" indicates pre-specification prior to experimental testing to prevent post-hoc hypothesis redefinition based on favorable results. It does NOT mean research questions can never be revised if foundational assumptions are invalidated.
> 
> Detailed Phase 2 formulation, metrics, target leakage constraints, and falsification criteria are recorded in [`research/phase-2/research_gap_rq1_hypothesis.md`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/research/phase-2/research_gap_rq1_hypothesis.md) and [`research/phase-2/experiment_map.md`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/research/phase-2/experiment_map.md).

---

## Approved Research Gap (Version 1)

> **Although recent turbofan prognostic studies provide well-calibrated and increasingly risk-aware RUL prediction intervals, their evaluation remains dominated by aggregate or marginal reliability metrics. Related prognostic research demonstrates that such aggregate calibration can conceal severe conditional undercoverage under changing degradation states or operating regimes. The operational significance of this conditional miscalibration—particularly its effect on late maintenance, premature intervention, wasted useful life, failure risk, and maintenance cost—remains insufficiently characterized for turbofan RUL decision support.**

---

## Formal Research Questions and Hypotheses

### Research Question 1 (RQ1: Conditional RUL Interval Reliability)

- **Status**: **Locked / Provisional v1** (Pre-specified prior to experiments)
- **Question**: *To what extent can nominally calibrated RUL prediction intervals conceal conditional reliability failures across degradation stages and operating regimes in turbofan prognostics?*
- **Theoretical Basis**:
  - *Marginal Calibration*: $P(Y \in C(X)) \approx 1-\alpha$ evaluated across the entire fleet dataset.
  - *Conditional Reliability*: $P(Y \in C(X) \mid G=g) \approx 1-\alpha$ evaluated for specific subgroups $G=g$ (e.g., degradation stages or operating regimes).
  - Satisfactory marginal coverage over an entire test fleet does not imply reliable subgroup coverage.
- **Null Hypothesis ($H_{0,1}$)**:
  > Once nominal marginal calibration has been achieved, RUL prediction-interval coverage does not exhibit practically or statistically meaningful differences across degradation stages or operating regimes.
  $$\forall g \in \mathcal{G}, \quad P(Y \in C(X) \mid G=g) \approx 1-\alpha$$
- **Alternative Hypothesis ($H_{1,1}$)**:
  > RUL prediction intervals that satisfy nominal marginal coverage exhibit systematic conditional coverage deviations across one or more degradation stages or operating regimes.
  $$\exists g \in \mathcal{G} : \left| P(Y \in C(X) \mid G=g) - (1-\alpha) \right| > \delta$$
  *(Note: $\delta > 0$ represents a pre-specified practical calibration tolerance to be fixed prior to final hypothesis testing).*
- **Primary Experimental Evaluation**: RQ1 will initially be evaluated through **Experiment A — Conditional Reliability Audit** (detailed protocol defined in [`research/phase-2/experiment_a_design.md`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/research/phase-2/experiment_a_design.md)).

---

### Research Question 2 (RQ2: Condition-Aware Calibration Efficacy)

- **Status**: **Locked / Provisional v1** (Pre-specified prior to experiments)
- **Question**: *Can condition-aware calibration methods improve worst-group RUL reliability across degradation stages and operating regimes without making prediction intervals excessively wide?*
- **Null Hypothesis ($H_{0,2}$)**:
  > Condition-aware calibration does not meaningfully improve worst-group RUL reliability compared with global calibration, or any apparent reliability improvement is achieved primarily through excessively wider prediction intervals.
- **Alternative Hypothesis ($H_{1,2}$)**:
  > Condition-aware calibration improves worst-group RUL reliability and reduces conditional calibration error compared with global calibration while maintaining practically useful prediction-interval sharpness.
- **Candidate Metrics**: Worst-Group Coverage ($WGC$), Conditional Coverage Error ($CE_g$), Maximum Conditional Calibration Gap ($MCG$), $PICP$, $MPIW$, normalized interval width (if justified later), Interval Score.

---

### Research Question 3 (RQ3: Maintenance Decision Utility)

- **Status**: **Locked / Provisional v1** (Pre-specified prior to experiments)
- **Question**: *Do improvements in conditional RUL calibration lead to better maintenance decisions than point-estimate and globally calibrated maintenance policies?*
- **Null Hypothesis ($H_{0,3}$)**:
  > Improvements in conditional RUL calibration do not produce practically meaningful improvements in downstream maintenance outcomes compared with point-estimate or globally calibrated policies.
- **Alternative Hypothesis ($H_{1,3}$)**:
  > Improved conditional RUL calibration produces better downstream maintenance outcomes by reducing late interventions and failure risk while limiting premature maintenance, wasted useful life, and total maintenance cost.
- **Candidate Decision Metrics**: Late interventions, failure events / missed safe-intervention opportunities, premature maintenance, wasted Remaining Useful Life, intervention lead time, preventive maintenance frequency, total simulated maintenance cost, failure-related cost, premature-replacement cost, decision utility / risk-adjusted cost (if later justified).

---

### Research Question 4 (RQ4: Robustness and Generalization)

- **Status**: **Locked / Provisional v1** (Pre-specified prior to experiments)
- **Question**: *Are the observed conditional calibration failures and their maintenance-decision consequences consistent across different operating conditions, fault modes, base RUL models, and random seeds?*
- **Null Hypothesis ($H_{0,4}$)**:
  > The observed conditional calibration and maintenance-decision effects are not robust and depend strongly on a particular dataset, model architecture, operating condition, fault mode, or random seed.
- **Alternative Hypothesis ($H_{1,4}$)**:
  > The principal conditional calibration and maintenance-decision findings persist across multiple operating conditions, fault modes, base RUL models, and repeated experimental runs.
- **Potential Robustness Dimensions**: C-MAPSS subsets, single-condition vs multi-condition datasets, different fault-mode complexity, multiple base RUL predictors, multiple random seeds, potentially different calibration constructions.

---

## Revision Protocol

1. All research questions (RQ1–RQ4) and hypotheses ($H_{0,1}$–$H_{0,4}$ / $H_{1,1}$–$H_{1,4}$) are pre-specified and locked prior to model development and experiments.
2. Every hypothesis maps strictly to pre-specified statistical metrics, unit-of-independence constraints, and falsification criteria.
3. If empirical evaluation in Experiment A does not reveal meaningful conditional reliability failure, Experiments B and C will be formally reconsidered rather than executed unchanged.
4. All architectural and methodological decisions are logged in [`research/decision_log.md`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/research/decision_log.md).


