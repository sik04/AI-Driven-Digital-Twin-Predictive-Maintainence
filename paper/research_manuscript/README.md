# IntelliTwin: AI-Driven Digital Twin Framework for Predictive Maintenance
## Peer-Reviewed Academic Research Manuscript Suite

- **Paper Title**: *IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance*
- **Institution**: Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad
- **Affiliating University**: Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow
- **Academic Session**: 2026–2027 | **Departmental Circular Ref**: `AKGEC/IT/CSIT/26-27/PROJ-m`
- **Project Supervisor**: Dr. Ruchi Gupta (Associate Professor, Department of Information Technology)
- **Student Authors**:
  1. **Shiksha Pandey** (University Roll No: `2300270110112`)
  2. **Mayank Singh** (University Roll No: `2300270310115`)

---

## 1. Directory Overview & Deliverables

This directory contains the authoritative research paper, verified scientific audits, figure sources, and reproducibility manifests developed according to IEEE conference and journal standards:

```
paper/research_manuscript/
├── README.md                                    # Master manuscript documentation (this file)
├── research_paper.pdf                           # Final 5-page IEEE two-column vector PDF (882,318 bytes)
├── research_paper.docx                          # Formatted OpenXML Word document (3,760 bytes)
├── research_paper.tex                           # Master IEEEtran LaTeX source code
├── references.bib                               # Verified 24-entry BibTeX database
├── research_paper.html                          # High-resolution semantic HTML source (786,428 bytes)
├── intellitwin_manuscript_overleaf.zip          # 1-click ready Overleaf package (1,195,215 bytes)
├── generate_research_manuscript.py              # Automated document generation script
├── PROJECT_CONTEXT_INVENTORY.md                 # Stage 1: Context retrieval and repository audit
├── TECHNICAL_RESEARCH_AUDIT.md                  # Stage 2: Technical and mathematical audit
├── EXPERIMENT_EVIDENCE_AUDIT.md                 # Stage 3: Confirmatory and exploratory results audit
├── LITERATURE_AND_REFERENCE_AUDIT.md            # Stage 4: Literature matrix and reference audit
├── RESEARCH_PAPER_OUTLINE.md                    # Stage 5: Structural outline and evidence mapping
├── research_paper_audit_report.md               # Stage 7: Final scientific audit report
├── reproducibility_checklist.md                 # NeurIPS/IEEE research reproducibility checklist
├── research_evidence_matrix.csv                 # Detailed claim-to-evidence matrix
├── reference_verification.csv                   # Reference verification matrix
├── experiment_summary.csv                       # Experiment inventory matrix
└── figure_sources/                              # High-resolution vector PDF and PNG figures
    ├── ablation_cost_vs_coverage.pdf (.png)
    ├── dropout_degradation.pdf (.png)
    ├── lower_upper_miss_rates_by_lifecycle_stage.pdf (.png)
    ├── noise_level_degradation.pdf (.png)
    ├── scale_asymmetry_routing_paired_effects.pdf (.png)
    ├── setting_bias_comparisons.pdf (.png)
    ├── architecture.tex
    └── causal_window.tex
```

---

## 2. Key Scientific Findings & Core Conclusions

1. **Massive Maintenance Cost Reductions**:
   - In confirmatory evaluation on 122 held-out test engines from NASA C-MAPSS FD002, the proposed decision-aware conformal calibration achieved **$+7.62$ SCU/engine** (GBR) and **$+10.99$ SCU/engine** (LSTM) cost improvements over global conformal baselines, and **$+7.50$** to **$+11.32$ SCU/engine** improvements over condition-aware baselines.
   - Zero in-service catastrophic failures occurred across the entire evaluation fleet ($\Deltafail = 0.0$).
2. **Transparent Preregistered Reporting**:
   - Under the preregistered Intersection-Union Testing (IUT) criteria, research questions RQ1–RQ4 were formally classified as **UNSUPPORTED** because empirical coverage in the late degradation lifecycle stage fell to $\sim 77\%$ (breaching the strict $E < 0.05$ ceiling with $E_{\text{stage}} \approx 0.13$).
   - The paper does not hide or whitewash this negative finding; it directly analyzes the mathematical trade-off between downstream operational cost savings and late-stage conditional coverage under non-stationary wear.
3. **Factorial Mechanism Isolation (Phase 8)**:
   - **Scale Dilation ($\gamma=2$ vs $0$)**: Drives an unweighted descriptive mean cost reduction of **$-10.4823$ SCU**.
   - **Directional Asymmetry ($\beta=-\ln 2$ vs $0$)**: Delivers consistent secondary cost savings of **$-1.2142$ SCU**.
   - **Regime Routing**: Shows null effect on single-condition fleets ($0.0000$ SCU on FD001) and a small cost penalty (**$+0.5594$ SCU**) on multi-regime fleets due to partition sample dispersion.

---

## 3. How to Use the Deliverables

### A. View or Submit the Compiled Paper
- **PDF (IEEE Two-Column Format, 5 pages)**: [`research_paper.pdf`](research_paper.pdf)
- **Word Document (Fully Editable)**: [`research_paper.docx`](research_paper.docx)

### B. 1-Click Upload to Overleaf
1. In Overleaf, click **"New Project"** $\rightarrow$ **"Upload Project"**.
2. Select [`intellitwin_manuscript_overleaf.zip`](intellitwin_manuscript_overleaf.zip).
3. Overleaf will unpack `research_paper.tex`, `references.bib`, and all figure files, compiling the complete paper with TikZ graphics and BibTeX references instantly.

### C. Re-generate Documents Locally
To recompile the HTML, PDF, Word, and Overleaf ZIP archives:
```bash
python paper/research_manuscript/generate_research_manuscript.py
```
*(Requires Google Chrome installed for headless vector PDF rendering).*
