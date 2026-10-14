# IntelliTwin Research Writing & Documentation Package

**Document Version**: `1.0`  
**Branch**: `docs/synopsis-evidence-preparation`  
**Source Commit Reviewed**: `224c741f5f3da19821a708e0a6da417d4810e9da`  
**Authoring Team**: Mayank Singh, Shiksha Pandey, Ruchi Gupta  
**Package Scope**: Complete, evidence-linked working drafts for Research Synopsis, IEEE Conference/Journal Manuscript, Academic Thesis, and Standalone Hypothesis Appendix.

---

## 1. Purpose and Governance Principle

This package contains the complete academic documentation package for the **IntelliTwin** research initiative. It provides substantive, mathematically rigorous, and evidence-linked drafts of the research background, literature review, methodology, system architecture, evaluation protocol, and hypothesis appendix while software development and experimental verification are conducted by Mayank Singh.

### Critical Scientific Boundaries
1. **No Supersession of Frozen Protocols**: These drafts explain and contextualize the existing research decisions; **they do not alter or supersede frozen research protocols, hypotheses, mathematical margins, or split manifests** established in `research/hypotheses/hypothesis_framework.yaml`, `research/decision_log.md` (ADR-018, ADR-021, ADR-023), and `research/research_design/`.
2. **Clear Evidence Demarcation**: All sections describing empirical performance, comparative advantages, and statistical decisions on held-out test data are explicitly marked as **`PENDING_EXPERIMENT`**. No results, tables, or conclusions are fabricated.
3. **No Phantom Integrations**: The system is accurately documented as an offline simulation-replay framework evaluated on the NASA C-MAPSS benchmark. No physical engine integration or bidirectional hardware synchronization is asserted.

---

## 2. Directory Structure

```text
docs/synopsis_preparation/
├── README.md                          # This document
├── research_document_map.md           # Master map linking RQs, code, and documentation
├── source_manifest.csv                # Complete audit of inspected repository & external sources
├── claims_evidence_matrix.csv         # Comprehensive audit of claims with strict status tracking
├── update_register.csv                # Register of future update milestones (UPD-01 to UPD-09)
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
├── figure_plan.md                     # Specifications for Figures F1–F7
├── presentation_outline.md            # Structured 12-slide presentation outline
├── previews/                          # Pre-compiled PDF deliverables for visual inspection
│   ├── synopsis_draft.pdf             # Working draft: Department Research Synopsis
│   ├── ieee_paper_draft.pdf           # Working draft: IEEE Conference/Journal Manuscript
│   ├── thesis_draft.pdf               # Working draft: Academic Thesis Manuscript
│   └── hypotheses_appendix.pdf        # Standalone Reference: Hypothesis Registry & Protocol
└── latex/                             # Fully modular LaTeX source tree
    ├── README.md                      # Compilation guide and package dependency notes
    ├── shared/                        # Shared macros, notation, and hypothesis environments
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
| **Academic Thesis** | LaTeX (`thesis/`) & PDF | Complete Draft | Results Pending (`results_discussion.tex`) | Master's / Doctoral thesis baseline |
| **Hypothesis Appendix** | LaTeX (`hypotheses/`) & PDF | Complete Standalone | Frozen Protocol (ADR-018) | Authoritative reference & defense appendix |
| **Core Markdown Drafts**| Markdown (8 files) | Complete Drafts | Results Pending | Rapid reading, editing, and PR review |
| **Results Tables (T1–T10)**| Markdown templates | Formatted Templates | Frozen (T1/T2); Pending (T3–T10) | Insertion of verified experimental outputs |
| **Figure Plan (F1–F7)** | Markdown specification | Detailed Specs | Formatted specs; plots pending run logs | Reproduction plotting pipeline |
| **Presentation Outline**| Markdown (12 slides) | Complete Outline | Slides 10–12 results-dependent | Defense and seminar presentation deck |

---

## 4. How to Compile the LaTeX Documents

The LaTeX documents are organized modularly using ordinary `\input` commands and link directly to the verified shared bibliography `references_verified.bib`.

### Prerequisites
- Modern TeX engine (`tectonic`, `latexmk`, or `pdflatex` + `bibtex`).
- Standard packages: `amsmath`, `amssymb`, `booktabs`, `hyperref`, `cite`, `geometry`, `enumitem`.

### Compilation with Tectonic (Recommended Standalone Engine)
Tectonic compiles directly to PDF and automatically downloads required packages without manual configuration:

```bash
# 1. Compile Research Synopsis
tectonic docs/synopsis_preparation/latex/synopsis/main.tex -o docs/synopsis_preparation/previews/synopsis_draft.pdf

# 2. Compile IEEE Paper Draft
tectonic docs/synopsis_preparation/latex/paper/main.tex -o docs/synopsis_preparation/previews/ieee_paper_draft.pdf

# 3. Compile Academic Thesis
tectonic docs/synopsis_preparation/latex/thesis/main.tex -o docs/synopsis_preparation/previews/thesis_draft.pdf

# 4. Compile Standalone Hypothesis Appendix
tectonic docs/synopsis_preparation/latex/hypotheses/main.tex -o docs/synopsis_preparation/previews/hypotheses_appendix.pdf
```

### Compilation with standard `pdflatex` & `bibtex`
```bash
cd docs/synopsis_preparation/latex/synopsis
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Auxiliary files (`*.aux`, `*.log`, `*.bbl`, `*.out`) are excluded by local git configuration in `.git/info/exclude`.

---

## 5. Updating after development milestones

When experimental verification and held-out evaluations are completed by Mayank Singh, the results must be incorporated systematically into this documentation package.

### Mandatory 10-Step Update Workflow

For each development milestone:

1. **Fetch Merged Development State**:
   - Fetch the latest `origin/main` (or verified release tag) and record the exact commit SHA.
2. **Record Commit & Exact New Artifacts**:
   - Identify the incoming JSON, CSV, or checkpoint artifacts. Record their paths and cryptographic SHA-256 hashes.
3. **Inspect Contents & Required Verification Gates**:
   - Verify that the incoming run executed under a clean Git working tree (`git_dirty: false`).
   - Confirm that the execution platform, PRNG seed sequences, and package versions match frozen protocols.
4. **Map Change to Stable Update ID**:
   - Locate the applicable update ID in `update_register.csv`:
     - `UPD-01`: Corrected pretest verification (`pretest_verification_v2`).
     - `UPD-02`: Held-out predictive and interval results.
     - `UPD-03`: Sequential maintenance outcomes.
     - `UPD-04`: Confirmatory decision intervals and RQ classifications.
     - `UPD-05`: Ablation and robustness sensitivity analyses.
     - `UPD-06`: Demonstrator GUI and interface captures.
     - `UPD-07`: Clean-environment reproduction and release logs.
     - `UPD-08`: Final authorship and institutional consensus.
     - `UPD-09`: Final target venue formatting and submission requirements.
5. **Update Evidence Matrix First**:
   - Update `claims_evidence_matrix.csv`, transitioning affected claim statuses from `PENDING_EXPERIMENT` to `VERIFIED_FROM_SOURCE` (or `CONTRADICTED` if hypotheses failed).
6. **Update Affected Markdown & LaTeX Sections**:
   - Update the relevant markdown drafts and corresponding modular LaTeX files (`.tex`).
   - If an RQ is Unsupported or Inconclusive, report that outcome directly and transparently. Never alter hypotheses or thresholds to fit observed data.
7. **Regenerate Affected Tables & Figures Only from Verified Outputs**:
   - Populate table templates T3–T10 in `results_table_templates.md` and their LaTeX equivalents strictly from verified JSON/CSV summary outputs.
   - Generate figures using verified replay traces; never fabricate synthetic result curves.
8. **Update Abstract & Conclusion Last**:
   - Reflect the actual aggregate findings across all 6 mandatory cells.
   - Do not claim success based only on favorable subsets, models, or scenarios.
9. **Rebuild & Visually Inspect All Affected PDFs**:
   - Recompile all four LaTeX entry points.
   - Inspect tables, equation formatting, page breaks, and references for defects.
10. **Commit Documentation Update on Fresh Docs Branch & Open PR**:
    - Commit strictly within `docs/synopsis_preparation/`.
    - Open a pull request cross-referencing the milestone update ID and verification hashes.

### Required Developer Handoff Contract
Any future handoff transferring experimental evidence from software development to documentation must include:
- Git commit hash of the execution run;
- Absolute or repository-relative paths to generated output artifacts;
- Exact dataset partition (Validation vs. Held-out Test) and experiment identifier (Experiment A, B, C, or D);
- Formal verification report confirming clean Git status and zero missing records;
- Explicit metric definitions and physical units;
- Confirmatory vs. exploratory designation;
- Any observed numerical anomalies or unresolved limitations.

> **Warning**: The existence of a new file in the repository does not constitute authorization to promote its numbers into scientific claims. Documentation updates must verify the integrity gates before updating drafts.
