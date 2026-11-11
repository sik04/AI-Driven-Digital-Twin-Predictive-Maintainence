# Comprehensive IEEE Formatting & Content Audit: IntelliTwin Research Paper

- **Document Version**: `1.0.0`
- **Audit Date**: `2026-11-11T16:50:00+05:30`
- **Designated Formatting Reference**: `INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf`
- **Subject Manuscript Under Correction**: `paper/research_manuscript/research_paper.pdf`
- **Baseline Context Documents**: `PROJECT SYNOPSIS.pdf` (AKGEC guidelines), `Synopsis1.pdf` (Oct 2026 initial student draft)
- **Auditors**: Antigravity Senior Academic Research & IEEE Formatting Specialists

---

## 1. Executive Summary

This audit performs a systematic, section-by-section comparison between the designated IEEE presentation reference (`INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf`), the existing generated paper (`research_paper.pdf`), and the authoritative repository research records. 

While the generated paper in `research_manuscript/` accurately captured the advanced mathematical conformal calibration and held-out test evidence, its visual presentation, author block, and metadata deviated from standard IEEE conference standards and institutional requirements. Conversely, the designated reference PDF exhibited ideal double-column IEEE typography but suffered from obsolete author affiliations (Mayank Singh listed under ECE with personal Gmail), unauthorized inclusion of the supervisor in the author block, and legacy single-dataset (FD001) empirical scope.

The corrected manuscript (`research_paper_ieee.tex` / `.pdf` / `.docx`) synthesizes the **strict IEEE presentation standards of the reference PDF** with the **authoritative, independently verified, multi-regime research evidence** of the approved IntelliTwin project.

---

## 2. 11-Point Detailed Comparative Audit Matrix

| Audit Dimension | Designated IEEE Reference (`DOUBLE_COLUMN.pdf`) | Subject Manuscript (`research_paper.pdf`) | Approved Repository Truth | Defect / Required Correction |
| :--- | :--- | :--- | :--- | :--- |
| **1. Author Ordering** | Mayank Singh (1st), Shiksha Pandey (2nd), Ruchi Gupta (3rd) | Shiksha Pandey (1st), Mayank Singh (2nd), Dr. Ruchi Gupta (3rd) | Approved project roster: Shiksha Pandey (Lead), Mayank Singh (Co-author) | **CORRECT**: Shiksha Pandey must appear as First Author; Mayank Singh as Second Author. |
| **2. Author Affiliations** | Mayank Singh: Dept. of ECE; Shiksha: Dept. of IT | Both listed under Dept. of IT | Both students belong strictly to Department of Information Technology (IT) | **CORRECT**: Remove ECE affiliation completely. Both authors must be attributed strictly to Dept. of IT, AKGEC. |
| **3. Project Guide Attribution** | Dr. Ruchi Gupta listed as third author with college email | Dr. Ruchi Gupta listed as third author with supervisory note | Dr. Ruchi Gupta is Faculty Project Supervisor, not a student author | **CORRECT**: Remove Dr. Ruchi Gupta from the author block. Acknowledge her in Section XI / Acknowledgments. |
| **4. Contact / Email Addresses** | Personal Gmail addresses (`mayanksingh2745@gmail.com`, `shikshapandey2004@gmail.com`) | Institutional email placeholders with roll numbers | Strict publication guidelines prohibit arbitrary personal emails | **CORRECT**: Completely exclude all Gmail, institutional, or placeholder email addresses from the author block. |
| **5. Author Block Layout** | Three separate vertical columns occupying substantial vertical space | Three horizontal blocks with subnotice line | Compact IEEE two-author arrangement | **CORRECT**: Implement standard compact IEEE author layout: **Shiksha Pandey¹, Mayank Singh²** with numbered affiliations below. |
| **6. Page Size & Geometry** | A4, 2-column IEEE format (5 pages) | Letter size, 2-column layout (5 pages) | Official AKGEC & IEEE format: A4 (210 $\times$ 297 mm) | **CORRECT**: Force A4 page size with standard IEEE margins (top/bottom: 0.75 in, left/right: 0.625 in, column gap: 0.22 in). |
| **7. Research Scope & Benchmark** | Single-dataset C-MAPSS FD001 (100 training, 100 test engines) | Multi-dataset C-MAPSS FD001, FD002, FD004 (122 held-out engines) | Multi-regime FD002 (primary) + FD001 (control) + FD004 (robustness) | **CORRECT**: Maintain authoritative multi-regime C-MAPSS scope with frozen Step 9 and Phase 8 evidence. |
| **8. Mathematical Rigor** | Symmetric absolute residual conformal score: $s = \|y - \mu\| / \sigma$ | Asymmetric decision-aware score: $\text{score} = \max(\frac{p-y}{a(p)}, \frac{y-p}{b(p)})$ | Exact formulas in `src/intellitwin/uncertainty/scores.py` ($\gamma=2, \beta=-\ln 2$) | **MAINTAIN**: Retain verified asymmetric nonconformity formulation and rational engine weighting. |
| **9. Empirical Integrity** | Claims 100% catastrophic failure prevention and 95.00% coverage on FD001 | Reports confirmatory test results: $+7.50$ to $+11.32$ SCU cost reduction; late-stage coverage breach | Preregistered IUT outcome: RQ1–RQ4 UNSUPPORTED due to $E_{\text{stage}} \approx 0.13 > 0.05$ | **MAINTAIN**: Transparently report preregistered confirmatory IUT outcomes and exploratory factor effects without fabrication. |
| **10. Citation Formatting** | 15 citations in citation order, IEEE format | 30 citations in citation order, IEEE format | 24 verified citations in `paper/references.bib` | **CORRECT**: Harmonize references using verified citations from `paper/references.bib` in strict IEEE citation order. |
| **11. Digital Twin Scope** | Claims live cyber-physical sync via Flask API (`intellitwin/api.py`) | Replay prototype with causal lookback ($w=30$) and zero lookahead | Software-based historical telemetry replay prototype (`apps/twin_dashboard/`) | **CORRECT**: Accurately describe the Digital Twin as a validation-telemetry replay prototype without false hardware claims. |

---

## 3. Structural Section-by-Section Correction Plan

1. **Title**:
   - *Title*: **IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance**
2. **Author Block**:
   ```
   Shiksha Pandey¹, Mayank Singh²
   ¹ Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, India
   ² Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, India
   ```
3. **Abstract & Index Terms**:
   - Compact, structured single-paragraph abstract (250 words) adhering to IEEE italic run-in style.
   - *Index Terms*—Predictive Maintenance, Remaining Useful Life, Digital Twin, Conformal Prediction, Uncertainty Quantification, Condition-Adaptive Calibration, Turbofan Engines, C-MAPSS.
4. **Section Hierarchy**:
   - I. INTRODUCTION
   - II. RELATED WORK
   - III. PROBLEM FORMULATION AND RESEARCH OBJECTIVES
   - IV. PROPOSED INTELLITWIN FRAMEWORK
   - V. MATHEMATICAL METHODOLOGY
   - VI. EXPERIMENTAL SETUP
   - VII. RESULTS AND DISCUSSION
   - VIII. ABLATION AND ROBUSTNESS ANALYSIS
   - IX. DIGITAL TWIN IMPLEMENTATION
   - X. LIMITATIONS AND THREATS TO VALIDITY
   - XI. CONCLUSION AND FUTURE WORK
   - ACKNOWLEDGMENT
   - REFERENCES

