# IntelliTwin: Research Paper Structural Outline & Evidence Mapping

- **Target Manuscript Title**: *IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance*
- **Target Venue Format**: IEEE Conference / Journal Two-Column Standard Layout
- **Author Roster**:
  - **Shiksha Pandey** (Student Author, Roll No: `2300270110112`)
  - **Mayank Singh** (Student Author, Roll No: `2300270310115`)
  - **Dr. Ruchi Gupta** (Faculty Project Supervisor, Associate Professor, Department of Information Technology)
- **Institutional Attribution**: Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, affiliated with Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow, India.
- **Governing Architecture Decision Records**: ADR-001 through ADR-029

---

## Section-by-Section Evidence & Traceability Mapping

| Section | Target Subsection / Heading | Core Scientific Content | Authoritative Source Files & Artifacts | Verified Empirical Evidence / Tables |
| :--- | :--- | :--- | :--- | :--- |
| **Title & Frontmatter** | Title, Authors, Abstract, Keywords | Official institutional metadata; structured 250-word abstract; IEEE keywords. | `synopsis/Final_Synopsis/main.tex`, ADR-029 | Approved roster and metadata from commit `989b4d6` |
| **Section I** | **Introduction** | Predictive maintenance economics; catastrophic failure vs overhaul waste; point RUL limitations; conformal prediction; contributions. | `research/research_design/contribution_statement.md`, `research/decision_log.md` (ADR-002, ADR-007) | Background from Saxena et al. (2008), Huang et al. (2021) |
| **Section II** | **Related Work** | Prognostics & RUL; uncertainty quantification; conformal prediction in PHM; Digital Twins; critical comparative table. | `research/literature/literature_synthesis.md`, `research/literature/closest_work_matrix.csv`, `paper/references.bib` | Comparative matrix against Javanmardi (2023), Diao (2026), Robinson (2026) |
| **Section III** | **Research Gap & Problem Formulation** | Mathematical formalization of multi-sensor degradation; true vs estimated RUL; conditional undercoverage; formal RQ1–RQ4. | `research/research_design/research_gap.md`, `research/research_questions.md`, `research/hypotheses/hypothesis_framework.yaml` | Locked RQ1–RQ4 definitions; $H_0/H_1$ under ADR-018 |
| **Section IV** | **Proposed IntelliTwin Framework** | Architectural components; causal sliding windows ($w=30$); disjoint engine partitions; offline anti-leakage boundary. | `src/intellitwin/data/splits.py`, `windowing.py`, `docs/synopsis_preparation/latex/shared/figures/architecture.tex` | Architecture diagram, causal lookback buffer ($w=30$, stride 1) |
| **Section V** | **Mathematical Methodology** | Asymmetric dilation score ($\gamma=2, \beta=-\ln 2$); hierarchical engine-weighted distribution; regime fallback rules; sequential simulator cost equation. | `src/intellitwin/uncertainty/scores.py`, `quantiles.py`, `calibration.py`, `src/intellitwin/simulator/costs.py` | Formulas: $\sigma(p), a(p), b(p), \text{score}(p, y), F_{\text{final}}(q)$, and SCU cost equations |
| **Section VI** | **Experimental Setup & Protocol** | NASA C-MAPSS FD001, FD002, FD004; GBR (510-dim) and LSTM; matched-conservatism baselines; 10,000 cluster bootstrap draws; IUT rules. | `research/research_design/dataset_qualification.md`, `statistical_inference_protocol.md`, `step07_base_predictor_specification.md` | Frozen splits (122 test engines), 5 training seeds, 98.75% decision intervals |
| **Section VII** | **Confirmatory Empirical Results** | Formal Step 9 confirmatory audit; performance across 122 test engines; cost reduction vs late-stage coverage breakdown; formal UNSUPPORTED classifications. | `experiments/confirmatory_v1/component_evidence.csv`, `cell_summary.csv`, `independent_audit.json`, `rq_decisions.json` | Exact metrics: $\Deltacost = +7.50$ to $+11.32$ SCU; $E_{\text{stage}} \approx 0.13 > 0.05$; zero fleet failures |
| **Section VIII** | **Post-Confirmatory Factorial Ablation & Stress Analysis** | $2 \times 2 \times 2$ factorial component ablation across 240 cells; factor main effects ($\gamma, \beta$, routing); 1,620 stress evaluations under sensor noise, dropout, and bias. | `experiments/phase08_exploratory_v3/factor_main_effects.csv`, `stress_summary.csv`, `research/results/phase08_submission_v1/figures/` | Factor effects: $\gamma$ ($-10.48$ SCU), $\beta$ ($-1.21$ SCU), routing ($+0.56$ SCU); 6 publication figures |
| **Section IX** | **Digital Twin Telemetry Replay Prototype** | Software architecture; causal window replay; interactive dashboard demonstration (`apps/twin_dashboard/`); numerical parity verification. | `src/intellitwin/twin/replay.py`, `apps/twin_dashboard/app.js`, `docs/development/twin_verification.md` | Verification at $\text{atol} \le 10^{-4}$ across all 18 benchmark cells |
| **Section X** | **Discussion, Limitations & Threats to Validity** | Trade-off between operational utility and conditional coverage; post-confirmatory limits; synthetic SCU costs; absence of live physical feedback. | `research/results/phase08_submission_v1/limitations.md`, `writing_handoff.md` | Honest analysis of late-stage non-stationarity and engineering assumptions |
| **Section XI** | **Conclusion & Future Directions** | Summary of verified findings; lessons learned from preregistered IUT testing; future multi-asset fleet synchronization and online adaptive calibration. | `research/roadmap.md`, `synopsis/Final_Synopsis/main.tex` | Defensible summary strictly bounded by repository evidence |
| **References** | **Bibliography** | 24 verified peer-reviewed and preprint citations with complete metadata. | `paper/references.bib`, `LITERATURE_AND_REFERENCE_AUDIT.md` | Cross-verified against IEEE, Elsevier, Springer, MDPI, Crossref |
