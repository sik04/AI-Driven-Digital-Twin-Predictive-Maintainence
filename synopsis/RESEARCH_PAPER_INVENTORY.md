# Research Paper Inventory & Literature Audit: IntelliTwin

**Auditor:** Senior Academic Research Assistant & AI/ML Project Auditor  
**Audit Date:** October 30, 2026  
**Repository Working Directory:** `C:\www\AI-Driven-Digital-Twin-Predictive-Maintainence`  
**Target Document:** `synopsis/RESEARCH_PAPER_INVENTORY.md`  

---

## 1. Executive Summary of Scanned Documents

A comprehensive recursive scan was conducted across the entire repository workspace for research documents in formats including `.pdf`, `.doc`, `.docx`, `.tex`, `.bib`, `.ris`, and `.enw`.

### Document Classification Breakdown
1. **Complete Research Papers (Full-Text PDFs physically stored in repo)**: **1 paper**
   - [`data/raw/cmapss/Damage Propagation Modeling.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/data/raw/cmapss/Damage%20Propagation%20Modeling.pdf) (Complete 9-page IEEE conference publication).
2. **Institutional & Proposal PDFs (Non-papers)**: **2 documents**
   - [`PROJECT SYNOPSIS.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/PROJECT%20SYNOPSIS.pdf) (Official college synopsis guidelines circular from AKGEC IT Department).
   - [`Synopsis1.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/Synopsis1.pdf) (Old/previous project synopsis proposal for B.Tech project).
3. **Internal Research Drafts & Previews (Compiled PDFs)**: **4 documents**
   - [`docs/synopsis_preparation/previews/synopsis_draft.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/synopsis_preparation/previews/synopsis_draft.pdf)
   - [`docs/synopsis_preparation/previews/ieee_paper_draft.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/synopsis_preparation/previews/ieee_paper_draft.pdf)
   - [`docs/synopsis_preparation/previews/thesis_draft.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/synopsis_preparation/previews/thesis_draft.pdf)
   - [`docs/synopsis_preparation/previews/hypotheses_appendix.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/synopsis_preparation/previews/hypotheses_appendix.pdf)
4. **Scholarly Bibliography & Metadata Databases (BibTeX & CSV)**:
   - [`paper/references.bib`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/paper/references.bib) (23 verified scholarly BibTeX entries).
   - [`docs/synopsis_preparation/references_verified.bib`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/synopsis_preparation/references_verified.bib) (Curated subset of independently verified peer-reviewed citations).
   - [`research/literature/paper_inventory.csv`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/research/literature/paper_inventory.csv) (Detailed inventory of 15 audited scholarly articles with verified DOIs).
   - [`docs/synopsis_preparation/reference_audit.csv`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/docs/synopsis_preparation/reference_audit.csv) (30-source bibliometric audit with inspection levels and claim checks).
5. **LaTeX Source Documents**:
   - `docs/synopsis_preparation/latex/` (Complete modular LaTeX trees for IEEE synopsis, journal paper, and thesis).

---

## 2. Inventory of Complete Research Papers Found in Repository

The scan identified exactly **1 complete research paper** physically hosted in full text within the repository:

### Paper 1: Foundational C-MAPSS Benchmark Paper
- **Title**: *Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation*
- **Authors**: Abhinav Saxena, Kai Goebel, Donald Simon, Neil Eklund
- **Year**: 2008
- **Venue**: 2008 International Conference on Prognostics and Health Management (PHM '08), Denver, CO, USA
- **Publisher**: IEEE
- **DOI / URL**: [10.1109/PHM.2008.4711414](https://doi.org/10.1109/PHM.2008.4711414)
- **Local Path**: [`data/raw/cmapss/Damage Propagation Modeling.pdf`](file:///c:/www/AI-Driven-Digital-Twin-Predictive-Maintainence/data/raw/cmapss/Damage%20Propagation%20Modeling.pdf)
- **Length**: 9 full pages (Complete manuscript including abstract, equations, figures, tables, and 20 references)
- **Research Problem**: Lack of realistic run-to-failure degradation datasets for developing, validating, and comparing data-driven prognostics algorithms in complex thermo-dynamical engineering assets.
- **Methodology**: Used NASA's Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) 90,000 lb thrust class turbofan engine model in closed-loop mode. Injected exponential degradation into High-Pressure Compressor (HPC) flow and efficiency modifiers across 6 diverse operating conditions (altitude, Mach number, throttle resolver angle). Combined health degradation with multi-stage noise (manufacturing variation, process noise, and sensor measurement noise).
- **Key Findings**: Defined a health index $H(t)$ based on minimum operative margins and formulated the official asymmetric PHM scoring function penalizing late RUL predictions more heavily than early predictions:
  $$s = \sum_{i=1}^n \left(e^{-d_i/10} - 1\right) \text{ for } d_i < 0, \quad \sum_{i=1}^n \left(e^{d_i/13} - 1\right) \text{ for } d_i \ge 0$$
- **Relevance to IntelliTwin**: Foundational primary source. Establishes the exact physical origin, sensor schemas, operating conditions, and degradation dynamics of the C-MAPSS dataset utilized as the benchmark for all base models, conformal calibrators, and digital twin replay modules in IntelliTwin.

---

## 3. Physical PDF Availability vs. Bibliographic Citations

Aside from the Saxena et al. (2008) paper, **no other complete third-party research paper PDFs are stored in the local repository**. 

This is standard best practice in open-source software and academic version control to prevent copyright infringement and repository bloat. Instead, the research team maintains an extensively audited bibliographic registry across `research/literature/paper_inventory.csv` and `docs/synopsis_preparation/reference_audit.csv`.

---

## 4. Key Research Topics & Recommended Authentic Literature

For the B.Tech final-year synopsis, the literature review must cover four core pillars. Below are the authentic, highly cited, and peer-reviewed scholarly papers with verified DOIs and official URLs recommended for inclusion:

### Pillar 1: Digital Twin Architectures for Industrial Predictive Maintenance

1. **Tao et al. (2019)**
   - **Title**: *Digital Twin in Industry: State-of-the-Art*
   - **Authors**: Fei Tao, He Zhang, Ang Liu, A. Y. C. Nee
   - **Journal**: IEEE Transactions on Industrial Informatics, Vol. 15, No. 4, pp. 2405–2415
   - **DOI**: [10.1109/TII.2018.2873186](https://doi.org/10.1109/TII.2018.2873186)
   - **Relevance**: Authoritative framework defining the 5-dimension Digital Twin model and industrial synchronization paradigms.

2. **Fuller et al. (2020)**
   - **Title**: *Digital Twin: Enabling Technologies, Challenges and Open Research*
   - **Authors**: Aiden Fuller, Zhong Fan, Charles Day, Chris Barlow
   - **Journal**: IEEE Access, Vol. 8, pp. 108952–108971
   - **DOI**: [10.1109/ACCESS.2020.3001836](https://doi.org/10.1109/ACCESS.2020.3001836)
   - **Relevance**: Surveys the transition from passive digital shadows to active, AI-coupled predictive digital twin architectures.

3. **Huang et al. (2021)**
   - **Title**: *A Survey on AI-Driven Digital Twins in Industry 4.0: Smart Manufacturing and Advanced Robotics*
   - **Authors**: Ziqi Huang, Yang Shen, Jiayi Li, Marcel Fey, Christian Brecher
   - **Journal**: Sensors (MDPI), Vol. 21, No. 19, Art. 6340
   - **DOI**: [10.3390/s21196340](https://doi.org/10.3390/s21196340)
   - **Relevance**: Establishes taxonomy of AI and Digital Twin integration, noting the critical gap in statistical uncertainty quantification.

### Pillar 2: Remaining Useful Life (RUL) Prognostics & Deep Learning

4. **Ma and Mao (2021)**
   - **Title**: *Deep-Convolution-Based LSTM Network for Remaining Useful Life Prediction*
   - **Authors**: Meng Ma, Zhibin Mao
   - **Journal**: IEEE Transactions on Industrial Informatics, Vol. 17, No. 3, pp. 1658–1667
   - **DOI**: [10.1109/TII.2020.2991796](https://doi.org/10.1109/TII.2020.2991796)
   - **Relevance**: Evaluates recurrent deep architectures (LSTM) on multi-sensor degradation trajectories.

5. **Diao et al. (2026)**
   - **Title**: *Turbofan Engine Remaining Useful Life Prediction with Reliable Prediction Intervals via LSTM-Based Quantile Regression and Conformal Calibration*
   - **Authors**: Runsheng Diao, Mingzhe Zhou, Guanglei Meng, Shanze Wang
   - **Journal**: Sensors (MDPI), Vol. 26, No. 7, Art. 2249
   - **DOI**: [10.3390/s26072249](https://doi.org/10.3390/s26072249)
   - **Relevance**: Benchmarks LSTM quantile regression with conformalized calibration on C-MAPSS FD001 and FD002.

### Pillar 3: Distribution-Free Uncertainty Quantification & Conformal Prediction

6. **Javanmardi and Hüllermeier (2023)**
   - **Title**: *Conformal Prediction Intervals for Remaining Useful Lifetime Estimation*
   - **Authors**: Alireza Javanmardi, Eyke Hüllermeier
   - **Journal**: International Journal of Prognostics and Health Management, Vol. 14, No. 2, Art. 3417
   - **DOI**: [10.36001/ijphm.2023.v14i2.3417](https://doi.org/10.36001/ijphm.2023.v14i2.3417)
   - **Relevance**: Primary paper introducing split-conformal prediction intervals for RUL estimation on C-MAPSS and examining exchangeability assumptions.

7. **Lee, Barber, and Willett (2023)**
   - **Title**: *Distribution-Free Inference with Hierarchical Data*
   - **Authors**: Yonghoon Lee, Rina Foygel Barber, Rebecca Willett
   - **Venue**: arXiv:2306.06342 [math.ST] (Revised Aug 2025)
   - **URL**: [https://arxiv.org/abs/2306.06342](https://arxiv.org/abs/2306.06342)
   - **Relevance**: Foundational statistical theory for hierarchical conformal prediction, providing finite-sample bounds placing $1/(m+1)$ probability mass at infinity.

8. **Gneiting and Raftery (2007)**
   - **Title**: *Strictly Proper Scoring Rules, Prediction, and Estimation*
   - **Authors**: Tilmann Gneiting, Adrian E. Raftery
   - **Journal**: Journal of the American Statistical Association, Vol. 102, No. 477, pp. 359–378
   - **DOI**: [10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437)
   - **Relevance**: Mathematical foundation for the Winkler interval score used to evaluate interval width and coverage penalties.

### Pillar 4: Decision-Aware Uncertainty & Sequential Maintenance Optimization

9. **Cortes-Gomez et al. (2025)**
   - **Title**: *Utility-Directed Conformal Prediction: A Decision-Aware Framework for Actionable Uncertainty Quantification*
   - **Authors**: Santiago Cortes-Gomez, Carlos Miguel Patiño, Yewon Byun, Steven Wu, Eric Horvitz, Bryan Wilder
   - **Venue**: International Conference on Learning Representations (ICLR 2025)
   - **URL**: [https://openreview.net/forum?id=iOMnn1hSBO](https://openreview.net/forum?id=iOMnn1hSBO)
   - **Relevance**: Establishes framework for aligning conformal prediction intervals with downstream utility functions and economic decision costs.

10. **Chen et al. (2022)**
    - **Title**: *Data-Driven Predictive Maintenance Strategy Considering the Uncertainty in Remaining Useful Life Prediction*
    - **Authors**: Chuang Chen, Jiantao Shi, Ningyun Lu, Zheng Hong Zhu, Bin Jiang
    - **Journal**: Neurocomputing, Vol. 494, pp. 79–88
    - **DOI**: [10.1016/j.neucom.2022.04.055](https://doi.org/10.1016/j.neucom.2022.04.055)
    - **Relevance**: Demonstrates how predictive uncertainty intervals directly feed into cost-optimal replacement and inspection scheduling.
