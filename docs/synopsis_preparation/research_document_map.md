# IntelliTwin Research Document Map

**Document Version**: `2.0 (v4 Audit Alignment)`  
**Reviewed Repository Baseline**: `c163bb279e7427b8f1b6e75955af4969ff9370fd`  
**Committed Readiness Evidence**: `experiments/pretest_verification_v4/` (Audit Execution Commit: `550a7994d5746d3bcbfa28c26e7ed4f1a26a6153`, `git_dirty: false`, readiness: `PRETEST_READY`, held-out execution: `NOT_STARTED`, RQ outcomes: `PENDING`)  
**Purpose**: Provide an exhaustive cross-reference map connecting research questions, frozen protocols, implementation source code, experimental registries, and the newly prepared academic writing deliverables in `docs/synopsis_preparation/`.

> **Status Statement**: Base predictors and conformal calibrators are implemented and frozen. The committed v4 pre-test audit reports PASS and PRETEST_READY. Held-out execution has not started, and RQ1–RQ4 outcomes remain pending. Development validation and audit results do not establish confirmatory maintenance benefit, subgroup reliability, or robustness.

---

## 1. Master Cross-Reference Table

| Research Element | Question / Scope | Governing ADR | Authoritative Protocol | Source Code Implementation | Frozen Artifact Registry | New Deliverable Draft |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Research Direction & Problem** | Decision-aware condition-adaptive conformal calibration | ADR-002, ADR-006, ADR-007 | `research/research_questions.md`, `research/research_design/research_gap.md` | `src/intellitwin/uncertainty/calibration.py`, `src/intellitwin/decision/policies.py` | N/A (Theoretical Formulation) | `problem_and_objectives.md`, `introduction_draft.md` |
| **RQ1: Maintenance Utility & Coverage** | Does proposed calibration reduce maintenance cost by more than 0.20 SCU while preserving absolute coverage error $< 0.05$? | ADR-018 | `research/hypotheses/hypothesis_framework.yaml`, `statistical_inference_protocol.md` | `src/intellitwin/simulator/engine.py`, `src/intellitwin/decision/policies.py` | `experiments/pretest_verification_v4/protocol_freeze.json` | `hypotheses_explanation.md`, `evaluation_plan.md`, `latex/synopsis/sections/methodology.tex` |
| **RQ2: Conditional Subgroup Reliability** | Does proposed calibration improve worst-group error by more than 0.01 without MPIW/IS increase $> 1.0$ cycle? | ADR-018 | `research/hypotheses/hypothesis_framework.yaml`, `statistical_inference_protocol.md` | `src/intellitwin/evaluation/metrics.py`, `src/intellitwin/evaluation/bootstrap.py` | `experiments/pretest_verification_v4/protocol_freeze.json` | `hypotheses_explanation.md`, `evaluation_plan.md`, `latex/paper/sections/methodology.tex` |
| **RQ3: Decision-Value Attribution** | Are maintenance gains superior to 4 matched-conservatism controls across 3 families ($\Delta_{\text{cost}} > 0.20$ SCU)? | ADR-018, ADR-023 | `research/research_design/step09_control_selection.md` | `src/intellitwin/decision/controls.py`, `src/intellitwin/decision/policies.py` | `experiments/pretest_verification_v4/control_selection.json` | `hypotheses_explanation.md`, `evaluation_plan.md`, `latex/thesis/chapters/experimental_design.tex` |
| **RQ4: Robustness & Generalization** | Does benefit hold across 6 mandatory cells without material harm ($\Delta > -0.20$ SCU, $>-0.01$ error)? | ADR-018 | `research/hypotheses/hypothesis_framework.yaml`, `statistical_inference_protocol.md` | `src/intellitwin/evaluation/decisions.py` | `experiments/pretest_verification_v4/protocol_freeze.json` | `hypotheses_explanation.md`, `evaluation_plan.md`, `latex/thesis/chapters/results_discussion.tex` |
| **Dataset Splits & Isolation** | C-MAPSS FD001, FD002, FD004 engine-level leak-free 50/20/10/20 partitions | ADR-011, ADR-012, ADR-013 | `research/research_design/data_evaluation_protocol.md` | `src/intellitwin/data/schema.py`, `src/intellitwin/data/splits.py`, `src/intellitwin/data/preprocessing.py`, `src/intellitwin/data/windowing.py` | `data/splits/fd00{1,2,4}_engine_split_seed_2026.json` | `methodology_draft.md`, `latex/paper/sections/experimental_setup.tex` |
| **Base Point Predictors** | 30 frozen checkpoints across GBR (510 flat inputs) and LSTM (30x17 tensors) over 5 seeds | ADR-019, ADR-020 | `research/research_design/step07_base_predictor_specification.md`, `step07_base_predictor_freeze.md` | `src/intellitwin/models/gbr.py`, `src/intellitwin/models/lstm.py` | `experiments/base_models/model_registry.json` | `methodology_draft.md`, `latex/thesis/chapters/methodology.tex` |
| **Conformal Calibration** | 90 bundles across `global_hcp`, `regime_hcp`, and `decision_aware_hcp` (`gamma2_betam1`) | ADR-021, ADR-022 | `research/research_design/step08_calibration_specification.md` | `src/intellitwin/uncertainty/calibration.py`, `src/intellitwin/uncertainty/quantiles.py`, `src/intellitwin/uncertainty/scores.py` | `experiments/calibration/calibration_registry.json`, `selection_freeze.json` | `methodology_draft.md`, `latex/paper/sections/methodology.tex` |
| **Sequential Maintenance Simulator** | Discrete-event engine evaluating `simulate_engine_trajectory` and `simulate_fleet` under `primary_reference` | ADR-014, ADR-015, ADR-018 | `research/research_design/maintenance_simulator.md`, `maintenance_cost_scenarios.yaml` | `src/intellitwin/simulator/engine.py`, `src/intellitwin/simulator/costs.py` | `experiments/pretest_verification_v4/protocol_freeze.json` | `methodology_draft.md`, `system_description.md` |
| **Statistical Inference Engine** | 10000-draw stratified cluster bootstrap with PCG64 PRNG, Bonferroni FWER, and IUT rules | ADR-018, ADR-023 | `research/research_design/statistical_inference_protocol.md` | `src/intellitwin/evaluation/bootstrap.py`, `src/intellitwin/evaluation/decisions.py`, `src/intellitwin/evaluation/inference.py` | `experiments/pretest_verification_v4/protocol_freeze.json` | `evaluation_plan.md`, `latex/hypotheses/main.tex` |
| **Scholarly Literature Base** | Bounded review of 30 audited references across RUL, uncertainty calibration, and PdM | ADR-005 | `research/literature/literature_synthesis.md`, `source_verification.csv` | N/A | `research/literature/closest_work_matrix.csv`, `paper_inventory.csv` | `related_work_synthesis.md`, `reference_audit.csv`, `references_verified.bib` |

---

## 2. Directory Layout of `docs/synopsis_preparation/`

```text
docs/synopsis_preparation/
├── README.md                          # Master package guide, update procedure, and draft status
├── build_documents.py                 # Reproducible build script compiling all 4 LaTeX deliverables
├── build_manifest.json                # Cryptographic build manifest (hashes, compiler, status)
├── validate_documentation.py          # Strict fail-closed validator for documentation integrity
├── test_validate_documentation.py     # Isolated test suite for documentation validation rules
├── documentation_validation.json      # Structured validation report from executed checks
├── research_document_map.md           # This document: cross-reference map across all elements
├── source_manifest.csv                # Complete manifest of audited sources with exact locators
├── claims_evidence_matrix.csv         # Audit of project claims with strict status categorizations
├── update_register.csv                # Stable update IDs (UPD-01 to UPD-09, DEV-01 to DEV-04)
├── submission_requirements.md         # Explicit inventory of confirmed vs. pending venue details
├── author_contribution_record.md      # Neutral CRediT work plan preserving 3 named authors
├── completion_checklist.md            # Demarcation of completed docs vs. pending research
├── reference_audit.csv                # Detailed bibliometric audit of 30 scholarly references
├── related_work_matrix.csv            # Structured comparison of prior RUL UQ and maintenance works
├── related_work_synthesis.md          # 5-pillar literature synthesis and formal research gap
├── references_verified.bib            # Clean BibTeX database of verified records
├── introduction_draft.md              # Substantive draft: background, motivation, and scope
├── problem_and_objectives.md          # Substantive draft: problem formalization and RQ1–RQ4
├── hypotheses_explanation.md          # Substantive draft: detailed null/alt hypotheses and rules
├── methodology_draft.md               # Substantive draft: data, base models, calibration equations
├── evaluation_plan.md                 # Substantive draft: metrics, bootstrap, safeguards, IUT
├── system_description.md              # Substantive draft: digital twin prototype & simulation replay
├── limitations_draft.md               # Substantive draft: threats to validity and boundaries
├── reproducibility_draft.md           # Substantive draft: replication charter, seeds, and release
├── results_table_templates.md         # Formatted templates for Tables T1–T10 with PENDING placeholders
├── component_reporting_template.csv   # Complete 152-component reporting template from decisions.py
├── evaluation_matrix_template.csv     # Complete 186-cell evaluation matrix template from evidence_schema.py
├── figure_plan.md                     # Detailed specifications for Figures F1–F7
├── presentation_outline.md            # Complete 12-slide structured presentation outline
├── previews/                          # Compiled PDF drafts ready for visual inspection
│   ├── synopsis_draft.pdf             # Working draft: Department Research Synopsis
│   ├── ieee_paper_draft.pdf           # Working draft: IEEE Conference/Journal Manuscript
│   ├── thesis_draft.pdf               # Working draft: Academic Project Report / Thesis Draft
│   └── hypotheses_appendix.pdf        # Standalone Reference: Hypothesis Registry & Protocol
└── latex/                             # Fully modular LaTeX source tree
    ├── README.md                      # Compilation instructions and structure overview
    ├── shared/                        # Shared macros, notation, TikZ figures, and hypothesis fragments
    ├── synopsis/                      # IEEEtran synopsis entry point and modular sections
    ├── paper/                         # IEEEtran paper entry point and modular sections
    ├── thesis/                        # Standard report class 12pt A4 thesis entry point and chapters
    └── hypotheses/                    # Standalone hypothesis appendix entry point
```
