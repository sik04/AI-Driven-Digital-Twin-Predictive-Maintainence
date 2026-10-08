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
   $$S = \sum_{i=1}^{N} s_i, \quad s_i = \begin{cases} e^{-\frac{d_i}{13}} - 1 & \text{for } d_i < 0 \\ e^{\frac{d_i}{10}} - 1 & \text{for } d_i \ge 0 \end{cases}$$
   where $d_i = \text{predicted RUL} - \text{true RUL}$. For $d = \text{predicted RUL} - \text{true RUL}$: $d < 0$ means underestimating remaining life, producing an early/conservative prediction; $d > 0$ means overestimating remaining life, producing an optimistic prediction that risks late intervention; $d = 0$ is exact. Optimistic predictions ($d > 0$) that risk late intervention are penalized more severely ($e^{d/10} - 1$) than conservative early predictions ($d < 0$, $e^{-d/13} - 1$).
3. **Prediction Interval Coverage Probability (PICP)**:
   $$\text{PICP} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}(y_i \in [\hat{L}_i, \hat{U}_i])$$
4. **Mean Prediction Interval Width (MPIW)**:
   $$\text{MPIW} = \frac{1}{N} \sum_{i=1}^{N} (\hat{U}_i - \hat{L}_i)$$

---

## 5. Experiment Provenance and Artifact Logging

Every formal experiment must generate an entry following `experiments/templates/experiment_record.md` recording all 11 mandatory provenance fields:

1. **Dataset / Source Hashes**: Raw file SHA-256 (e.g. `train_FD002.txt`).
2. **Split Manifest Hash**: JSON split manifest SHA-256 (e.g. `fd002_engine_split_seed_2026.json`).
3. **Protocol Version**: Data & Evaluation Protocol version (e.g. Step 5 v1.0).
4. **Feature Order & Window Configuration**: Canonical 17-feature order and 30-cycle lookahead parameters.
5. **Preprocessing Artifact Hashes**: SHA-256 of setting scalers, K-means centroids, and sensor normalization statistics.
6. **Model Seed & Full Configuration**: Model run seed (`2026`–`2030`) and complete hyperparameter dict.
7. **Calibration Configuration**: Conformal calibration method, nonconformity score, and calibrator parameters.
8. **Nominal Coverage**: Target coverage level $1 - \alpha$ (90%, $\alpha=0.10$).
9. **Git SHA & Dirty Status**: Exact commit SHA and dirty worktree status (`git status --porcelain`).
10. **Python & Package Versions**: Executable version, PyTorch, NumPy, SciPy, scikit-learn versions.
11. **Output Artifact Locations**: File paths for model checkpoints, prediction logs, and summary JSON artifacts.

