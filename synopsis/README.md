# IntelliTwin — Project Synopsis Workspace

This directory contains the authoritative B.Tech final-year project synopsis documentation, project audits, paper inventories, and reference materials for the **IntelliTwin** project.

---

## 1. Project & Academic Metadata

| Attribute | Details |
| :--- | :--- |
| **Project Title** | **IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance** |
| **Institution** | Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad |
| **Affiliating University** | Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow |
| **Department** | Department of Information Technology |
| **Academic Session** | 2026–2027 |
| **Project Guide / Mentor**| Dr. Ruchi Gupta |
| **Document Circular Ref** | `AKGEC/IT/CSIT/26-27/PROJ-m` (Dated: 25-08-2026) |

### Team Members (Official Order)
1. **Shiksha Pandey** — Roll No: `2300270110112`
2. **Mayank Singh** — Roll No: `2300270310115`

---

## 2. Official College Synopsis Guidelines Summary

Derived strictly from the official departmental notification [`PROJECT SYNOPSIS.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/PROJECT%20SYNOPSIS.pdf):

### Document Structure & Page Budget
- **Total Body Length**: **6 to 8 pages**, strictly excluding Title/Cover page and References.
- **Mandatory Sections (11 Sections)**:
  1. Title of the Project (Title, Student Names & Roll Numbers, Guide Name)
  2. Introduction (Project background, industrial domain, relevance)
  3. Problem Statement (Precise formulation of the engineering/scientific problem)
  4. Rationale (Need and quantitative justification for the proposed solution)
  5. Objective and Scope of the Project (Scope boundaries, target beneficiaries, bulleted concrete objectives)
  6. Methodology (Architectural flow, block diagrams, system components, algorithms, formal equations)
  7. Expected Outcomes (Deliverables, empirical benchmarks, reproducible artifacts)
  8. Tools and Technologies Requirements (Software, libraries, frameworks, hardware, datasets)
  9. Project Schedule (Gantt or PERT chart over the academic timeframe)
  10. Conclusion (Summary of work, distinguishing innovations, novelty)
  11. References (Strict IEEE format citations)

### Formatting Specifications
- **Page Size**: A4 Normal Paper
- **Margins**: Top: `1.0"`, Bottom: `1.0"`, Left: `1.5"`, Right: `1.0"`
- **Page Numbering**: Bottom center of page
- **Font Face**: Times New Roman (throughout)
- **Font Sizes**:
  - Document Title: `18 pt` (Bold), Centered
  - Main Headings (Level 1): `14 pt` (Bold)
  - Sub Headings (Level 2): `12 pt` (Bold)
  - Body Content: `12 pt` (Regular)
- **Line Spacing**: `1.5`
- **Text Alignment**: Justified; Paragraph Indentation: Nil (`0 pt`)
- **Authoring Platform**: All documentation must be prepared exclusively in Overleaf (LaTeX) using the shared departmental template (`https://www.overleaf.com/read/ccvkzmsccqfs#84c5d4`).

### Mandatory Viva / Review Questions (Students must prepare min 100 words each):
- **Question 1**: Explain in at least 100 words the reasons why the department should approve your project.
- **Question 2**: What are the strengths and limitations of your proposed work?
- **Question 3**: Explain in at least 100 words what the positive impact of the project on society, academics, college, and industry will be.

---

## 3. Master Directory Layout & Phase Deliverables Index

```text
synopsis/
├── README.md                                  # Master synopsis workspace documentation (this file)
├── SYNOPSIS_PROGRESS.md                       # Complete audit tracking log (Phases 0–10 + Final Phase)
├── PROJECT_IMPLEMENTATION_AUDIT.md            # Exhaustive classification of all repository features
├── RESEARCH_PAPER_INVENTORY.md                # Physical & cited research paper audit and recommendations
├── references/                                # Storage for reference notes and bibliography assets
├── Phase_1_Title_Page/                        # Phase 1: Project Title Page, Departmental Header & Metadata
│   ├── title_page.tex, .pdf, .docx, .html
│   ├── generate_title_page.py, akgec_logo.png, README.md
├── Phase_2_Introduction/                      # Phase 2: Introduction, Industrial Domain & Rationale Formulation
│   ├── introduction.tex, .pdf, .docx, .html
│   ├── generate_introduction.py, README.md
├── Phase_3_Problem_Definition/                # Phase 3: Problem Definition, Research Gap and Research Questions
│   ├── problem_definition.tex, .pdf, .docx, .html
│   ├── generate_problem_definition.py, README.md
├── Phase_4_Literature_Survey/                 # Phase 4: Literature Survey (Thematic Review & Comparison Table)
│   ├── literature_survey.tex, .pdf, .docx, .html
│   ├── generate_literature_survey.py, README.md
├── Phase_5_Objectives_and_Scope/              # Phase 5: Objectives and Scope of the Project
│   ├── objectives_and_scope.tex, .pdf, .docx, .html
│   ├── generate_objectives_and_scope.py, README.md
├── Phase_6_Proposed_Methodology/              # Phase 6: Proposed Methodology & Algorithmic Formulation
│   ├── proposed_methodology.tex, .pdf, .docx, .html
│   ├── generate_proposed_methodology.py, README.md
├── Phase_7_System_Architecture/               # Phase 7: System Architecture & Workflow Diagrams
│   ├── system_architecture.tex, .pdf, .docx, .html
│   ├── generate_system_architecture.py, README.md
├── Phase_8_Implementation_and_Results/        # Phase 8: Implementation Status and Results / Expected Results
│   ├── implementation_and_results.tex, .pdf, .docx, .html
│   ├── generate_implementation_and_results.py, README.md
├── Phase_9_Tools_and_Technologies/            # Phase 9: Tools, Technologies and System Requirements
│   ├── tools_and_technologies.tex, .pdf, .docx, .html
│   ├── generate_tools_and_technologies.py, README.md
├── Phase_10_Conclusion_and_Future_Work/       # Phase 10: Conclusion and Future Work & Defense Preparation
│   ├── conclusion_and_future_work.tex, .pdf, .docx, .html
│   ├── generate_conclusion_and_future_work.py, README.md
└── Final_Synopsis/                            # Master Unified B.Tech Project Synopsis Package (6–8 Body Pages)
    ├── main.tex                               # Master Overleaf-compatible LaTeX source
    ├── references.bib                         # 14 verified IEEE BibTeX references
    ├── akgec_logo.png                         # High-resolution institutional emblem
    ├── synopsis.pdf                           # Final 10-page vector PDF (1 Title + 8 Body + 1 References)
    ├── synopsis.docx                          # Final editable Microsoft Word document
    ├── synopsis.html                          # Print-optimized HTML source
    ├── synopsis.odt                           # OpenDocument Text document
    ├── intellitwin_synopsis_overleaf.zip      # 1-Click ready-to-upload Overleaf zip package
    ├── generate_final_synopsis.py             # 100% deterministic packaging automation script
    └── README.md                              # Master final audit, page budget & Overleaf guide
```

---

## 4. Master Final Synopsis Deliverables & Submission Package

The definitive final synopsis package for institutional submission is located in [`synopsis/Final_Synopsis/`](Final_Synopsis/):

| Deliverable | File Path | Format & Specifications |
| :--- | :--- | :--- |
| **Complete Final PDF** | [`synopsis/Final_Synopsis/synopsis.pdf`](Final_Synopsis/synopsis.pdf) | High-resolution vector PDF (10 pages: 1 Title Page + 8 Body Pages + 1 References Page, strictly conforming to the 6–8 page body mandate). |
| **Complete Final Word Doc** | [`synopsis/Final_Synopsis/synopsis.docx`](Final_Synopsis/synopsis.docx) | Fully editable Microsoft Word document conforming to AKGEC synopsis specifications (Times New Roman, 1.4 spacing, A4, Left 1.5"). |
| **Overleaf LaTeX Package** | [`synopsis/Final_Synopsis/intellitwin_synopsis_overleaf.zip`](Final_Synopsis/intellitwin_synopsis_overleaf.zip) | Self-contained, ready-to-upload ZIP archive (`main.tex`, `references.bib`, `akgec_logo.png`) for instant 1-click Overleaf compilation. |
| **Master LaTeX Source** | [`synopsis/Final_Synopsis/main.tex`](Final_Synopsis/main.tex) | Overleaf-compatible master LaTeX source with all 11 mandatory circular sections. |
| **Verified Bibliography** | [`synopsis/Final_Synopsis/references.bib`](Final_Synopsis/references.bib) | 14 peer-reviewed scholarly sources formatted in IEEE reference standards. |
| **Deterministic Generator** | [`synopsis/Final_Synopsis/generate_final_synopsis.py`](Final_Synopsis/generate_final_synopsis.py) | Python automation script ensuring 100% bit-for-bit deterministic reproduction. |

---

## 5. Overleaf Import Instructions (1-Click Setup)

1. Open Overleaf at [https://www.overleaf.com](https://www.overleaf.com).
2. Click **New Project** $\rightarrow$ **Upload Project**.
3. Select [`synopsis/Final_Synopsis/intellitwin_synopsis_overleaf.zip`](Final_Synopsis/intellitwin_synopsis_overleaf.zip).
4. Click **Recompile**. The document will compile cleanly under standard pdfLaTeX with zero errors.


