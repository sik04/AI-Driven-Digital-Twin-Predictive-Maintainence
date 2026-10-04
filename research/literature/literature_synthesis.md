# Systematic Literature Synthesis and Research Positioning

**Authors**: Mayank Singh, Shiksha Pandey, Ruchi Gupta  
**Project**: IntelliTwin Research Initiative  
**Phase**: Phase 1 (Systematic Literature Review)  
**Status**: Formal Literature Evidence Synthesis  

---

## 1. Executive Summary and Methodological Boundary

This document synthesizes scholarly evidence across the 15 research works inventoried in the local repository alongside verified external closest-work literature and software artifacts. The objective is to position the IntelliTwin research framework against published prior art, expose threats to potential novelty claims, and delineate an evidence-grounded research baseline.

In accordance with strict academic integrity standards:
- Broad claims (e.g., combining AI with Digital Twins for predictive maintenance, or generating prediction intervals for RUL) are acknowledged as mature prior art or documented research directions, not novel contributions.
- All literature assertions cite verified bibliographic records indexed in [`paper/references.bib`](../../paper/references.bib) and mapped in [`research/literature/citation_map.csv`](citation_map.csv).
- Unverified leads (e.g., the 2026 thesis attributed to Osama Taha) are tracked separately as unresolved leads and excluded from verified peer-reviewed benchmarking.
- The identified research gap is under reassessment following corrections to the closest-work comparison.

---

## 2. Thematic Literature Synthesis

### Theme 1: Digital Twins and Predictive Maintenance
The integration of Digital Twins (DTs) with predictive maintenance (PdM) is well established across industrial manufacturing, civil infrastructure, and energy systems. Comprehensive surveys by Huang et al. (2021) [@huang2021survey], Hasan & Crawford (2025) [@hasan2025new], and Pathri & Ganduri (2025) [@pathri2025smart] document the evolution of multi-scale cyber-physical DTs from conceptual 3D representations into dynamic data-synchronized monitoring systems. 

In civil infrastructure, Diana et al. (2025) [@diana2025ai], Mazzetto (2024) [@mazzetto2024review], Mousavi et al. (2024) [@mousavi2024evolution], and Mahmud et al. (2025) [@mahmud2025ai] outline multi-tier architectures linking Internet-of-Things (IoT) sensor streams with Building Information Modeling (BIM) and predictive asset maintenance. Similarly, Wei (2024) [@wei2024digital] provides an engineering realization of an AI-driven digital twin for chiller plant predictive maintenance in an academic doctoral dissertation at Nanyang Technological University. Bello et al. (2024) [@bello2024ai] demonstrate the operational rationale for proactive DT-enabled maintenance in renewable energy platforms. 

**Synthesis Finding**: *Developing a Digital Twin for predictive maintenance is not novel.* The literature firmly establishes multi-tier architectural paradigms (Perception, Twin Modeling, Computational Analytics, Application Services).

---

### Theme 2: Remaining Useful Life (RUL) Point Prediction
Data-driven point prediction of Remaining Useful Life using benchmark degradation telemetry—most notably the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) dataset formulated by Saxena et al. (2008) [@saxena2008damage]—is mature. Hundreds of studies have benchmarked classical regression models against deep temporal neural architectures.

In the local repository corpus, Hosseinzadeh et al. (2023) [@hosseinzadeh2023predictive] benchmarked ML models for failure detection on sensor telemetry. Most critically, Wu et al. (2026) [@wu2026research] implemented a Digital Twin maintenance-support platform combining RVM, Random Forest, Elastic Net, autoregression, and LSTM with genetic-algorithm weight optimization, evaluated on CS2_35 lithium-ion battery laboratory data, identifying uncertainty limits as future work.

**Synthesis Finding**: *Proposing AI-driven RUL point prediction, even when coupled with a Digital Twin, possesses zero scientific novelty.* Point estimators provide no confidence boundaries, treating all predictions with equal epistemic certainty regardless of operational noise or wear stage.

---

### Theme 3: Probabilistic and Uncertainty-Aware RUL Prediction
Recognizing that deterministic point estimates create severe operational hazards, researchers have developed probabilistic and uncertainty-aware prognostic frameworks. Chen et al. (2022) [@chen2022data] investigated predictive maintenance strategies considering the uncertainty in RUL prediction. Walia & Kumar (2026) [@walia2026uncertainty] evaluated quantile regression with CNN/GRU and PPO optimal maintenance scheduling on NASA turbofan engine data.

**Synthesis Finding**: *Uncertainty-aware RUL prediction is documented in the reliability literature.* Full primary methodology for Chen et al. (2022) remains unverified in the current audit, while Walia & Kumar (2026) use quantile regression and PPO scheduling.

---

### Theme 4: Prediction Interval Calibration
Estimating prediction intervals $[L, U]$ requires statistical calibration so that empirical Prediction Interval Coverage Probability (PICP) aligns with target nominal levels. Xu et al. (2026) [@xu2026novel] proposed an uncertainty-aware framework for remaining useful life prediction integrating uncertainty quantification and calibration (primary methodology remains unverified in this audit).

**Synthesis Finding**: *Uncertainty quantification and post-hoc calibration are recognized requirements in prognostic literature.*

---

### Theme 5: Conformal Prediction for Prognostics
To overcome limitations of parametric assumptions, Inductive Conformal Prediction (ICP) has been applied to prognostic regression problems.

Javanmardi & Hüllermeier (2023) [@javanmardi2023conformal] evaluated conformal prediction intervals for remaining useful lifetime estimation on C-MAPSS using convolutional neural network and gradient boosting predictors under exchangeability assumptions. Diao et al. (2026) [@diao2026turbofan] applied LSTM quantile regression with conformal calibration/CQR to C-MAPSS FD001 and FD002, including life-stage analysis and cross-condition evaluation with labeled target adaptation. Robinson (2026) [@robinson2026riskaware] evaluated gradient boosting and asymmetric CQR across all four C-MAPSS subsets for risk-aware prediction intervals.

**Synthesis Finding**: *Applying conformal prediction to RUL estimation on C-MAPSS is established in prior art (Javanmardi & Hüllermeier 2023; Diao et al. 2026; Robinson 2026).*

---

### Theme 6: Conditional Reliability and Stage-Wise Analysis
Evaluating coverage guarantees across discrete degradation stages and operating regimes is essential for reliability diagnostics.

Diao et al. (2026) [@diao2026turbofan] conducted life-stage analysis and cross-condition evaluation with labeled target adaptation on C-MAPSS FD001 and FD002. BenAbdennour (2026) [@benabdennour2026grouped] presented leakage-controlled grouped validation and urgent/critical interval-safety diagnostics across engine, battery, and bearing degradation datasets. Yan (2026) [@yan2026audit] provided a software reproducibility artifact inspecting C-MAPSS conformal comparisons, operating-regime/conditional auditing, and maintenance-cost evaluation.

---

### Theme 7: Operating-Regime Shifts and Conditional Diagnostics
Yang et al. (2026) [@yang2026empirical] evaluated operating-regime conditional-reliability diagnostics on a ten-bearing PHME subset using a predictive-representation model, empirical residual calibration, a post-hoc regime-conditioned calibration diagnostic, and retrospective maintenance-trigger comparisons.

---

### Theme 8: Maintenance Decision Support and Risk Optimization
Predictive maintenance literature connects probabilistic forecasts with operational decision engines.

Zhu et al. (2025) [@zhu2025predictive] evaluated deep-learning/Monte Carlo dropout prediction intervals and maintenance-cost optimization using aero-engine data. Walia & Kumar (2026) [@walia2026uncertainty] applied PPO reinforcement learning maintenance scheduling. Shehadeh (2024) [@shehadeh2024evaluating] demonstrated empirical KPI improvements when transitioning from reactive to proactive maintenance in power plants. Brighenti et al. (2024) [@brighenti2024forecasting] integrated reliability indices into bridge maintenance prioritization.

---

### Theme 9: Maintenance Cost and Asymmetric Loss Interpretation
Asymmetric evaluation of RUL prediction error $d = \text{predicted RUL} - \text{true RUL}$ reflects operational maintenance reality:
- For $d = \text{predicted RUL} - \text{true RUL}$: $d < 0$ means underestimating remaining life, producing an early/conservative prediction; $d > 0$ means overestimating remaining life, producing an optimistic prediction that risks late intervention; $d = 0$ is exact.

---

### Theme 10: Closest Work Comparison Matrix

Table 1 summarizes the primary characteristics of verified closest works:

| Study | Benchmark / Dataset | Primary Method / Model | UQ / Calibration | Maintenance / Decision Evaluation | Peer Review / Access Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Wu et al. (2026)** [@wu2026research] | CS2_35 battery lab data | Ensemble (RVM, RF, ElasticNet, AR, LSTM) | Future work | Digital Twin platform | Peer-reviewed (Sensors) |
| **Chen et al. (2022)** [@chen2022data] | Not verified in current audit | Not verified in current audit | Not verified in current audit | Predictive maintenance under uncertainty | Peer-reviewed (Neurocomputing) |
| **Zhu et al. (2025)** [@zhu2025predictive] | Aero-engine data (C-MAPSS identified) | Deep learning prediction intervals | Monte Carlo dropout intervals | Maintenance-cost optimization | Peer-reviewed (QREI) |
| **Diao et al. (2026)** [@diao2026turbofan] | C-MAPSS FD001, FD002 | LSTM Quantile Regression + CQR | Conformal calibration (CQR) | Upstream of full prescriptive optimization | Peer-reviewed (Sensors) |
| **Walia & Kumar (2026)** [@walia2026uncertainty] | NASA turbofan engine data | Quantile regression with CNN/GRU | Quantile regression | PPO maintenance scheduling | Peer-reviewed (RESS) |
| **Xu et al. (2026)** [@xu2026novel] | Not verified in current audit | Not verified in current audit | Not verified in current audit | Not verified in current audit | Peer-reviewed (RESS) |
| **Yang et al. (2026)** [@yang2026empirical] | Ten-bearing PHME subset | Predictive representation & empirical calibration | Post-hoc regime-conditioned diagnostic | Retrospective maintenance triggers | Preprint (arXiv:2607.08273) |
| **Javanmardi & Hüllermeier (2023)** [@javanmardi2023conformal] | NASA C-MAPSS | CNN and Gradient Boosting | Split conformal prediction | None | Peer-reviewed (IJPHM) |
| **Yan (2026)** [@yan2026audit] | NASA C-MAPSS | Conformal prediction intervals | Conformal calibration | Maintenance-cost evaluation | Zenodo Software Artifact |
| **Robinson (2026)** [@robinson2026riskaware] | C-MAPSS FD001-FD004 | Gradient boosting & asymmetric CQR | Asymmetric CQR conformal calibration | Risk-aware prediction intervals | Peer-reviewed (IJPHM) |
| **BenAbdennour (2026)** [@benabdennour2026grouped] | Engine, battery & bearing data | Grouped validation | Interval-safety calibration | Urgent/critical safety diagnostics | Peer-reviewed (Machines) |

---

### Theme 11: Reassessment of Research Gap

Prior work already includes conformal RUL prediction, life-stage and operating-regime diagnostics, and maintenance-related evaluation. The present evidence does not establish conditional calibration plus maintenance decisions as a novel contribution. IntelliTwin’s research gap is under reassessment following corrections to the closest-work comparison. A possible next direction is a controlled replication and extension examining sequential decisions, information availability, and replacement conservatism; its originality is not yet established.

---

## 3. Audit of Unverified Leads and Exclusions

1. **Osama Taha (2026 Thesis Lead)**:
   - *Title*: "Decision-Oriented Predictive Maintenance: Calibrated RUL Uncertainty and Cost-Based Maintenance Policy Simulation"
   - *Audit Findings*: Kept as an unresolved lead. Document exists on Scribd; no record found in E-JUST institutional repository or indexed scholarly sources. Do not call nonexistent or fabricated.

2. **Hong Yan (2026 Software Artifact)**:
   - *Title*: "Conformal prediction intervals for turbofan remaining useful life: an audit across operating regimes (code and run artifacts)"
   - *Audit Findings*: Included—software artifact; deposit and selected archive files inspected in the supplied audit (Zenodo DOI 10.5281/zenodo.21330745). Corresponding peer-reviewed publication not verified.

---

## 4. Methodological Implications for Subsequent Phases

1. **Phase 2 (Gap, Questions, and Hypotheses Formalization)**:
   - Existing v1 research questions and hypothesis framework thresholds are preserved, but their novelty justification requires revision after the corrected literature comparison.
2. **Phase 3 (Dataset Study & Protocol)**:
   - Enforce strict engine-isolated cross-validation and calibration splits.
3. **Phase 5 & 6 (Baseline Benchmarks & Proposed Model)**:
   - Benchmark point predictors, quantile regression baselines, and conformalized models against verified comparators.
4. **Phase 7 (Uncertainty & Decision Experiments)**:
   - Evaluate marginal and conditional coverage metrics alongside maintenance cost functions using Saxena et al. (2008) asymmetric error score interpretations.
5. **Phase 9 (Digital Twin Software Layer)**:
   - Connect calibrated prediction intervals and risk states into the Digital Twin streaming framework.
