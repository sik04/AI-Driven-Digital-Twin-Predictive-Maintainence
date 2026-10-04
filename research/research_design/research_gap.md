# Research Gap Formulation (Version 1)

> **Document Status**: **Locked for Current Research Iteration**
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
> **Date**: 2026-10-04
> **Governance Policy**: Locked for the current research iteration, but subject to revision if later evidence or methodological constraints justify a documented research-design revision.

---

## 1. Context and Scope Boundaries

In industrial prognostic health management (PHM) and digital twin frameworks for turbofan engines:
- **Deterministic RUL prediction** using deep neural networks, recurrent architectures, and transformers is mature and well-established in current literature.
- **Calibrated RUL prediction intervals** and distribution-free uncertainty estimation techniques (e.g., split conformal prediction, quantile regression) have already been demonstrated on benchmark datasets such as NASA C-MAPSS.
- **Uncertainty-aware maintenance decision support** linking interval bounds to maintenance scheduling heuristics or risk bounds has been previously explored in isolated settings.

---

## 2. Approved Research Gap Statement (Version 1)

> **Although recent turbofan prognostic studies provide well-calibrated and increasingly risk-aware RUL prediction intervals, their evaluation remains dominated by aggregate or marginal reliability metrics. Related prognostic research demonstrates that such aggregate calibration can conceal severe conditional undercoverage under changing degradation states or operating regimes. The operational significance of this conditional miscalibration—particularly its effect on late maintenance, premature intervention, wasted useful life, failure risk, and maintenance cost—remains insufficiently characterized for turbofan RUL decision support.**

---

## 3. Literature-Grounded Rationale and Non-Claims

### 3.1 What IntelliTwin Is NOT Claiming
To maintain scientific integrity and avoid unsupportable claims during peer review, IntelliTwin explicitly rejects the following broad novelty assertions:
- We do **NOT** claim to be the "first" to combine AI, Digital Twins, and predictive maintenance (established by Huang et al. 2021, Hasan & Crawford 2025, Wei 2024).
- We do **NOT** claim to be the "first" to predict RUL inside a Digital Twin framework (established by Wu et al. 2026).
- We do **NOT** claim to be the "first" to apply split conformal prediction intervals to C-MAPSS (established by Javanmardi & Hüllermeier 2023, Diao et al. 2026).
- We do **NOT** claim to be the "first" to use prediction intervals for maintenance scheduling (established by Chen et al. 2022, Zhu et al. 2025).

### 3.2 Candidate Scientific Contribution
The specific candidate contribution of IntelliTwin is narrower:
**Investigating the operational consequences of conditional RUL calibration failures across degradation stages and operating regimes within a Digital Twin predictive maintenance framework.**

---

## 4. Marginal Calibration vs. Conditional Reliability

### 4.1 Theoretical Distinction
- **Marginal Calibration**: A prediction interval generator $C(X)$ constructed at confidence level $1-\alpha$ satisfies marginal calibration if:
  $$P(Y \in C(X)) \approx 1-\alpha$$
  evaluated over the entire joint distribution of feature inputs $X$ and targets $Y$.
- **Conditional Reliability**: A prediction interval generator $C(X)$ satisfies conditional reliability across an operationally meaningful subgroup $G=g$ if:
  $$P(Y \in C(X) \mid G=g) \approx 1-\alpha \quad \forall g \in \mathcal{G}$$
  where $G$ denotes a discrete group variable such as a specific **degradation stage** (e.g., early life, mid life, near failure) or **operating regime** (e.g., specific flight altitude/throttle setting combinations).

### 4.2 The Conditional Concealment Phenomenon
Satisfactory marginal coverage over an entire test fleet does not guarantee reliable subgroup coverage. Aggregate metrics can conceal local undercoverage in critical regimes (e.g., severe undercoverage near end-of-life masked by overcoverage during early stable operation).

---

## 5. Methodological & Statistical Cautions

### 5.1 Target Leakage Protection
- **Scientific Audit**: True RUL ($y_i$) may be used *retrospectively* during offline auditing to assign predictions to degradation stages.
- **Deployable Policy Constraint**: True RUL must **NEVER** be used as an input feature for any online calibration method, adaptive thresholding scheme, or deployable maintenance decision policy. Online condition-aware calibration must rely strictly on inference-time-observable data (operating settings, sequence history, predicted RUL $\hat{y}_i$, or inferred regime state).

### 5.2 Unit of Independence Constraint
- Sequential time windows extracted from the same physical engine unit exhibit strong autocorrelation and cannot be assumed independent.
- Statistical inference, confidence intervals, bootstrap resampling, and hypothesis testing must be structured at the **engine unit level** rather than treating individual temporal windows as independent samples.

---

## 6. Framework Reference

The formal hypothesis definitions, metric specifications, pre-specified practical thresholds, and decision rules corresponding to this research gap are maintained in the machine-readable hypothesis registry:

[`research/hypotheses/hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml)
