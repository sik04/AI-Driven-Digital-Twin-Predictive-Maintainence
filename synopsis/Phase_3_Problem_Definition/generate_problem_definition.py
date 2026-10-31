"""
Generator script for Phase 3: Problem Definition, Research Gap and Research Questions.
Compiles problem_definition.html to high-resolution problem_definition.pdf via Chrome Headless
and creates an editable OpenXML problem_definition.docx adhering to AKGEC formatting standards.
"""

import os
import subprocess
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "problem_definition.html")
PDF_PATH = os.path.join(SCRIPT_DIR, "problem_definition.pdf")
DOCX_PATH = os.path.join(SCRIPT_DIR, "problem_definition.docx")

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

    body_elements = []

    # Main Heading
    body_elements.append(p("3. Problem Definition, Research Gap and Research Questions", is_bold=True, size=28, space_after=240))

    # Subsection 3.1
    body_elements.append(p("3.1 Problem Statement", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "In modern industrial systems and mission-critical cyber-physical production environments, rotary engineering "
        "assets—most notably commercial aviation turbofan engines, industrial gas turbines, and high-load transmission "
        "assemblies—operate under relentless thermal gradients, mechanical fatigue, and variable aerodynamic stresses. "
        "Sustaining high operational availability while precluding in-service catastrophic failure constitutes the primary "
        "objective of Prognostics and Health Management (PHM) and Predictive Maintenance (PdM) [1], [2]."
    ))
    body_elements.append(p(
        "Formally, consider a fleet of industrial assets indexed by i in {1, 2, ..., N}. Each asset undergoes continuous "
        "physical degradation across discrete operational time cycles t in {1, 2, ..., Ti}, where Ti in N denotes the true, "
        "unobserved end-of-life cycle at which the machine suffers functional failure. At any operational cycle t, the true "
        "Remaining Useful Life (RUL) of asset i is defined as the remaining operational duration prior to terminal failure:"
    ))
    body_elements.append(p("yi(t) = Ti - t      (1)", is_italic=True, align="center", space_after=160))
    body_elements.append(p(
        "At each cycle t, onboard condition-monitoring sensors record a multivariate telemetry observation vector xi(t) in R^{dx} "
        "alongside external operating regime descriptors si(t) in R^{ds} (such as altitude, Mach number, and throttle settings) [1]. "
        "To ensure physical causality and prevent future-state data leakage, prognostic predictions at cycle t must depend strictly "
        "upon the causal historical trajectory up to time t, encapsulated by a fixed sliding window of length W:"
    ))
    body_elements.append(p("Xi(t) = [zi(t - W + 1), zi(t - W + 2), ..., zi(t)] in R^{W x (dx + ds)}      (2)", is_italic=True, align="center", space_after=160))
    body_elements.append(p("where zi(t) = [xi(t), si(t)] denotes the combined condition-setting feature vector at cycle t."))
    body_elements.append(p(
        "While standard machine learning approaches train a deterministic regression function f: R^{W x (dx + ds)} -> R+ to generate "
        "scalar point estimates y_hat_i(t) = f(Xi(t)), point predictions fail to capture aleatoric sensor noise and epistemic model "
        "uncertainty [3], [4]. In safety-critical industrial operations, predictive maintenance requires calibrated prediction intervals:"
    ))
    body_elements.append(p("C_{1-alpha}(Xi(t)) = [Li(t), Ui(t)]      (3)", is_italic=True, align="center", space_after=160))
    body_elements.append(p("targeting a pre-specified nominal marginal coverage probability 1 - alpha in (0, 1), such that:"))
    body_elements.append(p("P(yi(t) in [Li(t), Ui(t)]) >= 1 - alpha      (4)", is_italic=True, align="center", space_after=160))
    body_elements.append(p(
        "Crucially, predictive maintenance is not an isolated statistical estimation task; rather, prognostic intervals directly "
        "drive a sequential operational stopping time tau_i in {W, W+1, ...} at which the asset is retired for overhaul:"
    ))
    body_elements.append(p("tau_i = inf { t >= W : pi(C_{1-alpha}(Xi(t))) = MAINTAIN }      (5)", is_italic=True, align="center", space_after=160))
    body_elements.append(p(
        "where pi represents the operational maintenance policy. The resulting lifecycle economic cost incurred by asset i is governed by severe asymmetric penalties:"
    ))
    body_elements.append(p(
        "Ci(tau_i) = C_PM * 1(tau_i < Ti) + C_FAIL * 1(tau_i >= Ti) + C_WASTE * (Ti - tau_i) * 1(tau_i < Ti)      (6)",
        is_italic=True, align="center", space_after=160
    ))
    body_elements.append(p(
        "where C_PM represents the baseline cost of a scheduled preventive replacement, C_FAIL is the severe penalty associated with an unscheduled, "
        "catastrophic in-service breakdown (C_FAIL >> C_PM), and C_WASTE denotes the economic penalty per cycle of unutilized, discarded useful life [5], [6]. "
        "The central problem investigated by IntelliTwin is formulating an uncertainty-aware framework that connects condition-adaptive conformal RUL "
        "prediction intervals directly with this sequential stopping decision, systematically evaluating whether decision-aware calibration can enhance "
        "maintenance utility while preserving rigorous coverage guarantees [3], [7]."
    ))

    # Subsection 3.2
    body_elements.append(p("3.2 Limitations of Existing Approaches", is_bold=True, size=24, space_after=160))
    body_elements.append(p("A systematic audit of the contemporary prognostic and predictive maintenance literature reveals four major structural limitations in existing approaches:"))
    body_elements.append(li(
        "1.", "Pervasive Reliance on Uncalibrated Point Predictions:",
        "The overwhelming majority of deep learning and ensemble RUL models benchmark performance exclusively on symmetric loss metrics "
        "such as Mean Squared Error (MSE) or Root Mean Squared Error (RMSE) [1], [8]. Point estimators implicitly treat every prediction with uniform "
        "certainty, providing no probabilistic margin or tail risk quantification [3], [4]. In real-world asset management, overestimating RUL by 10 cycles "
        "produces catastrophic in-flight failure, whereas underestimating RUL by 10 cycles merely causes premature overhaul [1]. Point predictors are "
        "fundamentally incapable of communicating this operational asymmetry to plant decision-makers."
    ))
    body_elements.append(li(
        "2.", "Conditional Miscalibration and Subgroup Vulnerability:",
        "Conventional uncertainty quantification methods—including Gaussian Process regression, Monte Carlo dropout, and standard Inductive "
        "Conformal Prediction (ICP)—predominantly assume exchangeable or independent and identically distributed (i.i.d.) observations [4], [9]. "
        "However, machine degradation telemetry violates exchangeability due to profound temporal autocorrelation and operating regime transitions "
        "(e.g., multi-altitude flight envelopes in C-MAPSS FD002) [1], [3]. While global conformal calibration guarantees marginal coverage over the "
        "entire population, recent studies indicate that it frequently conceals severe conditional miscalibration, suffering systematic undercoverage "
        "during high-stress operating regimes or critical late-life degradation stages (t -> Ti) [3], [10]. An engine approaching its end-of-life may "
        "experience true coverage substantially below the nominal 1 - alpha target, creating hidden catastrophic operational hazards."
    ))
    body_elements.append(li(
        "3.", "Decoupling of Statistical Uncertainty from Downstream Decision Economics:",
        "In published prognostic research, uncertainty quantification and maintenance decision optimization are almost universally formulated "
        "as disjoint, uncoupled problems [6], [7]. Statistical calibrators are typically optimized to minimize symmetric interval width (MPIW) or "
        "Winkler interval loss [11], without accounting for the fact that downstream maintenance policies trigger replacement based predominantly "
        "on the conservative lower prediction bound Li(t) [6], [7]. Consequently, an interval calibration that appears statistically optimal under "
        "symmetric loss may trigger excessive false alarms in low-risk operational states or fail to provide adequate conservatism during critical wear phases."
    ))
    body_elements.append(li(
        "4.", "Conflation of Genuine Decision Value with Trivial Over-Conservatism:",
        "When maintenance policies employ lower confidence bounds to schedule overhauls, naive baselines—such as uniformly widening prediction intervals, "
        "adding ad-hoc point-prediction safety margins, or systematically shifting maintenance triggers to earlier flight cycles—can artificially eliminate "
        "in-service failures [6], [12]. However, this failure avoidance is achieved through extreme conservatism that squanders immense usable component "
        "life (C_WASTE) and inflates overall fleet lifecycle expenditure [5], [6]. Current literature lacks rigorous experimental controls to disambiguate "
        "whether observed maintenance cost reductions stem from informative, decision-aware uncertainty calibration or merely reflect trivial, over-conservative early replacement policies."
    ))
    body_elements.append(p(
        "Crucially, these limitations do not imply that all existing techniques fail simultaneously; rather, prior literature addresses these "
        "challenges in fragmented silos without a cohesive framework that unifies conditional calibration with downstream sequential maintenance utility [3], [6], [7]."
    ))

    # Subsection 3.3
    body_elements.append(p("3.3 Research Gap", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "Synthesizing the state-of-the-art across prognostic health management, conformal prediction, and maintenance optimization reveals a distinct research gap:"
    ))
    body_elements.append(p(
        "\"Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware "
        "maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating "
        "conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage. Our study will therefore "
        "investigate whether decision-aware, condition-adaptive conformal calibration can improve maintenance utility without sacrificing subgroup "
        "reliability or merely becoming more conservative.\"",
        is_italic=True, space_after=160
    ))
    body_elements.append(p("The boundaries of this research gap are delineated relative to verified prior art:"))
    body_elements.append(li(
        "•", "Javanmardi and Hüllermeier (2023) [4]:",
        "Evaluated split conformal prediction on C-MAPSS turbofan data, but focused strictly on marginal coverage without condition-adaptive scaling or downstream maintenance decision evaluation."
    ))
    body_elements.append(li(
        "•", "Diao et al. (2026) [3]:",
        "Integrated conformalized quantile regression (CQR) with LSTM networks on C-MAPSS FD001 and FD002, conducting life-stage analysis and target adaptation, but explicitly positioned their methodology upstream of prescriptive maintenance optimization."
    ))
    body_elements.append(li(
        "•", "Zhu et al. (2025) [5] & Walia and Kumar (2026) [8]:",
        "Modeled maintenance-cost optimization and reinforcement learning scheduling on aero-engine telemetry, but utilized parametric distributions or quantile heuristics that lack finite-sample, distribution-free coverage guarantees."
    ))
    body_elements.append(li(
        "•", "Robinson (2026) [10]:",
        "Developed asymmetric CQR prediction intervals across C-MAPSS subsets, but did not incorporate hierarchical engine-level weighting or benchmark against prespecified matched-conservatism baselines."
    ))
    body_elements.append(li(
        "•", "Cortes-Gomez et al. (2025) [7]:",
        "Introduced utility-directed conformal prediction in generic machine learning benchmarks, yet its formulation has not been investigated or established for the sequential, non-exchangeable degradation dynamics inherent to predictive maintenance digital twins."
    ))
    body_elements.append(p(
        "IntelliTwin does not assert absolute novelty for conformal prediction, deep prognostic modeling, or maintenance cost simulation in isolation; "
        "rather, the project investigates their method-level integration within a rigorous, pre-registered empirical framework."
    ))

    # Subsection 3.4
    body_elements.append(p("3.4 Proposed Research Questions", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "To investigate the identified research gap, the IntelliTwin research design establishes four formal, pre-registered research questions "
        "(RQ1–RQ4). In strict accordance with the project's frozen research protocol (ADR-018), the exact approved wording is preserved:"
    ))

    body_elements.append(p("Research Question 1 (RQ1)", is_bold=True, size=24, space_after=120))
    body_elements.append(p("Can a decision-aware, condition-adaptive conformal RUL calibration method improve sequential maintenance utility while preserving reliable prediction-interval coverage?", is_italic=True, space_after=120))
    body_elements.append(li(
        "•", "Investigation & Experiment Mapping:",
        "Evaluated via Experiment A, benchmarking the proposed decision-aware, condition-adaptive conformal calibration method against global conformal calibration and standard condition-aware calibration on C-MAPSS FD002 under the primary reference scenario (C_PM = 1.0, C_FAIL = 5.0, C_WASTE = 0.20) at 90% nominal coverage [1], [6]."
    ))
    body_elements.append(li(
        "•", "Evaluation Criteria:",
        "Primary outcome is total simulated maintenance cost contrast Delta_cost = Cost_B - Cost_P > 0.20 Standardized Cost Units (SCU) per engine over both baselines, subject to marginal and subgroup absolute coverage error ceilings E < 0.05 and non-increasing fleet failure rates."
    ))

    body_elements.append(p("Research Question 2 (RQ2)", is_bold=True, size=24, space_after=120))
    body_elements.append(p("Can the proposed method improve reliability across operating regimes and degradation conditions without excessively widening prediction intervals?", is_italic=True, space_after=120))
    body_elements.append(li(
        "•", "Investigation & Experiment Mapping:",
        "Evaluated via Experiment B, assessing conditional coverage and worst-group reliability across six discrete operating regimes and four degradation lifecycle quartiles on FD002 [1], [3]."
    ))
    body_elements.append(li(
        "•", "Evaluation Criteria:",
        "Primary outcome is worst-group conditional coverage error contrast Delta_error = WorstErr_B - WorstErr_P > 0.01 (1 percentage point), while restricting Mean Prediction Interval Width (MPIW) and Winkler interval score deterioration to under 1.0 cycle (D_width < 1.0, D_score < 1.0) [11]."
    ))

    body_elements.append(p("Research Question 3 (RQ3)", is_bold=True, size=24, space_after=120))
    body_elements.append(p("Are the maintenance benefits of the proposed method attributable to decision-aware uncertainty calibration rather than simply more conservative prediction intervals or earlier maintenance?", is_italic=True, space_after=120))
    body_elements.append(li(
        "•", "Investigation & Experiment Mapping:",
        "Evaluated via Experiment C, disambiguating true calibration decision value from naive conservatism by benchmarking against three prespecified matched-conservatism control families: widened prediction intervals, tuned point-prediction safety margins, and earlier-intervention heuristic policies [6]."
    ))
    body_elements.append(li(
        "•", "Evaluation Criteria:",
        "Primary outcome is achieving maintenance cost contrast Delta_cost > 0.20 SCU per engine against every prespecified matched-conservatism control family while preserving coverage constraints (E < 0.05)."
    ))

    body_elements.append(p("Research Question 4 (RQ4)", is_bold=True, size=24, space_after=120))
    body_elements.append(p("Does the proposed method retain its calibration and maintenance-decision benefits across operating conditions, base RUL predictors, datasets, and repeated experimental runs?", is_italic=True, space_after=120))
    body_elements.append(li(
        "•", "Investigation & Experiment Mapping:",
        "Evaluated via Experiment D, testing generalizability across a mandatory 6-cell configuration matrix: FD001 (single regime), FD002 (multi-regime), and FD004 (multi-regime, multi-fault) across both Gradient Boosted Regressors (GBR) and Long Short-Term Memory (LSTM) neural networks across five random seeds (2026–2030), weighted equally (1/6 each) [1]."
    ))
    body_elements.append(li(
        "•", "Evaluation Criteria:",
        "Primary outcome is achieving weighted aggregate improvements (Delta_cost > 0.20 SCU, Delta_error > 0.01) without exhibiting material harm (Delta_cost < -0.20 SCU, Delta_error < -0.01) in any individual configuration cell."
    ))

    # Subsection 3.5
    body_elements.append(p("3.5 Research Significance", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The research significance of the IntelliTwin initiative resides in establishing a mathematically principled, "
        "economically grounded methodology that bridges statistical uncertainty quantification with physical asset management:"
    ))
    body_elements.append(li(
        "1.", "Methodological Grounding:",
        "Conformal prediction provides finite-sample, distribution-free marginal coverage guarantees without relying on restrictive "
        "Gaussian or asymptotic assumptions [4], [9]. IntelliTwin extends this framework to address the temporal autocorrelation and operating "
        "regime shifts characteristic of turbofan engines, formulating engine-level cluster bootstrapping and family-wise error rate control "
        "(Bonferroni alpha = 0.05 / 4 = 0.0125) to preclude false discoveries [13]."
    ))
    body_elements.append(li(
        "2.", "Economic Alignment via Standardized Cost Units:",
        "Rather than evaluating prognostic algorithms solely on abstract statistical loss functions, IntelliTwin evaluates decision policies "
        "within a discrete-event sequential simulator governed by Standardized Cost Units (SCU) [5], [6]. This ensures that prediction intervals "
        "are judged directly by their operational efficacy in balancing planned maintenance against catastrophic breakdown."
    ))
    body_elements.append(li(
        "3.", "Open-Science Governance and Demarcation:",
        "In strict compliance with academic research integrity, all research questions, hypotheses, and decision criteria are pre-registered "
        "prior to confirmatory evaluation. The project explicitly distinguishes implemented engineering pipelines from experimental questions "
        "under empirical investigation. By establishing formal criteria for both supportive and non-supportive outcomes, IntelliTwin ensures that "
        "its empirical findings deliver unbiased, reproducible scientific value to the engineering community."
    ))

    # Subsection 3.6
    body_elements.append(p("3.6 Problem Scope and Boundaries", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "To maintain academic rigor and engineering precision, the experimental boundaries of the IntelliTwin framework are explicitly delineated based on repository evidence:"
    ))
    body_elements.append(li(
        "•", "Target Benchmark Assets:",
        "The study evaluates turbofan engine degradation utilizing the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) benchmark suite [1]: "
        "FD001 (1 condition, 1 fault mode; 100 train / 100 test engines, baseline control); "
        "FD002 (6 conditions, 1 fault mode; 260 train / 259 test engines, primary multi-regime benchmark); and "
        "FD004 (6 conditions, 2 fault modes; 249 train / 248 test engines, complex robustness benchmark)."
    ))
    body_elements.append(li(
        "•", "Feature Representation:",
        "In accordance with the project's verified schema, 6 invariant/non-informative sensor channels (indices 1, 5, 10, 16, 18, 19) are removed, "
        "leaving 14 active degradation sensor measurements alongside 3 operational setting descriptors (17 features total). Sensor values are standardized "
        "via training-only Z-score normalization (mean, std fitted solely on training splits with ddof = 0)."
    ))
    body_elements.append(li(
        "•", "Causal Windowing Protocol:",
        "Telemetry is processed into strictly causal backward sliding windows of length W = 30 cycles, completely barring future-cycle information."
    ))
    body_elements.append(li(
        "•", "Base Prognostic Models:",
        "Evaluates two distinct supervised learning paradigms: Histogram Gradient Boosting Regressors (HistGradientBoostingRegressor) over flattened "
        "30 x 17 = 510-dimensional vectors, and unidirectional PyTorch Long Short-Term Memory (LSTMRegressor) networks over 3D sequence tensors (B, 30, 17) [1], [8]."
    ))
    body_elements.append(li(
        "•", "Decision Simulator Parameters:",
        "Evaluated within a discrete-event sequential maintenance simulator under Standardized Cost Units (C_PM = 1.0, C_FAIL = 5.0, C_WASTE = 0.20 per cycle) [6]."
    ))
    body_elements.append(li(
        "•", "Explicit Scope Exclusions:",
        "No Live Physical Sensor Ingestion: The framework does not interface with live edge IoT hardware, physical sensor transceivers, or industrial "
        "fieldbus protocols (e.g., OPC UA, MQTT, Modbus). No Physical Closed-Loop Actuation: The framework does not transmit physical actuation signals "
        "or feedback control back into operational machinery. Digital Twin Scope: The Digital Twin is implemented as an offline, trace-driven simulation "
        "replay engine (TwinReplayEngine and FastAPI web service at port 8000) that streams historical C-MAPSS telemetry cycle-by-cycle at verified "
        "numerical parity (atol <= 1e-4), providing real-time prognostic dashboard visualization without physical back-coupling [2]."
    ))

    # References
    body_elements.append(p("References", is_bold=True, size=24, space_after=160))
    refs = [
        "[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, \"Damage propagation modeling for aircraft engine run-to-failure simulation,\" in 2008 International Conference on Prognostics and Health Management, IEEE, 2008, pp. 1–9, doi: 10.1109/PHM.2008.4711414.",
        "[2] Z. Huang, Y. Shen, J. Li, M. Fey, and C. Brecher, \"A survey on AI-driven digital twins in Industry 4.0: Smart manufacturing and advanced robotics,\" Sensors, vol. 21, no. 19, p. 6340, 2021, doi: 10.3390/s21196340.",
        "[3] R. Diao, M. Zhou, G. Meng, and S. Wang, \"Turbofan engine remaining useful life prediction with reliable prediction intervals via LSTM-based quantile regression and conformal calibration,\" Sensors, vol. 26, no. 7, p. 2249, 2026, doi: 10.3390/s26072249.",
        "[4] A. Javanmardi and E. Hüllermeier, \"Conformal prediction intervals for remaining useful lifetime estimation,\" International Journal of Prognostics and Health Management, vol. 14, no. 2, pp. 1–14, 2023, doi: 10.36001/ijphm.2023.v14i2.3417.",
        "[5] Z. Zhu, L. Wang, M. Chen, and X. Zhao, \"Predictive maintenance strategies for aero-engines considering remaining useful life prediction interval,\" Quality and Reliability Engineering International, 2025, doi: 10.1002/qre.70043.",
        "[6] C. Chen, J. Shi, N. Lu, Z. H. Zhu, and B. Jiang, \"Data-driven predictive maintenance strategy considering the uncertainty in remaining useful life prediction,\" Neurocomputing, vol. 494, pp. 79–88, 2022, doi: 10.1016/j.neucom.2022.04.055.",
        "[7] S. Cortes-Gomez, C. M. Patiño, Y. Byun, S. Wu, E. Horvitz, and B. Wilder, \"Utility-directed conformal prediction: A decision-aware framework for actionable uncertainty quantification,\" in International Conference on Learning Representations (ICLR), 2025.",
        "[8] G. K. Walia and M. Kumar, \"Uncertainty-aware remaining useful life prediction and PPO based optimal maintenance scheduling in industrial IoT,\" Reliability Engineering & System Safety, p. 112356, 2026, doi: 10.1016/j.ress.2026.112356.",
        "[9] Y. Lee, R. F. Barber, and R. Willett, \"Distribution-free inference with hierarchical data,\" arXiv preprint arXiv:2306.06342, 2023.",
        "[10] C. D. Robinson, \"Remaining Useful Life Estimation for Aircraft Engines with Risk-Aware Prediction Intervals via Conformalized Quantile Regression,\" International Journal of Prognostics and Health Management, vol. 17, no. 1, p. 4724, 2026, doi: 10.36001/ijphm.2026.v17i1.4724.",
        "[11] T. Gneiting and A. E. Raftery, \"Strictly proper scoring rules, prediction, and estimation,\" Journal of the American Statistical Association, vol. 102, no. 477, pp. 359–378, 2007, doi: 10.1198/016214506000001437.",
        "[12] A. BenAbdennour, \"Leakage-Controlled Grouped Validation and Interval-Safety Calibration for RUL/SOH Prediction Using Engine, Battery, and Bearing Degradation Data,\" Machines, vol. 14, no. 10, p. 1124, 2026, doi: 10.3390/machines14101124.",
        "[13] D. Lakens, \"Equivalence tests: A practical primer for t tests, correlations, and meta-analyses,\" Social Psychological and Personality Science, vol. 8, no. 4, pp. 355–362, 2017, doi: 10.1177/1948550617697177.",
        "[14] J. Wu, Y. Zhou, X. Wang, C. Chen, Y. Ma, and C. Zhang, \"Research on remaining useful life prediction of equipment based on digital twins,\" Sensors, vol. 26, no. 4, p. 1240, 2026, doi: 10.3390/s26041240."
    ]
    for r in refs:
        body_elements.append(p(r, size=21, align="left", space_after=120))

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

    with zipfile.ZipFile(DOCX_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", package_rels)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("word/styles.xml", styles_xml)
        z.writestr("word/document.xml", document_xml)

    print(f"Generated DOCX: {DOCX_PATH} ({os.path.getsize(DOCX_PATH)} bytes)")

if __name__ == "__main__":
    build_pdf()
    build_docx()

