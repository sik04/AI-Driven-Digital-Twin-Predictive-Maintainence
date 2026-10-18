# IntelliTwin Research Writing & Documentation Package

**Document Version**: `2.0 (v4 Audit Alignment)`  
**Branch**: `fix/research-docs-v4-alignment`  
**Reviewed Repository Baseline**: `c163bb279e7427b8f1b6e75955af4969ff9370fd`  
**Committed Readiness Evidence**: `experiments/pretest_verification_v4/` (Audit Execution Commit: `550a7994d5746d3bcbfa28c26e7ed4f1a26a6153`, `git_dirty: false`, readiness: `PRETEST_READY`, held-out execution: `NOT_STARTED`, RQ outcomes: `PENDING`)  
**Authoring Team**: Mayank Singh (Lead Software Developer), Shiksha Pandey, Ruchi Gupta (Individual partner attributions pending consensus confirmation)  
**Package Scope**: Complete, evidence-linked working drafts for Research Synopsis, IEEE Conference/Journal Manuscript, Academic Thesis / Project Report Draft, and Standalone Hypothesis Appendix.

> **Status Statement**: Base predictors and conformal calibrators are implemented and frozen. The committed v4 pre-test audit reports PASS and PRETEST_READY. Held-out execution has not started, and RQ1–RQ4 outcomes remain pending. Development validation and audit results do not establish confirmatory maintenance benefit, subgroup reliability, or robustness.

---

## 1. Purpose and Governance Principle

This package contains the complete academic documentation package for the **IntelliTwin** research initiative. It provides substantive, mathematically rigorous, and evidence-linked drafts of the research background, literature review, methodology, system architecture, evaluation protocol, and hypothesis appendix while software development and experimental verification are conducted.

### Theoretical Foundation and Scope Boundaries
IntelliTwin uses an engine-weighted conformal construction motivated by hierarchical conformal prediction. Formal coverage results require the hierarchical sampling and exchangeability assumptions stated in the underlying theory. Equal engine weighting does not establish these assumptions for ordered, lifetime-stratified degradation trajectories. This study therefore evaluates marginal and subgroup coverage empirically. It does not claim guaranteed coverage for each engine, lifecycle stage, operating regime, complete trajectory, or adaptively selected maintenance time. Nominal 90% coverage is a target, not a guaranteed realized coverage proportion. Maintenance outcomes are evaluated separately under the frozen simulator.

### Critical Scientific Boundaries
1. **No Supersession of Frozen Protocols**: These drafts explain and contextualize the existing research decisions; **they do not alter or supersede frozen research protocols, hypotheses, mathematical margins, or split manifests** established in `research/hypotheses/hypothesis_framework.yaml`, `research/decision_log.md` (ADR-018, ADR-021, ADR-023), and `research/research_design/`.
2. **Clear Evidence Demarcation**: All sections describing empirical performance, comparative advantages, and statistical decisions on held-out test data are explicitly marked as **`PENDING_EXPERIMENT`**. No results, tables, or conclusions are fabricated.
3. **No Phantom Integrations**: The system is accurately documented as an offline, trace-driven prognostic decision-support research prototype evaluated on the NASA C-MAPSS benchmark. No physical engine integration or bidirectional hardware synchronization is asserted.

---

## 2. Directory Structure

```text
docs/synopsis_preparation/
├── README.md                          # This document
├── build_documents.py                 # Reproducible build script compiling all 4 LaTeX deliverables
├── build_manifest.json                # Cryptographic build manifest (hashes, compiler, status)
├── validate_documentation.py          # Strict fail-closed validator for documentation integrity
├── test_validate_documentation.py     # Isolated test suite for documentation validation rules
├── documentation_validation.json      # Structured validation report from executed checks
├── research_document_map.md           # Master map linking RQs, code, and documentation
├── source_manifest.csv                # Complete audit of inspected repository & external sources
├── claims_evidence_matrix.csv         # Comprehensive audit of claims with strict status tracking
├── update_register.csv                # Register of future update milestones (UPD-01 to UPD-09, DEV-01 to DEV-04)
├── submission_requirements.md         # Explicit inventory of confirmed vs. pending venue details
├── author_contribution_record.md      # Neutral CRediT work plan preserving 3 named authors
├── completion_checklist.md            # Demarcation of completed docs vs. pending research
├── reference_audit.csv                # Bibliometric verification of 30 scholarly sources
├── related_work_matrix.csv            # Prior work comparison on RUL, UQ, and maintenance
├── related_work_synthesis.md          # 5-pillar literature synthesis and research gap analysis
├── references_verified.bib            # Clean BibTeX database of verified records
├── introduction_draft.md              # Research background, industrial problem, and scope
├── problem_and_objectives.md          # Formal problem statement and research questions RQ1–RQ4
├── hypotheses_explanation.md          # Null/alternative hypotheses, margins, and decision logic
├── methodology_draft.md               # Data pipeline, base models, and calibration equations
├── evaluation_plan.md                 # 98.75% cluster bootstrap, controls, safeguards, and IUT
├── system_description.md              # Digital twin simulation prototype & replay architecture
├── limitations_draft.md               # Scientific boundaries, assumptions, and threats to validity
├── reproducibility_draft.md           # Replication instructions, seed policies, and releases
├── results_table_templates.md         # Empty templates for Tables T1–T10 with PENDING placeholders
├── component_reporting_template.csv   # Complete 152-component reporting template from decisions.py
├── evaluation_matrix_template.csv     # Complete 186-cell evaluation matrix template from evidence_schema.py
├── figure_plan.md                     # Specifications for Figures F1–F7
├── presentation_outline.md            # Structured 12-slide presentation outline
├── previews/                          # Pre-compiled PDF deliverables for visual inspection
│   ├── synopsis_draft.pdf             # Working draft: Department Research Synopsis
│   ├── ieee_paper_draft.pdf           # Working draft: IEEE Conference/Journal Manuscript
│   ├── thesis_draft.pdf               # Working draft: Academic Project Report / Thesis Draft
│   └── hypotheses_appendix.pdf        # Standalone Reference: Hypothesis Registry & Protocol
└── latex/                             # Fully modular LaTeX source tree
    ├── README.md                      # Compilation guide and package dependency notes
    ├── shared/                        # Shared macros, notation, figures, and hypothesis fragments
    ├── synopsis/                      # IEEEtran synopsis entry point and modular sections
    ├── paper/                         # IEEEtran paper entry point and modular sections
    ├── thesis/                        # Report class thesis entry point and modular chapters
    └── hypotheses/                    # Standalone hypothesis appendix entry point
```

---

## 3. Current Draft Status

| Deliverable | Format | Completion Status | Result Dependency | Target Role |
| :--- | :--- | :--- | :--- | :--- |
| **Department Synopsis** | LaTeX (`synopsis/`) & PDF | Complete Draft | Results Pending (`status_results.tex`) | Departmental research defense & proposal |
| **IEEE Paper** | LaTeX (`paper/`) & PDF | Complete Draft | Results Pending (`results.tex`, `discussion.tex`) | Conference / Journal submission draft |
| **Academic Thesis** | LaTeX (`thesis/`) & PDF | Complete Draft | Results Pending (`results_discussion.tex`) | Project report / Thesis draft baseline |
| **Hypothesis Appendix** | LaTeX (`hypotheses/`) & PDF | Complete Standalone | Frozen Protocol (ADR-018) | Authoritative reference & defense appendix |
| **Core Markdown Drafts**| Markdown (8 files) | Complete Drafts | Results Pending | Rapid reading, editing, and PR review |
| **Results Tables (T1–T10)**| Markdown templates | Formatted Templates | Frozen (T1/T2); Pending (T3–T10) | Insertion of verified experimental outputs |
| **Figure Plan (F1–F7)** | Markdown specification | Detailed Specs | F1/F2 implemented; F3–F7 pending | Reproduction plotting pipeline |
| **Presentation Outline**| Markdown (12 slides) | Complete Outline | Slides 10–12 results-dependent | Defense and seminar presentation deck |

---

## 4. How to Compile the LaTeX Documents

The recommended and reproducible method to compile all four documents into `docs/synopsis_preparation/previews/` and generate the cryptographic build manifest is:

```bash
python docs/synopsis_preparation/build_documents.py
```

### Manual Compilation with Tectonic
Tectonic compiles directly to PDF and automatically downloads required packages. When using `-o`, pass an output directory (not a filename):

```bash
# 1. Compile Research Synopsis
tectonic docs/synopsis_preparation/latex/synopsis/main.tex -o docs/synopsis_preparation/previews/
mv docs/synopsis_preparation/previews/main.pdf docs/synopsis_preparation/previews/synopsis_draft.pdf

# 2. Compile IEEE Paper Draft
tectonic docs/synopsis_preparation/latex/paper/main.tex -o docs/synopsis_preparation/previews/
mv docs/synopsis_preparation/previews/main.pdf docs/synopsis_preparation/previews/ieee_paper_draft.pdf

# 3. Compile Academic Thesis
tectonic docs/synopsis_preparation/latex/thesis/main.tex -o docs/synopsis_preparation/previews/
mv docs/synopsis_preparation/previews/main.pdf docs/synopsis_preparation/previews/thesis_draft.pdf

# 4. Compile Standalone Hypothesis Appendix
tectonic docs/synopsis_preparation/latex/hypotheses/main.tex -o docs/synopsis_preparation/previews/
mv docs/synopsis_preparation/previews/main.pdf docs/synopsis_preparation/previews/hypotheses_appendix.pdf
```

### Compilation with Latexmk
From each document directory (`docs/synopsis_preparation/latex/{synopsis,paper,thesis,hypotheses}/`):
```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

---

## 5. Updating after Development Milestones

When experimental verification and held-out evaluations are completed, the results must be incorporated systematically into this documentation package.

### Mandatory Update IDs
- `UPD-01`: Committed v4 pretest readiness verification (`experiments/pretest_verification_v4/`). Status: `COMMITTED`.
- `UPD-02`: Held-out predictive and interval results. Status: `PENDING`.
- `UPD-03`: Sequential maintenance outcomes. Status: `PENDING`.
- `UPD-04`: Confirmatory decision intervals and RQ classifications. Status: `PENDING`.
- `UPD-05`: Ablation and robustness sensitivity analyses. Status: `PENDING`.
- `UPD-06`: Demonstrator GUI and interface captures. Status: `PENDING`.
- `UPD-07`: Clean-environment reproduction and release logs. Status: `PENDING`.
- `UPD-08`: Final authorship and institutional consensus. Status: `PENDING`.
- `UPD-09`: Final target venue formatting and submission requirements. Status: `PENDING`.
- `DEV-01` to `DEV-04`: Developer-owned audit limitations and release handoff items. Status: `PENDING_DEVELOPER`.
