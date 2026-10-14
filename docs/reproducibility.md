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

---

## 6. Hierarchical Conformal Calibration Reproduction Protocol (Step 8)

For conformal calibration reproducibility under `step08-v1` and ADR-024:
1. **Engine-Weighted Non-Interpolated Quantiles**: Each contributing engine receives equal total probability mass ($1/m$). Window-count weighting and numpy percentile interpolation are strictly prohibited.
2. **Exact Rational Threshold Verification**: Floating-point threshold candidate boundaries are verified via exact rational arithmetic using `fractions.Fraction`.
3. **Selection Freeze Gate**: Calibration candidate parameters are selected strictly on validation engines and frozen in Git before final calibrators are fitted on calibration engines.
4. **Independent Audit Script**: `scripts/audit_step08_calibration.py` independently verifies registry artifact hashes, reconstructs selection winners, refits numerical thresholds from prediction caches, and reproduces point predictions directly from frozen model checkpoints.
5. **Mandatory Raw Checkpoint CPU Reproduction & Baseline Classification**: Under ADR-024, raw prediction reproduction from checkpoints is mandatory across all 60 model/partition checks (3 datasets $\times$ 2 architectures $\times$ 5 seeds $\times$ 2 partitions [train, val]). Checkpoints must be executed on CPU in batches of 256, with absolute difference $\le 10^{-4}$ cycles required (observed max error: $0.0$). Baseline artifact manifests distinguish Category A (652 tracked protected artifacts in Git, verified against Git tree hash at `f1edce7fdf48b45513ff90a680da49701451d9cb`) from Category B (72 local-only tuning/search checkpoints preserved under `.gitignore`).

---

## 7. Pre-Test Confirmatory Protocol and Control Freeze (Step 9 / Phase 7)

For confirmatory evaluation preparation under `step09-v1`, ADR-024, and ADR-025:
1. **Validation-Only Matched-Control Selection**: Four prespecified benchmark controls (`matched_width_interval`, `widened_interval`, `point_safety_margin`, `earlier_intervention`) are parameterized exclusively on FD002 validation engines across all five model seeds jointly under `primary_reference` cost scenario at 90% nominal coverage (4,350 total candidates evaluated: 2,175 per family). Exact minimum-relative candidate filtering ($|x - \text{min}| \le 10^{-8}$) and deterministic tie-breaking (smaller parameter value, then `global_hcp` before `regime_hcp`) are strictly applied. Calibration-engine prediction caches and outcomes are strictly blinded during control selection.
2. **Stratified Engine-Cluster Bootstrap & Independent Draw Reconstruction**: 10,000 engine-cluster bootstrap replicates per dataset generated using PCG64 PRNG seeded deterministically by `SeedSequence([2026, 6, dataset_number])`. Lifetime-quartile stratum counts are preserved from split manifests, duplicate-engine multiplicity is retained, and identical draws are reused across all models, seeds, and methods within each dataset. Independent draw verification asserts 100% bit-for-bit array equality against generated NPZs.
3. **Conservative Error Contrasts & Bounded Statistics**: Subgroup error contrasts propagate conservative interval arithmetic ($\Delta_{\text{lower}} = \text{base}_L - \text{prop}_U$ and $\Delta_{\text{upper}} = \text{base}_U - \text{prop}_L$). Bounded statistics store explicit `_lower` and `_upper` replicate distributions; absent subgroups preserve $[0.0, 0.90]$.
4. **Complete 152 Hypothesis Component Evidence**: All 152 hypothesis components across RQ1–RQ4 are exported to `component_evidence.csv` with 19 canonical schema columns and verified via `validate_component_manifest_completeness` without skipping.
5. **Multi-Seed Point Predictions Export**: Point predictions across all 5 confirmatory seeds (2026–2030) are exported with unique composite keys and verified against frozen base model validation prediction caches.
6. **Rigorous Decision Rules**: Bonferroni / Intersection-Union Testing (IUT) rules evaluate improvement, noninferiority, and empirical failure safeguards. Degenerate zero-width decision intervals and exact boundary equality are classified as Indeterminate. Any single failed required component renders the RQ Unsupported.
7. **Strict Execution Provenance & Immutability**: All execution scripts capture HEAD commit SHA, initial clean worktree status, and complete environment dependencies at invocation entry via `src/intellitwin/provenance.py`. Writers enforce atomic, immutable artifact creation (`write_immutable_json`, `write_immutable_csv`, `write_immutable_npz`), failing on conflicting overwrite attempts.
8. **Anti-Leakage Barrier**: Confirmatory held-out test windows are not prepared, processed, or inspected during development. All pre-test smoke outputs are explicitly labeled `DEVELOPMENT_SMOKE_ONLY`, and confirmatory RQ1–RQ4 conclusions remain strictly PENDING until official test execution.
9. **Full Validation Smoke Evaluation & Strengthened Protocol Freeze**: Pre-test readiness requires complete execution of all 930 configurations (810 primary + 120 controls) on validation engines, producing exactly 19,590 engine-seed outcome rows, 186 cell summaries, 152 component evidence rows, and applied 10,000-replicate bootstrap contrast intervals. The final pre-test state is locked in `experiments/pretest_verification_v3/protocol_freeze.json` (SHA-256) and verified in `experiments/pretest_verification_v3/pretest_audit.json` with overall status `PASS` and pre-test readiness `PRETEST_READY`. Historical v2 records are preserved unchanged and formally superseded in `experiments/pretest_verification_v3/supersession.json`.

