# Phase 8 Exploratory Ablation and Robustness Analysis Protocol

- **Protocol Version**: `phase08-v1`
- **Schema Version**: `phase08-protocol-v1`
- **Stage**: Exploratory Post-Confirmatory Analysis (Designed after held-out confirmatory inspection)
- **Status**: Active Investigation
- **Baseline Confirmatory SHA**: `fa1aa75783d5e675f20afffe5a8c821b04691551` / `129b3d7cdd32bba04f2b8ea64af14ee3993f7d1a`
- **Scientific Status Note**: Held-out confirmatory results have already been inspected. All analyses under Phase 8 are strictly `EXPLORATORY_POST_CONFIRMATORY`. They do not replace, reinterpret as successful, or overwrite the frozen RQ1–RQ4 classifications (which remain `UNSUPPORTED`). No new winning model is selected, and the production system is not recalibrated.

---

## 1. Scope, Purpose, and Preregistered Post-Confirmatory Lock

This protocol defines the exact experimental procedures, mathematical formulations, perturbation seeds, inference rules, and acceptance criteria for **Phase 8 (Exploratory Ablation and Robustness Analysis)**.

### 1.1 Common Scope Across Experiments
- **Datasets**: C-MAPSS sub-corpora `FD001` (20 test engines), `FD002` (52 test engines), and `FD004` (50 test engines). Total held-out run-to-failure engines = 122.
- **Model Families**: Gradient Boosted Regressor (`GBR`) and Long Short-Term Memory network (`LSTM`).
- **Model Seeds**: `2026`, `2027`, `2028`, `2029`, `2030`.
- **Nominal Coverage**: $0.90$ (90%) only.
- **Cost Scenario**: Frozen `primary_reference` synthetic scenario ($C_{\text{pm}}=1.0$, $C_{\text{fail}}=5.0$, $C_{\text{waste}}=0.20$, $r_{\text{equal}}=20.0$).
- **Maintenance Policy**: Frozen `lower_bound_one_cycle_policy` ($\text{MAINTAIN\_NOW} \iff L \le 1.0$, else $\text{CONTINUE}$) evaluated on endpoints 30 through $T-1$, with cycle $T$ reserved for unmitigated failure events.
- **Ground Truth Targets**: Uncapped RUL targets $y \ge 0$, causal windowing (lookback 30), equal-engine weighting, and trajectory observability constraints.
- **Strict Prohibition**: No new model training, architecture search, threshold tuning on test engines, cost-scenario search, or hyperparameter optimization.

---

## 2. Experiment A: Complete Component Factorial Ablation

To systematically assess the mechanistic contributions of the three components of the proposed `decision_aware_hcp` method, a full $2 \times 2 \times 2$ factorial ablation is conducted:

### 2.1 Factorial Factors
1. **$\gamma$ (Prediction-Dependent Scale)**:
   - $\gamma = 0$: Standard unscaled score denominator ($\sigma(p) = 1$).
   - $\gamma = 2$: Proposed quadratic scale dilation ($\sigma(p) = (1 + p/125)^2$).
2. **$\beta$ (Directional Asymmetry)**:
   - $\beta = 0$ (`beta_code = 0`): Symmetric nonconformity score.
   - $\beta = -\ln(2)$ (`beta_code = -1`): Asymmetric safety buffer penalizing under-prediction in late life.
3. **Threshold Routing**:
   - `global`: Single global hierarchical conformal threshold applied across all operating regimes.
   - `regime`: Operating-regime-specific hierarchical thresholds with global fallback for insufficient support.

### 2.2 Factorial Variants (8 Candidates)
Each candidate is specified via `CandidateConfig.from_params(gamma, beta_code)`:
1. `gamma0_beta0_global` ($\gamma=0, \beta=0$, global routing) — functionally equivalent to `global_hcp`.
2. `gamma0_beta0_regime` ($\gamma=0, \beta=0$, regime routing) — functionally equivalent to `regime_hcp`.
3. `gamma0_betam1_global` ($\gamma=0, \beta=-\ln(2)$, global routing).
4. `gamma0_betam1_regime` ($\gamma=0, \beta=-\ln(2)$, regime routing).
5. `gamma2_beta0_global` ($\gamma=2, \beta=0$, global routing).
6. `gamma2_beta0_regime` ($\gamma=2, \beta=0$, regime routing).
7. `gamma2_betam1_global` ($\gamma=2, \beta=-\ln(2)$, global routing).
8. `gamma2_betam1_regime` ($\gamma=2, \beta=-\ln(2)$, regime routing) — full proposed `decision_aware_hcp` method.

### 2.3 Threshold Fitting and Evaluation Rules
- **Calibration-Only Fitting**: Thresholds are fitted strictly on clean calibration prediction caches using uncapped calibration labels (`rul_true`). Calibration engines alone fit thresholds; validation or test engines are never used for fitting.
- **Global Routing Execution**: For global routing, the candidate's global threshold is inverted using `invert_score_to_interval` with the **same** candidate configuration. It does not call the baseline `global_hcp` path in a way that discards asymmetry.
- **Isolated Artifacts**: Exploratory calibrators are saved under `experiments/phase08_exploratory_v1/exploratory_calibrators/` and are never registered into the production calibrator registry.
- **Reused Clean Predictions**: Point predictions are reused directly from the clean confirmatory held-out test predictions cache (`experiments/confirmatory_v1/point_predictions.csv`).
- **Matrix Volume**: $8 \text{ variants} \times 3 \text{ datasets} \times 2 \text{ models} \times 5 \text{ seeds} = 240$ evaluated cells.

### 2.4 Mandatory Equivalence Gates
- `gamma0_beta0_global` reproduces frozen `global_hcp` intervals at `atol=1e-10, rtol=0`.
- `gamma0_beta0_regime` reproduces frozen `regime_hcp` intervals at `atol=1e-10, rtol=0`.
- `gamma2_betam1_regime` reproduces frozen `decision_aware_hcp` intervals at `atol=1e-10, rtol=0`.
- On `FD001`, global and regime routing yield identical intervals for each candidate at `atol=1e-10, rtol=0`.
- Reconstructed thresholds match independent hierarchical quantile calculation at `atol=1e-10, rtol=0`.

---

## 3. Experiment B: Frozen-Method Stress Tests

Evaluates the empirical degradation behavior of the three original frozen calibration methods (`global_hcp`, `regime_hcp`, `decision_aware_hcp`) under 7 engineering stress probes across 18 stream conditions.

### 3.1 Stress Conditions
0. `clean`: Unperturbed baseline stream (1 replicate).
1. `noise_std_005`: Additive Gaussian sensor noise, $\sigma = 0.05$ (3 replicates).
2. `noise_std_010`: Additive Gaussian sensor noise, $\sigma = 0.10$ (3 replicates).
3. `noise_std_020`: Additive Gaussian sensor noise, $\sigma = 0.20$ (3 replicates).
4. `dropout_prob_005`: Independent sensor dropout, probability $p = 0.05$ (3 replicates).
5. `dropout_prob_010`: Independent sensor dropout, probability $p = 0.10$ (3 replicates).
6. `setting1_bias_plus_020`: Normalized operational setting1 measurement bias $+0.20$ (1 replicate).
7. `setting1_bias_minus_020`: Normalized operational setting1 measurement bias $-0.20$ (1 replicate).

Total stream conditions = $1 + 3 \times 3 + 2 \times 3 + 2 = 18$.  
Total method evaluations = $18 \times 3 \text{ datasets} \times 2 \text{ models} \times 5 \text{ seeds} \times 3 \text{ methods} = 1,620$ cells.

### 3.2 Perturbation Specifications
- **Temporal Consistency**: Perturbations are applied to the frozen-preprocessed feature stream **before** constructing overlapping windows. Every engine/cycle/feature has a single value shared across all windows covering that timepoint.
- **Sensor-Only Gaussian Noise**: Applied to the 14 retained degradation sensors (`s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21`) only. Setting columns are unperturbed. The three noise levels share the same underlying standard-normal draws ($z \sim \mathcal{N}(0, I)$): $\text{noise} = \sigma \cdot z$.
- **Causal Sensor Dropout**: Retained sensors are masked independently per cycle. Missing values are imputed using the last observed value of that sensor within the same engine (forward fill). If missing at cycle 1 before any observation exists, normalized 0.0 is used. Future values or cross-engine observations are strictly prohibited. The two dropout rates share the same underlying uniform draws ($u \sim \mathcal{U}(0, 1)$): masked if $u < p$.
- **Setting Measurement Bias**: Constant $\pm 0.20$ added to normalized `setting1`. Regime routing and preprocessing assignment remain fixed to clean regime IDs. Explicitly defined as an input measurement bias probe, not a physical operating regime alteration.
- **Deterministic PRNG**: NumPy `PCG64` initialized with:
  $$\text{SeedSequence}([2026, 8, \text{dataset\_number}, \text{engine\_id}, \text{perturbation\_family}, \text{replicate\_id}])$$
  where `dataset_number` is 1 for FD001, 2 for FD002, 4 for FD004; `family=1` for Gaussian noise, `family=2` for dropout; `replicate_id` $\in \{0, 1, 2\}$.
- **CPU Inference**: Run in batches of 256, 2 CPU threads, one model at a time.

---

## 4. Statistical Inference and Exploratory Contrasts

### 4.1 Statistical Unit and Averaging Hierarchy
- **Statistical Unit**: The engine ($i = 1, \dots, N$).
- **Seed Averaging**: Model seeds $s \in \{2026, \dots, 2030\}$ are averaged within each engine.
- **Replicate Averaging**: For stochastic stress conditions, perturbation replicates $r \in \{0, 1, 2\}$ are averaged within each engine. Model seeds and perturbation replicates are never treated as independent engines.

### 4.2 Paired Stratified Bootstrap
- **Replicates**: $B = 10,000$.
- **PRNG**: `np.random.Generator(PCG64(SeedSequence([2026, 8, dataset_number])))`.
- **Stratification**: Frozen lifetime quartiles ($Q_1, Q_2, Q_3, Q_4$).
- **Pairing**: Replicate draws are identical across all variants and stress conditions within each dataset.
- **Quantiles**: 95% empirical percentile confidence intervals via `numpy.quantile(..., method="linear")` with $\alpha = [0.025, 0.975]$.
- **Contrasts**:
  - Ablations: Variant minus Full Method ($\Delta = \text{Metric}_{\text{variant}} - \text{Metric}_{\text{full}}$).
  - Factor Main Effects: On-minus-Off contrast averaged equally across the four matched settings of the other two factors.
  - Stress Degradation: Stressed minus Clean ($\Delta = \text{Metric}_{\text{stressed}} - \text{Metric}_{\text{clean}}$).
- **Subgroup Eligibility**: Minimum 10 distinct engines required in clean evaluation data. Missing groups contribute conservative bounds $[0, 0.90]$.

---

## 5. Acceptance and Audit Criteria

1. **Pre-Execution Lock**: Configuration and protocol committed prior to execution.
2. **Equivalence Verification**: Exact reproduction of baseline intervals at `atol=1e-10`.
3. **Artifact Integrity**: All 14 specified files generated under `experiments/phase08_exploratory_v1/`.
4. **Independent Audit**: Complete reference verification confirming thresholds, metrics, bootstrap draws, and perturbation hashes with zero failing reasons.
