import os
import subprocess
import zipfile

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(DIR, "system_architecture.html")
PDF_PATH = os.path.join(DIR, "system_architecture.pdf")
DOCX_PATH = os.path.join(DIR, "system_architecture.docx")

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

    def box_callout(title, lines, border_color="0969DA", fill_color="F6F8FA"):
        xml_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        out = []
        out.append(f"""    <w:p>
      <w:pPr>
        <w:pBdr>
          <w:top w:val="single" w:sz="12" w:space="4" w:color="{border_color}"/>
          <w:left w:val="single" w:sz="24" w:space="12" w:color="{border_color}"/>
          <w:bottom w:val="single" w:sz="12" w:space="4" w:color="{border_color}"/>
          <w:right w:val="single" w:sz="12" w:space="4" w:color="{border_color}"/>
        </w:pBdr>
        <w:shd w:val="clear" w:color="auto" w:fill="{fill_color}"/>
        <w:spacing w:line="300" w:lineRule="auto" w:before="140" w:after="80"/>
        <w:jc w:val="both"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="{border_color}"/></w:rPr>
        <w:t xml:space="preserve">{xml_title}</w:t>
      </w:r>
    </w:p>""")
        for ln in lines:
            xml_ln = ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            out.append(f"""    <w:p>
      <w:pPr>
        <w:pBdr>
          <w:left w:val="single" w:sz="24" w:space="12" w:color="{border_color}"/>
        </w:pBdr>
        <w:shd w:val="clear" w:color="auto" w:fill="{fill_color}"/>
        <w:spacing w:line="280" w:lineRule="auto" w:after="60"/>
        <w:jc w:val="both"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:sz w:val="20"/></w:rPr>
        <w:t xml:space="preserve">{xml_ln}</w:t>
      </w:r>
    </w:p>""")
        out.append(f"""    <w:p>
      <w:pPr>
        <w:pBdr>
          <w:bottom w:val="single" w:sz="12" w:space="4" w:color="{border_color}"/>
        </w:pBdr>
        <w:shd w:val="clear" w:color="auto" w:fill="{fill_color}"/>
        <w:spacing w:line="100" w:lineRule="auto" w:after="160"/>
      </w:pPr>
    </w:p>""")
        return "\n".join(out)

    body_elements = []

    # Section 7 Title
    body_elements.append(p("7. System Architecture and Workflow", is_bold=True, size=28, space_after=300))

    # 7.1
    body_elements.append(p("7.1 Architectural Overview and Multi-Tier Decomposition", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The IntelliTwin framework is structured around a decoupled, multi-tier cyber-physical research architecture designed "
        "to resolve the pervasive gap between data-driven Remaining Useful Life (RUL) estimation, finite-sample distribution-free "
        "uncertainty calibration, and sequential operational maintenance decision-making [1]–[3]. In industrial rotating machinery, "
        "such as commercial turbofan aircraft engines, standard point predictions optimize symmetric statistical metrics that fail "
        "to reflect asymmetric downtime losses (where unscheduled in-service failure penalty significantly exceeds scheduled preventive "
        "overhaul cost, C_FAIL ≫ C_PM) [1], [5]. Concurrently, digital twin implementations in manufacturing literature frequently "
        "prioritize high-fidelity 3D geometric visualizations or centralized SCADA dashboards without mathematically formalizing "
        "how predictive uncertainty should govern discrete intervention decisions [2], [13], [14]."
    ))
    body_elements.append(p("To bridge these disjoint paradigms, IntelliTwin decomposes the system into five modular, decoupled architectural tiers:"))
    body_elements.append(li(
        "1.", "Tier 1: Data Ingestion and Anti-Leakage Preprocessing Tier:",
        "Ingests multi-sensor run-to-failure streams from the NASA C-MAPSS corpus, enforces immutable engine-level disjoint split isolation, "
        "performs invariant sensor pruning, fits training-only normalization parameters, clusters operational settings, and constructs causal sliding lookback windows [1]."
    ))
    body_elements.append(li(
        "2.", "Tier 2: Prognostic Base Inference Tier:",
        "Houses complementary shallow gradient-boosted decision trees (HistGradientBoostingRegressor) and deep recurrent neural networks "
        "(PyTorch LSTM), generating continuous point predictions of Remaining Useful Life [3], [4]."
    ))
    body_elements.append(li(
        "3.", "Tier 3: Hierarchical Conformal Calibration Tier:",
        "Computes asymmetric nonconformity scores, evaluates exact engine-weighted quantiles under cluster exchangeability, stratifies calibration bounds "
        "across operational flight regimes, and inverts scores into finite-sample prediction intervals [Li(t), Ui(t)] targeting 90% nominal coverage [7], [9]."
    ))
    body_elements.append(li(
        "4.", "Tier 4: Sequential Decision and Maintenance Simulation Tier:",
        "Evaluates dynamic cycle-by-cycle stopping rules τi = inf{t ≥ W : Li(t) ≤ θ} against conservative lower conformal bounds, tracks economic lifecycle "
        "expenditures in Standardized Cost Units (SCU), executes matched-conservatism attribution controls, and conducts 10,000 cluster bootstrap hypothesis tests [5], [8], [12]."
    ))
    body_elements.append(li(
        "5.", "Tier 5: Digital Twin Synchronization and Presentation Tier:",
        "Formulates a real-time trace-driven state replication engine (TwinReplayEngine) adhering to ISO 23247 principles [14], guarantees strict numerical "
        "verification parity (atol ≤ 10^-4) against offline batch execution, and exposes streaming REST endpoints via FastAPI to an interactive HTML5/JavaScript operator dashboard [2], [13]."
    ))

    body_elements.append(p("Physical Integration and Research Demarcation", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("In alignment with rigorous academic reporting standards, the physical integration boundary of the IntelliTwin system is explicitly demarcated:"))
    body_elements.append(li(
        "•", "Offline Trace-Driven Simulation:",
        "The architecture operates on historical run-to-failure telemetry from the NASA C-MAPSS simulator [1]. No live turbofan engine is physically connected "
        "to the host system, and no hardware IoT sensor bus (e.g., MQTT, OPC UA) is claimed."
    ))
    body_elements.append(li(
        "•", "Advisory Decision Support:",
        "Maintenance orders dispatched by the simulation tier represent advisory recommendations for maintenance engineers; closed-loop physical actuation "
        "(e.g., automatic engine shutdown or thrust throttling) is strictly out of scope."
    ))
    body_elements.append(li(
        "•", "Strict Anti-Leakage Boundary:",
        "Held-out test trajectories are isolated from model training, hyperparameter grid search, and conformal score calibration. True failure times and oracle "
        "RUL values are revealed exclusively to offline evaluation routines for post-hoc scoring."
    ))

    # 7.2
    body_elements.append(p("7.2 Data Ingestion, Normalization, and Causal Windowing Pipeline", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The data pipeline ingests raw continuous multi-sensor records and transforms them into standardized tensor and vector representations while strictly "
        "eliminating temporal and inter-engine data leakage."
    ))
    body_elements.append(p("C-MAPSS Data Schema and Invariant Channel Pruning", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "The raw C-MAPSS dataset provides 26 columns per cycle: engine unit identifier, cycle index, 3 operational flight condition settings, and 21 thermo-mechanical "
        "degradation sensors [1]. Across multi-regime datasets (FD002, FD004), a systematic variance audit identified six invariant or uninformative channels exhibiting zero "
        "variance or uninformative responses across all regimes:"
    ))
    body_elements.append(formula("S_dropped = { s1 (T2), s5 (P2), s6 (P15), s10 (epr), s16 (farB), s19 (Nf_dmd) }"))
    body_elements.append(p(
        "Excluding these uninformative channels eliminates matrix rank deficiency and numerical instability. The retained schema comprises d = 17 informative channels: "
        "3 operating settings (z1, z2, z3) and 14 dynamic thermo-mechanical sensors (temperatures, pressures, core/fan speeds, fuel ratios, and coolant bleeds)."
    ))

    body_elements.append(p("Strict Engine-Level Split Partitioning", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("To prevent inter-engine correlation leakage, partitioning is strictly enforced at the engine unit level. For each benchmark dataset, entire run-to-failure engine trajectories belong exclusively to one split:"))
    body_elements.append(li("•", "FD001 (Single-Regime Control):", "100 total engines split into 50 Training, 20 Calibration, 10 Validation, and 20 Test engines."))
    body_elements.append(li("•", "FD002 (Multi-Regime Primary):", "260 total engines split into 130 Training, 52 Calibration, 26 Validation, and 52 Test engines."))
    body_elements.append(li("•", "FD004 (Multi-Regime / Multi-Fault Robustness):", "249 total engines split into 124 Training, 50 Calibration, 25 Validation, and 50 Test engines."))

    body_elements.append(p("Training-Only Normalization and Regime Clustering", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Standardization parameters (mean μ_train and population standard deviation σ_train, computed with ddof=0) are derived solely from the designated Training engines:"
    ))
    body_elements.append(formula("x̃_i(t) = (x_i(t) − μ_train) / (σ_train + ε)"))
    body_elements.append(p(
        "where ε = 10^-8 prevents division by zero. For multi-regime sub-corpora (FD002, FD004), operating settings (z1, z2, z3) are standardized and clustered into "
        "K = 6 operational regimes (C1 to C6) via K-means clustering (K = 6, random_state = 2026, n_init = 10) fitted exclusively on training data, preserving deterministic centroid ordering."
    ))

    body_elements.append(p("Causal Sliding-Window Formulation", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "To preserve temporal causality, feature representations are constructed using a fixed sliding lookback window of length W = 30 cycles with stride 1:"
    ))
    body_elements.append(formula("X_i(t) = [ x̃_i(t − W + 1),  x̃_i(t − W + 2),  …,  x̃_i(t) ]^T  ∈  ℝ^(30 × 17)"))
    body_elements.append(p(
        "For early operational cycles (1 ≤ t < W = 30), the causal buffer is filling; zero padding is strictly forbidden, and prognostic inference is deferred until cycle t = 30. "
        "Dual feature representations are constructed from this window:"
    ))
    body_elements.append(li("•", "Sequential Tensor:", "A 2D matrix X_i(t) ∈ ℝ^(30 × 17) preserving temporal ordering for the recurrent LSTM network."))
    body_elements.append(li("•", "Flattened Vector:", "A 1D vector v_i(t) = vec(X_i(t)) ∈ ℝ^510 flattened in C-order (row-major) for gradient-boosted decision trees."))

    # 7.3
    body_elements.append(p("7.3 Prognostic Base Inference Tier", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The prognostic inference tier transforms causal window representations into continuous point estimates of Remaining Useful Life ŷ_i(t)."
    ))
    body_elements.append(p("Dual Target Conventions", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "During base model training, Remaining Useful Life targets are clamped at an upper threshold R_max = 125 cycles:"
    ))
    body_elements.append(formula("y_train,i(t) = min(R_max,  T_i − t)"))
    body_elements.append(p(
        "reflecting the empirical physical reality that initial operational wear does not exhibit measurable degradation signatures during early component life [1]. "
        "In contrast, during held-out test evaluation, the true uncapped linear degradation target y_eval,i(t) = T_i − t is preserved to assess genuine lifetime prognostic accuracy."
    ))

    body_elements.append(p("Model Architecture Workflows", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("Two diverse, complementary model families are trained and frozen under Architecture Decision Record ADR-018:"))
    body_elements.append(li(
        "•", "HistGradientBoostingRegressor (GBR):",
        "Ingests flattened 510-dimensional vectors v_i(t). Optimizes the asymmetric pinball loss function L_ρ(y, ŷ) = max(ρ(y − ŷ), (1 − ρ)(ŷ − y)) across quantiles "
        "ρ ∈ {0.05, 0.50, 0.95} with histogram-binned split finding (max bins = 255, learning rate = 0.05, max leaf nodes = 31, L2 reg = 1.0)."
    ))
    body_elements.append(li(
        "•", "PyTorch Deep Bidirectional LSTM:",
        "Ingests sequential tensors X_i(t) ∈ ℝ^(30 × 17). Features two stacked bidirectional LSTM recurrent layers (h = 64 hidden units per direction, 128 concatenated), "
        "variational recurrent dropout (p = 0.20), and a LeakyReLU projection head. Optimized using AdamW (η = 10^-3, weight decay = 10^-4) under Mean Squared Error loss with cosine annealing scheduling."
    ))
    body_elements.append(p(
        "Point predictions are non-negatively clipped: p̂_i(t) = max(0, ŷ_i(t)). A total of 30 model checkpoints (3 datasets × 2 architectures × 5 seeds [2026..2030]) are registered and frozen."
    ))

    # 7.4
    body_elements.append(p("7.4 Hierarchical Conformal Calibration and Interval Inversion Workflow", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The conformal calibration tier converts raw point predictions into statistically guaranteed, finite-sample prediction intervals C_1−α(X_i(t)) = [L_i(t), U_i(t)] "
        "targeting nominal 90% coverage (1 − α = 0.90) [4], [7], [9]."
    ))
    body_elements.append(p("Asymmetric Decision-Aware Nonconformity Scoring", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "To penalize hazardous overestimation (ŷ > y, risking in-service failure) more heavily than premature underestimation (ŷ < y, resulting in early inspection), "
        "nonconformity scores incorporate state-dependent dynamic scaling [7]:"
    ))
    body_elements.append(formula("σ(p̂) = (1 + p̂ / 125.0)^γ,       z(p̂) = exp(−p̂ / 20.0)"))
    body_elements.append(formula("a(p̂) = σ(p̂) · exp(β · z(p̂)),       b(p̂) = σ(p̂) · exp(−β · z(p̂))"))
    body_elements.append(formula("s_i(t) = max( (p̂_i(t) − y_i(t)) / a(p̂_i(t)),   (y_i(t) − p̂_i(t)) / b(p̂_i(t)),   0 )"))
    body_elements.append(p("with candidate parameters γ = 2 and β = −ln 2 ≈ −0.693147, optimized via grid search on the Validation split."))

    body_elements.append(p("Exact Engine-Weighted Quantile Solver", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "To resolve the clustered temporal autocorrelation of repeated observations within engines, each observation (i, t) from calibration engine i ∈ {1, …, m} "
        "is assigned weight w_i,t = 1 / ((m + 1) · n_i). Total finite probability mass equals m / (m + 1), with the remaining 1 / (m + 1) assigned to +∞ [9]:"
    ))
    body_elements.append(formula("F_dev(q) = (1 / (m + 1)) · ∑_(i=1..m) [ (1 / n_i) · ∑_(t=1..n_i)  𝕀(s_i,t ≤ q) ]"))
    body_elements.append(p(
        "The conformal quantile q̂_1−α is the smallest observed calibration score satisfying F_dev(q̂_1−α) ≥ 1 − α. When calibrating within specific operational flight "
        "regimes k ∈ {1, …, K}, condition-adaptive thresholds q̂_1−α^(k) are computed; if a regime cluster contains fewer than m_g ≥ 10 calibration engines, fallback "
        "routing to the global threshold q̂_1−α^(global) is automatically triggered."
    ))

    body_elements.append(p("Closed-Form Prediction Interval Inversion", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("Given the calibrated threshold q̂_1−α, the finite-sample prediction interval is evaluated via closed-form inversion:"))
    body_elements.append(formula("L_i(t) = max(0,  p̂_i(t) − q̂_1−α · a(p̂_i(t))),       U_i(t) = p̂_i(t) + q̂_1−α · b(p̂_i(t))"))
    body_elements.append(p("where L_i(t) represents the conservative lower bound on Remaining Useful Life that directly drives downstream maintenance policies."))

    # 7.5
    body_elements.append(p("7.5 Discrete-Event Sequential Maintenance Utility Simulation Workflow", is_bold=True, size=24, space_after=160))
    body_elements.append(p("The simulation tier models asset lifecycle progression cycle-by-cycle using a discrete-event simulator (src/intellitwin/simulator/engine.py) [5], [8]."))
    body_elements.append(p("Sequential Stopping Policy", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "At each operational cycle t ≥ 30, the simulator evaluates the lower conformal bound L_i(t). When the lower bound breaches an operational threshold θ "
        "(with default θ = 1.0 cycle), a preventive maintenance order is dispatched immediately:"
    ))
    body_elements.append(formula("τ_i = inf{ t ≥ W : L_i(t) ≤ 1.0 }"))
    body_elements.append(p(
        "If τ_i < T_i, planned maintenance is successfully executed at cycle τ_i, terminating the trajectory without in-service incident. If the engine reaches its terminal "
        "cycle before maintenance is triggered (τ_i ≥ T_i), an unscheduled catastrophic failure occurs at cycle T_i."
    ))

    body_elements.append(p("Standardized Cost Units (SCU) Evaluation", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("Total simulated lifecycle cost for engine i is calculated under the primary reference scenario:"))
    body_elements.append(formula("Cost_i(τ_i) = C_PM + C_WASTE · (T_i − τ_i)      if τ_i < T_i  (Planned Maintenance)"))
    body_elements.append(formula("Cost_i(τ_i) = C_FAIL                              if τ_i ≥ T_i  (Unscheduled Failure)"))
    body_elements.append(p(
        "with economic parameters: planned overhaul C_PM = 1.0 SCU, in-service failure penalty C_FAIL = 5.0 SCU, and wasted component life penalty C_WASTE = 0.20 SCU per cycle."
    ))

    body_elements.append(p("Controlled Attribution Protocol", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "To verify that cost reductions stem from genuine uncertainty calibration rather than heuristic over-conservatism, outcomes are evaluated against three pre-registered "
        "matched-conservatism control families:"
    ))
    body_elements.append(li("1.", "Uniformly Widened Intervals (δ-Widened):", "q̂′ = q̂ + δ."))
    body_elements.append(li("2.", "Point Safety Margins (Δ-Margin):", "p̂′(t) = p̂(t) − Δ."))
    body_elements.append(li("3.", "Earlier Scheduled Intervention (θ-Offset):", "θ′ = θ + τ_advance."))
    body_elements.append(p(
        "Statistical significance is established via 10,000 engine-level cluster bootstrap draws under Bonferroni family-wise error rate control (α = 0.0125) and "
        "Two One-Sided Tests (TOST) non-harm equivalence bounds [12]."
    ))

    # 7.6
    body_elements.append(p("7.6 Digital Twin State Synchronization and Replay Engine", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "To translate scientific models into an interactive operational prototype, IntelliTwin implements a real-time trace-driven Digital Twin synchronization engine "
        "(TwinReplayEngine) in src/intellitwin/twin/replay.py [2], [13], [14]."
    ))
    body_elements.append(p("Thread-Safe Replay State Machine", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("The replay engine manages asset state transitions through an explicit lifecycle state machine protected by mutual exclusion locks:"))
    body_elements.append(li("•", "WARMING_UP (Cycles 1 … 29):", "Sensor frames are buffered into the causal history. Inference is deferred; no prediction bounds or maintenance actions are emitted."))
    body_elements.append(li("•", "ACTIVE (Cycles 30 … min(τ_i, T_i − 1)):", "The engine maintains the active 30 × 17 sliding window, applies training Z-scores, computes dual GBR/LSTM forecasts, derives conformal bounds [L_i(t), U_i(t)], calculates dynamic Health Index HI_i(t) = min(1.0, p̂_i(t) / 125), and evaluates maintenance policy rules."))
    body_elements.append(li("•", "MAINTAINED (Cycle τ_i):", "Triggered when L_i(t) ≤ 1.0. The session locks, records a planned overhaul event, and halts further telemetry advancement."))
    body_elements.append(li("•", "FAILED (Cycle T_i):", "Reached if cycle t attains total failure cycle T_i without intervention. Records catastrophic failure and terminates the session."))

    body_elements.append(p("Numerical Parity Verification", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("To guarantee that real-time replay does not introduce numerical artifacts or windowing drift, the replay engine is audited against offline batch execution:"))
    body_elements.append(formula("max_t | p̂_stream(t) − p̂_batch(t) | ≤ 10^-4,       max_t | L_stream(t) − L_batch(t) | ≤ 10^-4"))
    body_elements.append(p(
        "Parity is verified across all benchmark datasets via 37 automated pytest modules, establishing that the interactive operator dashboard displays mathematically identical "
        "outputs to the scientific evaluation pipeline."
    ))

    body_elements.append(p("REST API Architecture and Operator Dashboard", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("The replay engine is exposed via a high-performance FastAPI service (src/intellitwin/twin/api.py):"))
    body_elements.append(li("•", "GET /api/health:", "System health check, runtime metadata, and frozen model registry status."))
    body_elements.append(li("•", "GET /api/catalog:", "Available benchmark datasets (FD001, FD002, FD004), model families, and test engines."))
    body_elements.append(li("•", "POST /api/sessions:", "Spawns a stateful replay session for a designated engine unit."))
    body_elements.append(li("•", "POST /api/sessions/{id}/advance:", "Consumes exactly one cycle observation, returning updated telemetry, predictions, bounds, and maintenance status."))
    body_elements.append(li("•", "POST /api/sessions/{id}/reset:", "Resets the replay session to cycle 0."))
    body_elements.append(li("•", "GET /api/sessions/{id}/trace.csv:", "Exports complete cycle-by-cycle operational traces for auditing."))
    body_elements.append(p(
        "The frontend interface (apps/twin_dashboard/) renders an interactive HTML5/JavaScript cockpit featuring dynamic sensor time-series charts, RUL prediction intervals "
        "with confidence bands, gauge dials for Health Index, and visual alert indicators (NOMINAL, ADVISORY, CRITICAL_INTERVENTION)."
    ))

    # 7.7
    body_elements.append(p("7.7 Architectural Schematics and Workflow Diagrams", is_bold=True, size=24, space_after=160))

    # Figure 7.1 Callout Box
    body_elements.append(box_callout(
        "FIGURE 7.1: Multi-Tier System Architecture and Information Flow",
        [
            "[Tier 1: Telemetry & Disjoint Splits] C-MAPSS FD001 (50/20/10/20), FD002 (130/52/26/52), FD004 (124/50/25/50)",
            "  ├── [Training Split] → Fit training Z-scores & K-means 6 regimes → Fit GBR & LSTM (target: min(RUL, 125))",
            "  ├── [Validation Split] → Grid search (γ=2, β=−ln 2) & Matched-control baseline tuning (Zero test leakage)",
            "  ├── [Calibration Split] → Reserved engine-weighted quantiles (finite mass m/(m+1); regime fallback mg ≥ 10)",
            "  └── [Held-Out Test Split] → STRICT OFFLINE BOUNDARY (Isolated unseen engines, zero feedback to selection)",
            "[Tier 4: Frozen Decision Policy] Input: L(t) = max(0, p̂ − q̂ · a(p̂)) → Trigger: Maintain iff L(t) ≤ 1.0 cycle",
            "[Tier 5: Offline Simulator Replay] Standardized Cost Units: CPM=1.0, CFAIL=5.0, CWASTE=0.20/cycle | 10k Bootstraps",
            "[Digital Twin Replay Engine] ISO 23247 Sync | State Machine | Parity ≤ 10^-4 | FastAPI (:8000) & HTML5 Cockpit"
        ],
        border_color="0969DA", fill_color="F0F8FF"
    ))
    body_elements.append(p(
        "Figure 7.1: Multi-Tier System Architecture and Information Flow. Telemetry is partitioned by physical engine unit across disjoint splits. "
        "Training parameters and conformal calibration bounds flow strictly forward into the frozen decision policy. Held-out test evaluation is isolated "
        "behind a strict offline boundary with zero feedback to model selection or parameter tuning.",
        is_italic=True, size=20, space_after=180
    ))

    # Figure 7.2 Callout Box
    body_elements.append(box_callout(
        "FIGURE 7.2: Causal Sliding Lookback Window Construction & Target Attachment",
        [
            "Timeline:  [Cycles 1 … 29 (Warm-Up Horizon)] ───────► [Causal Window: Cycles t−29 … t] ───────► [Cycle t+1 … Ti]",
            "  • Warm-Up (1..29): Telemetry buffer accumulates; zero padding forbidden; inference strictly deferred.",
            "  • Causal Observation Window (W = 30 cycles, Stride = 1): Strictly within engine boundaries; zero future snooping.",
            "  • Dual Feature Representations at cycle t:",
            "      - PyTorch LSTM Tensor: 2D Matrix (30 time steps × 17 sensor/setting channels) for sequential memory.",
            "      - Scikit-Learn GBR Vector: 1D Vector (510 features) flattened in C-order (row-major) for quantile trees.",
            "  • Dual Target Ground Truth Formulations at cycle t:",
            "      - Training Target: y_train = min(Ti − t, 125 cycles) [Piecewise-linear early-life capping convention].",
            "      - Evaluation Target: y_eval = Ti − t cycles [Uncapped true Remaining Useful Life for honest audit]."
        ],
        border_color="1A7F37", fill_color="F2FFF5"
    ))
    body_elements.append(p(
        "Figure 7.2: Causal Sliding Lookback Window Construction (W = 30), Dual Representation Mappings (Sequential LSTM Matrix vs. Flattened GBR Vector), "
        "and Target Ground Truth Assignment (Capped Training RUL vs. Uncapped Evaluation RUL).",
        is_italic=True, size=20, space_after=180
    ))

    # Figure 7.3 Callout Box
    body_elements.append(box_callout(
        "FIGURE 7.3: Cycle-by-Cycle Digital Twin Replay Engine and Decision Flowchart",
        [
            "[Step 1] Ingest telemetry observation for engine i at cycle t.",
            "[Step 2] Decision: Is t < 30? ──► YES: Buffer telemetry; Status: WARMING_UP; Advance to cycle t + 1.",
            "                           └──► NO (t ≥ 30): Proceed to operational inference.",
            "[Step 3] Extract active causal window Xi(t) ∈ ℝ^(30 × 17); apply training Z-scores (μ_train, σ_train).",
            "[Step 4] Execute dual forward pass: GBR & LSTM → p̂(t); retrieve regime threshold q̂_1−α^(k); invert to [L(t), U(t)].",
            "[Step 5] Compute dynamic Health Index: HI(t) = min(1.0, p̂(t) / 125).",
            "[Step 6] Decision: Is L(t) ≤ 1.0 Cycle? ──► YES: Dispatch Planned Overhaul; Status: MAINTAINED; End episode.",
            "                                     └──► NO: Check if terminal cycle.",
            "[Step 7] Decision: Is t = Ti (Failure)? ──► YES: In-Service Failure; Penalty CFAIL=5.0 SCU; Status: FAILED; End.",
            "                                     └──► NO: Set alert (NOMINAL/ADVISORY); Stream to port 8000; t ← t + 1."
        ],
        border_color="BC4C00", fill_color="FFF8F0"
    ))
    body_elements.append(p(
        "Figure 7.3: Cycle-by-Cycle Digital Twin Replay Engine and Sequential Maintenance Decision Workflow. Telemetry frames enter the causal buffer; "
        "once t ≥ 30, point predictions and conformal bounds are computed. A maintenance intervention is dispatched when the conservative lower bound "
        "Li(t) breaches the 1.0 cycle threshold, preventing costly in-service failure while avoiding excessive wasted component life.",
        is_italic=True, size=20, space_after=240
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
