# Completion Checklist: Documentation Preparation vs. Research Execution

**Document Version**: `1.0`  
**Commit Audited**: `224c741f5f3da19821a708e0a6da417d4810e9da`  
**Governing Standard**: Distinguish documentation preparation completed from scientific research completed.  
**Allowed States**: `DONE` | `PARTIAL` | `BLOCKED` | `PENDING_DEVELOPMENT`

---

## 1. Documentation Preparation Tasks

| Task ID | Task Description | Target File / Artifact | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **DOC-01** | Dedicated docs branch creation from `origin/main` | `docs/synopsis-evidence-preparation` | `DONE` | Branch branched from commit `224c741` without operating in development checkout. |
| **DOC-02** | Documentation control registers authoring | `source_manifest.csv`, `claims_evidence_matrix.csv`, `update_register.csv`, `discrepancy_register.md` | `DONE` | Completely authored with precise locators, commit hashes, and allowed statuses. |
| **DOC-03** | Submission and authorship management records | `submission_requirements.md`, `author_contribution_record.md` | `DONE` | Preserves 3 authors; marks unknown institutional details explicitly. |
| **DOC-04** | Master document navigation and tracking map | `README.md`, `research_document_map.md` | `DONE` | Outlines complete package structure, source SHA, and compilation rules. |
| **DOC-05** | Scholarly literature audit and synthesis package | `reference_audit.csv`, `related_work_matrix.csv`, `related_work_synthesis.md`, `references_verified.bib` | `DONE` | Bounded audit of 30 scholarly sources across RUL, UQ, and PdM. |
| **DOC-06** | Core research markdown drafts | `introduction_draft.md`, `problem_and_objectives.md`, `hypotheses_explanation.md`, `methodology_draft.md`, `evaluation_plan.md`, `system_description.md`, `limitations_draft.md`, `reproducibility_draft.md` | `DONE` | Substantive prose covering locked formulas, splits, costs, and boundaries. |
| **DOC-07** | Results table templates & figure plan | `results_table_templates.md`, `figure_plan.md` | `DONE` | Empty tables T1–T10 with explicit `PENDING` entries; detailed figure specs. |
| **DOC-08** | Presentation outline | `presentation_outline.md` | `DONE` | Complete 12-slide structured outline covering problem, methods, and status. |
| **DOC-09** | Editable LaTeX synopsis source tree | `latex/synopsis/main.tex`, `latex/synopsis/sections/*.tex` | `DONE` | Modular IEEEtran conference layout with working draft banner. |
| **DOC-10** | Editable LaTeX IEEE paper source tree | `latex/paper/main.tex`, `latex/paper/sections/*.tex` | `DONE` | Modular IEEEtran manuscript with results-pending statements. |
| **DOC-11** | Editable LaTeX thesis source tree | `latex/thesis/main.tex`, `latex/thesis/chapters/*.tex` | `DONE` | Standard LaTeX report class, 12pt, A4, one-sided layout. |
| **DOC-12** | Editable LaTeX standalone hypothesis appendix | `latex/hypotheses/main.tex`, `latex/shared/hypotheses.tex`, `latex/shared/notation.tex` | `DONE` | Exact reproduction of ADR-018 hypotheses and statistical rules. |
| **DOC-13** | Standalone PDF compilation and visual review | `previews/synopsis_draft.pdf`, `previews/ieee_paper_draft.pdf`, `previews/thesis_draft.pdf`, `previews/hypotheses_appendix.pdf` | `DONE` | Compiled via Tectonic engine into `docs/synopsis_preparation/previews/`. |

---

## 2. Research & Development Tasks (Pending Scientific Evidence)

| Research Phase | Milestone Description | Target Verification Artifact | Status | Owner Role / Blocker |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | Governance and Packaging Verification | CI workflow, `pyproject.toml` | `DONE` | Mayank Singh / All Authors |
| **Phase 1** | Systematic Literature Review & Matrix | `research/literature/` | `DONE` | Research Partner / All Authors |
| **Phase 2** | Research Gap, RQ1–RQ4, Hypothesis Framework | `research/research_questions.md` | `DONE` | Frozen under ADR-018 |
| **Phase 3** | C-MAPSS Dataset Splits & Preprocessing Protocol | `data/splits/`, `data_evaluation_protocol.md` | `DONE` | Frozen under ADR-011, ADR-012, ADR-013 |
| **Phase 4** | Initial Manuscript Outline & Strategy | `paper/outline.md` | `DONE` | Superseded by current comprehensive drafts |
| **Phase 5** | 30 Base Predictor Matrix & Frozen Checkpoints | `experiments/base_models/model_registry.json` | `DONE` | Frozen under ADR-020 (30 checkpoints verified) |
| **Phase 6** | 90 Calibrator Bundles & Selection Freeze | `experiments/calibration/calibration_registry.json` | `DONE` | Frozen under ADR-021 (`gamma2_betam1` selected) |
| **Phase 6 Audit** | Step 8 Corrective Audit & Reproduction | `experiments/pretest_verification_v2/` | `PENDING_DEVELOPMENT` | Tracked under `UPD-01`; checkpoint reproduction `NOT RUN` in v1 |
| **Phase 7 (Pre-test)**| Confirmatory Protocol & Matched-Control Freeze | `experiments/confirmatory_development/protocol_freeze.json` | `DONE` | Frozen under ADR-023 (smoke test executed) |
| **Phase 7 (Test)** | Official Held-out Test Data Preparation & Evaluation | `experiments/confirmatory_evaluation/` | `PENDING_DEVELOPMENT` | Strictly not started; prevents data leakage |
| **Phase 7 (RQs)** | Confirmatory Statistical Decision Intervals (RQ1–RQ4) | Held-out bootstrap results | `PENDING_DEVELOPMENT` | Tracked under `UPD-02`, `UPD-03`, `UPD-04` |
| **Phase 8** | Ablation & Robustness Analyses (Secondary Scenarios) | Secondary coverage & cost logs | `PENDING_DEVELOPMENT` | Tracked under `UPD-05` |
| **Phase 9** | Demonstrator GUI & Interactive Simulation Realization | Demonstrator code & telemetry replay UI | `PENDING_DEVELOPMENT` | Tracked under `UPD-06` |
| **Phase 10** | Clean-Environment Verification & Release Audit | Independent reproduction log | `PENDING_DEVELOPMENT` | Tracked under `UPD-07` |
| **Phase 11** | Final Manuscript Polishing & Publication Submission | Final approved manuscript & thesis | `PENDING_DEVELOPMENT` | Tracked under `UPD-08`, `UPD-09` |
| **Phase 12** | Open-Science Archival & Public Artifact Release | Zenodo DOI & public GitHub release | `PENDING_DEVELOPMENT` | Awaits manuscript acceptance |

---

## 3. Clear Demarcation Statement

The documentation preparation tasks listed in Section 1 are **COMPLETED**. All required background, methodology, hypothesis explanation, literature synthesis, LaTeX structures, table templates, figure plans, and preview PDFs have been established in `docs/synopsis_preparation/`.

However, the scientific research tasks listed in Section 2 are **IN PROGRESS / PENDING DEVELOPMENT**. In accordance with scientific ethics, **no confirmatory claims of maintenance improvement, coverage superiority, or decision attribution are made** until official held-out test evaluations are executed by Mayank Singh and audited by the research team.
