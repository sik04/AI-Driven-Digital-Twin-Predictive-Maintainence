import os
import sys
import subprocess
import zipfile
import base64

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(DIR, "research_paper_ieee.html")
PDF_PATH = os.path.join(DIR, "research_paper_ieee.pdf")
DOCX_PATH = os.path.join(DIR, "research_paper_ieee.docx")
FIG_DIR = os.path.join(DIR, "research_manuscript", "figure_sources")

def get_base64_img(filename):
    path = os.path.join(FIG_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return ""

def build_html():
    img_effects = get_base64_img("scale_asymmetry_routing_paired_effects.png")
    img_miss = get_base64_img("lower_upper_miss_rates_by_lifecycle_stage.png")
    img_ablation = get_base64_img("ablation_cost_vs_coverage.png")

    raw_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance</title>
<style>
  @page {
    size: A4;
    margin: 0.75in 0.65in 0.75in 0.65in;
    @bottom-center {
      content: counter(page);
      font-family: "Times New Roman", Times, serif;
      font-size: 9pt;
    }
  }

  body {
    font-family: "Times New Roman", Times, serif;
    font-size: 9.5pt;
    line-height: 1.22;
    color: #000000;
    margin: 0;
    padding: 0;
    text-align: justify;
  }

  .paper-header {
    text-align: center;
    margin-bottom: 12pt;
  }

  .paper-title {
    font-size: 21pt;
    font-weight: bold;
    line-height: 1.15;
    margin-bottom: 12pt;
    letter-spacing: -0.2pt;
  }

  .authors-block {
    text-align: center;
    margin-bottom: 14pt;
    line-height: 1.35;
  }

  .author-names {
    font-size: 11.5pt;
    font-weight: bold;
    margin-bottom: 4pt;
  }

  .author-affiliations {
    font-size: 9pt;
    color: #222222;
  }

  .abstract-keywords-container {
    margin: 0 0 10pt 0;
    width: 100%;
    font-size: 8.5pt;
    line-height: 1.22;
    text-align: justify;
    break-inside: avoid;
    -webkit-column-break-inside: avoid;
    page-break-inside: avoid;
  }

  .abstract-heading {
    font-weight: bold;
    font-style: italic;
    display: inline;
  }

  .keywords-heading {
    font-weight: bold;
    font-style: italic;
    display: inline;
  }

  /* Two Column Layout */
  .columns-container {
    column-count: 2;
    column-gap: 0.22in;
    column-fill: balance;
  }

  h2 {
    font-size: 10pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    text-align: center;
    margin-top: 10pt;
    margin-bottom: 4pt;
    padding: 1.5pt 0;
    break-after: avoid;
  }

  h3 {
    font-size: 9.5pt;
    font-weight: bold;
    font-style: italic;
    margin-top: 6pt;
    margin-bottom: 2pt;
    break-after: avoid;
  }

  p {
    text-indent: 1em;
    margin-top: 0;
    margin-bottom: 3.5pt;
  }

  p.no-indent {
    text-indent: 0;
  }

  .equation {
    text-align: center;
    margin: 5pt 0;
    font-family: "Cambria Math", "Times New Roman", serif;
    font-size: 9.5pt;
  }

  .equation table {
    width: 100%;
    border: none;
    margin: 0;
  }

  .equation-content {
    text-align: center;
  }

  .equation-number {
    text-align: right;
    width: 10%;
    font-family: "Times New Roman", serif;
  }

  table.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 7.8pt;
    line-height: 1.15;
    margin: 6pt 0;
  }

  table.data-table th, table.data-table td {
    padding: 2.5pt 3pt;
    text-align: left;
  }

  table.data-table th {
    border-top: 1.2pt solid #000;
    border-bottom: 0.8pt solid #000;
    font-weight: bold;
  }

  table.data-table td {
    border-bottom: 0.4pt solid #ddd;
  }

  .figure-box {
    margin: 6pt 0;
    text-align: center;
    break-inside: avoid;
  }

  .figure-box img {
    max-width: 100%;
    height: auto;
    border: 0.5pt solid #ccc;
  }

  .caption {
    font-size: 8pt;
    margin-top: 3pt;
    text-align: justify;
    line-height: 1.18;
  }

  .caption-label {
    font-weight: bold;
  }

  .references-list {
    font-size: 8pt;
    line-height: 1.15;
    padding-left: 1.5em;
    margin-top: 4pt;
  }

  .references-list li {
    margin-bottom: 3pt;
    text-indent: -1.5em;
    padding-left: 1.5em;
  }

  .doi-link {
    color: #000;
    text-decoration: none;
    font-family: monospace;
    font-size: 7.5pt;
  }
</style>
</head>
<body>

<div class="paper-header">
  <div class="paper-title">IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance</div>

  <div class="authors-block">
    <div class="author-names">Shiksha Pandey&sup1;, Mayank Singh&sup2;</div>
    <div class="author-affiliations">
      &sup1; Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, India<br>
      &sup2; Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, India
    </div>
  </div>
</div>

<div class="columns-container">
  <div class="abstract-keywords-container">
  <p class="no-indent">
    <span class="abstract-heading">Abstract&mdash;</span>In industrial predictive maintenance of gas turbine engines, unexpected mechanical failure incurs severe airworthiness risks and catastrophic economic penalties (5x to 10x scheduled overhaul), while premature overhaul discards valuable residual component life. Conventional Remaining Useful Life (RUL) prognostic systems rely on deterministic point estimators that optimize symmetric cycle error metrics without quantifying prediction variance or aligning with downstream maintenance costs. Standard inductive conformal prediction provides marginal coverage guarantees but conceals severe conditional undercoverage across accelerating degradation stages and varying operating regimes. In this work, we present <strong>IntelliTwin</strong>, an uncertainty-aware prognostic framework integrating Gradient Boosted Regressors (GBR) and Long Short-Term Memory (LSTM) networks with hierarchical, decision-aware conformal calibration. IntelliTwin enforces strictly disjoint engine-level partitioning, causal temporal windowing (w=30, stride 1), exact rational engine weighting (m/(m+1) mass), and an asymmetric nonconformity score parameterized by scale dilation (&gamma;=2) and directional asymmetry (&beta;=-ln 2). We evaluate the framework under a frozen confirmatory protocol on 122 held-out test engines from NASA C-MAPSS sub-corpora FD001, FD002, and FD004 across 10,000 lifetime-stratified cluster-bootstrap draws with Bonferroni-controlled 98.75% decision intervals. In confirmatory testing, the proposed method achieved substantial maintenance cost reductions (+7.50 to +11.32 Simulated Cost Units per engine on FD002) with zero fleet failures. However, under preregistered Intersection-Union Testing criteria, RQ1&ndash;RQ4 were formally classified as UNSUPPORTED because late-stage degradation coverage error breached the 0.05 ceiling (E_stage &asymp; 0.13, empirical coverage ~ 77%). Through post-confirmatory factorial ablation across 240 cells, we isolate that scale dilation (&gamma;) reduces cost by an unweighted mean of -10.48 SCU and directional asymmetry (&beta;) reduces cost by -1.21 SCU, whereas regime routing provides null effects on single-condition fleets and small cost penalties (+0.56 SCU) on multi-condition fleets due to partition sample dispersion. Finally, we provide an open, fully reproducible historical validation-telemetry replay prototype.
  </p>
  <div style="margin-top: 4pt;">
    <span class="keywords-heading">Index Terms&mdash;</span>Predictive Maintenance, Remaining Useful Life, Digital Twin, Conformal Prediction, Uncertainty Quantification, Condition-Adaptive Calibration, Turbofan Engines, C-MAPSS.
  </div>
</div>


  <h2>I. Introduction</h2>
  <p>
    Prognostics and Health Management (PHM) for high-value rotating machinery has emerged as a cornerstone of operational safety and economic sustainability across commercial aviation, energy generation, and advanced manufacturing [28], [13]. In commercial aircraft gas turbine turbofans, unscheduled engine removals and catastrophic in-flight failures impose disproportionate costs&mdash;frequently exceeding scheduled overhaul expenses by five- to ten-fold&mdash;while posing critical flight safety risks [22], [18]. Conversely, legacy time-based preventative maintenance discards substantial remaining operational lifespan, severely inflating life-cycle overhaul expenditure [30], [17].
  </p>
  <p>
    Modern data-driven prognostic paradigms utilize multi-sensor telemetry to predict an asset's Remaining Useful Life (RUL) [5]. Deep learning models, including Long Short-Term Memory (LSTM) networks and gradient-boosted regression ensembles, have achieved impressive cycle-level error reductions on standardized run-to-failure benchmarks such as NASA C-MAPSS [28], [8]. However, standard point-regression models suffer from three structural shortcomings when deployed into operational maintenance decision pipelines:
  </p>
  <p>
    <em>1) Unquantified Point Variance:</em> A single deterministic cycle estimate provides no measure of epistemic or aleatoric uncertainty, preventing operators from distinguishing high-confidence prognostic estimates from high-risk extrapolations [25], [3].
  </p>
  <p>
    <em>2) Conditional Reliability Breakdown:</em> Inductive split conformal prediction has emerged as an attractive, distribution-free methodology to construct finite-sample prediction intervals [L, U] with marginal coverage guarantees P(y &isin; [L, U]) &ge; 1 - &alpha; [23], [8]. Nevertheless, marginal coverage guarantees do not ensure conditional coverage across varying operating regimes or accelerating wear stages [9], [4]. In turbofan engines subject to dynamic throttle and atmospheric variations, standard conformal calibrators frequently undercover in late degradation phases where accurate risk bounds are most critical.
  </p>
  <p>
    <em>3) Decoupling of Uncertainty from Economic Consequences:</em> Standard prognostic objectives minimize symmetric errors (RMSE, MAE). In operational aviation maintenance, overestimating RUL leads to uncontained mechanical breakdown, whereas underestimating RUL causes only premature overhaul waste [16], [2]. Symmetric prediction intervals fail to reflect this severe operational loss asymmetry.
  </p>
  <p>
    To bridge this operational and theoretical gap, we introduce <strong>IntelliTwin</strong>, an AI-driven framework that unifies deep sequence modeling, hierarchical conformal calibration, and asymmetric sequential maintenance simulation within an interactive Digital Twin replay architecture.
  </p>

  <h2>II. Related Work</h2>
  <p>
    <em>A. Prognostics and RUL Estimation:</em> Data-driven RUL estimation has evolved from classical statistical hazard modeling (Weibull, degradation filters) to complex neural architectures [28]. Modern benchmarks heavily leverage the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) dataset, which models 90,000-lb thrust turbofan degradation under mixed sea-level and high-altitude flight envelopes [28], [8]. While recurrent and convolutional architectures achieve low RMSE, raw point predictions provide insufficient assurance for mission-critical dispatch [5], [6].
  </p>
  <p>
    <em>B. Uncertainty Quantification in PHM:</em> Bayesian neural networks, Monte Carlo dropout, and deep ensemble methods have been investigated to estimate RUL variance [25], [10]. However, Bayesian methods require strong prior assumptions, and ensemble variances often lack empirical coverage guarantees under distribution shift. Conformal prediction addresses this limitation by producing distribution-free, finite-sample prediction intervals [23]. Javanmardi and H&uuml;llermeier [23] demonstrated split conformal prediction on C-MAPSS FD001. Diao et al. [8] coupled LSTM quantile regression with conformal calibration. However, prior studies evaluated conformal intervals using standard symmetric coverage (PICP) and width (MPIW) metrics, overlooking the economic consequences of bound failures in sequential decision-making.
  </p>
  <p>
    <em>C. Digital Twins and Decision-Directed Conformal Inference:</em> Digital Twins combine sensor telemetry, virtual models, and real-time state synchronization to track physical degradation [26], [15], [12]. Recent theoretical developments by Cortes-Gomez et al. [14] formalized utility-directed conformal prediction for static decision problems, while Lee et al. [24] established distribution-free inference for hierarchical data. Robinson [2] introduced risk-aware conformal quantile regression for aircraft engines. IntelliTwin builds upon these foundations by unifying hierarchical engine weighting, state-dependent nonconformity scaling, and sequential discrete maintenance simulation into a single reproducible framework.
  </p>

  <h2>III. Problem Formulation and Research Objectives</h2>
  <p>
    <em>A. Degradation Process and Temporal Windowing:</em> Let an industrial turbofan engine i operate across discrete operational cycles t &isin; {1, ..., T_i}, where T_i denotes the terminal cycle of functional failure. At each cycle t, a vector of operational settings and sensor measurements s_{i,t} is observed. Observations are buffered into causal sliding windows of fixed length w=30 with unit stride:
  </p>
  <div class="equation">
    <table><tr><td class="equation-content">X_{i,t} = [s_{i,t-w+1}, ..., s_{i,t}]^T &isin; R^{w &times; D}, &forall; t &ge; w.</td><td class="equation-number">(1)</td></tr></table>
  </div>
  <p>
    Cycles t &lt; w constitute a non-predictive warm-up horizon. The true remaining useful life at observation endpoint t is y_{i,t} = T_i - t. During model training, target values are clipped according to standard industry practice: y_train = min(y_{i,t}, 125) cycles. During evaluation and maintenance simulation, the true uncapped remaining life y_{i,t} is evaluated.
  </p>
  <p>
    <em>B. Sequential Maintenance Simulator Contract:</em> We model asset maintenance as a discrete-time stopping problem over cycles t &isin; [w, T_i - 1]. At each cycle, the decision agent observes telemetry history X_{i,t}, computes calibrated lower bound L(t), and executes an action a_t &isin; {CONTINUE, MAINTAIN_NOW} according to the policy:
  </p>
  <div class="equation">
    <table><tr><td class="equation-content">a_t = MAINTAIN_NOW if L(t) &le; 1.0 cycle, else CONTINUE.</td><td class="equation-number">(2)</td></tr></table>
  </div>
  <p>
    If proactive maintenance is triggered at cycle t_action &lt; T_i, the engine is removed from service, incurring preventive replacement cost C_PM plus wasted life penalty proportional to discarded cycles:
  </p>
  <div class="equation">
    <table><tr><td class="equation-content">Cost(i) = C_PM + C_WASTE &times; (T_i - t_action).</td><td class="equation-number">(3)</td></tr></table>
  </div>
  <p>
    If no maintenance action is triggered and the engine reaches terminal cycle T_i, catastrophic in-service failure occurs, incurring heavy penalty Cost(i) = C_FAIL. Under the primary reference economic scenario, costs are set to C_PM = 1.0, C_FAIL = 5.0, and C_WASTE = 0.20 Simulated Cost Units (SCU) per engine.
  </p>
  <p>
    <em>C. Formal Research Questions:</em> We establish four preregistered research questions:
    <strong>RQ1:</strong> Can decision-aware conformal calibration improve sequential maintenance utility (&Delta;_cost &gt; 0.20 SCU) while preserving prediction-interval coverage (E &lt; 0.05)?
    <strong>RQ2:</strong> Can the proposed method improve worst-group conditional coverage (&Delta;_error &gt; 0.01) without excessive interval widening (D_width &lt; 1.0 cycle)?
    <strong>RQ3:</strong> Are maintenance benefits attributable to decision-aware calibration rather than simple over-conservatism or premature intervention?
    <strong>RQ4:</strong> Does the method retain calibration and utility benefits across operating conditions, base models, and datasets?
  </p>

  <h2>IV. Proposed IntelliTwin Framework</h2>
  <p>
    The architecture of IntelliTwin comprises five decoupled stages:
    1) <em>Engine-Disjoint Data Pipeline:</em> Strict partitioning by physical engine ID prevents cross-trajectory leakage.
    2) <em>Prognostic Base Models:</em> Dual architectures (tree-based GBR and recurrent LSTM) trained on clipped RUL targets.
    3) <em>Asymmetric Conformal Scoring Engine:</em> Nonconformity scores parameterized by life-horizon dilation and risk asymmetry.
    4) <em>Hierarchical Engine Calibration:</em> Exact rational probability weighting ensuring valid distribution-free coverage.
    5) <em>Sequential Maintenance Simulator:</em> Discrete cycle evaluation translating lower bounds into realized maintenance costs.
  </p>

  <h2>V. Mathematical Methodology</h2>
  <p>
    <em>A. Asymmetric Decision-Aware Nonconformity Scoring:</em> Let p = max(0, y_hat) denote the non-negative evaluated point prediction in cycles, and let y denote the true Remaining Useful Life. The asymmetric nonconformity score scales deviations according to state-dependent shape factors:
  </p>
  <div class="equation">
    <table><tr><td class="equation-content">&sigma;(p) = (1 + p/125)^&gamma;, &nbsp; z(p) = exp(-p/20),</td><td class="equation-number">(4)</td></tr></table>
  </div>
  <div class="equation">
    <table><tr><td class="equation-content">a(p) = &sigma;(p) exp(&beta; z(p)), &nbsp; b(p) = &sigma;(p) exp(-&beta; z(p)),</td><td class="equation-number">(5)</td></tr></table>
  </div>
  <p>
    where &gamma; &isin; {0, 1, 2} controls variance dilation with life horizon, and &beta; &isin; {-ln 2, 0, +ln 2} governs directional risk asymmetry. The nonconformity score is defined as:
  </p>
  <div class="equation">
    <table><tr><td class="equation-content">score(p, y) = max((p - y)/a(p), (y - p)/b(p), 0).</td><td class="equation-number">(6)</td></tr></table>
  </div>
  <p>
    Inverting this score with respect to a calibrated quantile threshold q* produces valid prediction interval bounds:
  </p>
  <div class="equation">
    <table><tr><td class="equation-content">L = max(0, p - q* a(p)), &nbsp; U = p + q* b(p).</td><td class="equation-number">(7)</td></tr></table>
  </div>
  <p>
    Validation grid search across candidate pairs uniquely selected &gamma; = 2, &beta; = -ln 2 &asymp; -0.693147.
  </p>
  <p>
    <em>B. Hierarchical Engine-Weighted Calibration:</em> In final conformal calibration on m reserved calibration engines, each observation (i, t) within contributing engine i receives equal engine weight:
  </p>
  <div class="equation">
    <table><tr><td class="equation-content">F_cal(q) = (1/(m+1)) &sum;_{i=1}^m [ (1/n_i) &sum;_t 1_{score_{it} &le; q} ].</td><td class="equation-number">(8)</td></tr></table>
  </div>
  <p>
    Each finite endpoint carries probability mass 1/((m+1)n_i), placing total finite mass m/(m+1) on calibration observations, with remaining mass 1/(m+1) assigned to +&infin;.
  </p>
  <p>
    <em>C. Operating Regime Stratification &amp; Fallback Rules:</em> Operating setting variables are clustered into 6 flight regimes via k-means. A flight regime cluster g possesses sufficient calibration support if and only if m_g &ge; max(10, ceil(1/&alpha;) - 1). At 90% nominal coverage (&alpha; = 0.10), m_g &ge; 10 distinct engines are required. If a regime fails this support requirement, the calibrator deterministically falls back to the pooled global threshold q*_global.
  </p>

  <h2>VI. Experimental Setup</h2>
  <p>
    <em>A. Datasets and Disjoint Partitions:</em> Experiments evaluate NASA C-MAPSS sub-corpora: FD001 (100 engines, 1 regime, HPC fault), FD002 (260 engines, 6 regimes, HPC fault), and FD004 (249 engines, 6 regimes, HPC+Fan faults). Engine-level disjoint splits:
    FD001 (50 Train / 20 Cal / 10 Val / 20 Test); FD002 (130 Train / 52 Cal / 26 Val / 52 Test); FD004 (124 Train / 50 Cal / 25 Val / 50 Test). Total held-out confirmatory test engines: 20 + 52 + 50 = 122 engines.
  </p>
  <p>
    <em>B. Base Predictor Models:</em>
    GBR flattens 30x17 windows into 510-dim vectors (max_iter=300, lr=0.05, max_leaf_nodes=31). LSTM incorporates two layers (64, 32 units, dropout 0.1) trained via Adam (lr=1e-3, batch size 64). Five model seeds: [2026, 2027, 2028, 2029, 2030].
  </p>
  <p>
    <em>C. Statistical Inference:</em> Evaluated via 10,000 paired engine-cluster bootstrap resamples stratified by lifetime quartiles (Q1--Q4) using PCG64 PRNG with Bonferroni-corrected 98.75% decision intervals (&alpha; = 0.0125) and Intersection-Union Testing.
  </p>

  <h2>VII. Results and Discussion</h2>
  <p>
    Confirmatory results across 122 held-out test engines are summarized in Table I.
  </p>

  <table class="data-table">
    <thead>
      <tr>
        <th>Component ID</th>
        <th>Mod</th>
        <th>Comp</th>
        <th>Metric</th>
        <th>Point</th>
        <th>98.75% CI</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>RQ1_GBR_global_cost</td>
        <td>GBR</td>
        <td>glob</td>
        <td>&Delta;_cost</td>
        <td>+7.62</td>
        <td>[6.64, 8.65]</td>
        <td><strong>PASS</strong></td>
      </tr>
      <tr>
        <td>RQ1_GBR_regime_cost</td>
        <td>GBR</td>
        <td>reg</td>
        <td>&Delta;_cost</td>
        <td>+7.50</td>
        <td>[6.63, 8.39]</td>
        <td><strong>PASS</strong></td>
      </tr>
      <tr>
        <td>RQ1_GBR_marginal_cov</td>
        <td>GBR</td>
        <td>90%</td>
        <td>|Cov - .9|</td>
        <td>0.029</td>
        <td>[0.004, 0.049]</td>
        <td><strong>PASS</strong></td>
      </tr>
      <tr>
        <td>RQ1_GBR_stage_ceiling</td>
        <td>GBR</td>
        <td>90%</td>
        <td>E_stage</td>
        <td>0.132</td>
        <td>[0.096, 0.174]</td>
        <td><strong style="color:red;">FAIL</strong></td>
      </tr>
      <tr>
        <td>RQ1_LSTM_global_cost</td>
        <td>LSTM</td>
        <td>glob</td>
        <td>&Delta;_cost</td>
        <td>+10.99</td>
        <td>[9.77, 12.37]</td>
        <td><strong>PASS</strong></td>
      </tr>
      <tr>
        <td>RQ1_LSTM_regime_cost</td>
        <td>LSTM</td>
        <td>reg</td>
        <td>&Delta;_cost</td>
        <td>+11.32</td>
        <td>[10.10, 12.74]</td>
        <td><strong>PASS</strong></td>
      </tr>
      <tr>
        <td>RQ1_LSTM_stage_ceiling</td>
        <td>LSTM</td>
        <td>90%</td>
        <td>E_stage</td>
        <td>0.128</td>
        <td>[0.092, 0.191]</td>
        <td><strong style="color:red;">FAIL</strong></td>
      </tr>
    </tbody>
  </table>

  <p>
    <strong>Confirmatory RQ Outcomes:</strong>
    1) <em>RQ1 (UNSUPPORTED):</em> The method delivered decisive maintenance cost reductions (+7.50 to +11.32 SCU/engine) with zero fleet failures. However, under IUT criteria, worst-stage coverage error breached the 0.05 ceiling (E_stage &asymp; 0.13), formally deciding RQ1 as UNSUPPORTED.
    2) <em>RQ2 (UNSUPPORTED):</em> Failed conditional regime error reduction and worst-stage ceilings.
    3) <em>RQ3 (UNSUPPORTED):</em> Outperformed widened intervals and earlier intervention, but failed point safety margin cost margin.
    4) <em>RQ4 (UNSUPPORTED):</em> Cross-fleet cost improvements achieved, but failed aggregate regime error and worst-stage ceilings.
  </p>

  <h2>VIII. Ablation and Robustness Analysis</h2>
  <div class="figure-box">
    <img src="REPLACE_IMG_EFFECTS" alt="Factor Main Effects">
    <div class="caption"><span class="caption-label">Fig. 1.</span> Paired main factor effects (On - Off) for scale dilation (&gamma;), directional asymmetry (&beta;), and operating regime routing across the six dataset/model cells with 10,000-draw stratified bootstrap 95% confidence intervals.</div>
  </div>
  <p>
    <em>A. Factorial Main Effects:</em> As shown in Fig. 1:
    1) <em>Scale Dilation (&gamma;=2 vs 0):</em> Yields an unweighted descriptive mean cost reduction of <strong>-10.4823 SCU</strong> across all 6 cells (range: -17.16 to -6.54 SCU).
    2) <em>Directional Asymmetry (&beta;=-ln 2 vs 0):</em> Provides secondary cost reduction of <strong>-1.2142 SCU</strong> (range: -1.44 to -0.87 SCU).
    3) <em>Regime Routing (regime vs global):</em> Shows an unweighted descriptive mean cost increase of <strong>+0.5594 SCU</strong>. On FD001, routing has exactly zero effect (0.0000 SCU) by mathematical equivalence; on multi-regime datasets, regime partitioning reduces calibration sample density, slightly degrading empirical threshold precision.
  </p>

  <div class="figure-box">
    <img src="REPLACE_IMG_MISS" alt="Tail Miss Rates">
    <div class="caption"><span class="caption-label">Fig. 2.</span> Empirical lower (y &lt; L) vs. upper (y &gt; U) tail miss rates across early, mid, and late lifecycle stages.</div>
  </div>
  <p>
    <em>B. Lifecycle Stage Miss-Rate Asymmetry:</em> Fig. 2 decomposes tail misses. In early life (t &isin; [w, T/3]), coverage exceeds 95%. In late life (t &isin; [2T/3, T]), rapid physical wear acceleration causes increased lower-tail misses (y &lt; L), directly explaining the breach of the E &lt; 0.05 worst-stage coverage ceiling.
  </p>
  <p>
    <em>C. Engineering Stress Probes:</em> Under Gaussian sensor noise probes (&sigma; &isin; {0.05, 0.10, 0.20} across 54 combinations), mean paired cost increase relative to clean telemetry was +0.5633 SCU. Under causal forward-fill sensor dropout (p &isin; {0.05, 0.10} across 36 combinations), mean paired coverage delta was -0.0007.
  </p>

  <h2>IX. Digital Twin Implementation</h2>
  <div class="figure-box">
    <img src="REPLACE_IMG_ABLATION" alt="Ablation Cost vs Coverage">
    <div class="caption"><span class="caption-label">Fig. 3.</span> Empirical trade-off between total maintenance cost and empirical coverage across all 8 factorial variants.</div>
  </div>
  <p>
    IntelliTwin includes a browser-based historical telemetry replay prototype (apps/twin_dashboard/). The prototype operates causally on C-MAPSS validation runs, streaming multi-sensor telemetry, GBR/LSTM point predictions, conformal uncertainty envelopes, and policy decision triggers with zero future lookahead. The implementation was audited and verified to achieve exact numerical parity (atol &le; 1e-4) against cached validation arrays across all 18 benchmark cells.
  </p>

  <h2>X. Limitations and Threats to Validity</h2>
  <p>
    <em>A. Operational Utility vs. Conditional Coverage:</em> The central insight of this investigation is the fundamental tension between operational maintenance utility and conditional coverage guarantees. By dilating intervals in early life (&gamma;=2) and skewing bounds downward near end-of-life (&beta; &lt; 0), IntelliTwin drastically reduced simulated maintenance costs (+7.50 to +11.32 SCU/engine) and prevented all functional failures. However, this asymmetric tuning sacrificed late-stage conditional coverage (~ 77% vs. 90% nominal). In safety-critical engineering, whether this trade-off is acceptable depends entirely on operational risk tolerance.
  </p>
  <p>
    <em>B. Threats to Validity:</em>
    1) C-MAPSS is an industry-standard simulation, but real aero-engines experience complex thermomechanical degradation not fully captured in synthetic runs.
    2) The evaluated 1 : 5 : 0.20 cost structure represents an engineering benchmark rather than an airline accounting ledger.
    3) Phase 8 factorial ablations were designed after inspecting held-out test data.
    4) The Digital Twin is strictly a validation telemetry replay prototype without physical bi-directional control.
  </p>

  <h2>XI. Conclusion and Future Work</h2>
  <p>
    This paper presented IntelliTwin, a decision-aware, condition-adaptive conformal prediction framework for industrial turbofan predictive maintenance. By integrating deep prognostics with state-dependent nonconformity scaling and hierarchical engine weighting, the framework achieved substantial maintenance cost reductions with zero fleet failures. Under a frozen confirmatory protocol, the primary research questions were formally classified as UNSUPPORTED due to conditional coverage degradation in late-life wear stages. Post-confirmatory factorial ablation demonstrated that scale dilation and directional asymmetry drive the observed cost reductions, while operating regime routing introduces variance penalties on multi-condition fleets. Future research will explore online adaptive conformal prediction to restore conditional late-life coverage.
  </p>

  <h2>Acknowledgment</h2>
  <p class="no-indent" style="font-size: 8.5pt;">
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
                         .replace("REPLACE_IMG_ABLATION", img_ablation)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"Generated HTML: {HTML_PATH} ({os.path.getsize(HTML_PATH)} bytes)")

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
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    document_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="20"/>
        <w:color w:val="000000"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:line="240" w:lineRule="auto" w:before="0" w:after="80"/>
        <w:jc w:val="both"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>"""

    doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="0" w:after="160"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="42"/></w:rPr>
        <w:t>IntelliTwin: Decision-Aware, Condition-Adaptive Conformal Prediction for Industrial Turbofan Predictive Maintenance</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="0" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="23"/></w:rPr>
        <w:t>Shiksha Pandey¹, Mayank Singh²</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="0" w:after="200"/>
        <w:sectPr>
          <w:type w:val="continuous"/>
        </w:sectPr>
      </w:pPr>
      <w:r>
        <w:rPr><w:sz w:val="18"/></w:rPr>
        <w:t>¹ Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, India</w:t>
      </w:r>
      <w:r><w:br/></w:r>
      <w:r>
        <w:rPr><w:sz w:val="18"/></w:rPr>
        <w:t>² Department of Information Technology, Ajay Kumar Garg Engineering College (AKGEC), Ghaziabad, India</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:spacing w:before="120" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:i/><w:sz w:val="20"/></w:rPr>
        <w:t>Abstract—</w:t>
      </w:r>
      <w:r>
        <w:rPr><w:sz w:val="19"/></w:rPr>
        <w:t>In industrial predictive maintenance of gas turbine engines, unexpected mechanical failure incurs severe airworthiness risks and catastrophic economic penalties (5x to 10x scheduled overhaul), while premature overhaul discards valuable residual component life. In this research, we present IntelliTwin, an uncertainty-aware prognostic framework integrating Gradient Boosted Regressors and Long Short-Term Memory networks with hierarchical, decision-aware conformal calibration. IntelliTwin enforces strictly disjoint engine-level partitioning, causal temporal windowing (w=30, stride 1), exact rational engine weighting, and an asymmetric nonconformity score parameterized by scale dilation (gamma=2) and directional asymmetry (beta=-ln 2). In confirmatory testing across 122 held-out test engines from NASA C-MAPSS FD001, FD002, and FD004, the proposed method achieved substantial maintenance cost reductions (+7.50 to +11.32 Simulated Cost Units per engine on FD002) with zero fleet failures. However, under preregistered Intersection-Union Testing criteria, RQ1-RQ4 were formally classified as UNSUPPORTED because late-stage degradation coverage error breached the 0.05 ceiling. Post-confirmatory factorial ablation across 240 cells isolates that scale dilation and directional asymmetry drive cost reductions, while regime routing introduces variance penalties on multi-condition fleets. Finally, we provide an open historical validation-telemetry replay prototype.</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:spacing w:before="40" w:after="160"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:i/><w:sz w:val="20"/></w:rPr>
        <w:t>Index Terms—</w:t>
      </w:r>
      <w:r>
        <w:rPr><w:sz w:val="19"/></w:rPr>
        <w:t>Predictive Maintenance, Remaining Useful Life, Digital Twin, Conformal Prediction, Uncertainty Quantification, Condition-Adaptive Calibration, Turbofan Engines, C-MAPSS.</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="160" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="22"/></w:rPr>
        <w:t>I. INTRODUCTION</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:t>Prognostics and Health Management (PHM) for high-value rotating machinery has emerged as a cornerstone of operational safety and economic sustainability. In aircraft turbofan fleets, unscheduled engine removals and catastrophic in-service failures impose disproportionate costs, while legacy time-based preventative overhaul strategies discard substantial remaining operational lifespan. Deep learning prognostic models provide point predictions that conceal predictive uncertainty. Standard split conformal prediction provides marginal guarantees but conceals severe conditional undercoverage in late wear stages. IntelliTwin addresses this challenge by coupling deep prognostics with asymmetric conformal calibration and sequential maintenance simulation.</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="160" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="22"/></w:rPr>
        <w:t>II. RELATED WORK</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:t>Data-driven RUL estimation leverages the NASA C-MAPSS benchmark. Split conformal prediction intervals for RUL were explored by Javanmardi and Huellermeier (2023) and Diao et al. (2026). Utility-directed conformal prediction was formalized by Cortes-Gomez et al. (2025), and hierarchical calibration by Lee et al. (2023). IntelliTwin unifies these developments into a sequential maintenance simulation pipeline.</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="160" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="22"/></w:rPr>
        <w:t>III. MATHEMATICAL METHODOLOGY</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:t>The asymmetric nonconformity score scales deviations according to state-dependent shape factors: sigma(p) = (1 + p/125)^gamma, z(p) = exp(-p/20), a(p) = sigma(p) exp(beta z(p)), and b(p) = sigma(p) exp(-beta z(p)). Inverting this score produces prediction interval bounds L = max(0, p - q* a(p)) and U = p + q* b(p). Calibrated quantiles enforce hierarchical engine weighting with finite mass m/(m+1) on calibration observations and 1/(m+1) at +infinity.</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="160" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="22"/></w:rPr>
        <w:t>IV. CONFIRMATORY RESULTS AND ABLATION</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:t>In held-out confirmatory evaluation on 122 test engines, the proposed method achieved +7.62 SCU cost improvement (GBR) and +10.99 SCU improvement (LSTM) over global conformal baselines with zero fleet failures. However, because late-stage coverage error reached 0.132 (breaching the 0.05 ceiling), RQ1-RQ4 were formally decided as UNSUPPORTED under preregistered IUT criteria. Factorial component ablation across 240 cells confirmed that scale dilation reduces cost by -10.48 SCU and directional asymmetry reduces cost by -1.21 SCU, while regime routing has null effect on single-regime fleets and small penalty (+0.56 SCU) on multi-condition fleets.</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:before="160" w:after="80"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="22"/></w:rPr>
        <w:t>V. CONCLUSION</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:t>IntelliTwin demonstrates that decision-aware conformal prediction substantially reduces maintenance costs and prevents physical failures, while transparently identifying the trade-off of late-stage conditional coverage degradation. Complete source code, models, and artifacts are published openly.</w:t>
      </w:r>
    </w:p>
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1080" w:right="900" w:bottom="1080" w:left="900"/>
      <w:cols w:num="2" w:space="720"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    with zipfile.ZipFile(DOCX_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/_rels/document.xml.rels", document_rels)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/document.xml", doc_xml)
    print(f"Generated DOCX: {DOCX_PATH} ({os.path.getsize(DOCX_PATH)} bytes)")

if __name__ == "__main__":
    print("Building Corrected IEEE IntelliTwin Research Manuscript...")
    build_html()
    build_pdf()
    build_docx()
    print("All corrected IEEE deliverables generated successfully!")

