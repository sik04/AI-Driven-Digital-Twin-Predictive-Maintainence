# Phase 2: Research Gap, Formal Research Questions (RQ1–RQ4), and Hypotheses Formulation (Version 1)

> **Document Status**: **Locked for Current Research Iteration**
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
> **Date**: 2026-10-04
> **Governance Policy**: "Locked for the current research iteration, but subject to revision if later evidence or methodological constraints invalidate the formulation." This pre-specification prevents post-hoc hypothesis redefinition based on favorable empirical results.

---

## 1. Context and Research Gap (Version 1)

### 1.1 Context and Scope Boundaries
In industrial prognostic health management (PHM) and digital twin frameworks for turbofan engines:
- **Deterministic RUL prediction** using deep neural networks, recurrent architectures, and transformers is well-established in current literature.
- **Calibrated RUL prediction intervals** and distribution-free uncertainty estimation techniques (e.g., split conformal prediction, quantile regression) are established on benchmark datasets such as NASA C-MAPSS.
- **Uncertainty-aware maintenance decision support** linking interval bounds to maintenance scheduling heuristics or risk bounds has been previously explored in isolated settings.

### 1.2 Approved Research Gap Statement (Version 1)

> **Although recent turbofan prognostic studies provide well-calibrated and increasingly risk-aware RUL prediction intervals, their evaluation remains dominated by aggregate or marginal reliability metrics. Related prognostic research demonstrates that such aggregate calibration can conceal severe conditional undercoverage under changing degradation states or operating regimes. The operational significance of this conditional miscalibration—particularly its effect on late maintenance, premature intervention, wasted useful life, failure risk, and maintenance cost—remains insufficiently characterized for turbofan RUL decision support.**

---

## 2. Research Question 1 (Version 1)

> **RQ1: To what extent can nominally calibrated RUL prediction intervals conceal conditional reliability failures across degradation stages and operating regimes in turbofan prognostics?**

### 2.1 Theoretical Framework: Marginal Calibration vs. Conditional Reliability

#### Marginal Calibration
A prediction interval generator $C(X)$ constructed at confidence level $1-\alpha$ satisfies marginal calibration if:
$$P(Y \in C(X)) \approx 1-\alpha$$
where the probability is evaluated over the entire joint distribution of feature inputs $X$ and targets $Y$.

#### Conditional Reliability
A prediction interval generator $C(X)$ satisfies conditional reliability across an operationally meaningful subgroup $G=g$ if:
$$P(Y \in C(X) \mid G=g) \approx 1-\alpha \quad \forall g \in \mathcal{G}$$
where $G$ denotes a discrete group variable such as a specific **degradation stage** (e.g., early life, mid life, near failure) or **operating regime** (e.g., specific flight altitude/throttle setting combinations).

**Core Scientific Premise**: Satisfactory marginal coverage over an entire test fleet does not guarantee reliable subgroup coverage. Aggregate metrics can mask local undercoverage in critical regimes.

### 2.2 Formal Hypotheses for RQ1

- **Null Hypothesis ($H_{0,1}$)**:
  > Once nominal marginal calibration has been achieved, RUL prediction-interval coverage does not exhibit practically or statistically meaningful differences across degradation stages or operating regimes.
  $$\forall g \in \mathcal{G}, \quad P(Y \in C(X) \mid G=g) \approx 1-\alpha$$

- **Alternative Hypothesis ($H_{1,1}$)**:
  > RUL prediction intervals that satisfy nominal marginal coverage exhibit systematic conditional coverage deviations across one or more degradation stages or operating regimes.
  $$\exists g \in \mathcal{G} : \left| P(Y \in C(X) \mid G=g) - (1-\alpha) \right| > \delta$$
  *(Note: $\delta > 0$ represents a pre-specified practical calibration tolerance parameter to be fixed prior to final hypothesis testing).*

---

## 3. Research Question 2 (Version 1)

> **RQ2: Can condition-aware calibration methods improve worst-group RUL reliability across degradation stages and operating regimes without making prediction intervals excessively wide?**

### 3.1 Formal Hypotheses for RQ2

- **Null Hypothesis ($H_{0,2}$)**:
  > Condition-aware calibration does not meaningfully improve worst-group RUL reliability compared with global calibration, or any apparent reliability improvement is achieved primarily through excessively wider prediction intervals.

- **Alternative Hypothesis ($H_{1,2}$)**:
  > Condition-aware calibration improves worst-group RUL reliability and reduces conditional calibration error compared with global calibration while maintaining practically useful prediction-interval sharpness.

---

## 4. Research Question 3 (Version 1)

> **RQ3: Do improvements in conditional RUL calibration lead to better maintenance decisions than point-estimate and globally calibrated maintenance policies?**

### 4.1 Formal Hypotheses for RQ3

- **Null Hypothesis ($H_{0,3}$)**:
  > Improvements in conditional RUL calibration do not produce practically meaningful improvements in downstream maintenance outcomes compared with point-estimate or globally calibrated policies.

- **Alternative Hypothesis ($H_{1,3}$)**:
  > Improved conditional RUL calibration produces better downstream maintenance outcomes by reducing late interventions and failure risk while limiting premature maintenance, wasted useful life, and total maintenance cost.

---

## 5. Research Question 4 (Version 1)

> **RQ4: Are the observed conditional calibration failures and their maintenance-decision consequences consistent across different operating conditions, fault modes, base RUL models, and random seeds?**

### 5.1 Formal Hypotheses for RQ4

- **Null Hypothesis ($H_{0,4}$)**:
  > The observed conditional calibration and maintenance-decision effects are not robust and depend strongly on a particular dataset, model architecture, operating condition, fault mode, or random seed.

- **Alternative Hypothesis ($H_{1,4}$)**:
  > The principal conditional calibration and maintenance-decision findings persist across multiple operating conditions, fault modes, base RUL models, and repeated experimental runs.

---

## 6. Candidate Metrics Suite

### 6.1 Calibration & Reliability Metrics
- **Marginal Prediction Interval Coverage Probability (PICP)**:
  $$PICP = \frac{1}{N} \sum_{i=1}^{N} \mathbb{1}(y_i \in [L_i, U_i])$$
- **Conditional PICP ($PICP_g$)**:
  $$PICP_g = \frac{1}{N_g} \sum_{i \in g} \mathbb{1}(y_i \in [L_i, U_i])$$
- **Conditional Coverage Error ($CE_g$)**:
  $$CE_g = \left| PICP_g - (1-\alpha) \right|$$
- **Worst-Group Coverage (WGC)**:
  $$WGC = \min_{g \in \mathcal{G}} PICP_g$$
- **Maximum Conditional Calibration Gap (MCG)**:
  $$MCG = \max_{g \in \mathcal{G}} \left| PICP_g - (1-\alpha) \right|$$

### 6.2 Sharpness & Efficiency Metrics
- **Mean Prediction Interval Width (MPIW)**:
  $$MPIW = \frac{1}{N} \sum_{i=1}^{N} (U_i - L_i)$$
- **Normalized Interval Width** (if justified later)
- **Interval Score (Winkler Score)**: Evaluates trade-off between coverage penalty and interval width.

### 6.3 Maintenance Decision Metrics
- Late interventions (count and magnitude)
- Failure events / missed safe-intervention opportunities
- Premature maintenance interventions
- Wasted Remaining Useful Life ($RUL_{\text{wasted}}$)
- Intervention lead time distribution
- Preventive maintenance frequency
- Total simulated maintenance cost ($C_{\text{total}} = C_{\text{failure}} + C_{\text{preventive}} + C_{\text{wasted}}$)
- Failure-related cost vs. premature-replacement cost
- Decision utility / risk-adjusted cost (if later justified)

---

## 7. Methodological & Statistical Constraints

### 7.1 Target Leakage Constraint
- **Post-hoc Evaluation**: True RUL ($y_i$) may be used *retrospectively* during offline scientific auditing to assign predictions to degradation stages.
- **Deployable Policy Constraint**: True RUL must **NEVER** be used as an input feature for any online calibration method, adaptive thresholding scheme, or deployable maintenance decision policy.
- Online condition-aware calibration methods must rely strictly on inference-time-observable data (sensor settings, sequence history, predicted RUL $\hat{y}_i$, or inferred regime state).

### 7.2 Unit of Independence Constraint
- Sequential time windows extracted from the same physical engine unit exhibit strong autocorrelation and cannot be assumed independent.
- Statistical inference, confidence intervals, bootstrap resampling, and hypothesis testing must be structured at the **engine unit level** rather than treating individual temporal windows as independent samples.

### 7.3 Degradation-Stage & Operating-Regime Protocols
- Stage partitioning and operating-regime boundaries must be defined based on reproducible criteria (prior literature, engineering justification, or pre-specified observable clustering fit strictly on training engines) and fixed prior to test set evaluation.

---

## 8. Falsification Criteria and Possible Outcomes

### 8.1 Falsification Criteria
RQ1 shall be considered **unsupported** or **weakly supported** if:
1. Nominal marginal coverage is achieved ($PICP \approx 1-\alpha$), AND
2. Group-level coverages ($PICP_g$) across all degradation stages and operating regimes consistently remain within tolerance $\delta$, AND
3. Worst-Group Coverage ($WGC$) does not drop significantly below nominal level, AND
4. Observed subgroup variations are statistically indistinguishable from random sampling fluctuations under engine-level bootstrap testing.

### 8.2 Possible Experimental Outcomes

| Outcome | Description | Research Implications |
| :--- | :--- | :--- |
| **Outcome A: Strong Conditional Failure** | Marginal calibration appears satisfactory ($PICP \approx 1-\alpha$), but one or more critical subgroups exhibit severe undercoverage ($PICP_g \ll 1-\alpha$). | Strongly supports $H_{1,1}$ and justifies investigating downstream decision impacts in Experiments B & C. |
| **Outcome B: Moderate Conditional Variation** | Mild subgroup coverage variation observed, but within acceptable operational bounds. | Weakly supports $H_{1,1}$; requires assessing whether decision impact is operationally significant. |
| **Outcome C: No Meaningful Conditional Failure** | Both marginal and subgroup coverages remain stable across all degradation stages and regimes. | Falsifies $H_{1,1}$; triggers formal re-evaluation of central research premise before proceeding. |

---

## 9. Guiding Research Principle

> **The objective is not to prove that conditional calibration failure exists. The objective is to test whether it exists, quantify its magnitude if present, determine the conditions under which it occurs, and later investigate whether it has meaningful consequences for predictive-maintenance decisions.**
