# Experiment A — Proposed Method Evaluation Protocol Design

> **Document Status**: **Locked Protocol Design**  
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta  
> **Date**: 2026-10-04  
> **Scientific Role**: Primary Proposed-Method Evaluation  

> **Role Notice**: Experiment A serves as the **primary proposed-method evaluation** for RQ1, comparing decision-aware, condition-adaptive conformal calibration against global conformal calibration and standard condition-aware calibration under sequential maintenance constraints. The conditional-reliability audit serves as a supporting diagnostic/replication component.

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

---

## 3. Dataset Scope & Base Predictor Families

### 3.1 Datasets
- **Primary Dataset**: C-MAPSS FD002 (multi-regime operational shifts).
- **Control Dataset**: C-MAPSS FD001 (single-condition control baseline).

### 3.2 Base Model Families
- **Gradient Boosting Regressor (GBR)**: Non-recurrent tree-based ensemble architecture.
- **Long Short-Term Memory Network (LSTM)**: Recurrent temporal deep learning architecture.

---

## 4. Supporting Diagnostic Component

The conditional-reliability audit (evaluating marginal vs. subgroup coverage across operating regimes and degradation stages) remains an integrated supporting diagnostic component within Experiment A to verify that maintenance utility gains do not sacrifice subgroup coverage reliability.

---

## 5. Unfinalized Parameters (Deferred to Phase 3–4)

The following design choices are explicitly deferred and will not be implemented or fixed in Phase 2:
- Exact algorithm implementation and nonconformity loss functions
- Exact sequential maintenance cost ratios ($C_{\text{failure}} / C_{\text{preventive}}$)
- Exact numerical decision thresholds or practical effect limits
