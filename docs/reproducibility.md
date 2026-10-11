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

Let $N$ denote the total number of evaluated engines, $T_i$ denote engine $i$'s failure cycle, $V_i = \{30, 31, \dots, T_i\}$ denote the qualified evaluation endpoints, and $n_i = |V_i| = T_i - 29$ ($T_i \ge 30$).

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} |p_{it} - y_{it}| \right]$$

2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} (p_{it} - y_{it})^2 \right]}$$
   *(Governance Rule: RMSE is the square root of the mean engine MSEs; engine-specific RMSEs must NOT be averaged).*

3. **Prediction Interval Coverage Probability (PICP)**:
   $$\text{PICP} = \frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} \mathbf{1}\{L_{it} \le y_{it} \le U_{it}\} \right]$$

4. **Mean Prediction Interval Width (MPIW)**:
   $$\text{MPIW} = \frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} (U_{it} - L_{it}) \right]$$

5. **Central Winkler Interval Score ($\text{IS}_\alpha$)**:
   $$\bar{\text{IS}}_\alpha = \frac{1}{N} \sum_{i=1}^N \left[ \frac{1}{n_i} \sum_{t \in V_i} \text{IS}_\alpha(L_{it}, U_{it}; y_{it}) \right]$$
   where $\text{IS}_\alpha(L, U; y) = (U - L) + \frac{2}{\alpha}(L - y)\mathbf{1}\{y < L\} + \frac{2}{\alpha}(y - U)\mathbf{1}\{y > U\}$ for primary $\alpha = 0.10$.

6. **Mean Simulated Maintenance Cost**:
   $$\bar{C} = \frac{1}{N} \sum_{i=1}^N C_i$$

---

## 5. Experiment Provenance and Artifact Logging

Every formal experiment must generate an entry following `experiments/templates/experiment_record.md` recording all mandatory provenance fields:

1. **Dataset / Source Hashes**: Raw file exact-byte SHA-256 (e.g. `train_FD002.txt`).
2. **Split Manifest Hash**: JSON split manifest exact-byte SHA-256 (e.g. `fd002_engine_split_seed_2026.json`).
3. **Protocol Version**: Data & Evaluation Protocol version (Step 5 v1.0).
4. **Feature Order & Window Configuration**: Canonical 17-feature order and 30-cycle causal lookback parameters.
5. **Preprocessing Artifact Hashes**: SHA-256 of setting scalers, K-means centroids, and sensor normalization statistics.
6. **Model Seed & Full Configuration**: Model run seed (`2026`–`2030`) and complete hyperparameter dict.
7. **Calibration Configuration**: Conformal calibration method, nonconformity score, and calibrator parameters.
8. **Nominal Coverage**: Target coverage level $1 - \alpha$ (primary 90%, $\alpha=0.10$; secondary 80%, 95%).
9. **Git SHA & Dirty Status**: Exact commit SHA and dirty worktree status (`git status --porcelain`).
10. **Python & Package Versions**: Executable version, PyTorch, NumPy, SciPy, scikit-learn versions.
11. **Output Artifact Locations**: File paths for model checkpoints, prediction logs, and summary JSON artifacts.

### Source-Code Hash Scheme (`sha256-utf8-lf-v1`)

To guarantee verifiable code provenance across platforms regardless of git line-ending configurations (CRLF on Windows vs. LF on Linux/macOS), all source-code file hashes recorded in experimental provenance use the `sha256-utf8-lf-v1` scheme:
1. Decode the source file content as UTF-8 text.
2. Normalize all line endings (`\r\n` and `\r`) to standard Unix line feeds (`\n`).
3. Compute the SHA-256 cryptographic digest over the resulting UTF-8 bytes.

This ensures identical source code checked out on Windows and Linux produces the exact same cryptographic hash.
Raw data files (`.txt`) and JSON split manifests use exact binary byte SHA-256 hashes without line-ending normalization.


