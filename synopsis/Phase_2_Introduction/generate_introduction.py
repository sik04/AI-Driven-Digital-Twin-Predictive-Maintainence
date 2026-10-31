"""
Generator script for Phase 2: Introduction.
Compiles introduction.html to high-resolution introduction.pdf via Chrome Headless
and creates an editable OpenXML introduction.docx adhering to AKGEC formatting standards.
"""

import os
import subprocess
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "introduction.html")
PDF_PATH = os.path.join(SCRIPT_DIR, "introduction.pdf")
DOCX_PATH = os.path.join(SCRIPT_DIR, "introduction.docx")

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
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
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
        # escape XML
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

    def li(num_str, bold_prefix, text):
        xml_num = num_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml_bold = bold_prefix.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""    <w:p>
      <w:pPr>
        <w:ind w:left="720" w:hanging="360"/>
        <w:jc w:val="both"/>
        <w:spacing w:line="360" w:lineRule="auto" w:after="120"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t xml:space="preserve">{xml_num} </w:t>
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
    body_elements.append(p("1. Introduction", is_bold=True, size=28, space_after=240))

    # Subsection 1.1
    body_elements.append(p("1.1 Background", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "Industrial systems and high-capital engineering assets—most notably commercial aviation turbofan engines, "
        "heavy power generation turbines, and precision automated machinery—operate under demanding aerodynamic, thermal, "
        "and mechanical stress profiles. Sustaining uninterrupted operational availability while preventing catastrophic in-service "
        "degradation is a primary objective of modern industrial engineering and asset lifecycle management [1], [2]. Historically, "
        "industrial maintenance strategies have adhered to two traditional paradigms: reactive maintenance and preventive maintenance [3], [4]. "
        "In reactive (corrective or run-to-failure) maintenance, equipment is operated until a functional breakdown occurs. While this strategy "
        "extracts maximum operating life from individual components, unscheduled breakdowns in mission-critical machinery introduce severe "
        "flight disruptions, expensive secondary damage, and unacceptable safety hazards [1]. Conversely, conventional preventive (time-based "
        "or calendar-based) maintenance enforces component overhauls or replacements at predetermined, conservative operational intervals "
        "(such as fixed flight hours or operational cycles) [4]. Although preventive servicing substantially mitigates unexpected failures, "
        "it incurs immense economic waste, as healthy components exhibiting minimal wear are routinely retired with substantial usable life remaining [5]."
    ))
    body_elements.append(p(
        "To resolve this fundamental operational dilemma, Condition-Based Maintenance (CBM) and Predictive Maintenance (PdM) have emerged "
        "through the convergence of cyber-physical telemetry, comprehensive onboard sensor instrumentation, and advanced data analytics [2], [4]. "
        "Under the predictive maintenance paradigm, streaming multi-sensor observations—including rotational speeds, static and total gas path "
        "pressures, core temperatures, and fuel flow rates—are continuously monitored to track physical degradation and quantify Remaining Useful Life (RUL) [1], [6]. "
        "RUL represents the remaining operational duration (expressed in flight cycles or operating hours) before an asset breaches minimum acceptable "
        "structural or thermodynamic safety thresholds [1]. In parallel, Digital Twin (DT) technology has gained widespread prominence as an extensible "
        "computational architecture that constructs an accurate virtual representation of a physical asset, continuously synchronizing with streaming "
        "operational telemetry [2], [3]. Combined with artificial intelligence and machine learning (AI/ML), a predictive Digital Twin continuously "
        "ingests telemetry, tracks wear phenomena, estimates ongoing health indices, and delivers actionable, forward-looking maintenance intelligence "
        "to plant and fleet operators [2], [6]."
    ))

    # Subsection 1.2
    body_elements.append(p("1.2 Overview of IntelliTwin", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The IntelliTwin project formulates an AI-driven digital twin framework specifically designed for predictive maintenance and prognostic "
        "decision support in complex engineering assets. The framework investigates prognostics on commercial turbofan aircraft engines, utilizing "
        "the widely acknowledged Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) benchmark datasets developed by NASA [1]. The study "
        "focuses primarily on the complex, multi-regime degradation environments represented by subset FD002 (characterizing six distinct operating "
        "regimes and a single dominant high-pressure compressor failure mode), alongside subsets FD001 and FD004 for baseline control and robustness assessment [1], [7]."
    ))
    body_elements.append(p("Architecturally, the IntelliTwin framework comprises five modular layers:", space_after=120))
    body_elements.append(li("1.", "Data Preprocessing and Causal Windowing:",
        "Ingests raw multi-sensor telemetry, removes uninformative invariant sensors, performs training-only Z-score standardization, "
        "groups operating regimes via K-means clustering (k = 6), and extracts strictly causal 30-cycle backward lookback feature windows (W = 30) "
        "to prevent future-state data leakage [7]."))
    body_elements.append(li("2.", "Prognostic Base Predictors:",
        "Evaluates two complementary supervised learning paradigms for continuous RUL regression—a high-capacity non-neural tabular ensemble "
        "using Histogram Gradient Boosting Regressors (GBR) over flattened feature vectors, and a sequential recurrent neural network using "
        "unidirectional Long Short-Term Memory (LSTM) networks over multivariate time-series tensors [7], [8]."))
    body_elements.append(li("3.", "Uncertainty Quantification and Conformal Calibration:",
        "Implements an engine-weighted hierarchical split conformal calibration subsystem designed to construct finite-sample valid, distribution-free "
        "prediction intervals targeting a nominal 90% coverage level [9], [10]."))
    body_elements.append(li("4.", "Sequential Maintenance Decision Simulator:",
        "A discrete-event decision environment that translates predicted RUL intervals into concrete replacement decisions, penalizing maintenance "
        "actions using Standardized Cost Units (SCU) that weigh planned replacements against costly in-service failures and diagnostic inspections [6], [11]."))
    body_elements.append(li("5.", "Digital Twin Telemetry Replay Prototype:",
        "A trace-driven simulation replay service and web dashboard that emulates cycle-by-cycle sensor telemetry streaming, displays real-time health "
        "metrics, and visualizes calibrated prediction bounds [2], [3]."))
    body_elements.append(p(
        "Importantly, IntelliTwin is formally scoped and evaluated as an offline, trace-driven research prototype; the system does not assert physical "
        "IoT hardware deployment or live bidirectional engine actuation, focusing instead on methodological rigor and decision reliability [2]."
    ))

    # Subsection 1.3
    body_elements.append(p("1.3 Research Motivation", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "Despite substantial advances in deep learning for asset prognostics, the overwhelming majority of existing RUL models operate as deterministic "
        "point predictors [6], [8]. A deterministic model outputs a single scalar estimate ŷ (for instance, predicting an asset has exactly 15 cycles remaining) "
        "but provides no indication of predictive confidence or tail risk [9]. In safety-critical aerospace and industrial operations, relying exclusively "
        "on point predictions is hazardous [6], [11]. If an asset's true remaining life is subject to substantial variance, deferring maintenance based "
        "on an overconfident point estimate can result in sudden, catastrophic in-flight failure [1]. Conversely, underestimating RUL triggers premature "
        "servicing, squandering remaining component life and inflating operational budgets [5]."
    ))
    body_elements.append(p(
        "This asymmetry underscores the necessity of calibrated uncertainty quantification (UQ) that yields reliable prediction intervals "
        "C(x) = [L(x), U(x)] [7], [9]. However, traditional Bayesian and parametric UQ techniques (such as Gaussian Processes and Monte Carlo Dropout) "
        "rely heavily on restrictive distributional assumptions that rarely hold across complex, non-linear wear dynamics [9], [12]. While conformal "
        "prediction provides rigorous, distribution-free marginal coverage guarantees under data exchangeability [9], its application to degrading assets "
        "encounters critical domain challenges [7], [10]. Telemetry sequences within degrading engines are autocorrelated and non-exchangeable, creating "
        "risks of localized undercoverage during high-stress operational regimes or critical terminal life stages [10], [12]. Furthermore, downstream "
        "maintenance policies do not utilize prediction intervals symmetrically; replacement thresholds are predominantly triggered by the lower prediction "
        "bound L(x) [11]. A standard interval that widens symmetrically may achieve nominal coverage while severely inflating false-alarm costs, whereas "
        "an overly aggressive interval risks catastrophic missed failures [6], [11]."
    ))
    body_elements.append(p("Motivated by these challenges, IntelliTwin investigates the alignment between statistical conformal calibration and sequential maintenance economics, guided by four core research questions:", space_after=120))
    body_elements.append(li("•", "RQ1 (Maintenance Utility):", "Can decision-aware conformal RUL calibration reduce sequential maintenance costs while preserving reliable prediction-interval coverage?"))
    body_elements.append(li("•", "RQ2 (Subgroup Reliability):", "Can condition-adaptive calibration maintain acceptable coverage across distinct operating regimes and degradation stages without excessively expanding interval width?"))
    body_elements.append(li("•", "RQ3 (Decision-Value Attribution):", "Are maintenance cost differences attributable to genuine uncertainty calibration rather than trivial over-conservatism or arbitrary early replacement?"))
    body_elements.append(li("•", "RQ4 (Robustness and Generalization):", "Does the calibration framework generalize consistently across diverse base model architectures and operational datasets?"))

    # Subsection 1.4
    body_elements.append(p("1.4 Research Significance", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The research significance of the IntelliTwin initiative lies in bridging the foundational divide between distribution-free statistical uncertainty "
        "quantification and actionable industrial decision-making [9], [11]. By establishing a formal, reproducible methodology that links conformal "
        "nonconformity scores to downstream maintenance loss functions, the project contributes an evidence-based perspective on how prediction intervals "
        "can guide risk-informed replacement policies [6], [11]."
    ))
    body_elements.append(p(
        "From an academic perspective, the project enforces open-science principles, including strict pre-registration of experimental hypotheses, "
        "immutable baseline freezes, and complete split isolation to prevent data leakage [7]. From an industrial perspective, evaluating prognostic models "
        "within a standardized sequential cost simulator demonstrates how digital twin frameworks can systematically account for economic trade-offs "
        "between planned overhauls and unplanned breakdowns [2], [11]. In accordance with rigorous scientific practice, all hypotheses and prospective economic "
        "benefits are evaluated through pre-registered statistical protocols rather than assumed beforehand, ensuring that IntelliTwin provides an objective, "
        "verifiable contribution to the field of predictive maintenance [7], [10]."
    ))

    # References
    body_elements.append(p("References", is_bold=True, size=24, space_after=160))
    refs = [
        "[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, \"Damage propagation modeling for aircraft engine run-to-failure simulation,\" in 2008 International Conference on Prognostics and Health Management, IEEE, 2008, pp. 1–9, doi: 10.1109/PHM.2008.4711414.",
        "[2] Z. Huang, Y. Shen, J. Li, M. Fey, and C. Brecher, \"A survey on AI-driven digital twins in Industry 4.0: Smart manufacturing and advanced robotics,\" Sensors, vol. 21, no. 19, p. 6340, 2021, doi: 10.3390/s21196340.",
        "[3] F. Tao, H. Zhang, A. Liu, and A. Y. C. Nee, \"Digital twin in industry: State-of-the-art,\" IEEE Transactions on Industrial Informatics, vol. 15, no. 4, pp. 2405–2415, 2019, doi: 10.1109/TII.2018.2873186.",
        "[4] A. Fuller, Z. Fan, C. Day, and C. Barlow, \"Digital twin: Enabling technologies, challenges and open research,\" IEEE Access, vol. 8, pp. 108952–108971, 2020, doi: 10.1109/ACCESS.2020.3001836.",
        "[5] H. K. Shehadeh, \"Evaluating the impact of transitioning maintenance strategy from reactive to proactive in power generation companies: An empirical analysis,\" WSEAS Transactions on Business and Economics, vol. 21, pp. 838–856, 2024, doi: 10.37394/23207.2024.21.69.",
        "[6] C. Chen, J. Shi, N. Lu, Z. H. Zhu, and B. Jiang, \"Data-driven predictive maintenance strategy considering the uncertainty in remaining useful life prediction,\" Neurocomputing, vol. 494, pp. 79–88, 2022, doi: 10.1016/j.neucom.2022.04.055.",
        "[7] R. Diao, M. Zhou, G. Meng, and S. Wang, \"Turbofan engine remaining useful life prediction with reliable prediction intervals via LSTM-based quantile regression and conformal calibration,\" Sensors, vol. 26, no. 7, p. 2249, 2026, doi: 10.3390/s26072249.",
        "[8] M. Ma and Z. Mao, \"Deep-convolution-based LSTM network for remaining useful life prediction,\" IEEE Transactions on Industrial Informatics, vol. 17, no. 3, pp. 1658–1667, 2021, doi: 10.1109/TII.2020.2991796.",
        "[9] A. Javanmardi and E. Hüllermeier, \"Conformal prediction intervals for remaining useful lifetime estimation,\" International Journal of Prognostics and Health Management, vol. 14, no. 2, pp. 1–14, 2023, doi: 10.36001/ijphm.2023.v14i2.3417.",
        "[10] Y. Lee, R. F. Barber, and R. Willett, \"Distribution-free inference with hierarchical data,\" arXiv preprint arXiv:2306.06342, 2023.",
        "[11] S. Cortes-Gomez, C. M. Patiño, Y. Byun, S. Wu, E. Horvitz, and B. Wilder, \"Utility-directed conformal prediction: A decision-aware framework for actionable uncertainty quantification,\" in International Conference on Learning Representations (ICLR), 2025.",
        "[12] T. Gneiting and A. E. Raftery, \"Strictly proper scoring rules, prediction, and estimation,\" Journal of the American Statistical Association, vol. 102, no. 477, pp. 359–378, 2007, doi: 10.1198/016214506000001437."
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
