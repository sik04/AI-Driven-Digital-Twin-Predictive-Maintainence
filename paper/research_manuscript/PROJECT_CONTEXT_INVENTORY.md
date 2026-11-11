# IntelliTwin: Project Context & Repository Evidence Inventory

- **Document Version**: `1.0.0`
- **Timestamp**: `2026-11-11T16:15:00+05:30`
- **Repository**: `https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence`
- **Current Branch**: `main` (synchronized with `origin/main` at commit `989b4d6`)
- **Institution**: Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad
- **Affiliating University**: Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow
- **Department**: Information Technology | **Academic Session**: 2026–2027
- **Project Supervisor / Guide**: Dr. Ruchi Gupta (Associate Professor, Department of IT, AKGEC)
- **Student Authors**:
  1. Shiksha Pandey — University Roll No: `2300270110112`
  2. Mayank Singh — University Roll No: `2300270310115`

---

## 1. Project Environment & Git Audit

| Audit Property | Environment Value | Verification Status |
| :--- | :--- | :--- |
| **Working Directory** | `c:\www\AI-Driven-Digital-Twin-Predictive-Maintainence` | Authoritative local checkout |
| **Git Repository Root** | `c:\www\AI-Driven-Digital-Twin-Predictive-Maintainence` | Verified Git root |
| **Current Branch** | `main` | Verified tracking `origin/main` |
| **Configured Remote** | `https://github.com/sik04/AI-Driven-Digital-Twin-Predictive-Maintainence.git` | Fetch & Push verified |
| **Latest Commit Hash** | `989b4d6` (`docs: complete final synopsis sign-off and master progress tracker`) | Verified on remote |
| **Git Working Tree** | Clean; untracked: `PROJECT SYNOPSIS.pdf`, `Synopsis1.pdf`; modified: `experiments/phase08_exploratory_v3/stress_interval_predictions.csv.gz` | Baseline preservation verified |
| **Python Environment** | Python 3.14.0 (`.venv_confirmatory`) | Dependencies: `torch 2.14.1+cpu`, `scikit-learn 1.9.1`, `pandas 3.0.6`, `scipy 1.18.1` |
| **Rendering Engine** | Google Chrome Headless 133+ (`C:\Program Files\Google\Chrome\Application\chrome.exe`) | Vector PDF generation verified |

---

## 2. Antigravity Historical Context & Established Milestones

The project has advanced through a 12-phase research and academic milestone framework:

1. **Phases 0–10 (Synopsis Suite)**: Completed, audited, and approved (`synopsis/SYNOPSIS_PROGRESS.md`):
   - **Phase 0**: Discovery & Repository Audit (`1a5a16f`)
   - **Phase 1**: Title Page & Metadata Alignment (`1b78c07`, `598a7f3`)
   - **Phase 2**: Introduction & Industrial Rationale (`9be3732`, `78b8364`)
   - **Phase 3**: Problem Definition, Research Gap & RQs (`5763192`, `c487f90`)
   - **Phase 4**: Literature Survey & Forensic Audit (`85d160a`, `6b879b3`, `24783ea`)
   - **Phase 5**: Objectives & Scope Formulation (`576d033`, `193f5c0`)
   - **Phase 6**: Proposed Methodology & Algorithmic Formulation (`319f3ff`, `23839b8`)
   - **Phase 7**: System Architecture & Workflow Diagrams (`b0b0e3a`, `4328259`)
   - **Phase 8**: Implementation Status and Empirical Results (`1b5bb8c`, `ad6fb1c`)
   - **Phase 9**: Tools, Technologies, and System Requirements (`2059204`, `2afb145`)
   - **Phase 10**: Conclusion and Future Directions (`60a8b0d`, `3385b6f`)
   - **Final Phase**: Overleaf LaTeX Synchronization & Page Budget Audit (`67d8422`, `c4fbacc`, `989b4d6`)
2. **Confirmatory Testing (Step 9 / ADR-027)**:
   - Executed on 122 held-out test engines across C-MAPSS FD001, FD002, and FD004.
   - Evaluated 930 configurations (810 primary + 120 controls), 39,180 engine outcome records, 186 cell summaries, and 152 hypothesis components.
   - Independent reference audit passed with zero failing reasons (`experiments/confirmatory_v1/independent_audit.json`).
   - Under preregistered Intersection-Union Testing (IUT) and Bonferroni criteria, RQ1–RQ4 were classified as **UNSUPPORTED** due to late-stage degradation coverage ceiling breaches ($E < 0.05$ breached in late-life wear).
3. **Exploratory Post-Confirmatory Investigation (Phase 8 / ADR-028, ADR-029)**:
   - Conducted $2 \times 2 \times 2$ factorial component ablation across 240 cells ($\gamma \in \{0, 2\}$, $\beta \in \{-\ln 2, 0\}$, routing $\in \{\text{global}, \text{regime}\}$).
   - Executed engineering stress degradation battery across 1,620 evaluations (Gaussian noise, sensor dropout, setting bias).
   - Authoritative bundles verified in `experiments/phase08_exploratory_v3/` and reported in `research/results/phase08_submission_v1/`.

---

## 3. Comprehensive Repository Inventory

| File / Directory Path | Purpose | Key Information & Scope | Evidence Classification |
| :--- | :--- | :--- | :--- |
| `src/intellitwin/` | Core framework package | Production Python library with strict typing | **Authoritative / Approved** |
| `src/intellitwin/data/` | Preprocessing & ingestion | C-MAPSS parser, engine-disjoint splits, causal windowing ($w=30$) | **Authoritative / Approved** |
| `src/intellitwin/models/` | Base prognostics predictors | HistGradientBoostingRegressor and LSTM architectures | **Authoritative / Approved** |
| `src/intellitwin/uncertainty/` | Conformal calibration engine | Asymmetric nonconformity scoring, rational weighting, regime fallbacks | **Authoritative / Approved** |
| `src/intellitwin/simulator/` | Sequential maintenance engine | Discrete-cycle state machine, SCU pricing ($\CPM=1.0, \CFAIL=5.0, \CWASTE=0.20$) | **Authoritative / Approved** |
| `src/intellitwin/evaluation/` | Statistical inference engine | 10,000 paired engine-cluster bootstrap, IUT decision rules | **Authoritative / Approved** |
| `src/intellitwin/twin/` | Digital Twin replay engine | Historical validation-telemetry streaming without lookahead | **Authoritative / Approved** |
| `src/intellitwin/robustness/` | Exploratory verification | Independent mathematical reference routines with zero production calls | **Authoritative / Approved** |
| `apps/twin_dashboard/` | Operator user interface | Browser-based replay dashboard (`index.html`, `app.js`, `styles.css`) | **Authoritative / Approved** |
| `research/research_questions.md` | Authoritative RQs | Exact formulations of RQ1–RQ4 with primary outcomes and comparators | **Authoritative / Frozen** |
| `research/hypotheses/` | Hypothesis framework | Machine-readable YAML specification of $H_0/H_1$ and boundary criteria | **Authoritative / Frozen** |
| `research/research_design/` | Research methodology logs | Gap analysis, qualification, inference protocol, cost scenarios | **Authoritative / Frozen** |
| `research/decision_log.md` | Architecture Decision Records | Complete chronological governance log (ADR-001 through ADR-029) | **Authoritative / Approved** |
| `research/literature/` | Systematic literature review | Literature matrix, citation map, closest work comparison, search logs | **Authoritative / Approved** |
| `experiments/confirmatory_v1/` | Confirmatory test outputs | 122 test engines, 930 configurations, full bootstrap arrays, audit receipts | **Authoritative / Frozen** |
| `experiments/phase08_exploratory_v3/` | Factorial ablation & stress | 240 ablation cells, 1,620 stress evaluations, paired contrasts, main effects | **Authoritative / Approved** |
| `research/results/phase08_submission_v1/` | Publication evidence bundle | 6 publication figures (PDF/PNG), results summary, writing handoff | **Authoritative / Approved** |
| `paper/references.bib` | Scholarly bibliography | 24 verified references with authentic DOIs, titles, and journal venues | **Authoritative / Approved** |
| `paper/claims_evidence_matrix.csv` | Traceability audit matrix | Claims CLM-01 through CLM-18 mapped to artifacts and validation status | **Authoritative / Approved** |
| `synopsis/Final_Synopsis/` | Master synopsis suite | Approved 10-page academic synopsis (`synopsis.pdf`, `synopsis.docx`, `main.tex`) | **Authoritative / Approved** |
| `docs/synopsis_preparation/` | Historical draft files | Pre-confirmatory draft LaTeX sources and thesis previews | **Historical / Superseded** |
| `PROJECT SYNOPSIS.pdf` | Initial baseline proposal | Departmental submission reference file | **Historical Reference** |
| `Synopsis1.pdf` | Secondary baseline proposal | Departmental submission reference file | **Historical Reference** |

---

## 4. Evidence Classification Summary

- **Authoritative & Frozen**: The mathematical models, frozen confirmatory test evidence (`experiments/confirmatory_v1/`), pre-test verification protocols, and ADR decisions cannot be modified post-hoc.
- **Authoritative & Approved (Exploratory)**: Phase 8 factorial ablation and stress testing evidence (`experiments/phase08_exploratory_v3/` and `research/results/phase08_submission_v1/`) are verified by an independent reference audit and provide post-confirmatory diagnostic insight.
- **Historical / Superseded**: Early drafts in `docs/synopsis_preparation/` written before held-out test execution are preserved for provenance but superseded by the completed empirical evidence.
- **Zero Fabrication Mandate**: All numerical metrics, statistical contrasts, figures, and claims presented in the research manuscript must originate strictly from the verified evidence files above.
