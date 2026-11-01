import os
import subprocess
import zipfile

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(DIR, "proposed_methodology.html")
PDF_PATH = os.path.join(DIR, "proposed_methodology.pdf")
DOCX_PATH = os.path.join(DIR, "proposed_methodology.docx")

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

    def formula(text, space_after=160):
        xml_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:line="360" w:lineRule="auto" w:after="{space_after}"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:i/><w:sz w:val="22"/></w:rPr>
        <w:t xml:space="preserve">{xml_text}</w:t>
      </w:r>
    </w:p>"""

    body_elements = []

    # Main Heading
    body_elements.append(p("6. Proposed Methodology", is_bold=True, size=28, space_after=240))

    # Subsection 6.1
    body_elements.append(p("6.1 Methodological Framework and Algorithmic Overview", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The proposed IntelliTwin methodology establishes an integrated, mathematically grounded pipeline that transforms "
        "high-frequency multivariate telemetry from degrading industrial rotational machinery into calibrated, risk-aware "
        "sequential maintenance decisions [1]–[3]. Existing predictive maintenance approaches predominantly exhibit severe "
        "methodological fragmentation: machine learning models optimize symmetric statistical loss functions (e.g., Mean Squared Error) "
        "decoupled from operational cost penalties [1], [4]; conformal prediction algorithms evaluate marginal coverage in isolation without "
        "adapting to regime-induced non-exchangeability [3], [9]; and maintenance decision models rely on parametric distributional "
        "assumptions that fail under non-linear wear dynamics [5], [6]."
    ))
    body_elements.append(p(
        "To resolve these limitations, the IntelliTwin framework formulates a unified seven-stage methodological pipeline governed by rigorous data-leakage controls:"
    ))
    body_elements.append(li(
        "1.", "Causal Telemetry Ingestion and Multi-Regime Normalization:",
        "Standardizing continuous multivariate sensor streams from NASA C-MAPSS under strict 30-cycle causal lookback windowing (W = 30) "
        "and training-only Z-score normalization [1]."
    ))
    body_elements.append(li(
        "2.", "Dual Base Prognostic Estimation:",
        "Generating continuous point forecasts ŷi(t) of Remaining Useful Life via complementary shallow gradient-boosted decision trees "
        "(HistGradientBoostingRegressor) and deep recurrent neural networks (PyTorch LSTM) [3], [4]."
    ))
    body_elements.append(li(
        "3.", "Engine-Weighted Asymmetric Conformal Calibration:",
        "Inverting nonconformity scores weighted at the engine level to construct finite-sample prediction intervals C_(1-α)(Xi(t)) = [Li(t), Ui(t)] "
        "targeting nominal 90% coverage (1 - α = 0.90) [7], [9]."
    ))
    body_elements.append(li(
        "4.", "Condition-Adaptive Regime and Wear-Stage Partitioning:",
        "Structuring calibration bins across discrete operational flight regimes (k = 6) and piece-wise linear wear stages (t → Ti) "
        "to preserve conditional reliability under operational drift [4], [10]."
    ))
    body_elements.append(li(
        "5.", "Discrete-Event Sequential Maintenance Utility Simulation:",
        "Evaluating dynamic stopping times τi governed by lower prediction bounds Li(t) under asymmetric operational economics "
        "(C_FAIL ≫ C_PM) formalized in Standardized Cost Units (SCU) [5], [8]."
    ))
    body_elements.append(li(
        "6.", "Matched-Conservatism Attribution Auditing:",
        "Contrasting policy outcomes against widened-interval, safety-margin, and early-intervention control families to verify genuine decision-relevant uncertainty value [8], [12]."
    ))
    body_elements.append(li(
        "7.", "Digital Twin Replay Synchronization:",
        "Mirroring asset degradation in real time via an offline trace-driven replay engine (TwinReplayEngine) with strict numerical verification parity (atol ≤ 10^-4) linked to a FastAPI REST service and operator dashboard [2], [13], [14]."
    ))

    # Subsection 6.2
    body_elements.append(p("6.2 Telemetry Ingestion, Anti-Leakage Windowing and Normalization", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The experimental data foundation is established using the Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) "
        "benchmark corpus developed by NASA Ames Research Center [1]. To rigorously investigate multi-regime degradation dynamics, single-condition "
        "baselines, and cross-fault generalizability, three distinct sub-corpora are utilized:"
    ))
    body_elements.append(li(
        "•", "FD002 (Primary Multi-Regime Benchmark):",
        "260 training engines and 259 test engines operating across six discrete environmental regimes (altitude 0–42,000 ft, Mach number 0.0–0.84, "
        "throttle resolver angle 20–100) subject to high-pressure compressor (HPC) degradation."
    ))
    body_elements.append(li(
        "•", "FD001 (Single-Condition Control Benchmark):",
        "100 training engines and 100 test engines operating under sea-level static flight conditions with single-mode HPC degradation, providing a stationary reference baseline."
    ))
    body_elements.append(li(
        "•", "FD004 (Multi-Regime / Multi-Fault Robustness Benchmark):",
        "249 training engines and 248 test engines operating across six flight conditions with combined HPC and fan degradation modes."
    ))

    body_elements.append(p("Causal Sliding Window Formulation", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "At each discrete operating cycle t ≥ W, historical multivariate sensor telemetry is segmented into a causal sliding lookback "
        "window with fixed temporal horizon W = 30 cycles:"
    ))
    body_elements.append(formula("Xi(t) = [xi(t - W + 1), xi(t - W + 2), ..., xi(t)]^T  ∈  R^(W × d)"))
    body_elements.append(p(
        "where xi(τ) ∈ R^d denotes the sensory observation vector recorded for engine i at operating cycle τ. Causal windowing enforces "
        "that predictions at cycle t depend strictly on historical observations τ ≤ t, eliminating prospective temporal data leakage. "
        "During the initial warm-up phase (1 ≤ t < W), prognostic inference is deferred until a complete 30-cycle observation history is accumulated."
    ))

    body_elements.append(p("Feature Selection and Sensor Pruning", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "The raw C-MAPSS telemetry schema contains 26 columns: engine identifier, cycle index, three operational flight settings, and "
        "21 thermo-mechanical degradation sensors. An automated variance and rank-correlation audit across all datasets revealed six completely "
        "invariant or uninformative channels exhibiting zero variance or uninformative responses:"
    ))
    body_elements.append(formula("S_dropped = { s1 (T2), s5 (P2), s6 (P15), s10 (epr), s16 (farB), s19 (Nf_dmd) }"))
    body_elements.append(p(
        "These six invariant channels are pruned to prevent covariance rank deficiency and numerical instability during gradient backpropagation. "
        "The retained feature space comprises d = 17 dimensions: three operational flight condition settings (z1, z2, z3) and 14 informative degradation "
        "sensors (total temperatures at LPC/HPC/LPT outlets, total pressures, physical and corrected core/fan rotational speeds, static pressure, "
        "fuel flow ratio, coolant bleed rates)."
    ))

    body_elements.append(p("Anti-Leakage Normalization and Partitioning", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "To prevent data snooping across experimental splits, Z-score standardization parameters (mean μ_train and standard deviation σ_train) "
        "are computed exclusively on the designated training split:"
    ))
    body_elements.append(formula("X̃i(t) = (Xi(t) - μ_train) / (σ_train + ε)"))
    body_elements.append(p(
        "where ε = 10^-8 prevents division by zero. The exact training parameters (μ_train, σ_train) are subsequently applied immutably to normalize "
        "calibration, validation, and held-out test splits. Partitioning is strictly enforced at the engine level: all time-series observations "
        "originating from a given physical engine i belong exclusively to one split (Train, Calibration, Validation, or Test), ensuring zero inter-engine correlation leakage."
    ))

    # Subsection 6.3
    body_elements.append(p("6.3 Base Prognostic Regression Models", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "Prognostic regression estimates the continuous Remaining Useful Life yi(t) = Ti - t directly from the standardized window X̃i(t), "
        "where Ti denotes the total failure cycle of engine i. In accordance with standard aerospace reliability engineering [1], RUL targets "
        "are capped at an upper piece-wise linear threshold R_max = 125 cycles:"
    ))
    body_elements.append(formula("yi*(t) = min(R_max, Ti - t)"))
    body_elements.append(p(
        "reflecting the empirical physical reality that initial operational wear does not exhibit measurable degradation signatures during early engine life. "
        "To evaluate algorithmic robustness across diverse learning paradigms, two complementary base model families are constructed and frozen:"
    ))

    body_elements.append(p("1. HistGradientBoostingRegressor (GBR)", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "The GBR base model represents high-capacity tree-based ensemble learning. The temporal window X̃i(t) ∈ R^(30 × 17) is flattened into a "
        "510-dimensional vector vi(t) = vec(X̃i(t)). Multi-quantile gradient boosting optimizes the asymmetric pinball loss function:"
    ))
    body_elements.append(formula("L_ρ(y, ŷ) = max(ρ(y - ŷ), (1 - ρ)(ŷ - y))"))
    body_elements.append(p(
        "trained across quantiles ρ ∈ {0.05, 0.50, 0.95} with histogram-binned split finding (max bins = 255, learning rate = 0.05, max depth = 8, L2 regularization = 1.0)."
    ))

    body_elements.append(p("2. PyTorch Deep Long Short-Term Memory (LSTM)", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "The LSTM base model captures temporal dependencies directly from sequential tensor representations. The architecture comprises: "
        "(i) an input recurrent layer processing sequential vectors xi(τ) ∈ R^17 over sequence length W = 30; "
        "(ii) two stacked bidirectional LSTM layers with hidden dimension h = 64 (128 units bidirectional) incorporating variational dropout (p = 0.20) "
        "between recurrent layers; (iii) a fully connected projection head with non-linear LeakyReLU activation (α = 0.01), linear projection, and a scalar "
        "output neuron forecasting continuous point predictions ŷi(t); and (iv) optimization using AdamW (β1 = 0.9, β2 = 0.999, weight decay = 10^-4, "
        "learning rate η = 10^-3) under Mean Squared Error loss with cosine annealing scheduling."
    ))
    body_elements.append(p(
        "A complete 30-model benchmark matrix (3 datasets × 2 architectures × 5 seeds [2026, 2027, 2028, 2029, 2030]) is trained and frozen under Architecture Decision Record ADR-018."
    ))

    # Subsection 6.4
    body_elements.append(p("6.4 Condition-Adaptive Hierarchical Conformal Calibration", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "To provide finite-sample, distribution-free prediction intervals with mathematically guaranteed coverage, the IntelliTwin framework "
        "formulates an engine-weighted, condition-adaptive Inductive Conformal Prediction (ICP) calibration methodology [4], [7], [9]."
    ))

    body_elements.append(p("Asymmetric Decision-Aware Nonconformity Scoring", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Standard conformal prediction utilizes symmetric absolute residuals si(t) = |yi(t) - ŷi(t)|, which treat overestimation and underestimation "
        "errors identically [4]. In safety-critical aerospace prognostics, overestimation errors (ŷ > y) risk catastrophic in-flight failure, whereas "
        "underestimation errors (ŷ < y) result merely in premature overhaul [1]. To reflect this operational asymmetry, nonconformity scoring incorporates "
        "dynamic shape factors parameterized by scaling exponent γ ∈ {0, 1, 2} and asymmetry coefficient β ∈ R:"
    ))
    body_elements.append(formula("σ(p̂) = (1 + p̂ / 125.0)^γ,       z(p̂) = exp(-p̂ / 20.0)"))
    body_elements.append(formula("a(p̂) = σ(p̂) · exp(β · z(p̂)),       b(p̂) = σ(p̂) · exp(-β · z(p̂))"))
    body_elements.append(p("The decision-aware nonconformity score function is then formulated as:"))
    body_elements.append(formula("si(t) = max( (p̂i(t) - yi(t)) / a(p̂i(t)),  (yi(t) - p̂i(t)) / b(p̂i(t)),  0 )"))
    body_elements.append(p(
        "where p̂i(t) = ŷi(t) represents the base point prediction. When γ = 0 and β = 0, the shape factors reduce to a(p̂) = 1 and b(p̂) = 1, "
        "recovering the classical symmetric absolute residual score si(t) = |yi(t) - p̂i(t)|."
    ))

    body_elements.append(p("Engine-Weighted Hierarchical Empirical Quantiles", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Because run-to-failure engine telemetry contains multiple observations per physical asset, pooling all cycle observations equally violates "
        "the foundational exchangeability assumption of conformal prediction due to strong temporal autocorrelation and unequal engine lifespans [9]. "
        "To address this clustered data structure without discarding observations, calibration quantile estimation applies exact engine-level observation weighting."
    ))
    body_elements.append(p(
        "Let D_cal denote the calibration split containing m distinct physical engines, where engine i contributes ni valid temporal windows. "
        "Each individual observation from engine i is assigned weight w_(i,t) = 1 / (m · ni), guaranteeing that every physical engine exerts identical "
        "aggregate influence ∑_t w_(i,t) = 1 / m. The engine-weighted empirical cumulative distribution function is defined as:"
    ))
    body_elements.append(formula("F_dev(q) = (1 / m) ∑_(i=1)^m [ (1 / ni) ∑_(t=1)^ni 𝕀(s_(i,t) ≤ q) ]"))
    body_elements.append(p("For a target nominal coverage level 1 - α = 0.90, the conformal quantile threshold q̂_(1-α) is defined as:"))
    body_elements.append(formula("q̂_(1-α) = inf { q ∈ R : F_dev(q) ≥ ⌈(m + 1)(1 - α)⌉ / m }"))
    body_elements.append(p("which provides finite-sample coverage validity on held-out test engines under cluster exchangeability [9]."))

    body_elements.append(p("Condition-Adaptive Regime Partitioning and Interval Inversion", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "To prevent localized undercoverage during high-stress operating regimes (e.g., high altitude and high Mach number in FD002), operational "
        "conditions are clustered into K = 6 distinct regimes using K-means clustering on flight settings (z1, z2, z3). Conformal thresholds "
        "q̂_(1-α)^(k) are calibrated conditionally within each regime cluster k ∈ {1, ..., K}, ensuring that high-stress operational profiles "
        "receive appropriately calibrated uncertainty bands [4], [10]."
    ))
    body_elements.append(p("Given the calibrated threshold q̂_(1-α), prediction intervals C_(1-α)(Xi(t)) = [Li(t), Ui(t)] are computed via exact closed-form score inversion:"))
    body_elements.append(formula("Li(t) = max(0, p̂i(t) - q̂_(1-α) · a(p̂i(t))),       Ui(t) = p̂i(t) + q̂_(1-α) · b(p̂i(t))"))
    body_elements.append(p("where Li(t) represents the conservative lower bound on Remaining Useful Life utilized for risk-directed maintenance decisions."))

    # Subsection 6.5
    body_elements.append(p("6.5 Discrete-Event Sequential Maintenance Utility Simulation", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "Operational value is realized exclusively through the maintenance intervention decisions guided by prognostic intervals [5], [8]. "
        "IntelliTwin models sequential asset health monitoring via a cycle-by-cycle discrete-event maintenance simulator."
    ))
    body_elements.append(p("Sequential Decision Rule", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "At each flight cycle t ≥ W, the Digital Twin evaluates the lower conformal bound Li(t). When the conservative lower bound drops below "
        "a prespecified operational intervention threshold θ (default θ = 0), a preventive maintenance (PM) order is dispatched:"
    ))
    body_elements.append(formula("τi = inf { t ≥ W : Li(t) ≤ θ }"))
    body_elements.append(p("where τi denotes the sequential stopping time for physical engine i."))

    body_elements.append(p("Standardized Cost Units (SCU) Lifecycle Evaluation", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "If engine retirement occurs prior to catastrophic mechanical failure (τi < Ti), planned maintenance is successfully executed. "
        "If the engine reaches its terminal cycle before maintenance is triggered (τi ≥ Ti), an unscheduled in-service failure occurs at cycle Ti. "
        "Costs are evaluated in Standardized Cost Units (SCU) under the reference scenario:"
    ))
    body_elements.append(formula("Costi(τi) = C_PM + C_WASTE · (Ti - τi)    if τi < Ti (Successful Preventive Maintenance)"))
    body_elements.append(formula("Costi(τi) = C_FAIL                              if τi ≥ Ti (Unscheduled In-Service Failure)"))
    body_elements.append(p(
        "with standardized economic weights: C_PM = 1.0 SCU (planned overhaul), C_FAIL = 5.0 SCU (unscheduled in-service failure penalty), "
        "and C_WASTE = 0.20 SCU per cycle (usable component life discarded by premature early replacement). "
        "Total fleet maintenance cost is computed as the average lifecycle expenditure: Cost̄ = (1 / N) ∑_(i=1)^N Costi(τi)."
    ))

    # Subsection 6.6
    body_elements.append(p("6.6 Controlled Attribution Protocol (Matched-Conservatism Baselines)", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "A critical methodological vulnerability in prognostic literature is the failure to disambiguate genuine uncertainty calibration "
        "from trivial over-conservatism [8]. An uncalibrated heuristic that arbitrarily replaces engines 30 cycles early will trivially eliminate "
        "in-service failures (C_FAIL), but does so by squandering massive usable life (C_WASTE) [5], [8]."
    ))
    body_elements.append(p(
        "To address Research Question 3 (RQ3), IntelliTwin benchmarks the proposed decision-aware method against three prespecified matched-conservatism control families:"
    ))
    body_elements.append(li(
        "1.", "Family 1: Uniformly Widened Conformal Intervals (δ-Widened):",
        "Inflates the global conformal threshold by fixed scalar constants q̂' = q̂ + δ, testing whether improvements stem merely from wider coverage bands."
    ))
    body_elements.append(li(
        "2.", "Family 2: Point-Prediction Safety Margins (Δ-Margin):",
        "Implements deterministic safety offsets p̂'(t) = p̂(t) - Δ, triggering maintenance when p̂'(t) ≤ θ without interval calibration."
    ))
    body_elements.append(li(
        "3.", "Family 3: Earlier Scheduled Intervention Thresholds (θ-Offset):",
        "Advances maintenance triggers by raising the intervention threshold θ' = θ + τ_advance, evaluating whether simple early scheduling reproduces the proposed method's cost savings."
    ))
    body_elements.append(p(
        "A positive decision attribution is established only if the proposed method achieves statistically significant lifecycle cost savings "
        "(Δ_cost > 0.20 SCU per engine) against every matched-conservatism control family [12]."
    ))

    # Subsection 6.7
    body_elements.append(p("6.7 Statistical Inference Protocol and Decision Rules", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "To ensure rigorous hypothesis testing without distributional assumptions, statistical inference is conducted using engine-level "
        "cluster bootstrap with 10,000 resamples [12]."
    ))
    body_elements.append(p("Family-Wise Error Rate Control", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Across the four formal research questions (RQ1–RQ4), family-wise type I error is strictly controlled at α_family = 0.05 using the Bonferroni correction: "
        "α_test = 0.05 / 4 = 0.0125. All decision intervals are evaluated as 98.75% two-sided percentile bootstrap intervals ([Q_0.00625, Q_0.99375])."
    ))
    body_elements.append(p("Two One-Sided Tests (TOST) for Robustness", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "For Research Question 4 (RQ4), cross-condition robustness across the six evaluation cells (FD001, FD002, FD004 × GBR, LSTM) is audited "
        "against pre-registered non-harm equivalence bounds [12]:"
    ))
    body_elements.append(formula("Lower 98.75% CI of Δ_cost ≥ -0.20 SCU,       Lower 98.75% CI of Δ_error ≥ -0.01"))
    body_elements.append(p("guaranteeing that condition-adaptive calibration does not induce material operational degradation in any individual configuration."))

    # Subsection 6.8
    body_elements.append(p("6.8 Digital Twin Synchronization Replay Prototype", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "To ground the algorithmic formulation in operational engineering reality, IntelliTwin implements a real-time trace-driven Digital Twin "
        "synchronization engine (TwinReplayEngine) [2], [13], [14]."
    ))
    body_elements.append(p("Trace-Driven State Synchronization", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "The replay engine ingests pre-recorded run-to-failure sensor matrices and emits discrete telemetry frames cycle-by-cycle. State synchronization "
        "adheres to ISO 23247 digital twin principles [14], maintaining: (i) an active 30-cycle causal lookback window Xi(t); (ii) real-time Z-score scaling X̃i(t); "
        "(iii) dual RUL inference ŷ_GBR(t) and ŷ_LSTM(t); (iv) calibrated conformal uncertainty bounds [Li(t), Ui(t)]; (v) a dynamic health index estimator "
        "HIi(t) = min(1.0, p̂i(t) / R_max); and (vi) automated maintenance alert triggers (NOMINAL, ADVISORY, CRITICAL_INTERVENTION)."
    ))
    body_elements.append(p("Numerical Parity Verification", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("To guarantee that real-time replay does not introduce numerical artifacts, the replay engine is audited against offline batch execution:"))
    body_elements.append(formula("max_t | p̂_stream(t) - p̂_batch(t) | ≤ 10^-4,       max_t | L_stream(t) - L_batch(t) | ≤ 10^-4"))
    body_elements.append(p(
        "Parity is verified across all benchmark datasets via 37 automated pytest modules, establishing that the interactive Digital Twin operator "
        "dashboard at port 8000 displays mathematically identical outputs to the scientific evaluation pipeline."
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
