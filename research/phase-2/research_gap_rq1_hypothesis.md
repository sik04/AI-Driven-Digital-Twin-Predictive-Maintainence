# Phase 2: Research Gap, Formal Research Questions (RQ1–RQ4), and Hypotheses Formulation

> **Document Status**: **Superceded by Structured Design Docs**
> **Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta
> **Date**: 2026-10-04
> **Notice**: The authoritative specifications have been reorganized into:
> - [`research/research_design/research_gap.md`](../research_design/research_gap.md)
> - [`research/research_questions.md`](../research_questions.md)
> - [`research/hypotheses/hypothesis_framework.yaml`](../hypotheses/hypothesis_framework.yaml)
> - [`research/hypotheses/hypothesis_framework.tex`](../hypotheses/hypothesis_framework.tex)
> - [`research/research_design/contribution_statement.md`](../research_design/contribution_statement.md)
> - [`research/research_design/experiment_map.md`](../research_design/experiment_map.md)

---

## 1. Context and Research Problem

### 1.1 Final Research Problem Statement

> **Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage. Our study will therefore investigate whether decision-aware, condition-adaptive conformal calibration can improve maintenance utility without sacrificing subgroup reliability or merely becoming more conservative.**

---

## 2. Final Research Questions and Hypotheses

- **RQ1**: *Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?*
- **RQ2**: *Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?*
- **RQ3**: *Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?*
- **RQ4**: *Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?*

*(Refer to `research/hypotheses/hypothesis_framework.yaml` for authoritative H0/H1 definitions).*
