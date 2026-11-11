import os
import re
import subprocess
import base64
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

HTML_PATH = os.path.join(BASE_DIR, "research_paper_ieee_6pages.html")
PDF_PATH = os.path.join(BASE_DIR, "research_paper_ieee_6pages.pdf")
DOCX_PATH = os.path.join(BASE_DIR, "research_paper_ieee_6pages.docx")
TEX_PATH = os.path.join(BASE_DIR, "research_paper_ieee_6pages.tex")
BIB_PATH = os.path.join(BASE_DIR, "research_paper_ieee_6pages.bib")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    alt_chrome = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if os.path.exists(alt_chrome):
        CHROME_PATH = alt_chrome

def get_base64_image(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(path)[1].lower().replace(".", "")
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"

img_effects_path = os.path.join(BASE_DIR, "research_manuscript", "figure_sources", "scale_asymmetry_routing_paired_effects.png")
img_miss_path = os.path.join(BASE_DIR, "research_manuscript", "figure_sources", "lower_upper_miss_rates_by_lifecycle_stage.png")
img_ablation_path = os.path.join(BASE_DIR, "research_manuscript", "figure_sources", "ablation_cost_vs_coverage.png")

img_effects = get_base64_image(img_effects_path)
img_miss = get_base64_image(img_miss_path)
img_ablation = get_base64_image(img_ablation_path)

def build_html(font_size="9.5pt", line_height="1.20", margin_v="0.75in", margin_h="0.58in", p_margin="3.6pt"):
    raw_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance</title>
<style>
  @page {{
    size: A4;
    margin: MARGIN_V MARGIN_H MARGIN_V MARGIN_H;
  }}

  body {{
    font-family: 'Times New Roman', Times, serif;
    font-size: FONT_SIZE;
    line-height: LINE_HEIGHT;
    color: #000000;
    margin: 0;
    padding: 0;
    background: #ffffff;
    text-align: justify;
    text-justify: inter-word;
  }}

  .title-block {{
    text-align: center;
    margin-bottom: 11pt;
  }}

  h1.paper-title {{
    font-size: 19pt;
    font-weight: bold;
    line-height: 1.15;
    margin: 0 0 9pt 0;
    letter-spacing: -0.2pt;
  }}

  .authors-block {{
    text-align: center;
    margin-bottom: 12pt;
    line-height: 1.35;
  }}

  .author-names {{
    font-size: 11.2pt;
    font-weight: bold;
    margin-bottom: 3.5pt;
  }}

  .author-affiliations {{
    font-size: 8.8pt;
    color: #222222;
  }}

  /* Two Column Layout */
  .columns-container {{
    column-count: 2;
    column-gap: 0.22in;
    column-fill: balance;
  }}

  .abstract-keywords-container {{
    margin: 0 0 9pt 0;
    width: 100%;
    font-size: 8.4pt;
    line-height: 1.22;
    text-align: justify;
    break-inside: avoid;
    -webkit-column-break-inside: avoid;
    page-break-inside: avoid;
  }}

  .abstract-heading, .keywords-heading {{
    font-weight: bold;
    font-style: italic;
    display: inline;
  }}

  h2 {{
    font-size: 9.9pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.4pt;
    text-align: center;
    margin-top: 9pt;
    margin-bottom: 3.5pt;
    padding: 1pt 0;
    break-after: avoid;
  }}

  h3 {{
    font-size: 9.3pt;
    font-weight: bold;
    font-style: italic;
    margin-top: 5.5pt;
    margin-bottom: 2.5pt;
    break-after: avoid;
  }}

  p {{
    text-indent: 1em;
    margin-top: 0;
    margin-bottom: P_MARGIN;
  }}

  p.no-indent {{
    text-indent: 0;
  }}

  .equation {{
    text-align: center;
    margin: 4pt 0;
    font-style: italic;
    font-size: 9.2pt;
  }}

  .equation .eq-num {{
    float: right;
    font-style: normal;
  }}

  table.academic-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 5.5pt 0 4pt 0;
    font-size: 7.7pt;
    line-height: 1.15;
    break-inside: avoid;
  }}

  table.academic-table caption {{
    font-size: 8pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    margin-bottom: 3pt;
    text-align: center;
  }}

  table.academic-table th {{
    border-top: 1.2pt solid #000;
    border-bottom: 0.8pt solid #000;
    padding: 2.5pt 2.5pt;
    font-weight: bold;
    text-align: center;
  }}

  table.academic-table td {{
    padding: 2pt 2.5pt;
    text-align: center;
  }}

  table.academic-table tr.mid-line td {{
    border-top: 0.5pt solid #ddd;
  }}

  table.academic-table tr.total-line td {{
    border-top: 0.8pt solid #000;
    border-bottom: 1.2pt solid #000;
    font-weight: bold;
  }}

  .figure-container {{
    width: 100%;
    margin: 5.5pt 0 4pt 0;
    text-align: center;
    break-inside: avoid;
  }}

  .figure-container img {{
    width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
  }}

  .figure-caption {{
    font-size: 7.9pt;
    line-height: 1.16;
    margin-top: 3pt;
    text-align: justify;
  }}

  .figure-caption strong {{
    font-weight: bold;
  }}

  .algorithm-box {{
    border: 1pt solid #000;
    padding: 4.5pt 6pt;
    margin: 5.5pt 0;
    font-size: 7.8pt;
    line-height: 1.18;
    background: #fafafa;
    break-inside: avoid;
  }}

  .algorithm-title {{
    font-weight: bold;
    border-bottom: 0.8pt solid #000;
    padding-bottom: 2pt;
    margin-bottom: 3pt;
    text-transform: uppercase;
    letter-spacing: 0.3pt;
  }}

  .algorithm-box ol {{
    margin: 0;
    padding-left: 14pt;
  }}

  .algorithm-box li {{
    margin-bottom: 1.5pt;
  }}

  .references-list {{
    font-size: 7.6pt;
    line-height: 1.13;
    padding-left: 14pt;
    margin-top: 4pt;
    margin-bottom: 0;
  }}

  .references-list li {{
    margin-bottom: 2.2pt;
    text-indent: -1.2em;
    padding-left: 1.2em;
  }}

  a.doi-link {{
    color: #000000;
    text-decoration: none;
  }}
</style>
</head>
<body>

<div class="title-block">
  <h1 class="paper-title">IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance</h1>
  <div class="authors-block">
    <div class="author-names">Shiksha Pandey&sup1;, Mayank Singh&sup2;</div>
    <div class="author-affiliations">
      &sup1;Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, India<br/>
      &sup2;Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, India
    </div>
  </div>
</div>

<div class="columns-container">

  <div class="abstract-keywords-container">
    <p class="no-indent">
      <span class="abstract-heading">Abstract&mdash;</span>In industrial predictive maintenance of gas turbine engines, unexpected mechanical failure incurs severe airworthiness risks and catastrophic economic penalties (5x to 10x scheduled overhaul), while premature overhaul discards valuable residual component life. Conventional Remaining Useful Life (RUL) prognostic systems rely on deterministic point estimators that optimize symmetric cycle error metrics without quantifying prediction variance or aligning with downstream maintenance costs. Standard inductive conformal prediction provides marginal coverage guarantees but conceals severe conditional undercoverage across accelerating degradation stages and varying operating regimes. In this work, we present <strong>IntelliTwin</strong>, an uncertainty-aware prognostic framework integrating Gradient Boosted Regressors (GBR) and Long Short-Term Memory (LSTM) networks with hierarchical, decision-aware conformal calibration. IntelliTwin enforces strictly disjoint engine-level partitioning, causal temporal windowing (w=30, stride 1), exact rational engine weighting (m/(m+1) mass), and an asymmetric nonconformity score parameterized by scale dilation (&gamma;=2) and directional asymmetry (&beta;=-ln 2). We evaluate the framework under a frozen confirmatory protocol on 122 held-out test engines from NASA C-MAPSS sub-corpora FD001, FD002, and FD004 across 10,000 lifetime-stratified cluster-bootstrap draws with Bonferroni-controlled 98.75% decision intervals. In confirmatory testing, the proposed method achieved substantial maintenance cost reductions (+7.50 to +11.32 Simulated Cost Units per engine on FD002) with zero fleet failures. However, under preregistered Intersection-Union Testing criteria, RQ1&ndash;RQ4 were formally classified as UNSUPPORTED because late-stage degradation coverage error breached the 0.05 ceiling (E_stage &asymp; 0.13, empirical coverage ~ 77%). Through post-confirmatory factorial ablation across 240 cells, we isolate that scale dilation (&gamma;) reduces cost by an unweighted mean of -10.48 SCU and directional asymmetry (&beta;) reduces cost by -1.21 SCU, whereas regime routing provides null effects on single-condition fleets and small cost penalties (+0.56 SCU) on multi-condition fleets due to partition sample dispersion. Finally, we provide an open, fully reproducible historical validation-telemetry replay prototype.
    </p>
    <div style="margin-top: 3.5pt;">
      <span class="keywords-heading">Index Terms&mdash;</span>Predictive Maintenance, Remaining Useful Life, Digital Twin, Conformal Prediction, Uncertainty Quantification, Condition-Adaptive Calibration, Turbofan Engines, C-MAPSS.
    </div>
  </div>

  <h2>I. Introduction</h2>

  <p>
    Prognostics and Health Management (PHM) for high-value rotating machinery has emerged as a cornerstone of operational safety, asset reliability, and life-cycle economic sustainability across commercial aviation, energy generation, and advanced manufacturing [29], [13]. In commercial aircraft gas turbine turbofans, unexpected mechanical failures and in-flight shutdowns impose disproportionate penalties&mdash;frequently exceeding scheduled shop-visit overhaul costs by five- to ten-fold&mdash;while introducing grave airworthiness hazards [18], [23]. Conversely, legacy preventive maintenance paradigms relying on rigid, flight-hour schedules discard substantial healthy operational lifespan, inflating life-cycle overhaul expenditure and supply-chain logistical overhead [20], [17].
  </p>

  <p>
    Modern data-driven prognostic paradigms utilize multi-sensor telemetry to predict an asset's Remaining Useful Life (RUL) [5]. Deep learning architectures, including Long Short-Term Memory (LSTM) networks, temporal convolutional networks, and gradient-boosted decision trees, have demonstrated impressive cycle-level error reductions on standardized run-to-failure benchmarks such as NASA C-MAPSS [29], [8]. However, deterministic point-regression architectures exhibit three structural shortcomings when deployed into mission-critical maintenance pipelines:
  </p>

  <p>
    <em>1) Unquantified Point Variance:</em> A single deterministic cycle prediction provides no measure of epistemic or aleatoric uncertainty, preventing fleet operators from distinguishing high-confidence prognostic estimates from high-risk extrapolations [26], [3]. Point predictors provide false precision, particularly when machinery experiences novel flight operating conditions or non-stationary degradation dynamics.
  </p>

  <p>
    <em>2) Conditional Reliability Breakdown:</em> Inductive split conformal prediction has gained prominence as an attractive distribution-free methodology capable of delivering finite-sample prediction intervals [L, U] with guaranteed marginal coverage &fnof;(y &isin; [L, U]) &ge; 1 - &alpha; [24], [8]. However, marginal coverage guarantees do not ensure conditional coverage across varying operating regimes or accelerating wear stages [9], [4]. In turbofans experiencing dynamic throttle and atmospheric variations, standard conformal calibrators severely undercover during late degradation phases where accurate risk bounds are most essential.
  </p>

  <p>
    <em>3) Decoupling of Uncertainty from Economic Consequences:</em> Standard prognostic objectives minimize symmetric loss functions (e.g., Mean Squared Error) that penalize late predictions identically to early predictions [16], [2]. In operational aviation maintenance, overestimating RUL leads to uncontained physical failure, catastrophic unscheduled engine removals, and severe airworthiness penalties. In contrast, underestimating RUL merely causes premature scheduled overhaul, which incurs mild life-waste penalties. Deterministic models and standard symmetric conformal bands remain entirely decoupled from this profound economic asymmetry.
  </p>

  <p>
    To resolve these limitations, this paper presents <strong>IntelliTwin</strong>, an uncertainty-aware, decision-aware Digital Twin framework designed specifically for turbofan predictive maintenance. The primary technical contributions of this research are:
  </p>

  <p>
    &bull; <strong>Architectural Integration:</strong> A unified prognostic pipeline combining dual base backbones (GBR and LSTM) with condition-adaptive conformal calibration under strict disjoint engine-level partitioning and causal temporal windowing (w=30, stride 1).
  </p>

  <p>
    &bull; <strong>Decision-Aware Asymmetric Calibration:</strong> A novel nonconformity score parameterized by scale dilation (&gamma;=2.0) and directional asymmetry (&beta;=-ln 2 &asymp; -0.6931), paired with exact rational engine weighting (w_i = m_i/(m_i+1)) to resolve intra-engine telemetry correlation.
  </p>

  <p>
    &bull; <strong>Rigorous Confirmatory Audit:</strong> Pre-registered evaluation on 122 held-out test engines across NASA C-MAPSS FD001, FD002, and FD004 under 10,000 cluster-bootstrap resamples with Bonferroni-controlled 98.75% decision intervals.
  </p>

  <p>
    &bull; <strong>Factorial Component Isolation:</strong> An exhaustive 240-cell factorial ablation isolating the paired impacts of scale dilation, directional asymmetry, and regime routing on maintenance cost and conditional coverage.
  </p>

  <p>
    &bull; <strong>Reproducible Telemetry Replay:</strong> An open historical validation prototype operating with zero temporal lookahead, latency &lt; 15 ms, and audited numerical parity.
  </p>

  <h2>II. Related Work</h2>

  <h3>A. Data-Driven Prognostics for Turbofan Machinery</h3>
  <p>
    RUL estimation has transitioned from empirical physics-of-failure modeling to multivariate data-driven learning [29]. Deep recurrent neural networks, temporal convolutional networks, and gradient-boosted ensembles have achieved state-of-the-art cycle accuracy on run-to-failure turbofan benchmarks [8], [5], [6]. Despite low root mean squared errors, deterministic architectures cannot assess their own reliability under novel degradation dynamics. In safety-critical aviation, point predictions fail to convey the risk envelope required for dispatch planning.
  </p>

  <h3>B. Uncertainty Quantification in PHM</h3>
  <p>
    Probabilistic methods, such as Gaussian Process Regression, Bayesian Neural Networks, and Monte Carlo dropout, offer uncertainty intervals but depend heavily on restrictive parametric assumptions or expensive sampling [26], [10]. Inductive conformal prediction has recently emerged as an attractive distribution-free alternative [24]. However, standard split conformal calibrators guarantee only marginal coverage across the entire test distribution [24], [8]. Prior studies confirm that marginal guarantees frequently fail conditionally in degrading assets, yielding systematic undercoverage as machinery approaches end-of-life [9], [4].
  </p>

  <h3>C. Digital Twins and Decision-Directed Prognostic Inference</h3>
  <p>
    Digital Twins couple physical asset sensor streams with virtual computational models to mirror real-time operational health [27], [15], [12]. While early industrial implementations focused on 3D geometric visualization and telemetry dashboards [19], [21], recent advances prioritize closed-loop predictive decision-making [14], [25], [2]. Incorporating asymmetric loss structures into conformal inference allows intervals to align directly with operational utility, yet existing frameworks have not been validated under multi-regime turbofan degradation.
  </p>

  <h3>D. Identified Research Gaps</h3>
  <p>
    Despite rapid progress, three key research gaps remain: (1) standard conformal calibrators fail to account for hierarchical correlation among multi-cycle observations from identical engines; (2) operating regime transitions induce non-exchangeability across sub-populations; and (3) prognostic intervals remain disconnected from downstream maintenance cost matrices. IntelliTwin is designed specifically to bridge these gaps.
  </p>

  <h2>III. Problem Formulation &amp; Hypotheses</h2>

  <h3>A. Degradation Process and Causal Windowing</h3>
  <p>
    Consider a fleet of turbofan engines indexed by i &isin; {1, ..., N}. Each engine is observed across discrete operating cycles t &isin; {1, ..., T_i}, where T_i denotes the end-of-life failure cycle. At each cycle t, the engine emits raw sensor telemetry and operational setting vectors x_{i,t} &isin; &real;^D. The true Remaining Useful Life is defined causally as y_{i,t} = T_i - t. To prevent temporal leakage, feature representations are constructed via a causal rolling window of length w = 30 and stride 1:
  </p>
  <div class="equation">
    X_{i,t} = [x_{i, t-w+1}, x_{i, t-w+2}, ..., x_{i,t}] &isin; &real;^{w &times; D}
    <span class="eq-num">(1)</span>
  </div>
  <p class="no-indent">
    For initial cycles t &lt; w, the window is padded causally by repeating the initial cycle observation x_{i,1}. This ensures strictly zero future lookahead.
  </p>

  <h3>B. Sequential Maintenance Simulator Contract</h3>
  <p>
    Let [L_{i,t}, U_{i,t}] be the predicted conformal RUL interval at cycle t. A maintenance policy initiates scheduled overhaul at the earliest cycle t where the lower bound reaches the planning horizon H = 15 cycles:
  </p>
  <div class="equation">
    t_{\text{act}} = \min \{ t \ge 1 \mid L_{i,t} \le H \}
    <span class="eq-num">(2)</span>
  </div>
  <p class="no-indent">
    If t_{\text{act}} &ge; T_i, the asset experiences an uncontained physical failure at cycle T_i, incurring catastrophic penalty C_{\text{FAIL}} = 5.0 Simulated Cost Units (SCU) alongside base overhaul cost C_{\text{PM}} = 1.0 SCU. If t_{\text{act}} &lt; T_i, proactive maintenance is completed safely, but discarded operational cycles incur waste penalty C_{\text{WASTE}} = 0.20 SCU per unused cycle:
  </p>
  <div class="equation">
    \text{Cost}(t_{\text{act}}, T_i) = C_{\text{PM}} + C_{\text{FAIL}} \cdot \mathbb{I}(t_{\text{act}} \ge T_i) + C_{\text{WASTE}} \cdot (T_i - t_{\text{act}})^+
    <span class="eq-num">(3)</span>
  </div>
  <p class="no-indent">
    The fleet-wide objective is to minimize average cost per engine across the test set:
  </p>
  <div class="equation">
    \text{Cost}_{\text{fleet}} = \frac{1}{N_{\text{test}}} \sum_{i=1}^{{N_{\text{test}}}} \text{Cost}(t_{\text{act}}^{(i)}, T_i)
    <span class="eq-num">(4)</span>
  </div>

  <h3>C. Formal Research Questions and Hypotheses</h3>
  <p>
    The framework evaluates four pre-registered research questions:
  </p>
  <p>
    &bull; <strong>RQ1 (Cost Reduction):</strong> Does IntelliTwin achieve statistically significant cost savings over baseline conformal prediction?
  </p>
  <div class="equation">
    H_0^{(1)}: \Delta_{\text{cost}} \le 0 \quad \text{vs.} \quad H_1^{(1)}: \Delta_{\text{cost}} > 0
    <span class="eq-num">(5)</span>
  </div>
  <p>
    &bull; <strong>RQ2 (Safety Preservation):</strong> Does IntelliTwin avoid increasing fleet failure rates?
  </p>
  <div class="equation">
    H_0^{(2)}: \Delta_{\text{fail}} > 0 \quad \text{vs.} \quad H_1^{(2)}: \Delta_{\text{fail}} \le 0
    <span class="eq-num">(6)</span>
  </div>
  <p>
    &bull; <strong>RQ3 (Interval Compactness):</strong> Does the method avoid excessive interval inflation?
  </p>
  <div class="equation">
    H_0^{(3)}: D_{\text{width}} \le 0 \quad \text{vs.} \quad H_1^{(3)}: D_{\text{width}} > 0
    <span class="eq-num">(7)</span>
  </div>
  <p>
    &bull; <strong>RQ4 (Conditional Reliability):</strong> Does conditional coverage error remain below the 0.05 tolerance across all lifecycle stages?
  </p>
  <div class="equation">
    H_0^{(4)}: E_{\text{stage}} > 0.05 \quad \text{vs.} \quad H_1^{(4)}: E_{\text{stage}} \le 0.05
    <span class="eq-num">(8)</span>
  </div>
  <p class="no-indent">
    Under Intersection-Union Testing (IUT), overall success requires rejecting all four null hypotheses simultaneously: &Psi; = &cap;_{k=1}^4 (H_0^{(k)} \text{ rejected}).
  </p>

  <h2>IV. Proposed IntelliTwin Framework</h2>

  <h3>A. Architectural Overview</h3>
  <p>
    The IntelliTwin architecture encompasses five sequential modules: (1) streaming telemetry ingestion and causal windowing; (2) operating regime routing; (3) base prognostic point estimation; (4) asymmetric decision-aware conformal calibration; and (5) sequential maintenance decision triggering.
  </p>

  <h3>B. Base Deep Prognostic Backbones</h3>
  <p>
    We implement two complementary prognostic estimators:
  </p>
  <p>
    <em>1) Gradient Boosted Regressor (GBR):</em> LightGBM-based histogram gradient boosting operating on flattened 510-dimensional window vectors (w=30, 17 channels). Hyperparameters: 300 estimators, learning rate 0.05, max leaf nodes 31, subsample ratio 0.8.
  </p>
  <p>
    <em>2) Long Short-Term Memory (LSTM):</em> Dual-layer recurrent network (64 and 32 hidden units) with recurrent dropout (0.10) and linear projection, trained via Adam (learning rate 10^-3, batch size 64, early stopping patience 10). Five training random seeds are evaluated: [2026, 2027, 2028, 2029, 2030].
  </p>

  <h3>C. Decision-Aware Asymmetric Conformal Calibration</h3>
  <p>
    Standard conformal prediction computes nonconformity as symmetric residual magnitude |p_i - y_i|. To reflect asymmetric economic costs, IntelliTwin scales residuals by model variance &sigma;(p_i) and applies directional asymmetry parameter &beta; alongside scale dilation &gamma;:
  </p>
  <div class="equation">
    s_i = \max \left( \frac{p_i - y_i}{\sigma(p_i) e^{-\beta}}, \frac{y_i - p_i}{\sigma(p_i) e^{\beta}} \right)
    <span class="eq-num">(9)</span>
  </div>
  <p class="no-indent">
    Setting &beta; = -ln 2 &asymp; -0.6931 penalizes RUL overestimation twice as severely as underestimation, shifting lower bound L_{i,t} downwards as failure nears. Scale dilation &gamma; = 2.0 widens intervals in early life to reflect elevated epistemic variance.
  </p>

  <h3>D. Hierarchical Engine-Weighted Calibration</h3>
  <p>
    Turbofan telemetry contains variable numbers of cycles per engine (m_i), violating exchangeability. IntelliTwin assigns rational engine mass weights [25]:
  </p>
  <div class="equation">
    w_i = \frac{m_i}{m_i + 1}
    <span class="eq-num">(10)</span>
  </div>
  <p class="no-indent">
    The calibrated nonconformity quantile q* is computed as the (1 - &alpha;)-th quantile of the weighted empirical distribution. In multi-regime environments, regime-specific calibrators are deployed with automatic fallback to global calibration if sub-population sample size falls below n_{\text{min}} = 50.
  </p>

  <div class="algorithm-box">
    <div class="algorithm-title">Algorithm 1: IntelliTwin Asymmetric Calibration &amp; Policy</div>
    <ol>
      <li><strong>Inputs:</strong> Calibration telemetry D_cal, test stream X_{i,t}, target miscoverage &alpha;=0.10, horizon H=15.</li>
      <li>Train base estimator p(X) on disjoint development partition D_dev.</li>
      <li>Compute residuals r_{i,t} = y_{i,t} - p(X_{i,t}) and variance &sigma;(p) on D_cal.</li>
      <li>Evaluate asymmetric scores s_{i,t} via (9) with &gamma;=2.0 and &beta;=-ln 2.</li>
      <li>Assign rational engine weights w_i = m_i / (m_i + 1) via (10).</li>
      <li>Extract weighted quantile q* = ConformalQuantile({s_{i,t}}, {w_i}, 1-&alpha;).</li>
      <li><strong>Online Replay:</strong> For cycle t = 1, 2, ... do:</li>
      <li>&nbsp;&nbsp;Predict p_{i,t} = p(X_{i,t}) and bound L_{i,t} = p_{i,t} - q* &sigma;(p_{i,t}) e^{-\beta}.</li>
      <li>&nbsp;&nbsp;If L_{i,t} &le; H, trigger scheduled overhaul t_{\text{act}} = t; <strong>break</strong>.</li>
      <li>Compute maintenance cost via (3).</li>
    </ol>
  </div>

  <h2>V. Experimental Setup &amp; Methodology</h2>

  <h3>A. NASA C-MAPSS Fleets &amp; Sensor Selection</h3>
  <p>
    We evaluate on three standardized benchmark sub-corpora from NASA C-MAPSS:
  </p>
  <p>
    &bull; <strong>FD001:</strong> 100 train / 100 test engines, 1 operating condition (sea level), 1 failure mode (HPC degradation). Held-out test set: 20 engines.
  </p>
  <p>
    &bull; <strong>FD002:</strong> 260 train / 259 test engines, 6 operating regimes, 1 failure mode. Held-out test set: 52 engines.
  </p>
  <p>
    &bull; <strong>FD004:</strong> 249 train / 248 test engines, 6 operating regimes, 2 failure modes (HPC and fan degradation). Held-out test set: 50 engines.
  </p>
  <p class="no-indent">
    Total held-out evaluation pool encompasses 122 unique engines. Table III outlines the 14 selected sensor channels used for prognostic modeling after pruning constant signals.
  </p>

  <table class="academic-table">
    <caption>Table III: Selected Sensor Channels in NASA C-MAPSS Fleets</caption>
    <thead>
      <tr>
        <th>Index</th>
        <th>Description</th>
        <th>Units</th>
        <th>Trend</th>
        <th>Subsystem</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>s2</td>
        <td>Total temperature at LPC outlet</td>
        <td>&deg;R</td>
        <td>Increasing</td>
        <td>Low-Pressure Compressor</td>
      </tr>
      <tr>
        <td>s3</td>
        <td>Total temperature at HPC outlet</td>
        <td>&deg;R</td>
        <td>Increasing</td>
        <td>High-Pressure Compressor</td>
      </tr>
      <tr>
        <td>s4</td>
        <td>Total temperature at LPT outlet</td>
        <td>&deg;R</td>
        <td>Increasing</td>
        <td>Low-Pressure Turbine</td>
      </tr>
      <tr>
        <td>s7</td>
        <td>Total pressure at HPC outlet</td>
        <td>psia</td>
        <td>Decreasing</td>
        <td>High-Pressure Compressor</td>
      </tr>
      <tr>
        <td>s8</td>
        <td>Physical fan speed</td>
        <td>rpm</td>
        <td>Increasing</td>
        <td>Fan Rotor</td>
      </tr>
      <tr>
        <td>s9</td>
        <td>Physical core speed</td>
        <td>rpm</td>
        <td>Increasing</td>
        <td>Core Shaft</td>
      </tr>
      <tr>
        <td>s11</td>
        <td>Static pressure at HPC outlet</td>
        <td>psia</td>
        <td>Increasing</td>
        <td>Combustor / Diffuser</td>
      </tr>
      <tr>
        <td>s12</td>
        <td>Ratio of fuel flow to Ps30</td>
        <td>pps/psia</td>
        <td>Decreasing</td>
        <td>Fuel Metering Unit</td>
      </tr>
      <tr>
        <td>s13</td>
        <td>Corrected fan speed</td>
        <td>rpm</td>
        <td>Decreasing</td>
        <td>Fan Rotor</td>
      </tr>
      <tr>
        <td>s14</td>
        <td>Corrected core speed</td>
        <td>rpm</td>
        <td>Decreasing</td>
        <td>Core Shaft</td>
      </tr>
      <tr>
        <td>s15</td>
        <td>Bypass ratio</td>
        <td>&mdash;</td>
        <td>Increasing</td>
        <td>Bypass Duct</td>
      </tr>
      <tr>
        <td>s17</td>
        <td>Bleed enthalpy</td>
        <td>&mdash;</td>
        <td>Increasing</td>
        <td>Bleed Air Valves</td>
      </tr>
      <tr>
        <td>s20</td>
        <td>HPT coolant bleed flow</td>
        <td>lbm/s</td>
        <td>Decreasing</td>
        <td>High-Pressure Turbine</td>
      </tr>
      <tr class="total-line">
        <td>s21</td>
        <td>LPT coolant bleed flow</td>
        <td>lbm/s</td>
        <td>Decreasing</td>
        <td>Low-Pressure Turbine</td>
      </tr>
    </tbody>
  </table>

  <h3>B. Operating Regime Stratification</h3>
  <p>
    Operating regimes in FD002 and FD004 are identified via k-means clustering (k=6) over altitude [0, 42K ft], Mach number [0.0, 0.84], and Throttle Resolver Angle [20&deg;, 100&deg;]. Normalization parameters (&mu;_k, &sigma;_k) are estimated strictly on development splits to eliminate cross-regime data leakage.
  </p>

  <h3>C. Resampling Protocol and Bonferroni Control</h3>
  <p>
    To preserve inter-cycle correlation, statistical inference is conducted via 10,000 cluster-bootstrap draws resampled at the engine level. To strictly control family-wise error across the four research questions, confidence intervals are constructed at the Bonferroni-corrected 98.75% two-sided level (&alpha; = 0.05 / 4 = 0.0125).
  </p>

  <h2>VI. Empirical Results &amp; Audit</h2>

  <h3>A. Confirmatory Evaluation Outcomes</h3>
  <p>
    Table I details confirmatory performance across all six benchmark combinations. On FD002, IntelliTwin delivers substantial cost savings: +7.62 SCU/eng (GBR) and +10.99 SCU/eng (LSTM) over global conformal baselines, and +7.50 to +11.32 SCU/eng over regime-routed baselines. Fleet failure rates remained exactly 0.00% across all 122 test engines.
  </p>

  <table class="academic-table">
    <caption>Table I: Confirmatory Results across 122 Held-Out Engines (98.75% Bonferroni CIs)</caption>
    <thead>
      <tr>
        <th>Fleet</th>
        <th>Model</th>
        <th>Policy</th>
        <th>Cost (SCU)</th>
        <th>Fail (%)</th>
        <th>MPIW</th>
        <th>E_stage</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>FD001</td>
        <td>GBR</td>
        <td>Global</td>
        <td>15.28 &plusmn; 1.4</td>
        <td>0.00%</td>
        <td>42.1</td>
        <td>0.041</td>
      </tr>
      <tr>
        <td>FD001</td>
        <td>GBR</td>
        <td>Proposed</td>
        <td>14.85 &plusmn; 1.3</td>
        <td>0.00%</td>
        <td>46.8</td>
        <td>0.082</td>
      </tr>
      <tr class="mid-line">
        <td>FD002</td>
        <td>GBR</td>
        <td>Global</td>
        <td>28.45 &plusmn; 2.6</td>
        <td>0.00%</td>
        <td>54.2</td>
        <td>0.056</td>
      </tr>
      <tr>
        <td>FD002</td>
        <td>GBR</td>
        <td>Proposed</td>
        <td>20.83 &plusmn; 2.1</td>
        <td>0.00%</td>
        <td>61.5</td>
        <td>0.128</td>
      </tr>
      <tr class="mid-line">
        <td>FD002</td>
        <td>LSTM</td>
        <td>Global</td>
        <td>31.12 &plusmn; 2.9</td>
        <td>0.00%</td>
        <td>58.6</td>
        <td>0.061</td>
      </tr>
      <tr>
        <td>FD002</td>
        <td>LSTM</td>
        <td>Proposed</td>
        <td>20.13 &plusmn; 1.9</td>
        <td>0.00%</td>
        <td>63.2</td>
        <td>0.132</td>
      </tr>
      <tr class="mid-line">
        <td>FD004</td>
        <td>GBR</td>
        <td>Global</td>
        <td>29.74 &plusmn; 2.8</td>
        <td>0.00%</td>
        <td>56.1</td>
        <td>0.064</td>
      </tr>
      <tr class="total-line">
        <td>FD004</td>
        <td>GBR</td>
        <td>Proposed</td>
        <td>24.31 &plusmn; 2.3</td>
        <td>0.00%</td>
        <td>62.8</td>
        <td>0.135</td>
      </tr>
    </tbody>
  </table>

  <h3>B. Formal IUT Decision and Negative Finding</h3>
  <p>
    Despite large economic gains, the pre-registered Intersection-Union Test yielded a formal decision of <strong>UNSUPPORTED</strong> for RQ1&ndash;RQ4. While RQ1 (&Delta;_cost &gt; 0) and RQ2 (&Delta;_fail &le; 0) were strongly confirmed, RQ4 failed because late-stage coverage error breached the 0.05 ceiling:
  </p>
  <div class="equation">
    E_{\text{stage}} = \max_{{k \in \{\text{{early, mid, late}}\}}} |(1 - \alpha) - \text{{Cov}}_k| \approx 0.132 > 0.05
    <span class="eq-num">(11)</span>
  </div>

  <div class="figure-container">
    <img src="REPLACE_IMG_MISS" alt="Empirical Miss Rates by Lifecycle Stage"/>
    <div class="figure-caption">
      <strong>Fig. 1.</strong> Empirical miss rates decomposed across early (&gt;60 cycles), mid (20&ndash;60), and late (&lt;20 cycles) degradation stages. Asymmetric tuning induces severe lower-bound miss rate inflation (~23%) in late life.
    </div>
  </div>

  <h3>C. Analysis of Late-Stage Undercoverage</h3>
  <p>
    Fig. 1 reveals the structural cause of the IUT rejection. The asymmetric parameter &beta; = -ln 2 contracts the lower prediction bound L_{{i,t}} to ensure conservative maintenance triggering before physical failure. However, this intentional directional contraction inflates empirical lower miss rates to ~23% (empirical coverage ~77% vs. 90% nominal) during the final 20 operating cycles.
  </p>

  <h3>D. Factorial Parameter Ablation (240 Cells)</h3>
  <p>
    To isolate individual component contributions, a post-confirmatory factorial ablation was executed across 240 cells evaluating all combinations of scale dilation &gamma; &isin; {{1.0, 1.5, 2.0}}, asymmetry &beta; &isin; {{0, -0.35, -0.69}}, and regime routing &isin; {{Off, On}}.
  </p>

  <table class="academic-table">
    <caption>Table II: Factorial Main and Paired Parameter Effects</caption>
    <thead>
      <tr>
        <th>Factor Comparison</th>
        <th>&Delta; Cost (SCU)</th>
        <th>95% CI</th>
        <th>p-value</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Scale &gamma;=2.0 vs &gamma;=1.0</td>
        <td>-10.48</td>
        <td>[-11.12, -9.84]</td>
        <td>&lt; 0.0001</td>
      </tr>
      <tr>
        <td>Asymmetry &beta;=-ln 2 vs 0</td>
        <td>-1.21</td>
        <td>[-1.58, -0.84]</td>
        <td>&lt; 0.0001</td>
      </tr>
      <tr>
        <td>Regime Routing (Multi-Regime)</td>
        <td>+0.56</td>
        <td>[+0.12, +1.00]</td>
        <td>0.0124</td>
      </tr>
      <tr class="total-line">
        <td>Joint (&gamma;=2.0, &beta;=-ln 2)</td>
        <td>-11.69</td>
        <td>[-12.45, -10.93]</td>
        <td>&lt; 0.0001</td>
      </tr>
    </tbody>
  </table>

  <div class="figure-container">
    <img src="REPLACE_IMG_EFFECTS" alt="Paired Parameter Effects on Maintenance Cost"/>
    <div class="figure-caption">
      <strong>Fig. 2.</strong> Distribution of paired parameter differences on maintenance cost across 240 factorial ablation cells. Scale dilation drives primary cost reduction; regime routing introduces slight variance penalty.
    </div>
  </div>

  <p>
    As documented in Table II and Fig. 2, scale dilation &gamma; delivers the overwhelming majority of cost improvement (-10.48 SCU). Directional asymmetry &beta; provides an incremental -1.21 SCU saving and guarantees zero fleet failures. In contrast, regime routing offers zero benefit on single-regime fleets and introduces a +0.56 SCU penalty on multi-regime fleets due to partition sample dispersion.
  </p>

  <div class="figure-container">
    <img src="REPLACE_IMG_ABLATION" alt="Ablation of Maintenance Cost vs Empirical Coverage"/>
    <div class="figure-caption">
      <strong>Fig. 3.</strong> Trade-off frontier between nominal miscoverage level and realized fleet maintenance cost across baseline, dilated, and asymmetric calibrator configurations.
    </div>
  </div>

  <h3>E. Engineering Stress Robustness Probes</h3>
  <p>
    The framework was stressed under additive Gaussian sensor noise (&sigma;_noise &isin; {{0.05, 0.10, 0.20}}) and Bernoulli telemetry packet dropouts (p_drop &isin; {{0.05, 0.10, 0.15}}). Even under 20% noise and 15% dropout, fleet failure rates remained below 0.8% with average cost inflation under 1.85 SCU.
  </p>

  <h2>VII. Digital Twin Replay Prototype</h2>
  <p>
    IntelliTwin provides an open historical validation telemetry replay prototype (implemented in Python and Streamlit, located in <code>apps/twin_dashboard/</code>). Operating strictly with zero future lookahead, the replay engine processes historical test telemetry cycle-by-cycle, calculating real-time point predictions, asymmetric conformal bands, and maintenance triggers with mean execution latency &lt; 15 ms per cycle. Independent verification confirmed exact numerical parity (absolute tolerance &le; 10^-4) against precomputed experimental arrays across all 18 benchmark cells.
  </p>

  <h2>VIII. Discussion &amp; Limitations</h2>

  <h3>A. Operational Utility vs. Coverage Trade-off</h3>
  <p>
    Our experimental findings illuminate a fundamental engineering trade-off: in asymmetric risk environments, optimizing for operational utility (preventing failure while minimizing wasted life) directly conflicts with symmetric conditional coverage guarantees. IntelliTwin intentionally accepts late-stage undercoverage to eliminate catastrophic engine failure. In commercial aviation, where safety margins are strictly non-negotiable, this trade-off is operationally advantageous and aligns with fail-safe airworthiness mandates.
  </p>

  <h3>B. Threats to Validity</h3>
  <p>
    We transparently identify four primary threats: (1) <em>Synthetic Degradation:</em> NASA C-MAPSS is a thermodynamic simulation that may not capture localized crack propagation; (2) <em>Cost Ratios:</em> The 1.0 : 5.0 : 0.20 cost structure represents an engineering benchmark rather than a dynamic airline operational ledger; (3) <em>Post-Confirmatory Exploration:</em> Phase 8 factorial ablations were formulated after inspecting confirmatory data; and (4) <em>Software Boundary:</em> The twin operates as a historical validation prototype without physical actuation.
  </p>

  <h2>IX. Conclusion and Future Work</h2>
  <p>
    This paper introduced IntelliTwin, an uncertainty-aware Digital Twin framework for turbofan predictive maintenance. By integrating deep prognostics with asymmetric, decision-aware conformal calibration, the framework achieved significant maintenance cost reductions (+7.50 to +11.32 SCU on FD002) with zero fleet failures. Under a frozen confirmatory protocol, primary hypotheses were formally judged UNSUPPORTED due to late-stage conditional coverage degradation. Post-confirmatory ablation established that scale dilation and directional asymmetry drive economic gains, whereas regime routing incurs sample dispersion penalties. Future work will investigate online adaptive conformal prediction to restore conditional coverage near end-of-life and extend the architecture to multi-asset fleet synchronization.
  </p>

  <h2>Acknowledgment</h2>
  <p>
    The authors express their sincere gratitude to the Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, and project supervisor Dr. Ruchi Gupta for academic guidance and computational resources.
  </p>

  <h2>References</h2>
  <ol class="references-list">
    <li>A. BenAbdennour, &ldquo;Leakage-Controlled Grouped Validation and Interval-Safety Calibration for RUL/SOH Prediction,&rdquo; <em>Machines</em>, vol. 14, no. 10, p. 1124, 2026. DOI: <a class="doi-link" href="https://doi.org/10.3390/machines14101124">10.3390/machines14101124</a></li>
    <li>C. D. Robinson, &ldquo;Remaining Useful Life Estimation for Aircraft Engines with Risk-Aware Prediction Intervals,&rdquo; <em>Int. J. Progn. Health Manag.</em>, vol. 17, no. 1, p. 4724, 2026. DOI: <a class="doi-link" href="https://doi.org/10.36001/ijphm.2026.v17i1.4724">10.36001/ijphm.2026.v17i1.4724</a></li>
    <li>G. K. Walia and M. Kumar, &ldquo;Uncertainty-aware remaining useful life prediction and PPO based optimal maintenance scheduling,&rdquo; <em>Reliab. Eng. Syst. Saf.</em>, p. 112356, 2026. DOI: <a class="doi-link" href="https://doi.org/10.1016/j.ress.2026.112356">10.1016/j.ress.2026.112356</a></li>
    <li>H. Yan, &ldquo;Conformal prediction intervals for turbofan remaining useful life: an audit across operating regimes,&rdquo; Zenodo, 2026. DOI: <a class="doi-link" href="https://doi.org/10.5281/zenodo.21330745">10.5281/zenodo.21330745</a></li>
    <li>J. Wu et al., &ldquo;Research on Remaining Useful Life Prediction of Equipment Based on Digital Twins,&rdquo; <em>Sensors</em>, vol. 26, no. 4, p. 1240, 2026. DOI: <a class="doi-link" href="https://doi.org/10.3390/s26041240">10.3390/s26041240</a></li>
    <li>M. A. Belay, A. Rasheed, and P. S. Rossi, &ldquo;Digital Twin-Driven Communication-Efficient Federated Anomaly Detection for Industrial IoT,&rdquo; Preprint, NTNU / IEEE, 2026.</li>
    <li>M. Hisamuddin, M. T. Hussain, and R. Fatima, &ldquo;AI-Driven Digital Twins for Smart Urban Infrastructure,&rdquo; Tech. Report, Khaja Bandanawaz Univ., 2026.</li>
    <li>R. Diao, M. Zhou, G. Meng, and S. Wang, &ldquo;Turbofan Engine Remaining Useful Life Prediction with Reliable Prediction Intervals,&rdquo; <em>Sensors</em>, vol. 26, no. 7, p. 2249, 2026. DOI: <a class="doi-link" href="https://doi.org/10.3390/s26072249">10.3390/s26072249</a></li>
    <li>S. Yang, J. Wang, and Y. Wang, &ldquo;Empirical Calibration and Conditional-Reliability Diagnostics for Bearing RUL Prediction,&rdquo; arXiv:2607.08273, 2026.</li>
    <li>W. Xu, S. Gao, Z. Wang, and E. Zio, &ldquo;A novel uncertainty-aware framework for remaining useful life prediction,&rdquo; <em>Reliab. Eng. Syst. Saf.</em>, vol. 275, p. 112763, 2026. DOI: <a class="doi-link" href="https://doi.org/10.1016/j.ress.2026.112763">10.1016/j.ress.2026.112763</a></li>
    <li>A. K. M. R. Mahmud et al., &ldquo;AI-Augmented Digital Twin Architecture for Predictive Maintenance,&rdquo; <em>Eur. J. Appl. Sci. Eng. Technol.</em>, vol. 3, no. 5, pp. 45&ndash;58, 2025. DOI: <a class="doi-link" href="https://doi.org/10.59324/ejaset.2025.3(5).04">10.59324/ejaset.2025.3(5).04</a></li>
    <li>B. P. Pathri and K. V. Ganduri, &ldquo;From Smart Cities to Manufacturing: A Comprehensive Study on Digital Twin Applications,&rdquo; <em>IET Digit. Twins Appl.</em>, vol. 2, p. e70014, 2025. DOI: <a class="doi-link" href="https://doi.org/10.1049/dgt2.70014">10.1049/dgt2.70014</a></li>
    <li>D. Diana, Putri, and A. A. Mukti, &ldquo;AI-Driven Digital Twin for Predictive Maintenance in Urban Infrastructure,&rdquo; <em>Civil Eng. Sci. Technol.</em>, vol. 1, no. 1, pp. 63&ndash;74, 2025. DOI: <a class="doi-link" href="https://doi.org/10.51903/3c72e647">10.51903/3c72e647</a></li>
    <li>S. Cortes-Gomez et al., &ldquo;Utility-Directed Conformal Prediction: A Decision-Aware Framework,&rdquo; in <em>Proc. ICLR</em>, 2025.</li>
    <li>S. K. K. Hasan and C. W. Crawford, &ldquo;A new era for digital twins: progress and industry adoption,&rdquo; <em>Digital Twin</em>, vol. 2, no. 4, p. 2555877, 2025. DOI: <a class="doi-link" href="https://doi.org/10.1080/27525783.2025.2555877">10.1080/27525783.2025.2555877</a></li>
    <li>Z. Zhu et al., &ldquo;Predictive Maintenance Strategies for Aero-Engines Considering Remaining Useful Life Prediction Interval,&rdquo; <em>Qual. Reliab. Eng. Int.</em>, 2025. DOI: <a class="doi-link" href="https://doi.org/10.1002/qre.70043">10.1002/qre.70043</a></li>
    <li>F. Brighenti et al., &ldquo;Forecasting bridge damage within a predictive Structural Reliability-based DSS,&rdquo; <em>Autom. Constr.</em>, vol. 168, p. 105740, 2024. DOI: <a class="doi-link" href="https://doi.org/10.1016/j.autcon.2024.105740">10.1016/j.autcon.2024.105740</a></li>
    <li>H. K. Shehadeh, &ldquo;Evaluating the Impact of Transitioning Maintenance Strategy from Reactive to Proactive,&rdquo; <em>WSEAS Trans. Bus. Econ.</em>, vol. 21, pp. 838&ndash;856, 2024. DOI: <a class="doi-link" href="https://doi.org/10.37394/23207.2024.21.69">10.37394/23207.2024.21.69</a></li>
    <li>H. Wei, &ldquo;Digital Twin and AI Enabled Predictive Maintenance in Building Industry,&rdquo; Ph.D. dissertation, Nanyang Technological University, Singapore, 2024.</li>
    <li>S. F. Bello et al., &ldquo;AI-driven predictive maintenance and optimization of renewable energy systems,&rdquo; <em>Int. J. Sci. Res. Arch.</em>, vol. 13, no. 1, pp. 2823&ndash;2837, 2024. DOI: <a class="doi-link" href="https://doi.org/10.30574/ijsra.2024.13.1.1992">10.30574/ijsra.2024.13.1.1992</a></li>
    <li>S. Mazzetto, &ldquo;A Review of Urban Digital Twins Integration, Challenges, and Future Directions,&rdquo; <em>Sustainability</em>, vol. 16, no. 19, p. 8337, 2024. DOI: <a class="doi-link" href="https://doi.org/10.3390/su16198337">10.3390/su16198337</a></li>
    <li>V. Mousavi et al., &ldquo;Evolution of Digital Twin Frameworks in Bridge Management,&rdquo; <em>Remote Sens.</em>, vol. 16, no. 11, p. 1887, 2024. DOI: <a class="doi-link" href="https://doi.org/10.3390/rs16111887">10.3390/rs16111887</a></li>
    <li>A. Hosseinzadeh et al., &ldquo;A Predictive Maintenance Approach in Manufacturing Systems via AI-based Early Failure Detection,&rdquo; <em>Mfg. Lett.</em>, vol. 35, pp. 1179&ndash;1186, 2023. DOI: <a class="doi-link" href="https://doi.org/10.1016/j.mfglet.2023.08.125">10.1016/j.mfglet.2023.08.125</a></li>
    <li>A. Javanmardi and E. H&uuml;llermeier, &ldquo;Conformal Prediction Intervals for Remaining Useful Lifetime Estimation,&rdquo; <em>Int. J. Progn. Health Manag.</em>, vol. 14, no. 2, p. 3417, 2023. DOI: <a class="doi-link" href="https://doi.org/10.36001/ijphm.2023.v14i2.3417">10.36001/ijphm.2023.v14i2.3417</a></li>
    <li>Y. Lee, R. F. Barber, and R. Willett, &ldquo;Distribution-Free Inference with Hierarchical Data,&rdquo; arXiv:2306.06342v4, 2023.</li>
    <li>C. Chen et al., &ldquo;Data-driven predictive maintenance strategy considering the uncertainty in remaining useful life prediction,&rdquo; <em>Neurocomputing</em>, vol. 494, pp. 79&ndash;88, 2022. DOI: <a class="doi-link" href="https://doi.org/10.1016/j.neucom.2022.04.055">10.1016/j.neucom.2022.04.055</a></li>
    <li>Z. Huang, Y. Shen, J. Li, M. Fey, and C. Brecher, &ldquo;A Survey on AI-Driven Digital Twins in Industry 4.0,&rdquo; <em>Sensors</em>, vol. 21, no. 19, p. 6340, 2021. DOI: <a class="doi-link" href="https://doi.org/10.3390/s21196340">10.3390/s21196340</a></li>
    <li>D. Lakens, &ldquo;Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses,&rdquo; <em>Soc. Psychol. Personal. Sci.</em>, vol. 8, no. 4, pp. 355&ndash;362, 2017. DOI: <a class="doi-link" href="https://doi.org/10.1177/1948550617697177">10.1177/1948550617697177</a></li>
    <li>A. Saxena, K. Goebel, D. Simon, and N. Eklund, &ldquo;Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation,&rdquo; in <em>Proc. IEEE PHM</em>, 2008, pp. 1&ndash;9. DOI: <a class="doi-link" href="https://doi.org/10.1109/PHM.2008.4711414">10.1109/PHM.2008.4711414</a></li>
    <li>T. Gneiting and A. E. Raftery, &ldquo;Strictly Proper Scoring Rules, Prediction, and Estimation,&rdquo; <em>J. Am. Stat. Assoc.</em>, vol. 102, no. 477, pp. 359&ndash;378, 2007. DOI: <a class="doi-link" href="https://doi.org/10.1198/016214506000001437">10.1198/016214506000001437</a></li>
  </ol>

</div>

</body>
</html>
"""
    final_html = raw_html.replace("REPLACE_IMG_EFFECTS", img_effects)\
                         .replace("REPLACE_IMG_MISS", img_miss)\
                         .replace("REPLACE_IMG_ABLATION", img_ablation)\
                         .replace("FONT_SIZE", font_size)\
                         .replace("LINE_HEIGHT", line_height)\
                         .replace("MARGIN_V", margin_v)\
                         .replace("MARGIN_H", margin_h)\
                         .replace("P_MARGIN", p_margin)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(final_html)

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

    with open(PDF_PATH, "rb") as f:
        data = f.read()
    m = re.search(rb'/Type\s*/Pages.*?/Count\s+(\d+)', data, re.DOTALL)
    pages = int(m.group(1)) if m else -1
    return pages

if __name__ == "__main__":
    # Test combinations of layout parameters to find exact 6 pages
    configs = [
        {"font_size": "9.5pt", "line_height": "1.20", "margin_v": "0.75in", "margin_h": "0.58in", "p_margin": "3.6pt"},
        {"font_size": "9.6pt", "line_height": "1.21", "margin_v": "0.75in", "margin_h": "0.58in", "p_margin": "3.8pt"},
        {"font_size": "9.7pt", "line_height": "1.22", "margin_v": "0.75in", "margin_h": "0.58in", "p_margin": "4.0pt"},
        {"font_size": "9.8pt", "line_height": "1.23", "margin_v": "0.78in", "margin_h": "0.58in", "p_margin": "4.0pt"},
        {"font_size": "9.9pt", "line_height": "1.24", "margin_v": "0.80in", "margin_h": "0.58in", "p_margin": "4.2pt"},
    ]
    for idx, cfg in enumerate(configs, 1):
        build_html(**cfg)
        p = build_pdf()
        print(f"Config {idx} ({cfg['font_size']}, lh={cfg['line_height']}, p_m={cfg['p_margin']}): Pages = {p}")
        if p == 6:
            print(f"SUCCESS: Found exact 6-page configuration at Config {idx}!")
            break
