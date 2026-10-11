# Experiment A — Proposed Method Evaluation Protocol Design

> **Document Status**: **Frozen Protocol Design (ADR-018)**
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
> **Protocol Version**: `step06-v2`
> **Scientific Role**: Primary Proposed-Method Evaluation

> **Role Notice**: Experiment A serves as the **primary proposed-method evaluation** for RQ1, comparing decision-aware, condition-adaptive conformal calibration against global conformal calibration and standard condition-aware calibration under sequential maintenance constraints. The conditional-reliability audit serves as a supporting diagnostic component.

---

## 1. Primary Research Question Alignment

Experiment A directly addresses **RQ1**:

> **Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?**

---

## 2. High-Level Comparison Framework

Experiment A evaluates the proposed method against two benchmark calibration approaches under identical predictors and data protocols:

1. **Proposed Method**: Decision-aware, condition-adaptive conformal RUL calibration.
2. **Global Conformal Calibration Baseline**: Standard split conformal prediction applied uniformly across all operating conditions.
3. **Standard Condition-Aware Calibration Baseline**: Standard condition/regime-aware conformal prediction without explicit sequential maintenance utility optimization.

Both base model families (GBR and LSTM) must be evaluated separately; both must satisfy all criteria for full RQ1 support.

---

## 3. Dataset Scope & Base Predictor Families

### 3.1 Datasets
- **Primary Dataset**: C-MAPSS FD002 (multi-regime operational shifts; 260 engines total, 52 held-out test engines).
- **Secondary Sensitivity**: 80% and 95% nominal coverage analyses on FD002.

### 3.2 Base Model Families
- **Gradient Boosting Regressor (GBR)**: Non-recurrent tree-based ensemble architecture.
- **Long Short-Term Memory Network (LSTM)**: Recurrent temporal deep learning architecture.
- **Seeds**: Five fixed model training seeds: `[2026, 2027, 2028, 2029, 2030]`. Primary estimand averages over these 5 runs.

---

## 4. Frozen Evaluation Parameters (ADR-018)

- **Cost Scenario**: `primary_reference` ($C_{\text{PM}} = 1.0, C_{\text{FAIL}} = 5.0, C_{\text{WASTE}} = 0.20$ SCU).
- **Nominal Coverage**: 90% ($\alpha = 0.10$).
- **Primary Metric Contrast**: $\Delta_{\text{cost}} = \overline{\text{Cost}}_B - \overline{\text{Cost}}_P$ (SCU per engine).
- **Frozen Practical-Effect Margin**: $\Delta_{\text{cost}} > 0.20$ SCU per engine.
- **Reliability Constraints**:
  - Marginal absolute coverage error ceiling $E_{\text{marginal}} < 0.05$.
  - Worst-regime coverage error ceiling $E_{\text{regime}} < 0.05$.
  - Worst-stage coverage error ceiling $E_{\text{stage}} < 0.05$.
  - Finite-benchmark failure safeguard: Observed fleet failure rate increase $\le 0.0$ against both baselines.
- **Statistical Framework**: 98.75% cluster-bootstrap percentile decision intervals (10,000 resamples, Bonferroni $\alpha = 0.05 / 4 = 0.0125$).
- **Decision Rule**: Both GBR and LSTM must achieve lower CI of $\Delta_{\text{cost}} > 0.20$ SCU against both baselines, upper CI of all coverage errors $< 0.05$, and pass the failure safeguard.

---

## 5. Methodological Deferrals (Step 7+)

The following implementation items belong to later development steps:
- Step 7 base model neural network and tree architectures, training pipelines, and hyperparameters.
- Conformal calibration algorithms and nonconformity score functions.
- Deployable maintenance decision policy optimization.
