# Data & Evaluation Protocol — Step 5

This document serves as the authoritative specification for data preprocessing, label construction, feature engineering, sequence windowing, and experimental evaluation protocols for the IntelliTwin research platform.

---

## 1. RUL Target Construction

### 1.1 Mathematical Definition of `rul_true`

For a full run-to-failure engine trajectory $i$, let $T_{\text{failure}}(i)$ denote the final observed operational cycle of that engine, and let $t$ denote the current cycle number ($1 \le t \le T_{\text{failure}}(i)$).

The uncapped ground-truth Remaining Useful Life (RUL) for engine $i$ at cycle $t$ is defined as:

$$\text{RUL}_{\text{true}}(i, t) = T_{\text{failure}}(i) - t$$

- **Meaning**: `rul_true` represents the exact, uncapped actual number of remaining operational cycles until functional failure.
- **Role in Research Pipeline**: `rul_true` is retained exclusively for offline ground-truth scientific evaluation, post-hoc error metrics, degradation-stage labeling (to be specified in later Step 5 protocol sections), wasted RUL calculations, and post-hoc maintenance simulator consequence analysis.

### 1.2 Mathematical Definition of `rul_target`

The primary target used for supervised training of all RUL prediction models is defined as:

$$\text{RUL}_{\text{target}}(i, t) = \min\left(\text{RUL}_{\text{true}}(i, t), 125\right)$$

- **Fixed Cap Value**: The maximum target value is strictly locked at $125$ cycles.
- **Piecewise-Linear Target**: The training target is constant ($125$) during early operational cycles when $RUL_{\text{true}}(i, t) \ge 125$, and decreases linearly with a slope of $-1$ as the engine approaches failure once $RUL_{\text{true}}(i, t) < 125$.

### 1.3 Purpose of the Capped Training Target

1. **Physical Degradation Saturation**: Turbofan engines exhibit negligible component wear during early operational cycles. Prior to degradation onset, attempting to regress exact initial engine lifetimes (which vary across units) introduces noise into function approximators without physical basis.
2. **Standard Benchmark Protocol**: A piecewise-linear cap of 125 cycles reflects the standard benchmark convention in turbofan prognostic literature (e.g., Zheng et al., 2017; Diao et al., 2026), standardizing point prediction task formulation.
3. **No-Tuning Rule**: The cap value of 125 cycles is strictly fixed by research decision. It must **NOT** be tuned, optimized, or altered based on validation error, test set performance, or hyperparameter sweeps.

### 1.4 Distinction Between Training Target and Ground-Truth Evaluation

`rul_true` and `rul_target` represent distinct scientific quantities and must **NEVER** be treated as interchangeable:

- **Supervised Training**: All base RUL model architectures (e.g., linear baselines, temporal neural networks) are trained strictly using `rul_target` as the scalar regression target.
- **Scientific Evaluation & Maintenance Decision Analysis**: All final scientific evaluation metrics (e.g., MAE, RMSE, prediction interval coverage, conditional miscalibration auditing) and downstream maintenance simulator consequence metrics (e.g., wasted useful life $RUL_{\text{wasted}}$, late/failure intervention rates, total operational cost per engine) must use uncapped `rul_true` as the ground-truth benchmark.

### 1.5 Model Output Interpretation & Maintenance Consequence Analysis

- **Early-Life Saturation**: Because the base RUL predictor is trained against $\min(\text{RUL}_{\text{true}}, 125)$, point predictions and prediction intervals during early engine life are expected to saturate near the cap value of 125 cycles.
- **Reporting Rule**: The capped prediction target `rul_target` must **NEVER** be reported or interpreted as if it were the engine's actual uncapped remaining operational lifetime.
- **Wasted Useful Life Rule**: Wasted useful life resulting from premature maintenance interventions must be calculated strictly from uncapped `rul_true` ($\text{RUL}_{\text{wasted}} = \text{RUL}_{\text{true}}(i, t_{\text{replacement}})$), **NEVER** from `rul_target`.

### 1.6 Inference-Time Input Leakage Restrictions

Consistent with the Step 4 leakage governance rules (ADR-011):

1. Neither `rul_true`, `rul_target`, engine failure cycle $T_{\text{failure}}(i)$, nor any future-cycle information may be used as predictive model inputs at inference time.
2. Failure cycle $T_{\text{failure}}(i)$ may be used strictly to construct supervised labels for offline training on full run-to-failure trajectories.
3. `rul_true` is strictly prohibited from being used as:
   - A deployed model feature input
   - An operating-condition feature or regime identification input
   - A conformal calibration condition variable
   - A maintenance policy decision input
   - Information assumed to be available at prediction time

### 1.7 Summary Comparison of Target Quantities

| Quantity | Definition | Primary Purpose | Inference-Time Model Input? |
|---|---|---|---|
| `rul_true` | $T_{\text{failure}}(i) - t$ | Offline evaluation / post-hoc ground truth / maintenance consequences | **NO** (Strict Leakage Violation) |
| `rul_target` | $\min(\text{RUL}_{\text{true}}, 125)$ | Supervised model training target | **NO** (Strict Leakage Violation) |

---

## 2. Unresolved Protocol Specifications (Pending Later Step 5 Parts)

The following data preprocessing, feature engineering, and evaluation specifications remain explicitly unresolved and will be defined in subsequent Step 5 sub-steps:

- Sensor selection and filtering rules (Step 5.2)
- Operating-setting input policy and scaling strategy (Step 5.2)
- Feature normalization and preconditioning strategy (Step 5.3)
- Sequence length, window stride, and padding policy (Step 5.4)
- Handling of short engine trajectories (Step 5.4)
- Degradation-stage boundary construction ($RUL_{\text{true}}$ thresholds for early/mid/late failure stages) (Step 5.5)
- Subgroup eligibility thresholds for worst-group analysis (Step 5.5)
- Dataset-specific split protocols for FD001 and FD004 (Step 5.6)
- Official NASA test trajectory evaluation protocol (Step 5.6)
- Nominal conformal coverage levels ($\alpha$ levels) (Step 5.7)
- Model architecture specifications (Step 5.8)

No values or decisions for the above topics are locked by Step 5.1.
