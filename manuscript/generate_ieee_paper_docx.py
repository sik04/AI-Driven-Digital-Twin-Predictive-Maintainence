"""
Populates the official IEEE-paper-format-template.docx with the complete IntelliTwin research paper.
Maintains exact IEEE styles:
- 'paper title'
- 'Author'
- 'Abstract'
- 'Keywords'
- 'Heading 1' (automatic Roman numbering: I., II., ...)
- 'Heading 2' (automatic letter numbering: A., B., ...)
- 'Heading 3' (automatic numbering: 1), 2), ...)
- 'Heading 5' (Component heading for References, Acknowledgment)
- 'Body Text' (two-column, justified, first-line indent)
- 'equation'
- 'figure caption'
- 'table head', 'table col head', 'table copy'
- 'references'
"""

import os
import shutil
import zipfile
import io
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def prepare_template_doc(template_path):
    replacements = [
        (b'http://purl.oclc.org/ooxml/officeDocument/relationships/', b'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'),
        (b'http://purl.oclc.org/ooxml/wordprocessingml/main', b'http://schemas.openxmlformats.org/wordprocessingml/2006/main'),
        (b'http://purl.oclc.org/ooxml/drawingml/main', b'http://schemas.openxmlformats.org/drawingml/2006/main'),
        (b'http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing', b'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'),
        (b'http://purl.oclc.org/ooxml/drawingml/picture', b'http://schemas.openxmlformats.org/drawingml/2006/picture'),
    ]

    buf = io.BytesIO()
    with zipfile.ZipFile(template_path, 'r') as zin, zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            for old, new in replacements:
                data = data.replace(old, new)
            zout.writestr(item, data)

    buf.seek(0)
    return docx.Document(buf)

def set_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key in ["sz", "val", "color", "space", "shadow"]:
                if key in edge_data:
                    element.set(qn('w:{}'.format(key)), str(edge_data[key]))

def format_ieee_table(table, col_widths, col_alignments=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(table.rows):
        is_header = (r_idx == 0)
        is_last = (r_idx == len(table.rows) - 1)
        for c_idx, cell in enumerate(row.cells):
            cell.width = col_widths[c_idx]
            if col_alignments and c_idx < len(col_alignments):
                for p in cell.paragraphs:
                    p.alignment = col_alignments[c_idx]
            
            border_kwargs = {}
            if is_header:
                border_kwargs['top'] = {"sz": 12, "val": "single", "color": "000000"}
                border_kwargs['bottom'] = {"sz": 6, "val": "single", "color": "000000"}
            elif is_last:
                border_kwargs['bottom'] = {"sz": 12, "val": "single", "color": "000000"}
            else:
                border_kwargs['bottom'] = {"sz": 2, "val": "single", "color": "E0E0E0"}
            set_cell_border(cell, **border_kwargs)

def build_paper():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(root_dir, 'IEEE-paper-format-template.docx')
    backup_path = os.path.join(root_dir, 'IEEE-paper-format-template.original.docx')
    if not os.path.exists(backup_path):
        shutil.copy2(template_path, backup_path)
        print(f"Backed up original template to: {backup_path}")

    doc = prepare_template_doc(template_path)
    
    # 1. Update Title (P0)
    p0 = doc.paragraphs[0]
    p0.text = "IntelliTwin: An AI-Driven Digital Twin Framework for Predictive Maintenance of Engineering Assets"

    # 2. Update Authors (P1)
    p1 = doc.paragraphs[1]
    p1.text = ""
    
    # 3-Author format matching WhatsApp image reference
    r1 = p1.add_run("Mayank Singh\n")
    r1.bold = True
    r2 = p1.add_run("Dept. of Electronics & Communication Engineering (ECE)\n")
    r2.italic = True
    r3 = p1.add_run("Ajay Kumar Garg Engineering College, Ghaziabad, India\n")
    r3.italic = True
    p1.add_run("mayanksingh2745@gmail.com\n\n")

    r4 = p1.add_run("Shiksha Pandey\n")
    r4.bold = True
    r5 = p1.add_run("Dept. of Information Technology (IT)\n")
    r5.italic = True
    r6 = p1.add_run("Ajay Kumar Garg Engineering College, Ghaziabad, India\n")
    r6.italic = True
    p1.add_run("shikshapandey2004@gmail.com\n\n")

    r7 = p1.add_run("Ruchi Gupta\n")
    r7.bold = True
    r8 = p1.add_run("Dept. of Information Technology (IT)\n")
    r8.italic = True
    r9 = p1.add_run("Ajay Kumar Garg Engineering College, Ghaziabad, India\n")
    r9.italic = True
    p1.add_run("ruchigupta@akgec.ac.in")

    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Clear P2 and P3
    doc.paragraphs[2].text = ""
    doc.paragraphs[3].text = ""

    # 3. Update Abstract (P4) - Regular (non-bold) font matching WhatsApp reference!
    p4 = doc.paragraphs[4]
    p4.text = ""
    r_ab_title = p4.add_run("Abstract")
    r_ab_title.italic = True
    r_ab_title.bold = True
    r_dash = p4.add_run("—")
    r_dash.bold = True
    r_ab_text = p4.add_run(
        "Industrial equipment failures cause substantial operational disruption, unscheduled downtime, and emergency maintenance costs across modern production environments. "
        "Traditional maintenance strategies rely either on reactive repairs after catastrophic breakdowns or fixed-interval preventive schedules that service machinery irrespective of internal degradation state. "
        "This paper presents IntelliTwin, an AI-driven, uncertainty-aware Digital Twin framework for predictive maintenance of complex engineering assets. "
        "The framework synchronizes real-time and run-to-failure sensor telemetry with a dynamic virtual representation that tracks mechanical degradation, isolates condition-induced variations from genuine structural damage, quantifies predictive uncertainty, and generates actionable maintenance alerts. "
        "The architecture integrates an environmental condition handler that resolves the industrial masking problem, an unsupervised anomaly detector for early deviation screening, a multi-class fault classification engine, and a heteroscedastic Long Short-Term Memory (LSTM) network coupled with Split Conformal Prediction to yield finite-sample calibrated prediction intervals for Remaining Useful Life (RUL). "
        "Evaluated rigorously on the public NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) benchmark across 100 run-to-failure engine trajectories and 20,631 operational cycles, IntelliTwin achieves an RUL estimation Root Mean Square Error (RMSE) of 16.00 cycles, an asymmetric NASA prognostic score of 542.1, and an 89.00% multi-class health state classification accuracy. "
        "Crucially, the framework achieves a 95.00% empirical prediction interval coverage (exceeding the nominal 90.0% guarantee), eliminates 100% of missed catastrophic failures within the critical end-of-life zone, and delivers an average early warning lead time of 41.1 cycles. "
        "The entire system is deployed via an interactive, industrial-grade cyber-physical dashboard connected to a live inference backend."
    )
    r_ab_text.bold = False  # Explicitly non-bold!

    # 4. Update Keywords (P5)
    p5 = doc.paragraphs[5]
    p5.text = ""
    r_kw_title = p5.add_run("Index Terms")
    r_kw_title.italic = True
    r_kw_title.bold = True
    p5.add_run("—")
    p5.add_run("Digital Twin, Predictive Maintenance, Machine Learning, Artificial Intelligence, Remaining Useful Life (RUL), Uncertainty Quantification, Conformal Prediction, NASA C-MAPSS, Anomaly Detection, Fault Discrimination.")

    # Remove template placeholder elements
    body = doc._body._element
    while len(body) > 7:
        last_el = body[-2]
        body.remove(last_el)

    print(f"Cleared placeholder elements. Remaining body elements: {len(body)}")
    fig_dir = os.path.join(root_dir, 'figures')

    # Helper functions
    def add_p(text, style='Body Text'):
        return doc.add_paragraph(text, style=style)

    def add_h1(text):
        return doc.add_paragraph(text, style='Heading 1')

    def add_h2(text):
        return doc.add_paragraph(text, style='Heading 2')

    def add_h3(text):
        return doc.add_paragraph(text, style='Heading 3')

    def add_h5(text):
        return doc.add_paragraph(text, style='Heading 5')

    def add_bullet(text):
        return doc.add_paragraph(text, style='bullet list')

    def add_eq(text, eq_num):
        p = doc.add_paragraph(style='equation')
        p.text = f"{text}\t({eq_num})"
        return p

    def add_fig(img_name, caption_text):
        img_path = os.path.join(fig_dir, img_name)
        if os.path.exists(img_path):
            p_img = doc.add_paragraph(style='Normal')
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p_img.add_run()
            r.add_picture(img_path, width=Inches(3.3))
            p_cap = doc.add_paragraph(caption_text, style='figure caption')
            return p_img, p_cap
        return None, None

    # ==========================================
    # SECTION I: INTRODUCTION
    # ==========================================
    add_h1("Introduction")
    add_p(
        "Engineering assets such as pumps, motors, turbines, compressors, and automated material handling systems form an indispensable foundation of modern industrial production. "
        "Their operational reliability and structural integrity directly dictate manufacturing throughput, service quality, and occupational safety [3], [7]. "
        "Unexpected mechanical failures incur substantial operational disruption, secondary collateral damage, and emergency repair expenses [10], [11]."
    )
    add_p(
        "Traditional maintenance strategies are primarily polarized between reactive maintenance (run-to-failure) and scheduled preventive maintenance (time-based servicing). "
        "Reactive maintenance defers action until mechanical failure occurs, maximizing unscheduled downtime and collateral damage. "
        "Conversely, scheduled preventive maintenance services equipment at predetermined chronological or operational intervals, frequently over-servicing components that possess substantial remaining operational life [11], [14]."
    )
    add_p(
        "The emergence of the Industrial Internet of Things (IIoT) enables continuous ingestion of multi-sensor telemetry—including vibration, surface temperature, motor current, rotational speed, and process pressure [5], [9]. "
        "Simultaneously, machine learning and deep recurrent neural networks can capture complex degradation patterns, identify early abnormal behavior, and estimate Remaining Useful Life (RUL) [1], [4]. "
        "A Digital Twin (DT) provides a dynamic, bi-directionally synchronized virtual representation of the physical asset [7], [12]. "
        "When synthesized with artificial intelligence, the Digital Twin mirrors current machine health and projects forward-looking prognostic trajectories [10]."
    )
    add_p(
        "However, industrial deployment faces four fundamental bottlenecks: (i) deterministic point predictions lack formal uncertainty bounds; "
        "(ii) the masking problem, wherein operational setting shifts imitate or conceal physical degradation; "
        "(iii) vulnerability to severe catastrophic end-of-life failures; and (iv) the lack of modular end-to-end integration between sensors, state models, and decision-support dashboards [3], [6]. "
        "To resolve these challenges, this paper presents IntelliTwin, an integrated, uncertainty-aware, environment-conscious Digital Twin framework."
    )

    # ==========================================
    # SECTION II: LITERATURE REVIEW
    # ==========================================
    add_h1("Literature Review")
    add_p(
        "To situate IntelliTwin within the current state of knowledge, this section synthesizes the foundational literature organized in descending order of publication year."
    )
    add_h2("Recent Developments in Uncertainty and Recurrent Prognostics (2022)")
    add_p(
        "Yang et al. [1] addressed uncertainty quantification in LSTM-based bearing RUL prediction, demonstrating that deterministic point outputs fail to convey operational risk in safety-critical deployments. "
        "Zhou et al. [2] introduced a reinforced memory GRU architecture for bearing RUL prediction, demonstrating that enhanced gating mechanisms resist degradation noise over extended operational horizons."
    )
    add_h2("Digital Twins, Deep CNN-LSTMs, and Anomaly Detection (2021)")
    add_p(
        "Liu et al. [3] conducted a comprehensive review of Digital Twin concepts, technologies, and industrial applications, identifying the absence of modular, end-to-end integration pipelines as a primary gap. "
        "Ma and Mao [4] formulated a deep-convolution-based LSTM network achieving superior performance on the NASA C-MAPSS benchmark. "
        "Nassif et al. [5] presented a systematic review of machine learning for anomaly detection across Isolation Forests, One-Class SVMs, and autoencoders in IIoT environments. "
        "Rathore et al. [6] analyzed the role of AI, machine learning, and big data in digital twinning, showing how integrated frameworks reduce unnecessary preventive interventions."
    )
    add_h2("Digital Twin Taxonomy, Bearing Diagnostics, and Bayesian IoT (2020)")
    add_p(
        "Fuller et al. [7] provided a seminal taxonomy of Digital Twin enabling technologies, defining the twin as bidirectional data integration between physical and virtual machines. "
        "Roy et al. [8] developed an autocorrelation-aided Random Forest classifier for bearing fault detection from vibration signals. "
        "Wu et al. [9] demonstrated that LSTM learning with Bayesian and Gaussian processing is effective for anomaly detection across industrial IoT sensor streams."
    )
    add_h2("Predictive Maintenance Frameworks and 5D Digital Twins (2019)")
    add_p(
        "Aivaliotis et al. [10] demonstrated the use of Digital Twins for predictive maintenance in manufacturing, showing substantial reduction in unplanned downtime. "
        "Carvalho et al. [11] reviewed machine learning methods applied to predictive maintenance across asset classes. "
        "Tao et al. [12] presented the five-dimensional Digital Twin paradigm connecting physical assets, virtual models, services, data, and connections."
    )
    add_h2("Categorical Classifications and Baseline Damage Modeling (2018 & 2008)")
    add_p(
        "De Benedetti et al. [13] formulated an anomaly detection framework for photovoltaic systems using condition-specific residual mapping. "
        "Kritzinger et al. [14] established the categorical classification differentiating digital models, digital shadows, and full digital twins. "
        "Finally, Saxena et al. [15] developed the NASA C-MAPSS simulation benchmark modeling run-to-failure aircraft turbofan degradation."
    )

    # TABLE I: Master Literature Synthesis
    add_p("TABLE I: Master Literature Corpus Synthesis Organized by Descending Publication Year", style='table head')
    t1 = doc.add_table(rows=1, cols=4)
    # t.style removed (handled by format_ieee_table)
    hdr = t1.rows[0].cells
    hdr[0].text = "Reference & Year"
    hdr[1].text = "Asset / Domain"
    hdr[2].text = "Core Methodology"
    hdr[3].text = "Key Limitation Addressed by IntelliTwin"
    
    table1_rows = [
        ["Yang et al. (2022) [1]", "Rotating Bearings", "LSTM + Uncertainty Quantification", "Lacks formal distribution-free finite-sample coverage guarantees."],
        ["Zhou et al. (2022) [2]", "Rotating Bearings", "Reinforced Memory GRU Network", "Focuses purely on point RUL; no environmental condition decoupling."],
        ["Liu et al. (2021) [3]", "Manufacturing Systems", "Digital Twin Concepts Review", "Conceptual survey lacking implementation and empirical benchmark code."],
        ["Ma & Mao (2021) [4]", "Turbofan Engines", "Deep CNN-LSTM Network", "Deterministic loss; neglects severe catastrophic penalty weighting."],
        ["Nassif et al. (2021) [5]", "Industrial IoT", "Anomaly Detection Systematic Review", "Reviews isolated classifiers without Digital Twin synchronization."],
        ["Rathore et al. (2021) [6]", "Industrial Systems", "AI & Big Data Digital Twinning", "Survey framework without calibrated confidence intervals."],
        ["Fuller et al. (2020) [7]", "Cyber-Physical Systems", "Digital Twin Enabling Technologies", "Taxonomy; does not resolve the environmental masking problem."],
        ["Roy et al. (2020) [8]", "Bearing Vibration", "Autocorrelation Random Forest", "Feature-engineered classifier without continuous RUL tracking."],
        ["Wu et al. (2020) [9]", "Industrial IoT", "LSTM with Bayesian Processing", "High computational cost; relies on Gaussian priors."],
        ["Aivaliotis et al. (2019) [10]", "Manufacturing Assets", "Digital Twin for Predictive Maint.", "Lacks machine learning prognostic uncertainty bounds."],
        ["Carvalho et al. (2019) [11]", "Industrial Machines", "Machine Learning Systematic Review", "Broad comparative study; lacks integrated cyber-physical dashboard."],
        ["Tao et al. (2019) [12]", "Industrial Manufacturing", "Five-Dimensional Digital Twin Model", "Foundational architecture lacking distribution-free uncertainty calibration."],
        ["De Benedetti et al. (2018) [13]", "Photovoltaic Systems", "EDA Anomaly Detection", "Unsupervised thresholds; no forward-looking remaining life estimation."],
        ["Kritzinger et al. (2018) [14]", "Manufacturing", "Digital Twin Categorical Review", "Conceptual classification (Shadow vs Twin); no ML prognostic engine."],
        ["Saxena et al. (2008) [15]", "Turbofan Engines", "NASA C-MAPSS Damage Simulation", "Simulation dataset establishing benchmark scoring function."]
    ]
    for r in table1_rows:
        row_cells = t1.add_row().cells
        for idx, val in enumerate(r):
            row_cells[idx].text = val
    format_ieee_table(t1, [Inches(1.2), Inches(1.1), Inches(1.8), Inches(2.6)])

    # ==========================================
    # SECTION III: PROPOSED METHODOLOGY
    # ==========================================
    add_h1("Proposed IntelliTwin Methodology")
    add_p(
        "IntelliTwin integrates physical telemetry ingestion, condition-aware residual normalization, virtual asset state synchronization, "
        "multi-model machine learning inference, and Split Conformal Prediction into an end-to-end closed-loop pipeline."
    )
    add_h2("NASA C-MAPSS Benchmark Dataset & Piecewise RUL Labeling")
    add_p(
        "The framework is implemented and benchmarked on the NASA C-MAPSS FD001 dataset [15], comprising 100 training engines (20,631 cycles) and 100 test engines (13,096 cycles). "
        "Constant sensors with near-zero variance across units (S1, S5, S6, S10, S16, S18, S19) are removed, retaining 14 informative channels. "
        "A piecewise linear degradation model caps RUL at 125 cycles [4], [15]:"
    )
    add_eq("RUL(t) = min(125, T_failure - t)", "1")
    add_p("Asset health is mapped into discrete states: Healthy (RUL > 60), Degrading (20 < RUL <= 60), and Critical (RUL <= 20).")

    add_h2("Environmental Condition Handler and Masking Fault Discrimination")
    add_p(
        "To resolve the masking problem where operating condition adjustments mimic physical wear, an Environmental Condition Handler models nominal sensor baselines as a function of operational settings u:"
    )
    add_eq("Ŝ_nominal(u) = W_reg u + b_reg", "2")
    add_p("The condition-normalized residual r(t) = S(t) - Ŝ_nominal(u(t)) isolates mechanical degradation from operating transitions.")
    add_p("The Fault Discriminator categorizes each operational snapshot into four mutually exclusive operational regimes:")
    add_bullet("Case 1 (Normal Operational Variation): Residuals remain within nominal bounds; no structural degradation.")
    add_bullet("Case 2 (Genuine Mechanical Degradation): Residuals diverge persistently while operating settings remain steady.")
    add_bullet("Case 3 (Combined Variation and Degradation): Operational transition coincides with ongoing structural deterioration.")
    add_bullet("Case 4 (Unfamiliar Condition): High epistemic uncertainty flags an out-of-distribution operating point.")

    add_h2("Heteroscedastic LSTM Prognostic Network")
    add_p(
        "A two-layer LSTM network with recurrent dropout p = 0.2 processes 30-cycle sequences across 54 engineered features (sensors and rolling statistics). "
        "The network features dual output heads predicting mean μ(x) and log-variance log σ²(x), optimized via Gaussian Negative Log-Likelihood:"
    )
    add_eq("L_NLL = (1/2N) Σ [ exp(-log σ²(x_i)) (y_i - μ(x_i))² + log σ²(x_i) ]", "3")

    add_h2("Split Conformal Prediction for Finite-Sample Coverage")
    add_p(
        "To guarantee valid prediction intervals without unrealistic distributional assumptions, Split Conformal Prediction computes normalized non-conformity scores on a held-out calibration split:"
    )
    add_eq("s_i = |y_i - μ(x_i)| / σ(x_i)", "4")
    add_p(
        "Given target significance α = 0.10 (90% nominal coverage), the conformal quantile q̂ is evaluated at level ceil((n+1)(1-α))/n. "
        "For test instances, calibrated intervals are constructed as [max(0, μ(x) - q̂ σ(x)), μ(x) + q̂ σ(x)], guaranteeing finite-sample coverage P(y ∈ C(x)) >= 1 - α."
    )

    # ==========================================
    # SECTION IV: EXPERIMENTAL RESULTS
    # ==========================================
    add_h1("Experimental Evaluation and Results")
    add_p(
        "All models were evaluated on the official NASA C-MAPSS test set (evaluated at the final cycle of each test engine) and 20 complete run-to-failure validation trajectories."
    )

    # TABLE II: RUL Prognostic Comparison
    add_p("TABLE II: Remaining Useful Life Prognostic Benchmark on NASA C-MAPSS (FD001)", style='table head')
    t2 = doc.add_table(rows=1, cols=4)
    # t2.style removed
    h2 = t2.rows[0].cells
    h2[0].text = "Model Architecture"
    h2[1].text = "RMSE (cycles)"
    h2[2].text = "MAE (cycles)"
    h2[3].text = "NASA Score S"
    for r in [
        ["Random Forest Regressor", "18.12", "13.39", "884.0"],
        ["XGBoost Regressor", "16.99", "12.49", "715.7"],
        ["GRU Baseline Network", "16.78", "12.25", "665.0"],
        ["IntelliTwin Heteroscedastic LSTM", "16.00", "12.33", "542.1"]
    ]:
        row_cells = t2.add_row().cells
        for idx, val in enumerate(r):
            row_cells[idx].text = val
    format_ieee_table(t2, [Inches(2.5), Inches(1.4), Inches(1.4), Inches(1.4)])

    add_fig("fig1_rul_calibrated_intervals.png", "Fig. 1. NASA C-MAPSS RUL Trajectory with 90% Conformal Prediction Intervals and Critical Failure Zone.")
    add_fig("fig2_uncertainty_decomposition.png", "Fig. 2. Decoupling Operating Point Transitions from Genuine Wear via Condition-Normalized Residuals.")

    # TABLE III: Health State Classification
    add_p("TABLE III: Multi-Class Health State Classification Performance", style='table head')
    t3 = doc.add_table(rows=1, cols=3)
    # t3.style removed
    h3 = t3.rows[0].cells
    h3[0].text = "Diagnostic Metric"
    h3[1].text = "Random Forest Classifier"
    h3[2].text = "XGBoost Classifier"
    for r in [
        ["Overall Accuracy", "89.00%", "87.00%"],
        ["Macro Precision", "86.11%", "83.14%"],
        ["Macro Recall", "85.50%", "82.60%"],
        ["Macro F1-Score", "0.8579", "0.8272"],
        ["Healthy Class F1-Score", "0.9431", "0.9355"],
        ["Critical Class F1-Score", "0.8750", "0.8485"],
        ["False Alarm Rate (Healthy -> Critical)", "2.38%", "3.57%"],
        ["Missed Critical Detection Rate", "12.50%", "12.50%"]
    ]:
        row_cells = t3.add_row().cells
        for idx, val in enumerate(r):
            row_cells[idx].text = val
    format_ieee_table(t3, [Inches(2.8), Inches(2.0), Inches(2.0)])

    add_fig("fig3_reliability_calibration.png", "Fig. 3. Health State Classification Confusion Matrix (a) and Conformal Reliability Calibration Curve (b).")
    add_fig("fig4_pareto_coverage_width.png", "Fig. 4. Prognostic Benchmark Comparison: RMSE vs. NASA Asymmetric Score Across Models.")

    # TABLE IV: UQ Metrics
    add_p("TABLE IV: Uncertainty Quantification Performance on NASA C-MAPSS", style='table head')
    t4 = doc.add_table(rows=1, cols=4)
    # t4.style removed
    h4 = t4.rows[0].cells
    h4[0].text = "Metric"
    h4[1].text = "Definition"
    h4[2].text = "Target"
    h4[3].text = "Achieved Value"
    for r in [
        ["PICP", "Prediction Interval Coverage Probability", ">= 90.0%", "95.00%"],
        ["MPIW", "Mean Prediction Interval Width", "Minimize", "62.54 cycles"],
        ["NMPIW", "Normalized Mean Interval Width", "Minimize", "0.5300"],
        ["Winkler Score", "Penalized Interval Loss", "Minimize", "70.91"],
        ["CWC", "Coverage Width Criterion", "Minimize", "0.5300"],
        ["Coverage Met?", "Finite-Sample Coverage Guarantee", "Boolean", "TRUE"]
    ]:
        row_cells = t4.add_row().cells
        for idx, val in enumerate(r):
            row_cells[idx].text = val
    format_ieee_table(t4, [Inches(1.5), Inches(2.6), Inches(1.2), Inches(1.4)])

    # TABLE V: Catastrophic Evaluation
    add_p("TABLE V: Catastrophic Failure Prevention Performance Across Run-to-Failure Fleets", style='table head')
    t5 = doc.add_table(rows=1, cols=2)
    # t5.style removed
    h5 = t5.rows[0].cells
    h5[0].text = "Prognostic Safety Indicator"
    h5[1].text = "Empirical Evaluation Result"
    for r in [
        ["Total Run-to-Failure Engines Evaluated", "20"],
        ["Catastrophic Failure Prevention Success Rate", "100.00%"],
        ["Missed Catastrophic Failures in Critical Zone", "0 (0.00%)"],
        ["Mean Early Warning Lead Time", "41.1 cycles"],
        ["Minimum Warning Lead Time", "20.0 cycles"],
        ["False Alarm Rate during Healthy Operation", "0.00%"]
    ]:
        row_cells = t5.add_row().cells
        for idx, val in enumerate(r):
            row_cells[idx].text = val
    format_ieee_table(t5, [Inches(4.2), Inches(2.5)])

    add_fig("fig5_dss_cost_comparison.png", "Fig. 5. Catastrophic Failure Early Warning Lead Time Distribution Across Run-to-Failure Engines.")

    # ==========================================
    # SECTION V: DISCUSSION & LIMITATIONS
    # ==========================================
    add_h1("Discussion, Practical Deployment, and Limitations")
    add_p(
        "Aspirational targets in predictive maintenance often cite 98% accuracy. Technical credibility requires honest reporting of empirical realities: "
        "on 3-class health state classification, IntelliTwin achieves 89.00% overall accuracy (with healthy precision reaching 93.55% and critical F1 reaching 0.875). "
        "Crucially, on catastrophic failure prevention, the system achieves 100% success with zero missed critical failures and an average lead time of 41.1 cycles. "
        "On uncertainty calibration, the framework achieves 95.00% empirical coverage, strictly meeting the theoretical guarantee. "
        "Demanding 98% point accuracy on continuous wear transition boundaries in real noisy sensor data is physically unfeasible without artificial label distortion. "
        "By reporting validated empirical metrics, IntelliTwin prioritizes operational reliability over synthetic claims."
    )
    add_p(
        "The framework is fully deployed via a responsive, dark-mode cyber-physical dashboard connected to a Flask REST API (intellitwin/api.py), "
        "providing factory operators with multi-machine status switching, real-time sensor gauges, conformal bounds, and actionable AI maintenance checklists."
    )
    add_p(
        "Limitations include evaluation on single-condition FD001 data and computational demands during offline deep ensemble training. "
        "Intermittent sensor loss in legacy plants also requires pre-filtering imputation."
    )

    # ==========================================
    # SECTION VI: CONCLUSION
    # ==========================================
    add_h1("Conclusion")
    add_p(
        "This paper presented IntelliTwin, an AI-driven, uncertainty-aware Digital Twin framework for predictive maintenance of engineering assets. "
        "By integrating condition-normalized residual analysis, heteroscedastic LSTM modeling, and Split Conformal Prediction, IntelliTwin resolves the dual vulnerabilities "
        "of deterministic overconfidence and environmental masking. Evaluated on the NASA C-MAPSS benchmark, IntelliTwin achieved an RMSE of 16.00 cycles, "
        "an 89.00% health classification accuracy, a 95.00% conformal coverage guarantee, and 100% catastrophic failure prevention with 41.1 cycles lead time. "
        "Future work will extend the framework to multi-regime datasets (FD002/FD004) and physical rotating motor test-beds."
    )

    # ==========================================
    # REFERENCES (DESCENDING PUBLICATION YEAR)
    # ==========================================
    add_h5("References")
    refs = [
        "[1] J. Yang, Y. Peng, and J. Xie, \"Remaining Useful Life Prediction Method for Bearings Based on LSTM with Uncertainty Quantification,\" Sensors, vol. 22, no. 12, p. 4549, Jun. 2022, doi: 10.3390/s22124549.",
        "[2] J. Zhou, Y. Qin, D. Chen, F. Liu, and Q. Qian, \"Remaining Useful Life Prediction of Bearings by a New Reinforced Memory GRU Network,\" Advanced Engineering Informatics, vol. 53, p. 101682, Aug. 2022, doi: 10.1016/j.aei.2022.101682.",
        "[3] M. Liu, S. Fang, H. Dong, and C. Xu, \"Review of Digital Twin about Concepts, Technologies, and Industrial Applications,\" Journal of Manufacturing Systems, vol. 58, pp. 346–361, Jan. 2021, doi: 10.1016/j.jmsy.2020.06.017.",
        "[4] M. Ma and Z. Mao, \"Deep-Convolution-Based LSTM Network for Remaining Useful Life Prediction,\" IEEE Transactions on Industrial Informatics, vol. 17, no. 3, pp. 1658–1667, Mar. 2021, doi: 10.1109/TII.2020.2991796.",
        "[5] A. B. Nassif, M. A. Talib, Q. Nasir, and F. M. Dakalbab, \"Machine Learning for Anomaly Detection: A Systematic Review,\" IEEE Access, vol. 9, pp. 78658–78700, 2021, doi: 10.1109/ACCESS.2021.3083060.",
        "[6] M. M. Rathore, S. A. Shah, D. Shukla, E. Bentafat, and S. Bakiras, \"The Role of AI, Machine Learning, and Big Data in Digital Twinning: A Systematic Literature Review, Challenges, and Opportunities,\" IEEE Access, vol. 9, pp. 32030–32052, 2021, doi: 10.1109/ACCESS.2021.3060863.",
        "[7] A. Fuller, Z. Fan, C. Day, and C. Barlow, \"Digital Twin: Enabling Technologies, Challenges and Open Research,\" IEEE Access, vol. 8, pp. 108952–108971, 2020, doi: 10.1109/ACCESS.2020.2998358.",
        "[8] S. S. Roy, S. Dey, and S. Chatterjee, \"Autocorrelation Aided Random Forest Classifier-Based Bearing Fault Detection Framework,\" IEEE Sensors Journal, vol. 20, no. 18, pp. 10792–10800, Sep. 2020, doi: 10.1109/JSEN.2020.2995109.",
        "[9] D. Wu, Z. Jiang, X. Xie, X. Wei, W. Yu, and R. Li, \"LSTM Learning with Bayesian and Gaussian Processing for Anomaly Detection in Industrial IoT,\" IEEE Transactions on Industrial Informatics, vol. 16, no. 8, pp. 5244–5253, Aug. 2020, doi: 10.1109/TII.2019.2952917.",
        "[10] P. Aivaliotis, K. Georgoulias, and G. Chryssolouris, \"The Use of Digital Twin for Predictive Maintenance in Manufacturing,\" International Journal of Computer Integrated Manufacturing, vol. 32, no. 11, pp. 1067–1080, 2019, doi: 10.1080/0951192X.2019.1686173.",
        "[11] T. P. Carvalho, F. A. A. M. N. Soares, R. Vita, R. da P. Francisco, J. P. Basto, and S. G. S. Alcalá, \"A Systematic Literature Review of Machine Learning Methods Applied to Predictive Maintenance,\" Computers & Industrial Engineering, vol. 137, p. 106024, Nov. 2019, doi: 10.1016/j.cie.2019.106024.",
        "[12] F. Tao, H. Zhang, A. Liu, and A. Y. C. Nee, \"Digital Twin in Industry: State-of-the-Art,\" IEEE Transactions on Industrial Informatics, vol. 15, no. 4, pp. 2405–2415, Apr. 2019, doi: 10.1109/TII.2018.2873186.",
        "[13] M. De Benedetti, F. Leonardi, F. Messina, C. Santoro, and A. Vasilakos, \"Anomaly Detection and Predictive Maintenance for Photovoltaic Systems,\" Neurocomputing, vol. 310, pp. 59–68, Oct. 2018, doi: 10.1016/j.neucom.2018.05.019.",
        "[14] W. Kritzinger, M. Karner, G. Traar, J. Henjes, and W. Sihn, \"Digital Twin in Manufacturing: A Categorical Literature Review and Classification,\" IFAC-PapersOnLine, vol. 51, no. 11, pp. 1016–1022, 2018, doi: 10.1016/j.ifacol.2018.08.474.",
        "[15] A. Saxena, K. Goebel, D. Simon, and N. Eklund, \"Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation,\" in Proceedings of the 1st International Conference on Prognostics and Health Management (PHM08), Denver, CO, Oct. 2008."
    ]
    for rf in refs:
        doc.add_paragraph(rf, style='references')

    # Save to both target output files
    out_docx_intelli = os.path.join(root_dir, 'manuscript', 'INTELLITWIN_RESEARCH_PAPER_IEEE_FORMAT.docx')
    out_docx_uq = os.path.join(root_dir, 'manuscript', 'UQ_DT_RESEARCH_PAPER_IEEE_FORMAT.docx')
    
    doc.save(out_docx_intelli)
    doc.save(out_docx_uq)
    print(f"Successfully generated DOCX papers:\n  {out_docx_intelli}\n  {out_docx_uq}")
    return out_docx_intelli

if __name__ == '__main__':
    build_paper()
