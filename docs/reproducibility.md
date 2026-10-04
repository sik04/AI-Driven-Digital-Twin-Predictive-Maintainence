# Reproducibility Charter and Protocols

## 1. Principles of Reproducibility

Scientific progress in prognostics and health management (PHM) requires that every empirical finding can be independently reproduced. IntelliTwin adheres to strict reproducibility standards across all computational stages.

---

## 2. Seed Control and Determinism

All stochastic operations (pseudo-random number generators, model weight initialization, data shuffling, cross-validation folds) must be explicitly seeded.

- A fixed master seed (e.g., `42`) must be defined in every experiment configuration.
- Where multi-trial statistical tests are conducted, a deterministically generated list of distinct random seeds must be reported and logged in the corresponding `experiments/` record.
- Non-deterministic GPU operations must be constrained or explicitly acknowledged.

---

## 3. Data Leakage and Split Isolation

Data leakage is among the highest risks in time-series and degradation prognostic modeling:

1. **Engine-Level Isolation**:
   - Time-series cycles from the same physical asset (e.g., engine unit) must never be split across training, validation, or test subsets.
   - All standardizations (e.g., MinMax or Z-score scalers) must fit strictly on the training subset and transform validation/test subsets without lookahead.
2. **Temporal Windowing**:
   - Sequence windowing must respect temporal causality. Future sensor readings must never leak into historical feature windows.
3. **Hyperparameter Selection**:
   - Model selection and hyperparameter tuning must be performed exclusively on cross-validation or held-out validation subsets, never on test partitions.

---

## 4. Standard Metric Definitions

To prevent ambiguity, the following canonical metrics are mandated across all comparative experiments:

1. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}$$
2. **PHM 2008 Asymmetric Scoring Function**:
   $$S = \sum_{i=1}^{N} s_i, \quad s_i = \begin{cases} e^{-\frac{d_i}{13}} - 1 & \text{for } d_i < 0 \text{ (late prediction)} \\ e^{\frac{d_i}{10}} - 1 & \text{for } d_i \ge 0 \text{ (early prediction)} \end{cases}$$
   where $d_i = \hat{y}_i - y_i$. Late predictions are penalized more severely than early warnings.
3. **Prediction Interval Coverage Probability (PICP)**:
   $$\text{PICP} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}(y_i \in [\hat{L}_i, \hat{U}_i])$$
4. **Mean Prediction Interval Width (MPIW)**:
   $$\text{MPIW} = \frac{1}{N} \sum_{i=1}^{N} (\hat{U}_i - \hat{L}_i)$$

---

## 5. Experiment Provenance and Artifact Logging

Every formal experiment must generate an entry following `experiments/templates/experiment_record.md` recording:
- Experiment ID and date
- Exact Git commit SHA
- Hardware and operating environment (OS, CPU, GPU, Python version, library versions)
- Hyperparameter dictionary
- Raw metric outputs and artifact paths
