# Academic and Institutional Submission Requirements

**Document Version**: `1.0-draft`  
**Tracking Reference**: `UPD-09` (Venue & Requirements Specification)  
**Last Updated**: 2026-10-14  
**Status**: Provisional Working Register — All Unconfirmed Details Explicitly Marked

---

## 1. Executive Summary

This register tracks all academic, institutional, and venue-specific submission requirements for the IntelliTwin research outputs (Department Synopsis, IEEE Conference/Journal Manuscript, and Academic Thesis).

In strict adherence to research integrity standards, **no institutional details, supervisor names, approval certificates, target journal deadlines, or length limits have been fabricated**. All items awaiting administrative confirmation are explicitly marked as `PENDING_INSTITUTIONAL_SPECIFICATION` or `PENDING_VENUE_SELECTION`.

---

## 2. Parameter Status Overview

| Requirement Category | Specified Parameter | Current Status | Default / Provisional Setting in Drafts | Next Action / Acceptance Gate |
| :--- | :--- | :--- | :--- | :--- |
| **Department Synopsis** | Template & Layout Style | `PENDING_INSTITUTIONAL_SPECIFICATION` | IEEEtran conference two-column style (`latex/synopsis/main.tex`) | Obtain departmental guidelines from department academic coordinator |
| **Department Synopsis** | Page / Word Limit | `PENDING_INSTITUTIONAL_SPECIFICATION` | 6–8 pages provisional draft | Confirm whether 4-page, 8-page, or extended synopsis is required |
| **Department Synopsis** | Required Frontmatter | `PENDING_INSTITUTIONAL_SPECIFICATION` | Working draft banner; neutral title block | Confirm institutional cover page format |
| **IEEE Manuscript** | Target Publication Venue | `PENDING_VENUE_SELECTION` | Standard IEEE Conference (`IEEEtran.cls`, `conference` mode) | Select target conference (e.g., IEEE PHM, IEEE CASE, IEEE TII) |
| **IEEE Manuscript** | Final Page Limit | `PENDING_VENUE_SELECTION` | 6–8 pages standard double-column | Verify Call for Papers (CFP) page constraints and overlength fees |
| **IEEE Manuscript** | Submission Deadline | `PENDING_VENUE_SELECTION` | Not assigned | Pinned upon venue selection |
| **Academic Thesis** | University / Institution | `PENDING_INSTITUTIONAL_SPECIFICATION` | Generic title page placeholder with explicit draft warning | Record registered university and department names |
| **Academic Thesis** | Thesis Template / Layout | `PENDING_INSTITUTIONAL_SPECIFICATION` | Standard LaTeX `report` class, 12pt, A4, one-sided | Obtain official university thesis LaTeX package or styling guide |
| **Academic Thesis** | Supervisor & Committee | `PENDING_INSTITUTIONAL_SPECIFICATION` | Strictly omitted; no names or titles fabricated | Receive official supervisory allocation records |
| **Academic Thesis** | Declarations & Certificates | `PENDING_INSTITUTIONAL_SPECIFICATION` | Reserved chapter headings omitted; no signed declarations created | Insert official institutionally mandated wording upon defense clearance |
| **Academic Thesis** | Submission Deadline | `PENDING_INSTITUTIONAL_SPECIFICATION` | Not assigned | Obtain university academic calendar milestones |

---

## 3. Detailed Institutional Requirements (Pending Confirmation)

### 3.1 Department Synopsis
- **Department**: `[PENDING_INSTITUTIONAL_SPECIFICATION]`
- **Institution / University**: `[PENDING_INSTITUTIONAL_SPECIFICATION]`
- **Degree / Programme**: `[PENDING_INSTITUTIONAL_SPECIFICATION]` (e.g., M.Tech / B.Tech / Ph.D. Dissertation Synopsis)
- **Formatting Constraints**:
  - Font: Times New Roman or Computer Modern Roman (provisional LaTeX default)
  - Margins: 1 inch (25.4 mm) standard
  - Spacing: Single-spaced (IEEE style)
  - Sectioning: Introduction, Problem Formulation, Objectives, Related Work, Methodology, Proposed Architecture, Experimental Evaluation Plan, Preliminary Status, Limitations, Timeline
- **Draft Banner Notice**: All synopsis drafts must prominently state:  
  `"Research synopsis — working draft; final results pending."`

### 3.2 Target IEEE Publication Venue
- **Candidate Venues Under Discussion**:
  1. *IEEE International Conference on Prognostics and Health Management (IEEE PHM)*
  2. *IEEE Transactions on Industrial Informatics (IEEE TII)* — post-conference extended target
  3. *IEEE Transactions on Reliability (IEEE TRel)*
  4. *IEEE International Conference on Automation Science and Engineering (CASE)*
- **Formatting Mode**: `\documentclass[conference]{IEEEtran}` with `\bibliographystyle{IEEEtran}`
- **Authorship Representation**: Mayank Singh, Shiksha Pandey, Ruchi Gupta (provisional alphabetical/equal layout pending author agreement).
- **Results Notice**: Abstract and Results sections must explicitly declare that held-out confirmatory evaluation is pending.

### 3.3 Academic Master's / Doctoral Thesis
- **Document Class**: Standard LaTeX `report` class, 12pt, A4 paper, one-sided (`\documentclass[12pt,a4paper,oneside]{report}`).
- **Citation Format**: IEEE-style bracketed numerical citations (`[1]`, `[2]`).
- **Required University Frontmatter (To Be Supplied)**:
  - Official Title Page with University Crest / Logo
  - Certificate of Originality / Bona Fide Work (to be signed by supervisor)
  - Student Declaration of Research Ethics and Non-Plagiarism
  - Formal Acknowledgments (reserved until all authors agree)
  - Table of Contents, List of Figures, List of Tables, Abbreviations
- **Policy on Declarations**: In compliance with academic integrity, no certificates, signatures, or declarations of supervisor approval are generated prior to formal institutional defense.

---

## 4. Maintenance and Update Protocol
When institutional guidelines and venue CFPs are officially released:
1. File an update under `UPD-09` in `docs/synopsis_preparation/update_register.csv`.
2. Replace `PENDING_INSTITUTIONAL_SPECIFICATION` entries with authoritative parameters.
3. If an official university `.cls` or `.sty` file is provided, update `latex/thesis/main.tex` accordingly without altering chapter contents.
