# Completion Checklist: Documentation Preparation vs. Research Execution

**Document Version**: `2.0 (v4 Audit Alignment)`  
**Branch**: `fix/research-docs-v4-alignment`  
**Reviewed Repository Baseline**: `c163bb279e7427b8f1b6e75955af4969ff9370fd`  
**Committed Readiness Evidence**: `experiments/pretest_verification_v4/` (Audit Execution Commit: `550a7994d5746d3bcbfa28c26e7ed4f1a26a6153`, `git_dirty: false`, readiness: `PRETEST_READY`, held-out execution: `NOT_STARTED`, RQ outcomes: `PENDING`)  
**Governing Standard**: Distinguish documentation preparation completed from scientific research completed.  
**Allowed States**: `DONE` | `PARTIAL` | `BLOCKED` | `PENDING_DEVELOPMENT`

> **Status Statement**: Base predictors and conformal calibrators are implemented and frozen. The committed v4 pre-test audit reports PASS and PRETEST_READY. Held-out execution has not started, and RQ1–RQ4 outcomes remain pending. Development validation and audit results do not establish confirmatory maintenance benefit, subgroup reliability, or robustness.

---

## 1. Documentation Preparation Tasks

| Task ID | Task Description | Target File / Artifact | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **DOC-01** | Dedicated docs branch creation from `origin/main` | `fix/research-docs-v4-alignment` | `DONE` | Branched from baseline `c163bb279e7427b8f1b6e75955af4969ff9370fd` without modifying development checkout. |
| **DOC-02** | Documentation control registers authoring | `source_manifest.csv`, `claims_evidence_matrix.csv`, `update_register.csv`, `discrepancy_register.md` | `DONE` | Authored with precise locators, commit hashes, allowed statuses, and developer handoff items DEV-01 to DEV-04. |
| **DOC-03** | Submission and authorship management records | `submission_requirements.md`, `author_contribution_record.md` | `DONE` | Preserves 3 authors; Mayank lead developer; individual partner attributions pending consensus. |
| **DOC-04** | Master document navigation and tracking map | `README.md`, `research_document_map.md` | `DONE` | Outlines complete package structure, source SHA, and compilation rules. |
| **DOC-05** | Scholarly literature audit and synthesis package | `reference_audit.csv`, `related_work_matrix.csv`, `related_work_synthesis.md`, `references_verified.bib` | `DONE` | Bounded audit of 30 scholarly sources across RUL, UQ, and PdM. |
| **DOC-06** | Core research markdown drafts | `introduction_draft.md`, `problem_and_objectives.md`, `hypotheses_explanation.md`, `methodology_draft.md`, `evaluation_plan.md`, `system_description.md`, `limitations_draft.md`, `reproducibility_draft.md` | `DONE` | Substantive prose covering locked formulas, splits, costs, AdamW parameters, negative beta math, and boundaries. |
| **DOC-07** | Results table templates & reporting manifests | `results_table_templates.md`, `component_reporting_template.csv`, `evaluation_matrix_template.csv`, `figure_plan.md` | `DONE` | 152 components, 186 evaluation keys, empty templates T1–T10 with PENDING placeholders; F1/F2 implemented TikZ specs. |
| **DOC-08** | Presentation outline | `presentation_outline.md` | `DONE` | Complete 12-slide structured outline covering problem, methods, and status. |
| **DOC-09** | Editable LaTeX synopsis source tree | `latex/synopsis/main.tex`, `latex/synopsis/sections/*.tex` | `DONE` | Modular IEEEtran conference layout with working draft banner. |
| **DOC-10** | Editable LaTeX IEEE paper source tree | `latex/paper/main.tex`, `latex/paper/sections/*.tex` | `DONE` | Modular IEEEtran manuscript with results-pending statements and native TikZ diagrams. |
| **DOC-11** | Editable LaTeX thesis source tree | `latex/thesis/main.tex`, `latex/thesis/chapters/*.tex` | `DONE` | Standard LaTeX report class, 12pt, A4, one-sided layout with native TikZ diagrams. |
| **DOC-12** | Editable LaTeX standalone hypothesis appendix | `latex/hypotheses/main.tex`, `latex/shared/hypotheses.tex`, `latex/shared/notation.tex` | `DONE` | Exact reproduction of ADR-018 hypotheses, strict inequalities, and statistical rules. |
| **DOC-13** | Standalone PDF compilation and visual review | `previews/synopsis_draft.pdf`, `previews/ieee_paper_draft.pdf`, `previews/thesis_draft.pdf`, `previews/hypotheses_appendix.pdf` | `DONE` | Compiled via Tectonic into `docs/synopsis_preparation/previews/` with cryptographic build manifest. |

---

## 2. Research & Development Tasks (Pending Scientific Evidence)

| Research Phase | Milestone Description | Target Verification Artifact | Status | Owner Role / Blocker |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | Governance and Packaging Verification | CI workflow, `pyproject.toml` | `DONE` | Mayank Singh / All Authors |
| **Phase 1** | Systematic Literature Review & Matrix | `research/literature/` | `DONE` | Research Partner / All Authors |
| **Phase 2** | Research Gap, RQ1–RQ4, Hypothesis Framework | `research/research_questions.md` | `DONE` | Frozen under ADR-018 |
| **Phase 3** | C-MAPSS Dataset Splits & Preprocessing Protocol | `data/splits/`, `data_evaluation_protocol.md` | `DONE` | Frozen under ADR-011, ADR-012, ADR-013 |
| **Phase 4** | Initial Manuscript Outline & Strategy | `paper/outline.md` | `DONE` | Superseded by current comprehensive drafts |
| **Phase 5** | 30 Base Predictor Matrix & Frozen Checkpoints | `experiments/base_models/model_registry.json` | `DONE` | Frozen under ADR-020 (30 checkpoints verified across 5 seeds) |
| **Phase 6** | 90 Calibrator Bundles & Selection Freeze | `experiments/calibration/calibration_registry.json` | `DONE` | Frozen under ADR-021 (`gamma2_betam1` selected strictly on validation split) |
| **Phase 6/7 Audit** | Pre-test Readiness Audit & Regression Report | `experiments/pretest_verification_v4/pretest_audit.json` | `DONE` | Committed v4 pretest audit reports PASS and PRETEST_READY. 652 tracked protected artifacts verified vs 72 historical/unavailable entries; reused historical evidence: 60 records max diff 0.0; validation-smoke counts: 930 configs, 19,590 outcomes, 186 cells, 152 components, 10,000 bootstrap draws. |
| **Phase 7 (Pre-test)**| Confirmatory Protocol & Matched-Control Freeze | `experiments/pretest_verification_v4/protocol_freeze.json` | `DONE` | Frozen under ADR-023; controls reconstructed and verified (`control_selection.json`) |
| **Phase 7 (Test)** | Official Held-out Test Data Preparation & Evaluation | `experiments/confirmatory_evaluation/` | `PENDING_DEVELOPMENT` | Strictly not started; prevents data leakage |
| **Phase 7 (RQs)** | Confirmatory Statistical Decision Intervals (RQ1–RQ4) | Held-out bootstrap results | `PENDING_DEVELOPMENT` | Tracked under `UPD-02`, `UPD-03`, `UPD-04` |
| **Phase 8** | Descriptive Sensitivity Analyses (Secondary Scenarios) | Secondary coverage & cost logs | `PENDING_DEVELOPMENT` | Tracked under `UPD-05` (descriptive sensitivities, not ablations) |
| **Phase 9** | Demonstrator GUI & Interactive Simulation Realization | Demonstrator code & telemetry replay UI | `PENDING_DEVELOPMENT` | Tracked under `UPD-06` |
| **Phase 10** | Clean-Environment Verification & Release Audit | Independent reproduction log | `PENDING_DEVELOPMENT` | Tracked under `UPD-07` and `DEV-04` |
| **Phase 11** | Final Manuscript Polishing & Publication Submission | Final approved manuscript & thesis | `PENDING_DEVELOPMENT` | Tracked under `UPD-08`, `UPD-09` |
| **Phase 12** | Open-Science Archival & Public Artifact Release | Zenodo DOI & public GitHub release | `PENDING_DEVELOPMENT` | Awaits project completion; journal acceptance is not a prerequisite for release |

---

## 3. Clear Demarcation Statement

The documentation preparation tasks listed in Section 1 are **COMPLETED**. All required background, methodology, hypothesis explanation, literature synthesis, LaTeX structures, table templates, figure plans, and preview PDFs have been established in `docs/synopsis_preparation/`.

However, the scientific research tasks listed in Section 2 are **IN PROGRESS / PENDING DEVELOPMENT**. In accordance with scientific ethics, **no confirmatory claims of maintenance improvement, coverage superiority, or decision attribution are made** until official held-out test evaluations are executed by Mayank Singh and audited by the research team.
