# Author Contribution Record and Research Work Plan

**Tracking Reference**: `UPD-08` (Final Authorship & Institutional Metadata)  
**Governance Standard**: International Committee of Medical Journal Editors (ICMJE) & CRediT Taxonomy  
**Date Established**: 2026-10-04  
**Last Updated**: 2026-10-14  
**Status**: Active Research Work Plan — Contributions In Progress (Percentages and Final Order Unassigned)

---

## 1. Research Team Members

The IntelliTwin research initiative is conducted jointly by the three named researchers recorded in the repository governance documents:

1. **Mayank Singh**
2. **Shiksha Pandey**
3. **Ruchi Gupta**

All three researchers participate in conceptualization, project governance, and critical manuscript review.

---

## 2. Active Research Work Plan Division

To ensure rigorous execution and balanced progress across software engineering and academic documentation, the current phase operates under a collaborative division of responsibilities:

- **Software Development & Experimental Verification Lead**: **Mayank Singh**
  - Architecture of base predictor training matrices and data pipelines (`src/intellitwin/data/`, `src/intellitwin/models/`).
  - Conformal calibration engine and threshold solver implementation (`src/intellitwin/uncertainty/`).
  - Maintenance simulation replay and cost accounting engine (`src/intellitwin/simulator/`).
  - Control-selection scripts and execution audits (`scripts/`, `experiments/`).
  - Re-execution of the pre-test verification audit on a clean working tree (`experiments/pretest_verification_v2/`).
  - Execution of official held-out test evaluations upon protocol unfreezing.

- **Theoretical Framework & Research Documentation Lead**: **Research Partner** (Shiksha Pandey / Ruchi Gupta)
  - Theoretical formulation of decision-aware, condition-adaptive conformal inference and score functions.
  - Literature synthesis and bibliometric verification across RUL, uncertainty quantification, and predictive maintenance.
  - Development of the formal hypothesis appendix, mathematical notation, and statistical inference explanations.
  - Authorship of substantive drafts for the Department Synopsis, IEEE Conference/Journal Paper, and Academic Thesis.
  - Establishing and maintaining documentation control registers (`source_manifest.csv`, `claims_evidence_matrix.csv`, `discrepancy_register.md`, `update_register.csv`).
  - Packaging editable LaTeX source trees and generating review draft PDFs.

> **Governance Boundary**: This document does not infer which individual named partner is operating this AI coding assistant session, nor does it unilaterally assign completed contribution percentages or finalize the published author sequence. All final authorship allocations, ordering, and institutional affiliations will be established through mutual written consensus among all three authors prior to formal submission.

---

## 3. CRediT (Contributor Roles Taxonomy) Mapping

In accordance with scholarly integrity, role contributions are recorded neutrally:

| CRediT Role | Role Definition | Assigned Work Plan Scope | Completion Status |
| :--- | :--- | :--- | :--- |
| **Conceptualization** | Formulation or evolution of overarching research goals, questions, and hypotheses. | Mayank Singh, Shiksha Pandey, Ruchi Gupta | In Progress (RQ1–RQ4 locked under ADR-018) |
| **Methodology** | Development of calibration mechanisms, evaluation contracts, and statistical protocols. | Mayank Singh, Shiksha Pandey, Ruchi Gupta | Frozen under ADR-018, ADR-021, ADR-023 |
| **Software** | Programming, code implementation, test suites, and simulation pipelines. | Mayank Singh (Lead Developer) | Implemented (Pre-test machinery frozen; held-out pending) |
| **Validation & Experiments**| Execution of experiments, verification audits, and empirical replication. | Mayank Singh (Execution) | Pre-test complete; held-out pending |
| **Formal Analysis** | Application of statistical, mathematical, or computational techniques to analyze data. | Mayank Singh, Shiksha Pandey, Ruchi Gupta | Protocol frozen (10,000-draw cluster bootstrap IUT) |
| **Data Curation** | Acquisition, preprocessing, split isolation, and manifest verification. | Mayank Singh | Completed for C-MAPSS FD001, FD002, FD004 |
| **Writing – Original Draft**| Preparation, creation, and presentation of the initial published work. | Research Partner (Theory/Writing) | Substantive drafts complete in `docs/synopsis_preparation/` |
| **Writing – Review & Editing**| Critical review, commentary, and revision by all authors prior to submission. | Mayank Singh, Shiksha Pandey, Ruchi Gupta | Pending review of generated drafts |

---

## 4. Policy on Authorship Order and Consensus Agreement

1. **No Unilateral Alteration**: Neither the software lead nor the writing partner may unilaterally declare primary, first, or corresponding authorship.
2. **Evidence-Based Allocation**: Final authorship ordering and institutional metadata will be determined upon completion of all experimental phases (Phase 11 of the master roadmap) based on actual documented contributions.
3. **Formal Resolution Trigger**: Recorded in `update_register.csv` under `UPD-08`.
