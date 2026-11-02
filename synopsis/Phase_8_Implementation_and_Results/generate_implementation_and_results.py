import os
import subprocess
import zipfile

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(DIR, "implementation_and_results.html")
PDF_PATH = os.path.join(DIR, "implementation_and_results.pdf")
DOCX_PATH = os.path.join(DIR, "implementation_and_results.docx")

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
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
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

    def formula(text):
        xml_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:line="360" w:lineRule="auto" w:before="120" w:after="160"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:i/><w:sz w:val="24"/></w:rPr>
        <w:t xml:space="preserve">{xml_text}</w:t>
      </w:r>
    </w:p>"""

    def table_xml(headers, rows, widths=None):
        total_width = 8306  # available dxa on A4 with 1.5" left and 1.0" right margins
        if not widths:
            col_w = total_width // len(headers)
            widths = [col_w] * len(headers)
            widths[-1] = total_width - sum(widths[:-1])

        out = []
        out.append("    <w:tbl>")
        out.append("""      <w:tblPr>
        <w:tblW w:w="8306" w:type="dxa"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>
          <w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>
          <w:left w:val="none"/>
          <w:right w:val="none"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>
          <w:insideV w:val="none"/>
        </w:tblBorders>
        <w:tblCellMar>
          <w:top w:w="100" w:type="dxa"/>
          <w:bottom w:w="100" w:type="dxa"/>
          <w:left w:w="120" w:type="dxa"/>
          <w:right w:w="120" w:type="dxa"/>
        </w:tblCellMar>
      </w:tblPr>""")

        out.append("      <w:tblGrid>")
        for w in widths:
            out.append(f'        <w:gridCol w:w="{w}"/>')
        out.append("      </w:tblGrid>")

        # Header Row
        out.append("      <w:tr>")
        out.append("""        <w:trPr>
          <w:tblHeader/>
          <w:cantSplit/>
        </w:trPr>""")
        for idx, h in enumerate(headers):
            xml_h = h.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            w = widths[idx]
            out.append(f"""        <w:tc>
          <w:tcPr>
            <w:tcW w:w="{w}" w:type="dxa"/>
            <w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>
            <w:tcBorders>
              <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>
            </w:tcBorders>
          </w:tcPr>
          <w:p>
            <w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="0"/><w:jc w:val="left"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{xml_h}</w:t></w:r>
          </w:p>
        </w:tc>""")
        out.append("      </w:tr>")

        # Data Rows
        for r in rows:
            out.append("      <w:tr>")
            out.append("        <w:trPr><w:cantSplit/></w:trPr>")
            for idx, val in enumerate(r):
                xml_val = str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                w = widths[idx]
                out.append(f"""        <w:tc>
          <w:tcPr>
            <w:tcW w:w="{w}" w:type="dxa"/>
          </w:tcPr>
          <w:p>
            <w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="0"/><w:jc w:val="left"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{xml_val}</w:t></w:r>
          </w:p>
        </w:tc>""")
            out.append("      </w:tr>")

        out.append("    </w:tbl>")
        out.append("""    <w:p><w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="160"/></w:pPr></w:p>""")
        return "\n".join(out)

    body_elements = []

    # Section 8 Title
    body_elements.append(p("8. Implementation Status and Results / Expected Results", is_bold=True, size=28, space_after=300))

    # 8.1
    body_elements.append(p("8.1 Current Implementation Status and Verified Milestones", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The implementation of the IntelliTwin research framework is structured around a modular, reproducible Python codebase residing "
        "in src/intellitwin/ [1]–[3]. In strict compliance with pre-registered confirmatory research standards (Architecture Decision Records "
        "ADR-018 and ADR-022), all primary algorithmic subsystems, base model checkpoints, conformal calibration engines, maintenance simulation "
        "routines, and digital twin replay interfaces have been fully engineered, validated, and frozen prior to held-out test evaluation [4], [7], [9]."
    ))
    body_elements.append(p("The implemented software architecture comprises seven fully integrated functional modules, supported by a comprehensive automated test suite spanning 37 unit and integration test modules:"))
    body_elements.append(li(
        "1.", "Data Ingestion and Anti-Leakage Preprocessing Subsystem (src/intellitwin/data/):",
        "Implements automated ingestion pipelines for the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) corpus [1]. "
        "Performs systematic feature qualification by pruning six uninformative sensor channels displaying zero variance or rank correlation "
        "(S_dropped = {s1, s5, s6, s10, s16, s19}), retaining d = 17 informative operational channels. Enforces training-only Z-score standardization "
        "(μ_train, σ_train, computed with ddof=0), K = 6 K-means regime clustering on standardized flight settings, and causal sliding lookback "
        "windowing (W = 30 cycles, stride 1, zero-padding prohibited) [1], [10]."
    ))
    body_elements.append(li(
        "2.", "Prognostic Base Estimator Subsystem (src/intellitwin/models/):",
        "Houses two complementary model families: (i) multi-quantile HistGradientBoostingRegressor (GBR) operating on flattened 510-dimensional causal "
        "vectors, minimizing pinball loss across quantiles ρ ∈ {0.05, 0.50, 0.95}; and (ii) PyTorch deep Bidirectional LSTM processing sequential matrices "
        "Xi(t) ∈ ℝ^(30 × 17) with two recurrent layers (h = 64), variational dropout (p = 0.20), and AdamW optimization [3], [4]. A full 30-checkpoint "
        "benchmark matrix (3 sub-corpora × 2 architectures × 5 frozen seeds [2026, 2027, 2028, 2029, 2030]) has been trained, verified, and frozen under ADR-020."
    ))
    body_elements.append(li(
        "3.", "Hierarchical Conformal Calibration Subsystem (src/intellitwin/uncertainty/):",
        "Formulates exact rational nonconformity quantile solvers addressing cluster non-exchangeability across engines with variable trajectory lengths [9]. "
        "Implements asymmetric decision-aware nonconformity scoring parameterized by scaling exponent γ ∈ {0, 1, 2} and asymmetry coefficient β ∈ ℝ:"
    ))
    body_elements.append(formula("σ(p̂) = (1 + p̂ / 125.0)^γ,       z(p̂) = exp(−p̂ / 20.0)"))
    body_elements.append(formula("a(p̂) = σ(p̂) · exp(β · z(p̂)),       b(p̂) = σ(p̂) · exp(−β · z(p̂))"))
    body_elements.append(formula("s_i(t) = max( (p̂_i(t) − y_i(t)) / a(p̂_i(t)),   (y_i(t) − p̂_i(t)) / b(p̂_i(t)),   0 )"))
    body_elements.append(p(
        "Calibration quantiles place finite probability mass m / (m + 1) with point-at-infinity mass 1 / (m + 1), targeting nominal 1 − α = 0.90 coverage "
        "with automatic global fallback routing for regime clusters containing fewer than mg ≥ 10 calibration units [9]."
    ))
    body_elements.append(li(
        "4.", "Sequential Decision and Maintenance Simulator (src/intellitwin/simulator/):",
        "Implements cycle-by-cycle discrete-event asset lifecycle simulation [5], [8]. Evaluates dynamic stopping times τi = inf{t ≥ W : Li(t) ≤ 1.0} "
        "governed by lower conformal bounds, tracks economic lifecycle expenditures under the primary reference scenario in Standardized Cost Units "
        "(CPM = 1.0, CFAIL = 5.0, CWASTE = 0.20 SCU per cycle), and logs intervention events [5], [8]."
    ))
    body_elements.append(li(
        "5.", "Controlled Attribution and Baseline Protocol (src/intellitwin/decision/):",
        "Parameterizes four frozen matched-conservatism control configurations across three families (δ-widened intervals, Δ-safety margins, and θ-earlier "
        "intervention thresholds) to disambiguate genuine uncertainty calibration from heuristic over-conservatism [8], [12]."
    ))
    body_elements.append(li(
        "6.", "Confirmatory Statistical Inference Engine (src/intellitwin/evaluation/):",
        "Executes 10,000 stratified engine-cluster bootstrap resamples with replacement (using PCG64 PRNG), enforces Bonferroni family-wise error rate control "
        "(α_test = 0.0125, 98.75% decision intervals), and evaluates Intersection-Union Testing (IUT) decision rules across all 152 pre-registered hypothesis components [12]."
    ))
    body_elements.append(li(
        "7.", "Digital Twin Replay Engine and Operator Dashboard (src/intellitwin/twin/, apps/twin_dashboard/):",
        "Implements an ISO 23247-aligned state replication engine (TwinReplayEngine) managing a 4-state lifecycle machine (WARMING_UP, ACTIVE, MAINTAINED, FAILED) [14]. "
        "Guarantees strict numerical verification parity (atol ≤ 10^-4) against offline batch execution, exposed via a modular FastAPI service at port 8000 and "
        "an interactive HTML5/JavaScript dashboard [2], [13]."
    ))

    # Table 8.1
    body_elements.append(p("Table 8.1: Implementation Status of IntelliTwin Architectural Subsystems and QA Verification", is_bold=True, size=20, space_after=100))
    t1_headers = ["Subsystem", "Primary Implemented Capabilities", "Core Module Path", "Status"]
    t1_rows = [
        ["Data Preprocessing", "Ingestion, 17-feature selection, Z-scores, W=30 windowing", "src/intellitwin/data/", "VERIFIED"],
        ["Base Prognostics", "HistGBR (pinball loss) & PyTorch BiLSTM (MSE loss), 30 models", "src/intellitwin/models/", "VERIFIED"],
        ["Conformal Calibration", "Engine-weighted CDF, asymmetric scoring, regime stratification", "src/intellitwin/uncertainty/", "VERIFIED"],
        ["Maintenance Simulator", "Stopping time τi, SCU lifecycle accounting, event logging", "src/intellitwin/simulator/", "VERIFIED"],
        ["Matched Controls", "3 matched-conservatism baseline families (δ, Δ, θ)", "src/intellitwin/decision/", "VERIFIED"],
        ["Statistical Inference", "10k cluster bootstrap, Bonferroni α=0.0125, 152 IUT rules", "src/intellitwin/evaluation/", "VERIFIED"],
        ["Digital Twin Prototype", "State machine, parity ≤ 10^-4, FastAPI API, HTML5/JS dashboard", "src/intellitwin/twin/", "VERIFIED"],
        ["Automated Test Suite", "37 unit/integration test modules across all core subsystems", "tests/", "PASS (37/37)"]
    ]
    t1_widths = [1800, 3606, 1700, 1200]
    body_elements.append(table_xml(t1_headers, t1_rows, t1_widths))

    # 8.2
    body_elements.append(p("8.2 Dataset Qualification and Partition Split Statistics", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The empirical foundation of IntelliTwin is established on the NASA C-MAPSS turbofan degradation benchmark corpus [1]. "
        "To ensure rigorous evaluation across varying operational complexity, three distinct sub-corpora are utilized under immutable "
        "engine-level disjoint split manifests (ADR-011)."
    ))

    # Table 8.2
    body_elements.append(p("Table 8.2: C-MAPSS Dataset Characteristics, Operating Regimes, and Disjoint Split Partitioning", is_bold=True, size=20, space_after=100))
    t2_headers = ["Dataset", "Flight Conditions", "Fault Modes", "Total Engines", "Train (50%)", "Cal (20%)", "Val (10%)", "Test (20%)", "Window (W)"]
    t2_rows = [
        ["FD001", "1 (Sea level)", "1 (HPC)", "100", "50", "20", "10", "20", "30 cycles"],
        ["FD002", "6 (C1–C6)", "1 (HPC)", "260", "130", "52", "26", "52", "30 cycles"],
        ["FD004", "6 (C1–C6)", "2 (HPC + Fan)", "249", "124", "50", "25", "50", "30 cycles"],
        ["Total Fleet", "—", "—", "609", "304", "122", "61", "122", "30 cycles"]
    ]
    t2_widths = [900, 1306, 1100, 800, 800, 800, 800, 800, 1000]
    body_elements.append(table_xml(t2_headers, t2_rows, t2_widths))

    body_elements.append(p(
        "As detailed in Table 8.2, the complete fleet comprises 609 run-to-failure engines partitioned into 304 Training, 122 Calibration, "
        "61 Validation, and 122 held-out Test engines. Every split manifest is cryptographically hashed and stored in data/splits/, "
        "guaranteeing that no engine trajectory crosses partition boundaries."
    ))

    # 8.3
    body_elements.append(p("8.3 Frozen Base Model Performance and Development Validation Results", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "During the offline model development and qualification phase (Step 7 and Step 8 of the research protocol), hyperparameter grid searches "
        "and calibration candidate selections were performed strictly on the Training and Validation partitions [4], [7]."
    ))

    # Table 8.3
    body_elements.append(p("Table 8.3: Frozen Base Model Configurations, Validation Errors, and Selected Conformal Candidates", is_bold=True, size=20, space_after=100))
    t3_headers = ["Evaluation Cell", "Architecture", "Winning Configuration & Hyperparameters", "Validation RMSE (cycles)", "Selected Candidate"]
    t3_rows = [
        ["FD001 × GBR", "HistGradientBoosting", "gbr_lr010_leaf15_l2_0 (lr=0.10, leaf=15)", "28.42 ± 0.00", "gamma2_betam1 (γ=2, β=−ln 2)"],
        ["FD001 × LSTM", "Bidirectional LSTM", "lstm_h64_lr0010 (h=64, drop=0.20, lr=10^-3)", "29.90 ± 0.23", "gamma2_betam1 (γ=2, β=−ln 2)"],
        ["FD002 × GBR", "HistGradientBoosting", "gbr_lr010_leaf31_l2_0 (lr=0.10, leaf=31)", "34.66 ± 0.00", "gamma2_betam1 (γ=2, β=−ln 2)"],
        ["FD002 × LSTM", "Bidirectional LSTM", "lstm_h64_lr0010 (h=64, drop=0.20, lr=10^-3)", "35.14 ± 0.23", "gamma2_betam1 (γ=2, β=−ln 2)"],
        ["FD004 × GBR", "HistGradientBoosting", "gbr_lr010_leaf31_l2_0 (lr=0.10, leaf=31)", "48.83 ± 0.00", "gamma2_betam1 (γ=2, β=−ln 2)"],
        ["FD004 × LSTM", "Bidirectional LSTM", "lstm_h64_lr0010 (h=64, drop=0.20, lr=10^-3)", "48.67 ± 0.36", "gamma2_betam1 (γ=2, β=−ln 2)"]
    ]
    t3_widths = [1400, 1606, 2500, 1400, 1400]
    body_elements.append(table_xml(t3_headers, t3_rows, t3_widths))

    body_elements.append(p(
        "As documented in Table 8.3, across all six evaluation cells, the candidate gamma2_betam1 (γ = 2, β = −ln 2 ≈ −0.693147) was identified "
        "as the feasible optimal configuration under leave-one-engine-out validation cross-validation (ADR-021). The reported validation RMSE values "
        "represent the mean and standard deviation across the five frozen random seeds ([2026..2030])."
    ))
    body_elements.append(p("Scientific Demarcation Statement", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "In strict accordance with confirmatory empirical protocols, the validation metrics in Table 8.3 represent development partition performance. "
        "Held-out test trajectories (122 engines across FD001, FD002, FD004) remain strictly blinded prior to official confirmatory execution. "
        "Development validation success confirms the numerical stability and convergence of the base models, but does not constitute confirmatory "
        "evidence of maintenance cost superiority, subgroup reliability, or cross-condition generalizability."
    ))

    # 8.4
    body_elements.append(p("8.4 Pre-Registered Confirmatory Protocol and Expected Experimental Results", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The final scientific evaluation of IntelliTwin is framed around four pre-registered Research Questions (RQ1–RQ4) evaluated via 152 formal "
        "hypothesis components structured under an Intersection-Union Test (IUT) framework [12]."
    ))

    # Table 8.4
    body_elements.append(p("Table 8.4: Pre-Registered Confirmatory Research Questions, Evaluation Metrics, and Decision Margins", is_bold=True, size=20, space_after=100))
    t4_headers = ["Research Question", "Evaluation Target & Target Metric", "Pre-Registered Practical Margin", "Components"]
    t4_rows = [
        ["RQ1: Maintenance Utility", "Cost reduction & coverage validity on FD002 primary multi-regime", "Δ_cost > 0.20 SCU, E < 0.05, Δ_fail ≤ 0", "14"],
        ["RQ2: Subgroup Reliability", "Worst-subgroup coverage error across 6 regimes & 3 wear stages", "Δ_error > 0.01, E(g) < 0.05, D_width < 1.0", "20"],
        ["RQ3: Decision Attribution", "Cost improvement over 4 matched-conservatism control baselines", "Δ_cost > 0.20 SCU, E < 0.05, Δ_fail ≤ 0", "22"],
        ["RQ4: Matrix Generalization", "Weighted aggregate superiority & non-harm across all 6 cells", "Agg: >0.20, >0.01; Cell: ≥ −0.20, ≥ −0.01", "96"],
        ["Total Components", "Full Intersection-Union Test (IUT) specification across all cells", "Strictly fail-closed component logic", "152"]
    ]
    t4_widths = [1900, 3206, 2200, 1000]
    body_elements.append(table_xml(t4_headers, t4_rows, t4_widths))

    body_elements.append(p("Expected Confirmatory Experimental Outcomes", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("Based on the validated mathematical formulation and development experiments, the expected empirical outcomes on held-out test partitions are specified as follows:"))
    body_elements.append(li(
        "•", "Expected Outcome for RQ1 (Maintenance Utility):",
        "The proposed condition-adaptive conformal calibration method (decision_aware_hcp) is expected to achieve a statistically significant "
        "reduction in average fleet lifecycle maintenance cost exceeding 0.20 Standardized Cost Units (Δ_cost > 0.20 SCU) relative to standard "
        "global conformal prediction and uncalibrated point-prediction baselines, while strictly preserving marginal prediction interval coverage "
        "error within 5% (E = |(1−α) − PICP| < 0.05) without increasing observed in-service failure rates (Δ_fail ≤ 0) [5], [7], [8]."
    ))
    body_elements.append(li(
        "•", "Expected Outcome for RQ2 (Subgroup Conditional Reliability):",
        "Condition-adaptive regime and wear-stage partitioning is expected to eliminate severe localized undercoverage vulnerabilities observed in "
        "global conformal calibration. Specifically, worst-group coverage error is expected to improve by at least 1 percentage point (Δ_error > 0.01) "
        "across the six operational flight regimes (C1–C6) and three lifecycle wear stages (Early, Mid, Late), maintaining all subgroup errors "
        "within 5% (E(g) < 0.05) without inducing excessive interval width inflation (D_width < 1.0 cycle) [4], [10]."
    ))
    body_elements.append(li(
        "•", "Expected Outcome for RQ3 (Decision-Value Attribution):",
        "The proposed method is expected to maintain statistically significant cost superiority (Δ_cost > 0.20 SCU) when contrasted against all three "
        "matched-conservatism control families (uniformly widened intervals, point safety margins, and earlier scheduled overhaul thresholds), "
        "establishing that operational savings stem from genuine risk-directed uncertainty quantification rather than arbitrary early intervention [8], [12]."
    ))
    body_elements.append(li(
        "•", "Expected Outcome for RQ4 (Cross-Condition Generalization and Non-Harm):",
        "Across the complete 6-cell evaluation matrix (FD001, FD002, FD004 × GBR, LSTM), the weighted aggregate contrast is expected to demonstrate "
        "simultaneous cost reduction (Δ̄_cost > 0.20 SCU) and reliability improvement (Δ̄_error > 0.01). Concurrently, Two One-Sided Tests (TOST) "
        "are expected to establish non-harm in every individual evaluation cell (Lower 98.75% CI of Δ_cost ≥ −0.20 SCU, Δ_error ≥ −0.01) under "
        "strict Bonferroni family-wise error rate control (α = 0.0125) [12]."
    ))

    # 8.5
    body_elements.append(p("8.5 Verification, Audit Trail, and Reproducibility Matrix", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "To satisfy the highest standards of scientific reproducibility, the IntelliTwin repository maintains a comprehensive audit trail tracking "
        "executed verification, historical baselines, and pending confirmatory experiments (ADR-022)."
    ))

    # Table 8.5
    body_elements.append(p("Table 8.5: IntelliTwin Reproducibility, Verification Audit, and Artifact Status Matrix", is_bold=True, size=20, space_after=100))
    t5_headers = ["Category", "Audit Item", "Verification Scope & Criterion", "Evidence Artifact", "Status"]
    t5_rows = [
        ["Executed Verification", "Base Model Registry", "30 checkpoints across 3 datasets; SHA-256 integrity", "model_registry.json", "PASS"],
        ["Executed Verification", "Prediction Reproduction", "Exact numerical output match (GBR max diff 0.0000)", "step07_prediction_reproduction.json", "PASS"],
        ["Executed Verification", "Calibration Bundles", "90 calibrator bundles (270 coverage sets) validated", "calibration_registry.json", "PASS"],
        ["Executed Verification", "Candidate Selection", "Validation selection frozen under ADR-021", "selection_freeze.json", "PASS"],
        ["Executed Verification", "Step 8 Reproduction", "60 model/partition reproductions rechecked", "reused_evidence.json", "PASS"],
        ["Executed Verification", "Pre-Test Audit (v4)", "Step 9 evaluation scripts & controls audited", "pretest_audit.json", "PRETEST_READY"],
        ["Executed Verification", "Digital Twin Parity", "Replay engine parity ≤ 10^-4 vs batch across 37 pytests", "test_twin_replay.py", "PASS"],
        ["Historical Evidence", "Step 8 Full Audit v2", "Historical PR #25 verification baseline", "step08_full_audit.json", "HISTORICAL_PASS"],
        ["Historical Evidence", "Protected Artifacts", "652 tracked protected artifacts verified", "baseline_manifest.json", "HISTORICAL_PASS"],
        ["Blinded Trajectories", "Held-Out Test Data", "122 test engines strictly blinded prior to test", "experiments/confirmatory/", "NOT_STARTED"],
        ["Pending Experiments", "Primary Test Execution", "Held-out point and interval outcomes (UPD-02)", "Test evaluation logs", "PENDING"],
        ["Pending Experiments", "Maintenance Simulation", "Fleet lifecycle costs & failure rates (UPD-03)", "Simulation logs", "PENDING"],
        ["Pending Experiments", "IUT Decisions (152)", "10k cluster bootstrap hypothesis decisions (UPD-04)", "Confirmatory report", "PENDING"]
    ]
    t5_widths = [1600, 1606, 2600, 1500, 1000]
    body_elements.append(table_xml(t5_headers, t5_rows, t5_widths))

    # 8.6
    body_elements.append(p("8.6 Milestone Delivery and Next Steps", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "With the completion of Phase 8, the software implementation, dataset qualification, base model freezing, calibration pipeline, "
        "simulation engine, and pre-registered statistical protocol stand fully verified with PRETEST_READY audit status. Subsequent synopsis "
        "phases will document system requirements and tools (Phase 9), followed by conclusion and future roadmap (Phase 10), culminating in "
        "final Overleaf synchronization and total page budget alignment (6–8 pages per institutional circular AKGEC/IT/CSIT/26-27/PROJ-m)."
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
