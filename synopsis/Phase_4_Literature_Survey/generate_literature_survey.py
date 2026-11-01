"""
Generator script for Phase 4: Literature Survey.
Compiles literature_survey.html to high-resolution literature_survey.pdf via Chrome Headless
and creates an editable OpenXML literature_survey.docx adhering to AKGEC formatting standards.
"""

import os
import subprocess
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "literature_survey.html")
PDF_PATH = os.path.join(SCRIPT_DIR, "literature_survey.pdf")
DOCX_PATH = os.path.join(SCRIPT_DIR, "literature_survey.docx")

def build_pdf():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        raise FileNotFoundError(f"Chrome not found at {chrome_path}")

    html_uri = f"file:///{HTML_PATH.replace(os.sep, '/')}"
    cmd = [
        chrome_path,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_PATH}",
        html_uri
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    if res.returncode != 0 or not os.path.exists(PDF_PATH):
        raise RuntimeError(f"Chrome PDF generation failed: {res.stderr}")
    print(f"Generated PDF: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")

def build_docx():
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="24"/>
        <w:color w:val="000000"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:line="360" w:lineRule="auto" w:after="200"/>
        <w:jc w:val="both"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>"""

    def p(text, is_bold=False, is_italic=False, size=24, align="both", space_after=200):
        b_tag = "<w:b/>" if is_bold else ""
        i_tag = "<w:i/>" if is_italic else ""
        xml_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""    <w:p>
      <w:pPr>
        <w:jc w:val="{align}"/>
        <w:spacing w:line="360" w:lineRule="auto" w:after="{space_after}"/>
      </w:pPr>
      <w:r>
        <w:rPr>{b_tag}{i_tag}<w:sz w:val="{size}"/></w:rPr>
        <w:t xml:space="preserve">{xml_text}</w:t>
      </w:r>
    </w:p>"""

    def li(bullet_str, bold_prefix, text, indent=720):
        xml_bullet = bullet_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml_bold = bold_prefix.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""    <w:p>
      <w:pPr>
        <w:ind w:left="{indent}" w:hanging="360"/>
        <w:jc w:val="both"/>
        <w:spacing w:line="360" w:lineRule="auto" w:after="120"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t xml:space="preserve">{xml_bullet} </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t xml:space="preserve">{xml_bold} </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:sz w:val="24"/></w:rPr>
        <w:t xml:space="preserve">{xml_text}</w:t>
      </w:r>
    </w:p>"""

    def table_xml(headers, rows):
        col_widths = [1600, 1400, 1500, 1600, 800, 800, 700, 2100]
        tbl_xml = ["""    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="10500" w:type="dxa"/>
        <w:jc w:val="center"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="6" w:space="0" w:color="4B5563"/>
          <w:left w:val="single" w:sz="6" w:space="0" w:color="4B5563"/>
          <w:bottom w:val="single" w:sz="6" w:space="0" w:color="4B5563"/>
          <w:right w:val="single" w:sz="6" w:space="0" w:color="4B5563"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>
          <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E5E7EB"/>
        </w:tblBorders>
      </w:tblPr>
      <w:tblGrid>"""]
        for w in col_widths:
            tbl_xml.append(f'        <w:gridCol w:w="{w}"/>')
        tbl_xml.append("      </w:tblGrid>")

        # Header row
        tbl_xml.append('      <w:tr><w:trPr><w:tblHeader/></w:trPr>')
        for i, h in enumerate(headers):
            xml_h = h.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            tbl_xml.append(f"""        <w:tc>
          <w:tcPr><w:tcW w:w="{col_widths[i]}" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="F1F5F9"/></w:tcPr>
          <w:p><w:pPr><w:jc w:val="center"/><w:spacing w:line="240" w:lineRule="auto" w:after="60"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="17"/></w:rPr><w:t>{xml_h}</w:t></w:r>
          </w:p>
        </w:tc>""")
        tbl_xml.append('      </w:tr>')

        # Data rows
        for row in rows:
            tbl_xml.append('      <w:tr>')
            is_highlight = "IntelliTwin" in row[0]
            fill_color = "EFF6FF" if is_highlight else "FFFFFF"
            for i, val in enumerate(row):
                xml_v = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                b_tag = "<w:b/>" if is_highlight else ""
                align = "center" if i in [4, 5, 6] else "left"
                tbl_xml.append(f"""        <w:tc>
          <w:tcPr><w:tcW w:w="{col_widths[i]}" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="{fill_color}"/></w:tcPr>
          <w:p><w:pPr><w:jc w:val="{align}"/><w:spacing w:line="240" w:lineRule="auto" w:after="60"/></w:pPr>
            <w:r><w:rPr>{b_tag}<w:sz w:val="16"/></w:rPr><w:t xml:space="preserve">{xml_v}</w:t></w:r>
          </w:p>
        </w:tc>""")
            tbl_xml.append('      </w:tr>')
        tbl_xml.append('    </w:tbl>')
        return "\n".join(tbl_xml)

    body_elements = []

    # Main Heading
    body_elements.append(p("4. Literature Survey", is_bold=True, size=28, space_after=240))

    # Subsection 4.1
    body_elements.append(p("4.1 Thematic Overview and Survey Taxonomy", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The rapid convergence of cyber-physical systems, advanced sensory instrumentation, and artificial intelligence has catalyzed "
        "a fundamental paradigm shift in industrial reliability engineering and asset lifecycle management [1]–[3]. In mission-critical "
        "environments—most prominently commercial aviation turbofan propulsion, high-capacity energy generation, and automated industrial "
        "tooling—preventing unexpected mechanical failure while eliminating premature maintenance waste represents a paramount economic "
        "and operational objective [1], [4]. Achieving this balance requires transitioning from traditional calendar-based preventative "
        "overhauls and reactive corrective repairs toward condition-based predictive maintenance (PdM) governed by prognostic Digital Twins [2], [5]."
    ))
    body_elements.append(p(
        "To establish an authoritative empirical baseline for the IntelliTwin project, a systematic literature review was conducted across "
        "25 verified scholarly works cataloged in the repository's literature matrix alongside five foundational methodological papers. "
        "The analyzed corpus bifurcates into two distinct, complementary investigative domains:"
    ))
    body_elements.append(li(
        "1.", "Local Repository Literature Corpus (15 Studies, LOC-01 to LOC-15):",
        "Encompasses peer-reviewed journal articles, comprehensive domain surveys, and doctoral dissertations evaluating multi-tier Digital Twin "
        "architectures, IoT telemetry integration, industrial failure classification, and operational maintenance economics across smart manufacturing, "
        "civil infrastructure, and renewable energy platforms [2], [4]–[16]."
    ))
    body_elements.append(li(
        "2.", "Supplemental Closest-Work Corpus (10 Studies, SUP-01 to SUP-10):",
        "Comprises peer-reviewed prognostic publications and verified software artifacts investigating continuous Remaining Useful Life (RUL) "
        "regression, distribution-free conformal prediction intervals, conditional coverage calibration across degradation stages, and risk-directed "
        "maintenance scheduling heuristics on benchmark datasets [17]–[26]."
    ))
    body_elements.append(p("To synthesize these scholarly contributions systematically, the literature is organized into four core thematic pillars:"))
    body_elements.append(li("•", "Theme 1:", "Cyber-Physical Digital Twins and Predictive Maintenance Systems"))
    body_elements.append(li("•", "Theme 2:", "Data-Driven RUL Estimation and Prognostic Regression"))
    body_elements.append(li("•", "Theme 3:", "Distribution-Free Conformal Prediction and Uncertainty Calibration"))
    body_elements.append(li("•", "Theme 4:", "Decision-Aware Maintenance Optimization and Cost Modeling"))

    # Subsection 4.2
    body_elements.append(p("4.2 Critical Thematic Review of Prior Art", is_bold=True, size=24, space_after=160))

    body_elements.append(p("Theme 1: Cyber-Physical Digital Twins in Predictive Maintenance", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "A Digital Twin (DT) is conceptually defined as an evolving, multi-scale computational model of a physical asset that continuously mirrors "
        "its physical state, operating kinematics, and degradation trajectory through bi-directional data synchronization [2], [3]. Comprehensive "
        "surveys by Huang et al. (2021) [3], Hasan and Crawford (2025) [13], and Pathri and Ganduri (2025) [14] document the historical evolution "
        "of industrial DTs from static computer-aided design (CAD) representations into dynamic, data-driven decision frameworks within Industry 4.0. "
        "These surveys formalize a consensus four-tier architectural taxonomy comprising: (i) Physical Perception and Sensor Telemetry Ingestion, "
        "(ii) Virtual Twin Modeling and State Synchronization, (iii) Computational Analytics and Machine Learning, and (iv) Operational Decision Support Services [3], [12]."
    ))
    body_elements.append(p(
        "In civil and industrial infrastructure, Diana et al. (2025) [2], Mazzetto (2024) [4], Mousavi et al. (2024) [9], and Mahmud et al. (2025) [12] "
        "investigate AI-augmented DT frameworks linking IoT sensor networks with predictive structural maintenance, demonstrating how synchronized "
        "virtual counterparts enhance operational resilience. Similarly, Wei (2024) [5] presents a doctoral investigation at Nanyang Technological "
        "University detailing the physical deployment of an AI-driven digital twin for HVAC and chiller plant maintenance, addressing telemetry "
        "synchronization and automated fault detection. Bello et al. (2024) [6] and Shehadeh (2024) [8] examine the operational and macroeconomic "
        "rationale for proactive maintenance, with Shehadeh providing empirical evidence that transitioning from reactive to proactive maintenance in "
        "power generation facilities reduces unscheduled breakdown frequency by 35% and lowers total maintenance expenditure by over 20%. Belay et al. "
        "(2026) [16] explore communication-efficient federated anomaly detection leveraging DT simulation to generate synthetic training streams for "
        "distributed Industrial IoT (IIoT) networks."
    ))
    body_elements.append(p(
        "Most critically within the local corpus, Wu et al. (2026) [15] formulate an empirical Digital Twin maintenance-support platform for equipment "
        "RUL estimation, evaluated on CS2_35 lithium-ion battery laboratory data. Their framework couples a genetic algorithm (GA) ensemble—combining "
        "Relevance Vector Machines (RVM), Random Forests (RF), Elastic Net, Autoregression (AR), and Long Short-Term Memory (LSTM) networks—with an interactive "
        "operational dashboard. However, the authors explicitly conclude that their framework operates purely on deterministic point predictions, formally "
        "designating the quantification of prediction uncertainty and confidence bounds as critical future work [15]."
    ))
    body_elements.append(p(
        "Methodological Synthesis: The literature conclusively establishes that constructing a Digital Twin architecture for industrial asset monitoring "
        "is mature prior art [3], [13]. However, existing DT platforms predominantly treat machine learning components as black-box point estimators, "
        "lacking calibrated uncertainty quantification and risk-directed decision policies [14], [15].",
        is_italic=True, space_after=160
    ))

    body_elements.append(p("Theme 2: Data-Driven RUL Estimation and Prognostic Regression", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Data-driven prognostic modeling seeks to estimate an asset's Remaining Useful Life (yi(t) = Ti - t) directly from historical degradation sensor "
        "observations without requiring explicit physical partial differential equations [1], [7]. The foundational benchmark in this field is the "
        "Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) dataset developed by Saxena et al. (2008) at NASA Ames Research Center [1]. "
        "Generating run-to-failure degradation trajectories for commercial turbofan engines under varying flight altitudes, Mach numbers, and throttle "
        "resolver angles, Saxena et al. also formulated an asymmetric scoring metric to reflect industrial reality, penalizing late prognostic estimates "
        "(which risk catastrophic breakdown) far more severely than early estimates [1]."
    ))
    body_elements.append(p(
        "In the contemporary literature, hundreds of machine learning studies have investigated RUL regression on C-MAPSS. Within the local corpus, "
        "Hosseinzadeh et al. (2023) [7] benchmarked Random Forests, Support Vector Machines, Multilayer Perceptrons, and LSTMs for early failure "
        "detection on manufacturing telemetry, establishing that deep temporal architectures systematically outperform shallow classifiers in "
        "capturing non-linear wear dynamics. In broader literature, Zheng et al. (2017) and Ma and Mao (2021) established Convolutional Neural Networks "
        "(CNNs) and deep LSTMs as state-of-the-art baselines for temporal feature extraction from multivariate sensor sequences."
    ))
    body_elements.append(p(
        "Methodological Synthesis: Data-driven RUL point prediction is thoroughly investigated in the reliability literature. However, deterministic "
        "point estimators optimize symmetric loss functions (such as MSE or RMSE) that treat positive and negative prediction errors identically [1], [7]. "
        "In real-world aviation and energy operations, an overestimation error of +10 cycles leads to catastrophic in-service engine failure, whereas an "
        "underestimation error of -10 cycles merely results in premature maintenance [1]. Point predictors are fundamentally incapable of communicating "
        "tail risk or epistemic uncertainty to human operators.",
        is_italic=True, space_after=160
    ))

    body_elements.append(p("Theme 3: Distribution-Free Conformal Prediction and Uncertainty Calibration", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Recognizing the hazards of deterministic forecasting, reliability researchers have developed probabilistic prognostic methods, such as Gaussian "
        "Process regression, Bayesian Neural Networks, and Monte Carlo dropout [18], [21]. However, traditional Bayesian and parametric techniques depend "
        "heavily upon restrictive distributional assumptions (e.g., Gaussian noise priors) that rarely hold across severe, non-linear machine degradation dynamics [21], [23]."
    ))
    body_elements.append(p(
        "To provide distribution-free statistical validity, Inductive Conformal Prediction (ICP)—founded on algorithmic learning theory by Vovk et al.—has "
        "gained significant momentum in prognostics [23], [29]. Javanmardi and Hüllermeier (2023) [23] provided the first systematic evaluation of split "
        "conformal prediction for RUL estimation on NASA C-MAPSS, utilizing CNN and Gradient Boosted Decision Tree (GBDT) predictors to construct prediction "
        "intervals with guaranteed marginal coverage under exchangeability assumptions. Diao et al. (2026) [19] advanced this paradigm by combining LSTM-based "
        "Quantile Regression with Conformalized Quantile Regression (CQR) on C-MAPSS FD001 and FD002, demonstrating that conformal calibration corrects "
        "empirical undercoverage and incorporating degradation life-stage analysis. Robinson (2026) [25] introduced asymmetric CQR across all four C-MAPSS "
        "subsets, establishing risk-aware intervals that adjust coverage bounds to reflect operational risk. BenAbdennour (2026) [26] evaluated interval-safety "
        "calibration and leakage-controlled grouped validation across engine, battery, and bearing degradation benchmarks, emphasizing the critical importance of preventing temporal data leakage."
    ))
    body_elements.append(p(
        "Despite these advancements, standard conformal prediction assumes data exchangeability, which is fundamentally violated by industrial time-series "
        "telemetry exhibiting strong temporal autocorrelation and discrete operating regime shifts [22], [29]. Yang et al. (2026) [22] investigated bearing "
        "RUL degradation under operating regime shifts, proposing empirical residual calibration and revealing that global conformal calibration frequently "
        "masks severe conditional miscalibration across distinct operational regimes. Similarly, Hong Yan (2026) [24] deposited a comprehensive software "
        "reproducibility artifact auditing conformal prediction intervals across C-MAPSS operating regimes, exposing localized coverage vulnerabilities. "
        "To address clustered data structures, Lee, Barber, and Willett (2023) [29] established theoretical bounds for distribution-free hierarchical "
        "inference, providing mathematical foundations for multi-level calibration."
    ))
    body_elements.append(p(
        "Methodological Synthesis: Conformal prediction offers mathematically rigorous, finite-sample marginal coverage guarantees [23]. However, existing "
        "applications in prognostics either evaluate global marginal coverage in isolation or examine conditional diagnostics post-hoc without establishing "
        "how conditional calibration influences downstream operational decisions [19], [22].",
        is_italic=True, space_after=160
    ))

    body_elements.append(p("Theme 4: Decision-Aware Maintenance Optimization and Cost Modeling", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Prognostic models derive operational value exclusively through the maintenance decisions they inform [17], [18]. Chen et al. (2022) [17] investigated "
        "data-driven predictive maintenance strategies that explicitly account for RUL prediction uncertainty, modeling maintenance scheduling thresholds. "
        "Zhu et al. (2025) [18] investigated aero-engine predictive maintenance strategies on C-MAPSS by generating prediction intervals via deep-learning "
        "Monte Carlo dropout and integrating them into a maintenance-cost optimization model that weighs preventive replacement against unscheduled failure "
        "costs. Walia and Kumar (2026) [20] coupled quantile regression (CNN/GRU) with Proximal Policy Optimization (PPO) reinforcement learning to formulate "
        "an optimal sequential maintenance scheduling policy on NASA turbofan telemetry."
    ))
    body_elements.append(p(
        "In structural reliability, Brighenti et al. (2024) [10] developed a decision support system (DSS) integrating Markov Chain damage forecasting to "
        "prioritize maintenance interventions under budget constraints. Hisamuddin et al. (2026) [11] emphasized the necessity of integrating predictive models "
        "directly with multi-criteria maintenance decision engines in urban infrastructure. From a statistical decision-theoretic perspective, Cortes-Gomez "
        "et al. (2025) [30] introduced \"Utility-Directed Conformal Prediction\" at ICLR 2025, formulating a framework where conformal nonconformity scores "
        "are calibrated directly against downstream utility and decision loss rather than generic symmetric interval width. Standard scoring rules, such as "
        "the Winkler interval score analyzed by Gneiting and Raftery (2007) [28], provide statistical penalization for interval width and coverage breaches, "
        "while Lakens (2017) [27] formalizes statistical equivalence testing necessary for non-inferiority comparisons."
    ))
    body_elements.append(p(
        "Methodological Synthesis: Prior work demonstrates that linking uncertainty to maintenance decisions is vital [17], [18], [20]. However, existing "
        "frameworks either optimize decision heuristics using uncalibrated parametric intervals or evaluate calibrated conformal intervals using purely "
        "statistical loss metrics (MPIW/Winkler score) decoupled from sequential operational costs [18], [19], [30]. Furthermore, the literature lacks "
        "rigorous controls to verify whether observed maintenance benefits stem from genuine uncertainty calibration or merely reflect trivial over-conservatism "
        "(e.g., arbitrarily replacing components early) [17], [20].",
        is_italic=True, space_after=160
    ))

    # Subsection 4.3 Table
    body_elements.append(p("4.3 Comparative Synthesis and Closest-Work Comparison Matrix", is_bold=True, size=24, space_after=160))
    body_elements.append(p("To delineate the precise boundaries between existing literature and the IntelliTwin framework, Table 1 provides a multi-dimensional comparative synthesis of the ten closest verified works cataloged in the repository corpus:"))

    table_headers = ["Study & Citation", "Asset Benchmark", "Base Architecture", "Uncertainty / Calibration", "Cond. Cov.?", "Cost Sim.?", "DT Comp.?", "Primary Boundary / Gap"]
    table_rows = [
        ["Wu et al. (2026) [15]", "CS2_35 Battery", "GA-Ensemble (RVM, RF, AR, LSTM)", "None (Deterministic Point)", "No", "No", "Yes", "Uncertainty formally identified as future work."],
        ["Chen et al. (2022) [17]", "Industrial Assets", "Parametric Regression", "Variance Modeling", "No", "Yes", "No", "Parametric uncertainty; no distribution-free bounds."],
        ["Zhu et al. (2025) [18]", "C-MAPSS Aero-Engine", "Deep Learning", "Monte Carlo Dropout", "No", "Yes", "No", "Gaussian assumptions; lacks conformal calibration."],
        ["Diao et al. (2026) [19]", "C-MAPSS FD001, FD002", "LSTM Quantile Regression", "Conformalized Quantile Reg (CQR)", "Yes", "No", "No", "Upstream of decision support; no cost simulation."],
        ["Walia & Kumar (2026) [20]", "NASA Turbofan", "CNN / GRU", "Quantile Reg + PPO Scheduling", "No", "Yes", "No", "Lacks finite-sample conformal calibration bounds."],
        ["Xu et al. (2026) [21]", "Degradation Data", "Deep Neural Network", "UQ & Calibration Framework", "No", "No", "No", "Framework focused on UQ; uncoupled from cost."],
        ["Yang et al. (2026) [22]", "PHME Bearings", "Representation Model", "Empirical Residual Calibration", "Yes", "Retros.", "No", "Post-hoc diagnostics; lacks prospective policy."],
        ["Javanmardi et al. (2023) [23]", "C-MAPSS Benchmark", "CNN & GBDT", "Split Conformal Prediction (ICP)", "No", "No", "No", "Strictly marginal coverage; no regime modeling."],
        ["Robinson (2026) [25]", "C-MAPSS FD001–FD004", "Gradient Boosting", "Asymmetric CQR Calibration", "Yes", "No", "No", "Lacks hierarchical engine weighting & matched controls."],
        ["BenAbdennour (2026) [26]", "Engine, Battery, Bearing", "Multi-Domain ML", "Interval-Safety Calibration", "Yes", "Safety", "No", "Diagnostic safety scoring; lacks cost optimization."],
        ["IntelliTwin (Proposed)", "C-MAPSS FD001/002/004", "HistGBR & PyTorch LSTM", "Decision-Aware Hierarchical Conformal", "Yes", "Yes (SCU)", "Yes (Replay)", "Jointly evaluates condition-adaptive calibration, sequential utility, and matched-conservatism controls."]
    ]
    body_elements.append(table_xml(table_headers, table_rows))

    # Subsection 4.4
    body_elements.append(p("4.4 Critical Methodological Observations and Research Gap Formulation", is_bold=True, size=24, space_after=160))
    body_elements.append(p("A rigorous analysis of Table 1 and the broader literature synthesis yields four foundational methodological observations that formally establish the research gap addressed by IntelliTwin:"))
    body_elements.append(li(
        "1.", "Fragmentation between Conformal Calibration and Operational Economics:",
        "Prior research has treated conformal RUL prediction [19], [23], [25] and uncertainty-aware maintenance optimization [17], [18], [20] as completely "
        "decoupled disciplines. Studies developing conformal prediction intervals evaluate their performance exclusively against statistical metrics such as "
        "Mean Prediction Interval Width (MPIW) or Winkler scores [19], [23], which do not reflect the asymmetric economic reality where catastrophic in-service "
        "engine failure costs dramatically outweigh scheduled overhaul expenses (C_FAIL >> C_PM) [1], [18]. Conversely, studies evaluating maintenance cost policies "
        "rely on parametric distributions (e.g., Gaussian assumptions in MC dropout) or heuristic quantile regression that lack finite-sample, distribution-free "
        "statistical coverage guarantees [18], [20]."
    ))
    body_elements.append(li(
        "2.", "Vulnerability of Marginal Conformal Guarantees Under Operational Shifts:",
        "Standard split conformal prediction provides guaranteed marginal coverage over the entire data population under the assumption of exchangeability [23], [29]. "
        "However, machine degradation telemetry violates exchangeability due to operating regime transitions (e.g., 6 distinct flight conditions in C-MAPSS FD002) "
        "and non-stationary wear accumulation [1], [22]. As demonstrated by Diao et al. [19] and Yang et al. [22], global calibration can satisfy a nominal 90% "
        "marginal coverage requirement across a fleet while simultaneously exhibiting severe, systematic undercoverage during high-stress operational regimes or "
        "critical terminal life stages (t -> Ti). In safety-critical aerospace operations, a localized failure rate of 30% during terminal wear stages is unacceptable, "
        "regardless of whether fleet-wide marginal coverage reaches 90%."
    ))
    body_elements.append(li(
        "3.", "Absence of Matched-Conservatism Attribution Controls:",
        "In prognostic decision frameworks that utilize lower prediction bounds Li(t) as replacement triggers, simple heuristic policies—such as arbitrarily widening "
        "prediction intervals, enforcing ad-hoc safety margins, or systematically shifting maintenance interventions to earlier flight cycles—can artificially eliminate "
        "catastrophic failures [17], [18]. However, this safety is purchased through extreme conservatism that squanders massive usable component life (C_WASTE) and "
        "inflates lifecycle expenditure [8], [18]. Existing prognostic literature almost universally fails to include matched-conservatism control baselines, leaving it "
        "fundamentally unverified whether observed maintenance improvements stem from genuine decision-aware uncertainty calibration or merely reflect trivial "
        "over-conservative early replacement [20]."
    ))
    body_elements.append(li(
        "4.", "Disconnection between Machine Learning Models and Digital Twin Platforms:",
        "While industrial surveys emphasize the transformative potential of Digital Twins for predictive maintenance [3], [13], deployed and prototype DT platforms "
        "(such as Wu et al. [15]) remain reliant on deterministic point predictions, treating uncertainty quantification as an unresolved future problem [14], [15]. "
        "There is an absence of reproducible Digital Twin architectures that integrate continuous telemetry streaming, causal feature windowing, and calibrated "
        "conformal uncertainty intervals into an actionable operator dashboard [3], [15]."
    ))

    body_elements.append(p("The Identified Research Gap", is_bold=True, size=24, space_after=120))
    body_elements.append(p(
        "Synthesizing these observations confirms the precise research gap formulated in the project's pre-registered research design (ADR-018):"
    ))
    body_elements.append(p(
        "\"Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware "
        "maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions "
        "and downstream sequential maintenance consequences while preserving reliable uncertainty coverage. Our study will therefore investigate whether "
        "decision-aware, condition-adaptive conformal calibration can improve maintenance utility without sacrificing subgroup reliability or merely becoming more conservative.\"",
        is_italic=True, space_after=160
    ))
    body_elements.append(p(
        "In strict adherence to academic integrity, IntelliTwin does not assert global novelty for conformal prediction, deep learning prognostics, or Digital Twin "
        "architectures individually. Rather, the project's scientific contribution lies in the method-level integration and rigorous empirical investigation of "
        "condition-adaptive conformal calibration coupled directly to sequential maintenance economics and audited against matched-conservatism baselines [19], [23], [30]."
    ))

    # References
    body_elements.append(p("References", is_bold=True, size=24, space_after=160))
    refs = [
        "[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, \"Damage propagation modeling for aircraft engine run-to-failure simulation,\" in Proc. 2008 Int. Conf. Prognostics and Health Management (PHM), IEEE, 2008, pp. 1–9, doi: 10.1109/PHM.2008.4711414.",
        "[2] D. Diana, Putri, and A. A. Mukti, \"AI-Driven Digital Twin for predictive maintenance in urban infrastructure: Enhancing structural resilience and sustainability,\" Civil Engineering Science and Technology, vol. 1, no. 1, pp. 63–74, 2025, doi: 10.51903/3c72e647.",
        "[3] Z. Huang, Y. Shen, J. Li, M. Fey, and C. Brecher, \"A survey on AI-driven digital twins in Industry 4.0: Smart manufacturing and advanced robotics,\" Sensors, vol. 21, no. 19, p. 6340, 2021, doi: 10.3390/s21196340.",
        "[4] S. Mazzetto, \"A review of urban digital twins integration, challenges, and future directions in smart city development,\" Sustainability, vol. 16, no. 19, p. 8337, 2024, doi: 10.3390/su16198337.",
        "[5] H. Wei, \"Digital twin and AI enabled predictive maintenance in building industry,\" Ph.D. dissertation, School of Mechanical and Aerospace Engineering, Nanyang Technological University, Singapore, 2024.",
        "[6] S. F. Bello, I. U. Wada, O. B. Ige, E. C. Chianumba, and S. A. Adebayo, \"AI-driven predictive maintenance and optimization of renewable energy systems for enhanced operational efficiency and longevity,\" International Journal of Science and Research Archive, vol. 13, no. 1, pp. 2823–2837, 2024, doi: 10.30574/ijsra.2024.13.1.1992.",
        "[7] A. Hosseinzadeh, F. F. Chen, M. Shahin, and H. Bouzary, \"A predictive maintenance approach in manufacturing systems via AI-based early failure detection,\" Manufacturing Letters, vol. 35, pp. 1179–1186, 2023, doi: 10.1016/j.mfglet.2023.08.125.",
        "[8] H. K. Shehadeh, \"Evaluating the impact of transitioning maintenance strategy from reactive to proactive in power generation companies: An empirical analysis,\" WSEAS Transactions on Business and Economics, vol. 21, pp. 838–856, 2024, doi: 10.37394/23207.2024.21.69.",
        "[9] V. Mousavi, M. Rashidi, M. Mohammadi, and B. Samali, \"Evolution of digital twin frameworks in bridge management: Review and future directions,\" Remote Sensing, vol. 16, no. 11, p. 1887, 2024, doi: 10.3390/rs16111887.",
        "[10] F. Brighenti, M. F. Bado, F. Romeo, and D. Zonta, \"Forecasting bridge damage within a predictive structural reliability-based DSS,\" Automation in Construction, vol. 168, p. 105740, 2024, doi: 10.1016/j.autcon.2024.105740.",
        "[11] M. Hisamuddin, M. T. Hussain, and R. Fatima, \"AI-driven digital twins for smart urban infrastructure: A comparative survey of monitoring and predictive maintenance methodologies,\" Khaja Bandanawaz University, Research Report, 2026.",
        "[12] A. K. M. R. Mahmud, R. I. Hriti, M. M. Hasan, M. N. Uddin, and A. R. Roy, \"AI-augmented digital twin architecture for predictive maintenance in smart urban infrastructure: A cross-domain engineering framework,\" European Journal of Applied Science, Engineering and Technology, vol. 3, no. 5, pp. 45–58, 2025, doi: 10.59324/ejaset.2025.3(5).04.",
        "[13] S. K. K. Hasan and C. W. Crawford, \"A new era for digital twins: Progress and industry adoption,\" Digital Twin, vol. 2, no. 4, p. 2555877, 2025, doi: 10.1080/27525783.2025.2555877.",
        "[14] B. P. Pathri and K. V. Ganduri, \"From smart cities to manufacturing: A comprehensive study on digital twin applications and barrier,\" IET Digital Twins and Applications, vol. 2, p. e70014, 2025, doi: 10.1049/dgt2.70014.",
        "[15] J. Wu, Y. Zhou, X. Wang, C. Chen, Y. Ma, and C. Zhang, \"Research on remaining useful life prediction of equipment based on digital twins,\" Sensors, vol. 26, no. 4, p. 1240, 2026, doi: 10.3390/s26041240.",
        "[16] M. A. Belay, A. Rasheed, and P. S. Rossi, \"Digital twin-driven communication-efficient federated anomaly detection for industrial IoT,\" Preprint submitted to IEEE / NTNU, 2026.",
        "[17] C. Chen, J. Shi, N. Lu, Z. H. Zhu, and B. Jiang, \"Data-driven predictive maintenance strategy considering the uncertainty in remaining useful life prediction,\" Neurocomputing, vol. 494, pp. 79–88, 2022, doi: 10.1016/j.neucom.2022.04.055.",
        "[18] Z. Zhu, L. Wang, M. Chen, and X. Zhao, \"Predictive maintenance strategies for aero-engines considering remaining useful life prediction interval,\" Quality and Reliability Engineering International, 2025, doi: 10.1002/qre.70043.",
        "[19] R. Diao, M. Zhou, G. Meng, and S. Wang, \"Turbofan engine remaining useful life prediction with reliable prediction intervals via LSTM-based quantile regression and conformal calibration,\" Sensors, vol. 26, no. 7, p. 2249, 2026, doi: 10.3390/s26072249.",
        "[20] G. K. Walia and M. Kumar, \"Uncertainty-aware remaining useful life prediction and PPO based optimal maintenance scheduling in industrial IoT,\" Reliability Engineering & System Safety, p. 112356, 2026, doi: 10.1016/j.ress.2026.112356.",
        "[21] W. Xu, S. Gao, Z. Wang, and E. Zio, \"A novel uncertainty-aware framework for remaining useful life prediction integrating uncertainty quantification and calibration,\" Reliability Engineering & System Safety, vol. 275, p. 112763, 2026, doi: 10.1016/j.ress.2026.112763.",
        "[22] S. Yang, J. Wang, and Y. Wang, \"Empirical calibration and conditional-reliability diagnostics for bearing RUL prediction under operating-regime shift,\" arXiv preprint arXiv:2607.08273, 2026.",
        "[23] A. Javanmardi and E. Hüllermeier, \"Conformal prediction intervals for remaining useful lifetime estimation,\" International Journal of Prognostics and Health Management, vol. 14, no. 2, pp. 1–14, 2023, doi: 10.36001/ijphm.2023.v14i2.3417.",
        "[24] H. Yan, \"Conformal prediction intervals for turbofan remaining useful life: An audit across operating regimes (code and run artifacts),\" Zenodo reproducibility artifact, DOI: 10.5281/zenodo.21330745, 2026.",
        "[25] C. D. Robinson, \"Remaining useful life estimation for aircraft engines with risk-aware prediction intervals via conformalized quantile regression,\" International Journal of Prognostics and Health Management, vol. 17, no. 1, p. 4724, 2026, doi: 10.36001/ijphm.2026.v17i1.4724.",
        "[26] A. BenAbdennour, \"Leakage-controlled grouped validation and interval-safety calibration for RUL/SOH prediction using engine, battery, and bearing degradation data,\" Machines, vol. 14, no. 10, p. 1124, 2026, doi: 10.3390/machines14101124.",
        "[27] D. Lakens, \"Equivalence tests: A practical primer for t tests, correlations, and meta-analyses,\" Social Psychological and Personality Science, vol. 8, no. 4, pp. 355–362, 2017, doi: 10.1177/1948550617697177.",
        "[28] T. Gneiting and A. E. Raftery, \"Strictly proper scoring rules, prediction, and estimation,\" Journal of the American Statistical Association, vol. 102, no. 477, pp. 359–378, 2007, doi: 10.1198/016214506000001437.",
        "[29] Y. Lee, R. F. Barber, and R. Willett, \"Distribution-free inference with hierarchical data,\" arXiv preprint arXiv:2306.06342, 2023.",
        "[30] S. Cortes-Gomez, C. M. Patiño, Y. Byun, S. Wu, E. Horvitz, and B. Wilder, \"Utility-directed conformal prediction: A decision-aware framework for actionable uncertainty quantification,\" in International Conference on Learning Representations (ICLR), 2025."
    ]
    for r in refs:
        body_elements.append(p(r, size=20, align="left", space_after=100))

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
{chr(10).join(body_elements)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="2160" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    fixed_time = (2026, 11, 1, 0, 0, 0)
    with zipfile.ZipFile(DOCX_PATH, "w") as z:
        for arcname, data in [
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", package_rels),
            ("word/_rels/document.xml.rels", doc_rels),
            ("word/styles.xml", styles_xml),
            ("word/document.xml", document_xml)
        ]:
            zinfo = zipfile.ZipInfo(arcname, date_time=fixed_time)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zinfo, data)

    print(f"Generated DOCX: {DOCX_PATH} ({os.path.getsize(DOCX_PATH)} bytes)")

if __name__ == "__main__":
    build_pdf()
    build_docx()
