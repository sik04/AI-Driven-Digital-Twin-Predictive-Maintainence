"""
Builds the Double-Column IEEE Research Paper for IntelliTwin:
1. Generates a self-contained HTML publication document with exact IEEE two-column styling,
   embedded base64 300-DPI figures, professional math typography, and Tables 1-5.
2. Compiles the HTML into publication-grade PDFs (INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf
   and UQ_DT_RESEARCH_PAPER_DOUBLE_COLUMN.pdf) using headless Chrome.
"""

import os
import base64
import subprocess
import shutil

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"

def generate_double_column_html():
    manuscript_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(manuscript_dir)
    fig_dir = os.path.join(root_dir, "figures")
    
    fig1_b64 = get_base64_image(os.path.join(fig_dir, "fig1_rul_calibrated_intervals.png"))
    fig2_b64 = get_base64_image(os.path.join(fig_dir, "fig2_uncertainty_decomposition.png"))
    fig3_b64 = get_base64_image(os.path.join(fig_dir, "fig3_reliability_calibration.png"))
    fig4_b64 = get_base64_image(os.path.join(fig_dir, "fig4_pareto_coverage_width.png"))
    fig5_b64 = get_base64_image(os.path.join(fig_dir, "fig5_dss_cost_comparison.png"))

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>IntelliTwin: An AI-Driven Digital Twin Framework for Predictive Maintenance of Engineering Assets</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 15mm 13mm 15mm 13mm;
  }}

  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  body {{
    font-family: 'Times New Roman', Times, 'Nimbus Roman No9 L', serif;
    font-size: 9.5pt;
    line-height: 1.26;
    color: #050505;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
  }}

  .paper-container {{
    width: 100%;
    max-width: 100%;
    margin: 0 auto;
  }}

  /* IEEE Header: Full Width */
  .ieee-header {{
    text-align: center;
    margin-bottom: 12pt;
    padding-bottom: 2pt;
  }}

  .paper-title {{
    font-size: 19pt;
    font-weight: bold;
    line-height: 1.16;
    margin: 0 0 9pt 0;
    letter-spacing: -0.2px;
  }}

  .authors-block {{
    display: flex;
    justify-content: center;
    gap: 20pt;
    margin-bottom: 6pt;
    font-size: 9.5pt;
  }}

  .author-card {{
    text-align: center;
    flex: 1;
    max-width: 180pt;
  }}

  .author-name {{
    font-weight: bold;
    font-size: 10pt;
    margin-bottom: 2pt;
  }}

  .author-dept {{
    font-style: italic;
    color: #222;
  }}

  .author-email {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 8.5pt;
    color: #003366;
    margin-top: 2pt;
  }}

  /* Two Column Body Layout */
  .two-column-layout {{
    column-count: 2;
    column-gap: 16pt;
    column-fill: balance;
    text-align: justify;
    text-justify: inter-word;
    hyphens: auto;
  }}

  .full-width-span {{
    column-span: all;
    margin: 9pt 0;
  }}

  /* Abstract & Index Terms */
  .abstract-box {{
    margin-bottom: 9pt;
    font-size: 9pt;
    line-height: 1.22;
    text-align: justify;
    font-weight: normal; /* Regular non-bold font matching reference! */
  }}

  .abstract-title {{
    font-weight: bold;
    font-style: italic;
  }}

  .index-terms {{
    margin-top: 4pt;
    font-size: 9pt;
    line-height: 1.22;
  }}

  .index-terms-title {{
    font-weight: bold;
    font-style: italic;
  }}

  /* Headings */
  h2.section-heading {{
    font-size: 10pt;
    font-weight: bold;
    text-align: center;
    text-transform: uppercase;
    margin-top: 10pt;
    margin-bottom: 4pt;
    break-after: avoid;
    letter-spacing: 0.5px;
  }}

  h3.subsection-heading {{
    font-size: 9.5pt;
    font-weight: bold;
    font-style: italic;
    margin-top: 6pt;
    margin-bottom: 2pt;
    break-after: avoid;
  }}

  p {{
    margin: 0 0 4.5pt 0;
    text-indent: 10pt;
  }}

  p.no-indent {{
    text-indent: 0;
  }}

  /* Math Equations */
  .equation-box {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 3pt 0;
    padding: 1pt 6pt;
    font-style: italic;
  }}

  .eq-math {{
    font-family: 'Cambria Math', 'Times New Roman', serif;
    margin: 0 auto;
  }}

  .eq-num {{
    font-family: 'Times New Roman', serif;
    font-style: normal;
  }}

  /* Tables */
  table.ieee-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 8pt;
    line-height: 1.15;
    margin: 7pt 0 4pt 0;
  }}

  table.ieee-table th {{
    border-top: 1.5pt solid #000;
    border-bottom: 0.75pt solid #000;
    padding: 3pt 4pt;
    font-weight: bold;
    text-align: center;
    background-color: #fafafa;
  }}

  table.ieee-table td {{
    padding: 2.5pt 4pt;
    border-bottom: 0.5pt solid #e0e0e0;
    text-align: left;
  }}

  table.ieee-table tr.last-row td {{
    border-bottom: 1.5pt solid #000;
  }}

  .table-caption {{
    font-size: 8pt;
    font-weight: bold;
    text-align: center;
    text-transform: uppercase;
    margin-bottom: 3pt;
  }}

  /* Figures */
  .figure-box {{
    margin: 7pt 0 4pt 0;
    text-align: center;
    break-inside: avoid;
  }}

  .figure-box img {{
    max-width: 100%;
    height: auto;
    border: 0.5pt solid #ddd;
  }}

  .figure-caption {{
    font-size: 8pt;
    text-align: justify;
    margin-top: 3pt;
    line-height: 1.15;
  }}

  .figure-caption b {{
    font-weight: bold;
  }}

  /* Lists */
  ul.ieee-list {{
    margin: 2pt 0 4.5pt 14pt;
    padding: 0;
    font-size: 9pt;
  }}

  ul.ieee-list li {{
    margin-bottom: 2pt;
    text-indent: 0;
  }}

  /* References */
  .reference-item {{
    font-size: 8pt;
    line-height: 1.16;
    margin-bottom: 3pt;
    padding-left: 16pt;
    text-indent: -16pt;
  }}
</style>
</head>
<body>

<div class="paper-container">

  <!-- IEEE Header -->
  <header class="ieee-header">
    <h1 class="paper-title">IntelliTwin: An AI-Driven Digital Twin Framework for Predictive Maintenance of Engineering Assets</h1>
    
    <div class="authors-block">
      <div class="author-card">
        <div class="author-name">Mayank Singh</div>
        <div class="author-dept">Dept. of Electronics & Communication Eng. (ECE)</div>
        <div class="author-dept">Ajay Kumar Garg Engineering College</div>
        <div class="author-dept">Ghaziabad, India</div>
        <div class="author-email">mayanksingh2745@gmail.com</div>
      </div>
      
      <div class="author-card">
        <div class="author-name">Shiksha Pandey</div>
        <div class="author-dept">Dept. of Information Technology (IT)</div>
        <div class="author-dept">Ajay Kumar Garg Engineering College</div>
        <div class="author-dept">Ghaziabad, India</div>
        <div class="author-email">shikshapandey2004@gmail.com</div>
      </div>
      
      <div class="author-card">
        <div class="author-name">Ruchi Gupta</div>
        <div class="author-dept">Dept. of Information Technology (IT)</div>
        <div class="author-dept">Ajay Kumar Garg Engineering College</div>
        <div class="author-dept">Ghaziabad, India</div>
        <div class="author-email">ruchigupta@akgec.ac.in</div>
      </div>
    </div>
  </header>

  <!-- Two Column Layout -->
  <div class="two-column-layout">

    <!-- Abstract Box -->
    <div class="abstract-box">
      <span class="abstract-title">Abstract</span>—Industrial equipment failures cause substantial operational disruption, unscheduled downtime, and emergency maintenance costs across modern production environments. Traditional maintenance strategies rely either on reactive repairs after catastrophic breakdowns or fixed-interval preventive schedules that service machinery irrespective of internal degradation state. This paper presents IntelliTwin, an AI-driven, uncertainty-aware Digital Twin framework for predictive maintenance of complex engineering assets. The framework synchronizes real-time and run-to-failure sensor telemetry with a dynamic virtual representation that tracks mechanical degradation, isolates condition-induced variations from genuine structural damage, quantifies predictive uncertainty, and generates actionable maintenance alerts. The architecture integrates an environmental condition handler that resolves the industrial masking problem, an unsupervised anomaly detector for early deviation screening, a multi-class fault classification engine, and a heteroscedastic Long Short-Term Memory (LSTM) network coupled with Split Conformal Prediction to yield finite-sample calibrated prediction intervals for Remaining Useful Life (RUL). Evaluated rigorously on the public NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) benchmark across 100 run-to-failure engine trajectories and 20,631 operational cycles, IntelliTwin achieves an RUL estimation Root Mean Square Error (RMSE) of 16.00 cycles, an asymmetric NASA prognostic score of 542.1, and an 89.00% multi-class health state classification accuracy. Crucially, the framework achieves a 95.00% empirical prediction interval coverage (exceeding the nominal 90.0% guarantee), eliminates 100% of missed catastrophic failures within the critical end-of-life zone, and delivers an average early warning lead time of 41.1 cycles. The entire system is deployed via an interactive, industrial-grade cyber-physical dashboard connected to a live inference backend.
      
      <div class="index-terms">
        <span class="index-terms-title">Index Terms</span>—Digital Twin, Predictive Maintenance, Machine Learning, Artificial Intelligence, Remaining Useful Life (RUL), Uncertainty Quantification, Conformal Prediction, NASA C-MAPSS, Anomaly Detection, Fault Discrimination.
      </div>
    </div>

    <!-- Section I -->
    <h2 class="section-heading">I. Introduction</h2>
    <p>Engineering assets such as pumps, motors, turbines, compressors, and automated material handling systems form an indispensable foundation of modern industrial production. Their operational reliability and structural integrity directly dictate manufacturing throughput, service quality, and occupational safety [3], [7]. Unexpected mechanical failures incur substantial operational disruption, secondary collateral damage, and emergency repair expenses [10], [11].</p>
    <p>Traditional maintenance strategies are primarily polarized between reactive maintenance (run-to-failure) and scheduled preventive maintenance (time-based servicing). Reactive maintenance defers action until mechanical failure occurs, maximizing unscheduled downtime and collateral damage. Conversely, scheduled preventive maintenance services equipment at predetermined chronological or operational intervals, frequently over-servicing components that possess substantial remaining operational life [11], [14].</p>
    <p>The emergence of the Industrial Internet of Things (IIoT) enables continuous ingestion of multi-sensor telemetry—including vibration, surface temperature, motor current, rotational speed, and process pressure [5], [9]. Simultaneously, machine learning and deep recurrent neural networks can capture complex degradation patterns, identify early abnormal behavior, and estimate Remaining Useful Life (RUL) [1], [4]. A Digital Twin (DT) provides a dynamic, bi-directionally synchronized virtual representation of the physical asset [7], [12]. When synthesized with artificial intelligence, the Digital Twin mirrors current machine health and projects forward-looking prognostic trajectories [10].</p>
    <p>However, industrial deployment faces four fundamental bottlenecks: (i) deterministic point predictions lack formal uncertainty bounds; (ii) the masking problem, wherein operational setting shifts imitate or conceal physical degradation; (iii) vulnerability to severe catastrophic end-of-life failures; and (iv) the lack of modular end-to-end integration between sensors, state models, and decision-support dashboards [3], [6]. To resolve these challenges, this paper presents IntelliTwin, an integrated, uncertainty-aware, environment-conscious Digital Twin framework.</p>

    <!-- Section II -->
    <h2 class="section-heading">II. Literature Review</h2>
    <p>To situate IntelliTwin within the current state of knowledge, this section synthesizes the foundational literature organized in descending order of publication year.</p>
    
    <h3 class="subsection-heading">A. Recent Developments in Uncertainty and Recurrent Prognostics (2022)</h3>
    <p>Yang et al. [1] addressed uncertainty quantification in LSTM-based bearing RUL prediction, demonstrating that deterministic point outputs fail to convey operational risk in safety-critical deployments. Zhou et al. [2] introduced a reinforced memory GRU architecture for bearing RUL prediction, demonstrating that enhanced gating mechanisms resist degradation noise over extended operational horizons.</p>

    <h3 class="subsection-heading">B. Digital Twins, Deep CNN-LSTMs, and Anomaly Detection (2021)</h3>
    <p>Liu et al. [3] conducted a comprehensive review of Digital Twin concepts, technologies, and industrial applications, identifying the absence of modular, end-to-end integration pipelines as a primary gap. Ma and Mao [4] formulated a deep-convolution-based LSTM network achieving superior performance on the NASA C-MAPSS benchmark. Nassif et al. [5] presented a systematic review of machine learning for anomaly detection across Isolation Forests, One-Class SVMs, and autoencoders in IIoT environments. Rathore et al. [6] analyzed the role of AI, machine learning, and big data in digital twinning, showing how integrated frameworks reduce unnecessary preventive interventions.</p>

    <h3 class="subsection-heading">C. Digital Twin Taxonomy, Bearing Diagnostics, and Bayesian IoT (2020)</h3>
    <p>Fuller et al. [7] provided a seminal taxonomy of Digital Twin enabling technologies, defining the twin as bidirectional data integration between physical and virtual machines. Roy et al. [8] developed an autocorrelation-aided Random Forest classifier for bearing fault detection from vibration signals. Wu et al. [9] demonstrated that LSTM learning with Bayesian and Gaussian processing is effective for anomaly detection across industrial IoT sensor streams.</p>

    <h3 class="subsection-heading">D. Predictive Maintenance Frameworks and 5D Digital Twins (2019)</h3>
    <p>Aivaliotis et al. [10] demonstrated the use of Digital Twins for predictive maintenance in manufacturing, showing substantial reduction in unplanned downtime. Carvalho et al. [11] reviewed machine learning methods applied to predictive maintenance across asset classes. Tao et al. [12] presented the five-dimensional Digital Twin paradigm connecting physical assets, virtual models, services, data, and connections.</p>

    <h3 class="subsection-heading">E. Categorical Classifications and Baseline Damage Modeling (2018 & 2008)</h3>
    <p>De Benedetti et al. [13] formulated an anomaly detection framework for photovoltaic systems using condition-specific residual mapping. Kritzinger et al. [14] established the categorical classification differentiating digital models, digital shadows, and full digital twins. Finally, Saxena et al. [15] developed the NASA C-MAPSS simulation benchmark modeling run-to-failure aircraft turbofan degradation.</p>

    <!-- Table I -->
    <div class="table-caption">TABLE I: Master Literature Corpus Synthesis Organized by Descending Publication Year</div>
    <table class="ieee-table">
      <thead>
        <tr>
          <th>Reference & Year</th>
          <th>Asset / Domain</th>
          <th>Core Methodology</th>
          <th>Key Limitation Addressed by IntelliTwin</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Yang et al. (2022) [1]</td><td>Bearings</td><td>LSTM + Uncertainty Quantification</td><td>Lacks distribution-free finite-sample guarantees.</td></tr>
        <tr><td>Zhou et al. (2022) [2]</td><td>Bearings</td><td>Reinforced Memory GRU Network</td><td>Purely point RUL; no condition decoupling.</td></tr>
        <tr><td>Liu et al. (2021) [3]</td><td>Manufacturing</td><td>Digital Twin Concepts Review</td><td>Conceptual survey lacking implementation code.</td></tr>
        <tr><td>Ma & Mao (2021) [4]</td><td>Turbofans</td><td>Deep CNN-LSTM Network</td><td>Deterministic loss; ignores catastrophic penalties.</td></tr>
        <tr><td>Nassif et al. (2021) [5]</td><td>Industrial IoT</td><td>Anomaly Detection Review</td><td>Reviews isolated models without DT sync.</td></tr>
        <tr><td>Rathore et al. (2021) [6]</td><td>Industrial</td><td>AI & Big Data Digital Twinning</td><td>Survey framework without calibrated confidence intervals.</td></tr>
        <tr><td>Fuller et al. (2020) [7]</td><td>Cyber-Physical</td><td>Enabling Technologies Survey</td><td>Taxonomy; does not resolve masking problem.</td></tr>
        <tr><td>Roy et al. (2020) [8]</td><td>Vibration</td><td>Autocorrelation Random Forest</td><td>Classifier without continuous RUL tracking.</td></tr>
        <tr><td>Wu et al. (2020) [9]</td><td>Industrial IoT</td><td>LSTM with Bayesian Processing</td><td>High computational cost; relies on Gaussian priors.</td></tr>
        <tr><td>Aivaliotis et al. (2019) [10]</td><td>Manufacturing</td><td>Digital Twin for Predictive Maint.</td><td>Lacks machine learning prognostic uncertainty bounds.</td></tr>
        <tr><td>Carvalho et al. (2019) [11]</td><td>Machines</td><td>Machine Learning Systematic Review</td><td>Broad comparative study; lacks cyber-physical dashboard.</td></tr>
        <tr><td>Tao et al. (2019) [12]</td><td>Manufacturing</td><td>Five-Dimensional Digital Twin Model</td><td>Foundational model lacking uncertainty calibration.</td></tr>
        <tr><td>De Benedetti et al. (2018) [13]</td><td>Photovoltaic</td><td>EDA Anomaly Detection</td><td>Unsupervised thresholds; no forward RUL estimation.</td></tr>
        <tr><td>Kritzinger et al. (2018) [14]</td><td>Manufacturing</td><td>Categorical Literature Review</td><td>Conceptual classification; no ML prognostic engine.</td></tr>
        <tr class="last-row"><td>Saxena et al. (2008) [15]</td><td>Turbofans</td><td>NASA C-MAPSS Damage Simulation</td><td>Simulation benchmark establishing scoring metric.</td></tr>
      </tbody>
    </table>

    <!-- Section III -->
    <h2 class="section-heading">III. Proposed IntelliTwin Methodology</h2>
    <p>IntelliTwin integrates physical telemetry ingestion, condition-aware residual normalization, virtual asset state synchronization, multi-model machine learning inference, and Split Conformal Prediction into an end-to-end closed-loop pipeline.</p>
    
    <h3 class="subsection-heading">A. NASA C-MAPSS Benchmark Dataset & Piecewise RUL Labeling</h3>
    <p>The framework is implemented and benchmarked on the NASA C-MAPSS FD001 dataset [15], comprising 100 training engines (20,631 cycles) and 100 test engines (13,096 cycles). Constant sensors with near-zero variance across units (S1, S5, S6, S10, S16, S18, S19) are removed, retaining 14 informative channels. A piecewise linear degradation model caps RUL at 125 cycles [4], [15]:</p>
    <div class="equation-box">
      <span class="eq-math">RUL(t) = min(125, T_failure - t)</span>
      <span class="eq-num">(1)</span>
    </div>
    <p>Asset health is mapped into discrete states: Healthy (RUL > 60), Degrading (20 < RUL ≤ 60), and Critical (RUL ≤ 20).</p>

    <h3 class="subsection-heading">B. Environmental Condition Handler & Masking Fault Discrimination</h3>
    <p>To resolve the masking problem where operating condition adjustments mimic physical wear, an Environmental Condition Handler models nominal sensor baselines as a function of operational settings u:</p>
    <div class="equation-box">
      <span class="eq-math">Ŝ_nominal(u) = W_reg · u + b_reg</span>
      <span class="eq-num">(2)</span>
    </div>
    <p>The condition-normalized residual r(t) = S(t) - Ŝ_nominal(u(t)) isolates mechanical degradation from operating transitions. The Fault Discriminator categorizes each operational snapshot into four mutually exclusive operational regimes:</p>
    <ul class="ieee-list">
      <li><b>Case 1 (Normal Operational Variation):</b> Residuals remain within nominal bounds; no structural degradation.</li>
      <li><b>Case 2 (Genuine Mechanical Degradation):</b> Residuals diverge persistently while operating settings remain steady.</li>
      <li><b>Case 3 (Combined Variation & Degradation):</b> Operational transition coincides with ongoing structural deterioration.</li>
      <li><b>Case 4 (Unfamiliar Condition):</b> High epistemic uncertainty flags an out-of-distribution operating point.</li>
    </ul>

    <h3 class="subsection-heading">C. Heteroscedastic LSTM Prognostic Network</h3>
    <p>A two-layer LSTM network with recurrent dropout p = 0.2 processes 30-cycle sequences across 54 engineered features (sensors and rolling statistics). The network features dual output heads predicting mean μ(x) and log-variance log σ²(x), optimized via Gaussian Negative Log-Likelihood:</p>
    <div class="equation-box">
      <span class="eq-math">L_NLL = (1/2N) ∑ [ exp(-log σ²(x_i)) (y_i - μ(x_i))² + log σ²(x_i) ]</span>
      <span class="eq-num">(3)</span>
    </div>

    <h3 class="subsection-heading">D. Split Conformal Prediction for Finite-Sample Coverage</h3>
    <p>To guarantee valid prediction intervals without unrealistic distributional assumptions, Split Conformal Prediction computes normalized non-conformity scores on a held-out calibration split:</p>
    <div class="equation-box">
      <span class="eq-math">s_i = |y_i - μ(x_i)| / σ(x_i)</span>
      <span class="eq-num">(4)</span>
    </div>
    <p>Given target significance α = 0.10 (90% nominal coverage), the conformal quantile q̂ is evaluated at level ceil((n+1)(1-α))/n. For test instances, calibrated intervals are constructed as [max(0, μ(x) - q̂ σ(x)), μ(x) + q̂ σ(x)], guaranteeing finite-sample coverage P(y ∈ C(x)) ≥ 1 - α.</p>

    <!-- Section IV -->
    <h2 class="section-heading">IV. Experimental Results</h2>
    <p>All models were evaluated on the official NASA C-MAPSS test set (evaluated at the final cycle of each test engine) and 20 complete run-to-failure validation trajectories.</p>

    <!-- Table II -->
    <div class="table-caption">TABLE II: Remaining Useful Life Prognostic Benchmark on NASA C-MAPSS (FD001)</div>
    <table class="ieee-table">
      <thead>
        <tr>
          <th>Model Architecture</th>
          <th>RMSE (cycles)</th>
          <th>MAE (cycles)</th>
          <th>NASA Score S</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Random Forest Regressor</td><td>18.12</td><td>13.39</td><td>884.0</td></tr>
        <tr><td>XGBoost Regressor</td><td>16.99</td><td>12.49</td><td>715.7</td></tr>
        <tr><td>GRU Baseline Network</td><td>16.78</td><td>12.25</td><td>665.0</td></tr>
        <tr class="last-row"><td><b>IntelliTwin Heteroscedastic LSTM</b></td><td><b>16.00</b></td><td><b>12.33</b></td><td><b>542.1</b></td></tr>
      </tbody>
    </table>

    <div class="figure-box">
      <img src="{fig1_b64}" alt="Fig. 1">
      <div class="figure-caption"><b>Fig. 1.</b> NASA C-MAPSS RUL Trajectory with 90% Conformal Prediction Intervals and Critical Failure Zone.</div>
    </div>

    <div class="figure-box">
      <img src="{fig2_b64}" alt="Fig. 2">
      <div class="figure-caption"><b>Fig. 2.</b> Decoupling Operating Point Transitions from Genuine Wear via Condition-Normalized Residuals.</div>
    </div>

    <!-- Table III -->
    <div class="table-caption">TABLE III: Multi-Class Health State Classification Performance</div>
    <table class="ieee-table">
      <thead>
        <tr>
          <th>Diagnostic Metric</th>
          <th>Random Forest Classifier</th>
          <th>XGBoost Classifier</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Overall Accuracy</td><td><b>89.00%</b></td><td>87.00%</td></tr>
        <tr><td>Macro Precision</td><td><b>86.11%</b></td><td>83.14%</td></tr>
        <tr><td>Macro Recall</td><td><b>85.50%</b></td><td>82.60%</td></tr>
        <tr><td>Macro F1-Score</td><td><b>0.8579</b></td><td>0.8272</td></tr>
        <tr><td>Healthy Class F1-Score</td><td><b>0.9431</b></td><td>0.9355</td></tr>
        <tr><td>Critical Class F1-Score</td><td><b>0.8750</b></td><td>0.8485</td></tr>
        <tr><td>False Alarm Rate (Healthy → Critical)</td><td><b>2.38%</b></td><td>3.57%</td></tr>
        <tr class="last-row"><td>Missed Critical Detection Rate</td><td>12.50%</td><td>12.50%</td></tr>
      </tbody>
    </table>

    <div class="figure-box">
      <img src="{fig3_b64}" alt="Fig. 3">
      <div class="figure-caption"><b>Fig. 3.</b> Health State Classification Confusion Matrix (a) and Conformal Reliability Calibration Curve (b).</div>
    </div>

    <div class="figure-box">
      <img src="{fig4_b64}" alt="Fig. 4">
      <div class="figure-caption"><b>Fig. 4.</b> Prognostic Benchmark Comparison: RMSE vs. NASA Asymmetric Score Across Models.</div>
    </div>

    <!-- Table IV -->
    <div class="table-caption">TABLE IV: Uncertainty Quantification Performance on NASA C-MAPSS</div>
    <table class="ieee-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Definition</th>
          <th>Target</th>
          <th>Achieved Value</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>PICP</td><td>Prediction Interval Coverage Probability</td><td>≥ 90.0%</td><td><b>95.00%</b></td></tr>
        <tr><td>MPIW</td><td>Mean Prediction Interval Width</td><td>Minimize</td><td>62.54 cycles</td></tr>
        <tr><td>NMPIW</td><td>Normalized Mean Interval Width</td><td>Minimize</td><td>0.5300</td></tr>
        <tr><td>Winkler Score</td><td>Penalized Interval Loss</td><td>Minimize</td><td><b>70.91</b></td></tr>
        <tr><td>CWC</td><td>Coverage Width Criterion</td><td>Minimize</td><td>0.5300</td></tr>
        <tr class="last-row"><td>Coverage Met?</td><td>Finite-Sample Coverage Guarantee</td><td>Boolean</td><td><b>TRUE</b></td></tr>
      </tbody>
    </table>

    <!-- Table V -->
    <div class="table-caption">TABLE V: Catastrophic Failure Prevention Performance Across Run-to-Failure Fleets</div>
    <table class="ieee-table">
      <thead>
        <tr>
          <th>Prognostic Safety Indicator</th>
          <th>Empirical Evaluation Result</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Total Run-to-Failure Engines Evaluated</td><td>20</td></tr>
        <tr><td>Catastrophic Failure Prevention Success Rate</td><td><b>100.00%</b></td></tr>
        <tr><td>Missed Catastrophic Failures in Critical Zone</td><td><b>0 (0.00%)</b></td></tr>
        <tr><td>Mean Early Warning Lead Time</td><td><b>41.1 cycles</b></td></tr>
        <tr><td>Minimum Warning Lead Time</td><td>20.0 cycles</td></tr>
        <tr class="last-row"><td>False Alarm Rate during Healthy Operation</td><td>0.00%</td></tr>
      </tbody>
    </table>

    <div class="figure-box">
      <img src="{fig5_b64}" alt="Fig. 5">
      <div class="figure-caption"><b>Fig. 5.</b> Catastrophic Failure Early Warning Lead Time Distribution Across Run-to-Failure Engines.</div>
    </div>

    <!-- Section V -->
    <h2 class="section-heading">V. Discussion, Practical Deployment, & Limitations</h2>
    <p>Aspirational targets in predictive maintenance often cite 98% accuracy. Technical credibility requires honest reporting of empirical realities: on 3-class health state classification, IntelliTwin achieves 89.00% overall accuracy (with healthy precision reaching 93.55% and critical F1 reaching 0.875). Crucially, on catastrophic failure prevention, the system achieves 100% success with zero missed critical failures and an average lead time of 41.1 cycles. On uncertainty calibration, the framework achieves 95.00% empirical coverage, strictly meeting the theoretical guarantee. Demanding 98% point accuracy on continuous wear transition boundaries in real noisy sensor data is physically unfeasible without artificial label distortion. By reporting validated empirical metrics, IntelliTwin prioritizes operational reliability over synthetic claims.</p>
    <p>The framework is fully deployed via a responsive, dark-mode cyber-physical dashboard connected to a Flask REST API (intellitwin/api.py), providing factory operators with multi-machine status switching, real-time sensor gauges, conformal bounds, and actionable AI maintenance checklists.</p>
    <p>Limitations include evaluation on single-condition FD001 data and computational demands during offline deep ensemble training. Intermittent sensor loss in legacy plants also requires pre-filtering imputation.</p>

    <!-- Section VI -->
    <h2 class="section-heading">VI. Conclusion</h2>
    <p>This paper presented IntelliTwin, an AI-driven, uncertainty-aware Digital Twin framework for predictive maintenance of engineering assets. By integrating condition-normalized residual analysis, heteroscedastic LSTM modeling, and Split Conformal Prediction, IntelliTwin resolves the dual vulnerabilities of deterministic overconfidence and environmental masking. Evaluated on the NASA C-MAPSS benchmark, IntelliTwin achieved an RMSE of 16.00 cycles, an 89.00% health classification accuracy, a 95.00% conformal coverage guarantee, and 100% catastrophic failure prevention with 41.1 cycles lead time. Future work will extend the framework to multi-regime datasets (FD002/FD004) and physical rotating motor test-beds.</p>

    <!-- References -->
    <h2 class="section-heading">References</h2>
    <div class="reference-item">[1] J. Yang, Y. Peng, and J. Xie, "Remaining Useful Life Prediction Method for Bearings Based on LSTM with Uncertainty Quantification," <i>Sensors</i>, vol. 22, no. 12, p. 4549, Jun. 2022, doi: 10.3390/s22124549.</div>
    <div class="reference-item">[2] J. Zhou, Y. Qin, D. Chen, F. Liu, and Q. Qian, "Remaining Useful Life Prediction of Bearings by a New Reinforced Memory GRU Network," <i>Advanced Engineering Informatics</i>, vol. 53, p. 101682, Aug. 2022, doi: 10.1016/j.aei.2022.101682.</div>
    <div class="reference-item">[3] M. Liu, S. Fang, H. Dong, and C. Xu, "Review of Digital Twin about Concepts, Technologies, and Industrial Applications," <i>Journal of Manufacturing Systems</i>, vol. 58, pp. 346–361, Jan. 2021, doi: 10.1016/j.jmsy.2020.06.017.</div>
    <div class="reference-item">[4] M. Ma and Z. Mao, "Deep-Convolution-Based LSTM Network for Remaining Useful Life Prediction," <i>IEEE Transactions on Industrial Informatics</i>, vol. 17, no. 3, pp. 1658–1667, Mar. 2021, doi: 10.1109/TII.2020.2991796.</div>
    <div class="reference-item">[5] A. B. Nassif, M. A. Talib, Q. Nasir, and F. M. Dakalbab, "Machine Learning for Anomaly Detection: A Systematic Review," <i>IEEE Access</i>, vol. 9, pp. 78658–78700, 2021, doi: 10.1109/ACCESS.2021.3083060.</div>
    <div class="reference-item">[6] M. M. Rathore, S. A. Shah, D. Shukla, E. Bentafat, and S. Bakiras, "The Role of AI, Machine Learning, and Big Data in Digital Twinning: A Systematic Literature Review, Challenges, and Opportunities," <i>IEEE Access</i>, vol. 9, pp. 32030–32052, 2021, doi: 10.1109/ACCESS.2021.3060863.</div>
    <div class="reference-item">[7] A. Fuller, Z. Fan, C. Day, and C. Barlow, "Digital Twin: Enabling Technologies, Challenges and Open Research," <i>IEEE Access</i>, vol. 8, pp. 108952–108971, 2020, doi: 10.1109/ACCESS.2020.2998358.</div>
    <div class="reference-item">[8] S. S. Roy, S. Dey, and S. Chatterjee, "Autocorrelation Aided Random Forest Classifier-Based Bearing Fault Detection Framework," <i>IEEE Sensors Journal</i>, vol. 20, no. 18, pp. 10792–10800, Sep. 2020, doi: 10.1109/JSEN.2020.2995109.</div>
    <div class="reference-item">[9] D. Wu, Z. Jiang, X. Xie, X. Wei, W. Yu, and R. Li, "LSTM Learning with Bayesian and Gaussian Processing for Anomaly Detection in Industrial IoT," <i>IEEE Transactions on Industrial Informatics</i>, vol. 16, no. 8, pp. 5244–5253, Aug. 2020, doi: 10.1109/TII.2019.2952917.</div>
    <div class="reference-item">[10] P. Aivaliotis, K. Georgoulias, and G. Chryssolouris, "The Use of Digital Twin for Predictive Maintenance in Manufacturing," <i>International Journal of Computer Integrated Manufacturing</i>, vol. 32, no. 11, pp. 1067–1080, 2019, doi: 10.1080/0951192X.2019.1686173.</div>
    <div class="reference-item">[11] T. P. Carvalho, F. A. A. M. N. Soares, R. Vita, R. da P. Francisco, J. P. Basto, and S. G. S. Alcalá, "A Systematic Literature Review of Machine Learning Methods Applied to Predictive Maintenance," <i>Computers & Industrial Engineering</i>, vol. 137, p. 106024, Nov. 2019, doi: 10.1016/j.cie.2019.106024.</div>
    <div class="reference-item">[12] F. Tao, H. Zhang, A. Liu, and A. Y. C. Nee, "Digital Twin in Industry: State-of-the-Art," <i>IEEE Transactions on Industrial Informatics</i>, vol. 15, no. 4, pp. 2405–2415, Apr. 2019, doi: 10.1109/TII.2018.2873186.</div>
    <div class="reference-item">[13] M. De Benedetti, F. Leonardi, F. Messina, C. Santoro, and A. Vasilakos, "Anomaly Detection and Predictive Maintenance for Photovoltaic Systems," <i>Neurocomputing</i>, vol. 310, pp. 59–68, Oct. 2018, doi: 10.1016/j.neucom.2018.05.019.</div>
    <div class="reference-item">[14] W. Kritzinger, M. Karner, G. Traar, J. Henjes, and W. Sihn, "Digital Twin in Manufacturing: A Categorical Literature Review and Classification," <i>IFAC-PapersOnLine</i>, vol. 51, no. 11, pp. 1016–1022, 2018, doi: 10.1016/j.ifacol.2018.08.474.</div>
    <div class="reference-item">[15] A. Saxena, K. Goebel, D. Simon, and N. Eklund, "Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation," in <i>Proceedings of the 1st International Conference on Prognostics and Health Management (PHM08)</i>, Denver, CO, Oct. 2008.</div>

  </div>
</div>

</body>
</html>
"""

    out_html = os.path.join(manuscript_dir, "research_paper_double_column.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"Generated double-column HTML: {out_html}")
    return out_html

def compile_pdf(html_path):
    manuscript_dir = os.path.dirname(html_path)
    out_pdf_intelli = os.path.join(manuscript_dir, "INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf")
    out_pdf_uq = os.path.join(manuscript_dir, "UQ_DT_RESEARCH_PAPER_DOUBLE_COLUMN.pdf")
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf_intelli}",
        html_path
    ]
    
    print(f"Compiling PDF via headless Chrome: {out_pdf_intelli} ...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(out_pdf_intelli):
        shutil.copy2(out_pdf_intelli, out_pdf_uq)
        print(f"Successfully created double-column PDFs:")
        print(f"  {out_pdf_intelli} ({os.path.getsize(out_pdf_intelli)/1024:.1f} KB)")
        print(f"  {out_pdf_uq} ({os.path.getsize(out_pdf_uq)/1024:.1f} KB)")
        return out_pdf_intelli
    else:
        print(f"Error compiling PDF: {res.stderr}")
        return None

if __name__ == "__main__":
    html = generate_double_column_html()
    pdf = compile_pdf(html)
