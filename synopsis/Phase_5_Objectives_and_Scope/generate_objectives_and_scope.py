import os
import subprocess
import zipfile
import re

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(DIR, "objectives_and_scope.html")
PDF_PATH = os.path.join(DIR, "objectives_and_scope.pdf")
DOCX_PATH = os.path.join(DIR, "objectives_and_scope.docx")

def build_pdf():
    if not os.path.exists(CHROME_PATH):
        raise FileNotFoundError(f"Chrome not found at {CHROME_PATH}")
    html_uri = f"file:///{HTML_PATH.replace(os.sep, '/')}"
    cmd = [
        CHROME_PATH,
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

    def bq(text, size=24, space_after=200):
        xml_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""    <w:p>
      <w:pPr>
        <w:ind w:left="720" w:right="720"/>
        <w:jc w:val="both"/>
        <w:spacing w:line="360" w:lineRule="auto" w:after="{space_after}"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:i/><w:sz w:val="{size}"/></w:rPr>
        <w:t xml:space="preserve">{xml_text}</w:t>
      </w:r>
    </w:p>"""

    body_elements = []

    # Main Heading
    body_elements.append(p("5. Objectives and Scope", is_bold=True, size=28, space_after=240))

    # Subsection 5.1
    body_elements.append(p("5.1 Aim of the Project", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The overarching aim of the IntelliTwin research initiative is to design, implement, and rigorously evaluate an "
        "AI-driven Digital Twin framework that bridges the critical methodological division between data-driven Remaining "
        "Useful Life (RUL) prognostic regression, distribution-free uncertainty calibration, and sequential operational "
        "maintenance decision-making for safety-critical industrial rotational assets [1]–[3]. In modern cyber-physical production "
        "systems and aerospace operations, mechanical degradation processes are governed by highly non-linear kinematics, complex "
        "environmental stressors, and abrupt operational regime transitions [1], [4]. Traditional maintenance paradigms—predominantly "
        "calendar-based preventative maintenance (PM) or reactive run-to-failure corrective repairs—either squander substantial usable "
        "component life or expose critical infrastructure to catastrophic in-service breakdowns [5], [6]."
    ))
    body_elements.append(p(
        "While state-of-the-art prognostic frameworks leverage deep temporal neural networks and gradient-boosted decision trees to "
        "forecast RUL, they overwhelmingly operate as deterministic point predictors [3], [4], [13]. In operational environments "
        "characterized by severe asymmetric risk—where an unscheduled in-flight engine failure carries economic and safety costs orders "
        "of magnitude higher than a planned hangar overhaul—uncalibrated point estimates fail to communicate epistemic and aleatoric "
        "uncertainties to human operators [1], [5]. Furthermore, existing attempts to quantify prognostic uncertainty via parametric "
        "assumptions (e.g., Gaussian noise priors) or standard split conformal prediction frequently suffer from conditional miscalibration "
        "under operational regime shifts or decouple statistical interval metrics from downstream replacement economics [3], [7], [9]. "
        "IntelliTwin directly resolves these structural challenges by formulating a condition-adaptive, engine-weighted conformal calibration "
        "framework that explicitly optimizes sequential maintenance utility while preserving finite-sample coverage guarantees and "
        "providing trace-driven digital twin synchronization [2], [7], [14]."
    ))

    # Subsection 5.2
    body_elements.append(p("5.2 Primary Objective", is_bold=True, size=24, space_after=160))
    body_elements.append(p("The primary research objective of this B.Tech project is formally defined as:"))
    body_elements.append(bq(
        "\"To formulate, implement, and empirically validate an engine-weighted, condition-adaptive conformal calibration "
        "methodology for Remaining Useful Life (RUL) estimation that explicitly incorporates downstream sequential maintenance "
        "utility, achieving a statistically significant reduction in total lifecycle maintenance cost (exceeding 0.20 Standardized "
        "Cost Units per engine) while strictly preserving finite-sample prediction-interval coverage reliability across heterogeneous "
        "operating regimes without inducing trivial over-conservatism.\""
    ))
    body_elements.append(p(
        "This primary objective directly operationalizes the pre-registered research gap (ADR-018) and provides an empirical evaluation "
        "mechanism for Research Question 1 (RQ1) within a controlled, leakage-free benchmark setting [1], [7]."
    ))

    # Subsection 5.3
    body_elements.append(p("5.3 Specific Objectives", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "To accomplish the primary aim, the project is structured into eight concrete, measurable, and technically verifiable specific "
        "objectives traceable to the pre-registered research questions (RQ1–RQ4), statistical inference protocol, and software implementation architecture:"
    ))
    body_elements.append(li(
        "1.", "Systematic Telemetry Ingestion and Anti-Leakage Preprocessing:",
        "Ingest, clean, and standardize multi-regime multivariate run-to-failure telemetry from the NASA Commercial Modular Aero-Propulsion "
        "System Simulation (C-MAPSS) turbofan benchmark corpus [1]. Specifically prepare subset FD002 (primary multi-regime benchmark across six "
        "discrete operating conditions with high-pressure compressor degradation), subset FD001 (single-condition control benchmark), and "
        "subset FD004 (multi-regime, dual failure modes for robustness assessment). Implement a fixed 30-cycle causal sliding lookback window "
        "(W = 30 cycles), eliminate six invariant and uninformative sensor channels to retain an approved 17-feature schema (14 active degradation "
        "sensors plus three operational settings), apply training-only Z-score standardization, and enforce strict engine-level isolation across "
        "train, calibration, validation, and test subsets to completely eliminate temporal and cross-engine data leakage."
    ))
    body_elements.append(li(
        "2.", "Development and Checkpoint Freezing of Base Prognostic Predictors:",
        "Construct, optimize, and freeze two complementary machine learning prognostic regression model families exhibiting distinct inductive "
        "biases: (i) shallow non-linear ensemble models based on HistGradientBoostingRegressor (GBR) operating on flattened multi-sensor "
        "temporal features, and (ii) deep temporal neural networks based on PyTorch Long Short-Term Memory (LSTM) networks operating on sequential "
        "tensor sequences. Train, validate, and freeze a complete 30-model benchmark matrix spanning three datasets, two model families, and five "
        "official random seeds ([2026, 2027, 2028, 2029, 2030]) to guarantee 100% independent reproducibility across all downstream calibration stages."
    ))
    body_elements.append(li(
        "3.", "Formulation of Engine-Weighted Hierarchical Conformal Calibration:",
        "Implement an Inductive Conformal Prediction (ICP) calibration subsystem utilizing asymmetric nonconformity score inversion targeting "
        "a nominal 90% finite-sample prediction-interval coverage (1 - α = 0.90). Enhance standard conformal calibration with engine-level observation "
        "weighting to address within-engine temporal autocorrelation, and incorporate condition-adaptive calibration bins mapped to operating flight "
        "regimes and temporal lifecycle wear stages (t → Ti) to preserve conditional coverage validity where data exchangeability is violated [4], [9], [10]."
    ))
    body_elements.append(li(
        "4.", "Comprehensive Evaluation of Prediction Interval Validity and Sharpness:",
        "Evaluate the statistical validity, efficiency, and reliability of the generated conformal prediction intervals C_(1-α)(Xi(t)) = [Li(t), Ui(t)]. "
        "Quantify marginal empirical coverage, Mean Prediction Interval Width (MPIW), Winkler interval scores [11], and worst-subgroup conditional "
        "coverage error across operating regimes and degradation stages. Verify whether the proposed condition-adaptive calibration achieves significant "
        "reductions in conditional error (Δ_error > 0.01) without causing excessive interval widening or quality deterioration (D_width < 1.0 cycle, "
        "D_score < 1.0 cycle), directly addressing Research Question 2 (RQ2)."
    ))
    body_elements.append(li(
        "5.", "Discrete-Event Sequential Maintenance Utility Simulation:",
        "Develop and execute a cycle-by-cycle discrete-event sequential maintenance decision simulator governing engine retirement stopping times "
        "τi = inf { t ≥ W : π(C_(1-α)(Xi(t))) = MAINTAIN } triggered by lower conformal prediction bounds Li(t). Formalize maintenance economics in "
        "Standardized Cost Units (SCU) with asymmetric parameters reflecting industrial reality: preventive overhaul cost C_PM = 1.0, unscheduled "
        "catastrophic failure penalty C_FAIL = 5.0, and discarded usable life penalty C_WASTE = 0.20 per cycle. Quantify simulated lifecycle costs, "
        "fleet failure rates, and usable life utilization across diverse operating policies [5], [6], [8]."
    ))
    body_elements.append(li(
        "6.", "Decision-Value Attribution Analysis Against Matched-Conservatism Controls:",
        "Execute a controlled comparative attribution study contrasting the proposed decision-aware conformal framework against three prespecified "
        "matched-conservatism control baseline families: (i) widened prediction intervals, (ii) point-prediction safety margins, and (iii) earlier "
        "scheduled maintenance intervention heuristics. Empirically verify whether observed lifecycle cost improvements (Δ_cost > 0.20 SCU per engine) "
        "represent genuine decision-relevant uncertainty information rather than trivial, risk-averse early overhaul policies that artificially "
        "inflate component waste, addressing Research Question 3 (RQ3)."
    ))
    body_elements.append(li(
        "7.", "Cross-Condition, Multi-Model Robustness and Non-Harm Verification:",
        "Evaluate framework consistency across a six-cell confirmatory matrix (FD001, FD002, FD004 × GBR, LSTM across five seeds). Measure weighted "
        "aggregate utility contrasts alongside rigorous non-harm equivalence bounds (Δ_cost ≥ -0.20 SCU and Δ_error ≥ -0.01) across every individual "
        "evaluation cell under family-wise Bonferroni-corrected statistical significance (α = 0.05 / 4 = 0.0125) utilizing 10,000 engine-level "
        "cluster-bootstrap resamples [12], addressing Research Question 4 (RQ4)."
    ))
    body_elements.append(li(
        "8.", "Development and Validation of Digital Twin Synchronization Replay Prototype:",
        "Construct an operational software-based Digital Twin synchronization engine (TwinReplayEngine) capable of streaming multi-sensor degradation "
        "telemetry under causal lookback constraints with strict numerical parity (atol ≤ 10^-4 against offline batch execution). Couple the replay "
        "engine with a high-performance FastAPI REST API backend and an interactive HTML5/JavaScript operator dashboard that visualizes asset state "
        "trajectories, continuous RUL forecasts, dynamic health indices, calibrated conformal uncertainty bands, and real-time maintenance intervention triggers [2], [13], [14]."
    ))

    # Subsection 5.4
    body_elements.append(p("5.4 Scope of the Project", is_bold=True, size=24, space_after=160))
    body_elements.append(p("The scope of the IntelliTwin framework is rigorously defined across technical, operational, and computational dimensions:"))

    body_elements.append(p("1. Research and Application Domain", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "The investigation is situated within cyber-physical reliability engineering, machine learning for engineering prognostics, and Digital "
        "Twin-based operational decision support [2], [3]. The operational focus centers on industrial rotating machinery subject to continuous "
        "operational stress and wear degradation, using commercial aircraft gas turbine propulsion systems as the primary exemplar [1]."
    ))

    body_elements.append(p("2. Asset and Dataset Domain", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("The empirical corpus is derived exclusively from the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) benchmark suite [1]:"))
    body_elements.append(li(
        "•", "Subset FD002 (Primary Benchmark):",
        "Comprises 260 training engines and 259 test engines operating under complex combinations of six distinct flight conditions "
        "(altitude 0–42,000 ft, Mach number 0.0–0.84, throttle resolver angle 20–100) with high-pressure compressor (HPC) degradation. "
        "This serves as the primary dataset for condition-adaptive calibration and decision evaluation."
    ))
    body_elements.append(li(
        "•", "Subset FD001 (Single-Condition Control):",
        "Comprises 100 training and 100 test engines operating under sea-level static flight conditions with single-mode HPC degradation, "
        "providing a baseline control without regime shifts."
    ))
    body_elements.append(li(
        "•", "Subset FD004 (Multi-Regime / Multi-Fault Robustness):",
        "Comprises 249 training and 248 test engines operating under six flight conditions with complex dual failure modes (HPC and fan degradation), "
        "providing a rigorous stress-testing environment for cross-condition generalization."
    ))

    body_elements.append(p("3. Prognostic Task and Feature Representation", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "The modeling task is formulated as continuous Remaining Useful Life regression yi(t) = Ti - t for flight cycle t ≥ W. Telemetry features "
        "are structured into causal temporal sliding windows Xi(t) ∈ R^(W × 17) with fixed lookback W = 30 cycles. The feature schema comprises "
        "14 informative degradation sensor channels (total temperature, total pressure, bypass duct pressure, burner fuel-air ratio, physical "
        "and corrected core/fan speeds, static pressure, engine pressure ratio) and three operational settings. Six invariant sensor channels "
        "exhibiting zero variance or uninformative responses are excluded to prevent covariance degeneration."
    ))

    body_elements.append(p("4. Prognostic Architectures and Calibration Engine", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Prognostic regression is executed via scikit-learn HistGradientBoostingRegressor (GBR) using multi-quantile loss and PyTorch LSTM recurrent "
        "neural networks using mean squared error loss. Uncertainty calibration is implemented via Inductive Split Conformal Prediction with asymmetric "
        "nonconformity scores si(t) = max(Li(t) - yi(t), yi(t) - Ui(t)) calibrated at nominal 1 - α = 0.90 using engine-weighted empirical quantile estimators [4], [7], [9]."
    ))

    body_elements.append(p("5. Decision Simulation and Economic Metrics", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Operational decision evaluation is modeled through a sequential threshold replacement policy evaluated over complete run-to-failure "
        "trajectories in a discrete-event maintenance simulator. Primary evaluation metrics are formulated in Standardized Cost Units (SCU) "
        "under the reference scenario (C_PM = 1.0, C_FAIL = 5.0, C_WASTE = 0.20 per cycle). Statistical reliability metrics include marginal "
        "empirical coverage error, worst-group conditional coverage error across K-means operational clusters (k = 6) and piece-wise linear "
        "degradation stages, Mean Prediction Interval Width (MPIW), and Winkler interval scores [11]."
    ))

    body_elements.append(p("6. Software and Computational Environment", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "The software pipeline is implemented entirely in Python 3.12/3.13 utilizing NumPy, Pandas, Scikit-Learn, PyTorch, SciPy, and FastAPI. "
        "Computational experiments are verified on multicore CPU and CUDA GPU hardware architectures. Quality assurance is enforced via an "
        "automated test suite containing 37 pytest modules validating data loaders, windowing causality, split isolation, model inference, "
        "conformal calibration bounds, and simulator economics."
    ))

    # Subsection 5.5
    body_elements.append(p("5.5 Scope Boundaries and Limitations", is_bold=True, size=24, space_after=160))
    body_elements.append(p("To uphold academic integrity and prevent unsubstantiated claims, explicit boundaries and operational limitations are established:"))
    body_elements.append(li(
        "1.", "Trace-Driven Simulation vs. Live Hardware Ingestion:",
        "The Digital Twin implementation operates strictly as an offline trace-driven replay engine (TwinReplayEngine) streaming pre-recorded "
        "run-to-failure sensor trajectories. The scope excludes physical Internet-of-Things (IoT) edge hardware integration, live wireless sensor "
        "network deployment, and real-time physical communication bus protocols (e.g., CAN bus or ARINC 429)."
    ))
    body_elements.append(li(
        "2.", "Advisory Decision Support vs. Closed-Loop Actuation:",
        "The decision-support subsystem outputs predictive recommendations, risk alerts, and scheduled maintenance intervals for human fleet managers. "
        "It does not perform autonomous physical closed-loop actuator control, remote engine throttle modification, or automated shutdown sequencing."
    ))
    body_elements.append(li(
        "3.", "Benchmark Data vs. In-Flight Avionics Certification:",
        "The research evaluates simulated physics-based degradation models from the NASA C-MAPSS dataset. The framework is not certified under "
        "FAA or EASA DO-178C / DO-254 avionics software certification standards and has not undergone flight testing on commercial passenger aircraft."
    ))
    body_elements.append(li(
        "4.", "Pre-Registered Evaluation vs. Final Confirmatory Outcome Claims:",
        "The project methodology is strictly pre-registered under Architecture Decision Record ADR-018. The scope of this synopsis focuses on the "
        "mathematical formulation, algorithmic architecture, benchmark protocol, and validation pipeline. Experimental hypotheses (RQ1–RQ4) are "
        "framed as empirical questions under formal test rather than prematurely established positive results."
    ))

    # Subsection 5.6
    body_elements.append(p("5.6 Expected Scientific and Practical Contributions", is_bold=True, size=24, space_after=160))
    body_elements.append(p("The anticipated contributions of the IntelliTwin framework encompass:"))
    body_elements.append(li(
        "•", "Methodological Integration:",
        "Formulating a unified prognostic framework that couples condition-adaptive, engine-weighted conformal calibration directly with "
        "downstream sequential maintenance economics, eliminating the prevailing disconnection between statistical coverage metrics and industrial lifecycle costs [7], [8]."
    ))
    body_elements.append(li(
        "•", "Rigorous Matched-Control Attribution Protocol:",
        "Establishing a formal empirical benchmark that subjects prognostic maintenance policies to matched-conservatism controls, providing a "
        "replicable standard to disambiguate true uncertainty value from naive early-replacement conservatism."
    ))
    body_elements.append(li(
        "•", "Reproducible Open-Source Digital Twin Prototype:",
        "Delivering a modular, fully tested, and open-source software implementation integrating data-driven RUL forecasting, conformal "
        "calibration bounds, and discrete-event decision simulation with an interactive operator dashboard and validation parity ≤ 10^-4 [2], [14]."
    ))

    # References
    body_elements.append(p("References", is_bold=True, size=24, space_after=160))
    refs = [
        "[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, \"Damage propagation modeling for aircraft engine run-to-failure simulation,\" in Proc. 2008 Int. Conf. Prognostics and Health Management (PHM), IEEE, 2008, pp. 1–9.",
        "[2] Z. Huang, Y. Shen, J. Li, M. Fey, and C. Brecher, \"A survey on AI-driven digital twins in Industry 4.0: Smart manufacturing and advanced robotics,\" Sensors, vol. 21, no. 19, p. 6340, 2021.",
        "[3] R. Diao, M. Zhou, G. Meng, and S. Wang, \"Turbofan engine remaining useful life prediction with reliable prediction intervals via LSTM-based quantile regression and conformal calibration,\" Sensors, vol. 26, no. 7, p. 2249, 2026.",
        "[4] A. Javanmardi and E. Hüllermeier, \"Conformal prediction intervals for remaining useful lifetime estimation,\" Int. J. Progn. Health Manag., vol. 14, no. 2, pp. 1–14, 2023.",
        "[5] Z. Zhu, L. Wang, M. Chen, and X. Zhao, \"Predictive maintenance strategies for aero-engines considering remaining useful life prediction interval,\" Qual. Reliab. Eng. Int., 2025, doi: 10.1002/qre.70043.",
        "[6] C. Chen, J. Shi, N. Lu, Z. H. Zhu, and B. Jiang, \"Data-driven predictive maintenance strategy considering the uncertainty in remaining useful life prediction,\" Neurocomputing, vol. 494, pp. 79–88, 2022.",
        "[7] S. Cortes-Gomez, C. M. Patiño, Y. Byun, S. Wu, E. Horvitz, and B. Wilder, \"Utility-directed conformal prediction: A decision-aware framework for actionable uncertainty quantification,\" in Int. Conf. Learn. Represent. (ICLR), 2025.",
        "[8] G. K. Walia and M. Kumar, \"Uncertainty-aware remaining useful life prediction and PPO based optimal maintenance scheduling in industrial IoT,\" Reliab. Eng. Syst. Saf., p. 112356, 2026.",
        "[9] Y. Lee, R. F. Barber, and R. Willett, \"Distribution-free inference with hierarchical data,\" arXiv preprint arXiv:2306.06342, 2023.",
        "[10] C. D. Robinson, \"Remaining useful life estimation for aircraft engines with risk-aware prediction intervals via conformalized quantile regression,\" Int. J. Progn. Health Manag., vol. 17, no. 1, p. 4724, 2026.",
        "[11] T. Gneiting and A. E. Raftery, \"Strictly proper scoring rules, prediction, and estimation,\" J. Am. Stat. Assoc., vol. 102, no. 477, pp. 359–378, 2007.",
        "[12] D. Lakens, \"Equivalence tests: A practical primer for t tests, correlations, and meta-analyses,\" Soc. Psychol. Personal. Sci., vol. 8, no. 4, pp. 355–362, 2017.",
        "[13] J. Wu, Y. Zhou, X. Wang, C. Chen, Y. Ma, and C. Zhang, \"Research on remaining useful life prediction of equipment based on digital twins,\" Sensors, vol. 26, no. 4, p. 1240, 2026.",
        "[14] ISO 23247-1:2021, \"Automation systems and integration — Digital twin framework for manufacturing — Part 1: Overview and general principles,\" International Organization for Standardization, Geneva, Switzerland, 2021."
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
