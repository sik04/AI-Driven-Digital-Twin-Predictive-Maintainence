# Thematic Literature Synthesis and Research Positioning

**Document Version**: `1.0`  
**Focus**: Critical Synthesis of Prior Works Across RUL Prognostics, Uncertainty Calibration, Subgroup Reliability, and Sequential Maintenance Decisions  
**Governing Standard**: Bounded, evidence-verified literature review (not styled as a completed PRISMA systematic review)

---

## 1. Introduction & Synthesis Scope

The predictive maintenance (PdM) of critical rotating machinery—such as commercial aircraft turbofan engines—demands accurate prognostic estimates of Remaining Useful Life (RUL) to prevent catastrophic in-service failures while avoiding the costly premature disposal of serviceable components. In recent years, research at the intersection of deep learning, uncertainty quantification (UQ), and cyber-physical systems (Digital Twins) has expanded rapidly.

However, an audit of contemporary literature reveals significant fragmentation:
- Advanced prognostic machine learning architectures often prioritize marginal point accuracy without formal calibration guarantees.
- Modern conformal prediction methods provide rigorous distribution-free finite-sample marginal coverage, but typically treat all miscoverage errors symmetrically and assume independent, identically distributed (exchangeable) observations.
- Industrial degradation processes occur under dynamic, time-varying operating regimes and continuous wear, where subgroup conditional reliability is paramount.
- Downstream maintenance policies depend asymmetrically on prediction lower bounds, meaning symmetric uncertainty quantification can lead to severe operational inefficiencies.

This synthesis organizes the verified scholarly evidence around five structural themes, culminating in the precise empirical research question that IntelliTwin is designed to evaluate.

---

## 2. Theme 1: Point-Prediction RUL Architectures and Benchmarks

The benchmark foundation for prognostic health management in aero-engines was established by Saxena et al. (2008) through the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) datasets (FD001–FD004). C-MAPSS models run-to-failure degradation trajectories for a fleet of turbofan engines under varying combinations of operating flight conditions (sea level to high altitude) and fault modes (high-pressure compressor and fan degradation).

Subsequent literature developed high-capacity point-prediction architectures ranging from multi-layer perceptrons and support vector machines to Convolutional Neural Networks (CNNs), Long Short-Term Memory (LSTM) recurrent networks, and gradient-boosted decision trees (e.g., LightGBM, XGBoost, and scikit-learn's Histogram Gradient Boosting Regressor).

### Methodological Characteristics & Limitations
1. **Asymmetric Error Penalties**: Saxena et al. (2008) formalized the classical C-MAPSS asymmetric scoring metric, which penalizes overestimating RUL ($d > 0$, late intervention risk) exponentially more heavily than underestimating RUL ($d < 0$, early replacement risk). Despite this widespread evaluation metric, most base prognostic models are trained using symmetric loss functions (such as Mean Squared Error or Huber loss).
2. **Piecewise Capping of Training Targets**: Real-world industrial engines undergo extended initial healthy phases during which degradation is negligible. Standard practice caps the maximum training RUL target (typically at 125 cycles). However, as highlighted in the IntelliTwin data evaluation protocol, while training targets are capped, calibration nonconformity scores and evaluation metrics must be computed against true, uncapped remaining life to evaluate genuine physical longevity.
3. **Absence of Actionable Confidence**: Point predictors emit single-valued cycle predictions ($\hat{y}$) that fail to quantify estimation risk, offering maintenance decision-makers no probabilistic basis for scheduling safety-critical interventions.

---

## 3. Theme 2: Uncertainty Quantification and Conformal Calibration

To move beyond point estimates, researchers introduced probabilistic prognostic frameworks. Early approaches relied on Gaussian Process Regression (GPR), Bayesian Neural Networks (BNNs), and Monte Carlo (MC) dropout ensembles (e.g., Zhu et al., 2025). While these methods output predictive variances, their intervals depend heavily on parametric distributional assumptions (e.g., Gaussianity) that are routinely violated by non-stationary degradation trajectories.

Conformal prediction (Vovk et al., 2005; Shafer & Vovk, 2008) emerged as a rigorous, distribution-free framework for constructing prediction intervals with finite-sample marginal coverage guarantees:
$$P(y_{n+1} \in C(x_{n+1})) \ge 1 - \alpha$$
under the single assumption of data exchangeability.

### Conformal Prediction in RUL Estimation
Javanmardi and Hüllermeier (2023) pioneered the application of inductive split conformal prediction (ICP) to RUL estimation on C-MAPSS, showing that conformal intervals guarantee nominal marginal coverage regardless of the underlying point predictor (evaluating CNN and gradient boosting models). 

More recently, Conformalized Quantile Regression (CQR) was adapted to turbofans by Diao et al. (2026), who combined LSTM-based quantile regression with conformal calibration across FD001 and FD002, and Robinson (2026), who evaluated asymmetric CQR across all four C-MAPSS sub-datasets.

### Theoretical & Practical Boundaries
- **Exchangeability Violation in Time Series**: Conformal prediction guarantees finite-sample coverage under exchangeability. However, sensor time series within an engine trajectory are auto-correlated and sequentially non-exchangeable.
- **Hierarchical Clustering**: When calibration engines vary in trajectory length, pooling raw cycles over-represents long-lived units. Lee, Barber, and Willett (2023) established the theoretical framework for *hierarchical conformal inference*, demonstrating that to preserve finite-sample guarantees for a new, unseen group (engine), empirical quantile mass must be engine-weighted, total finite mass is bounded by $\frac{m}{m+1}$, and the remaining $\frac{1}{m+1}$ probability mass must be assigned to $+\infty$.

---

## 4. Theme 3: Grouped Reliability and Operating-Condition Diagnostics

While standard conformal prediction guarantees marginal coverage averaged across all test observations, industrial reliability requires *conditional coverage*: prediction intervals must protect the asset across specific operating regimes and throughout different phases of equipment wear.

Recent literature demonstrates that global conformal calibrators frequently exhibit severe localized coverage breakdown:
1. **Operating-Regime Shifts**: In complex engines operating across multiple flight envelopes (e.g., C-MAPSS FD002 with 6 discrete clusters), Yang et al. (2026) audited empirical calibration across operating regimes on bearing degradation, showing that marginal coverage masked severe conditional undercoverage in high-stress operating regimes.
2. **Lifecycle Degradation Stages**: BenAbdennour (2026) investigated grouped validation and interval-safety calibration across engine, battery, and bearing datasets, demonstrating that predictive uncertainty expands non-linearly as components transition from early operating cycles to late, accelerated wear. Diao et al. (2026) similarly noted that prediction interval coverage fluctuates across degradation stages.
3. **Worst-Group Reliability Auditing**: Standard evaluation criteria that report only mean interval width (MPIW) or marginal coverage fail to penalize localized failures. If an interval achieves 95% coverage in mild operating regimes but drops to 70% coverage during high-altitude or high-stress regimes, the machine remains vulnerable to catastrophic failure.

---

## 5. Theme 4: Maintenance Decision-Making and the Cost of Conservatism

The ultimate objective of prognostic modeling is not statistical score optimization, but the cost-effective orchestration of physical maintenance actions. 

A stream of literature has examined uncertainty-aware maintenance scheduling:
- Chen et al. (2022) formulated predictive maintenance strategies considering RUL uncertainty distributions.
- Zhu et al. (2025) optimized aero-engine maintenance scheduling using deep-learning prediction intervals.
- Walia and Kumar (2026) integrated quantile-based RUL predictions with Proximal Policy Optimization (PPO) reinforcement learning to schedule maintenance in industrial IoT environments.
- Cortes-Gomez et al. (2025) introduced *Utility-Directed Conformal Prediction* (UDCP) at ICLR 2025, proposing that conformal score functions should be tailored to downstream decision loss rather than standard symmetric residuals.

### The Conservatism Confound
In sequential maintenance simulation (e.g., replacing an asset when its predicted RUL lower bound drops below a safety threshold $L \le 1$), a critical scientific hazard arises:
- **Trivial Conservatism**: Any method that arbitrarily widens its prediction intervals or artificially deflates its lower bounds will trigger earlier maintenance.
- **The False Benefit of Early Intervention**: In finite simulation benchmarks with heavy failure penalties ($C_{\text{FAIL}} \gg C_{\text{PM}}$), early replacement can artificially reduce observed failure rates to zero, appearing superficially superior. However, this occurs at the expense of massive wasted useful life ($C_{\text{WASTE}} \cdot W$) and premature component scrapping.
- **The Attribution Gap**: Prior studies (e.g., Yan 2026) evaluated maintenance costs alongside conformal intervals, but did not prespecify matched-conservatism controls to prove that maintenance savings stemmed from superior, decision-aware uncertainty estimates rather than simple over-conservatism.

---

## 6. The Precise Research Question Evaluated by IntelliTwin

Synthesizing these four streams reveals the unresolved research gap:

> **Existing RUL research has separately studied conformal uncertainty calibration, condition/regime-aware calibration, and uncertainty-aware maintenance decision-making. What remains insufficiently established is a RUL-specific method that jointly adapts calibration to operating conditions and downstream sequential maintenance consequences while preserving reliable uncertainty coverage.**

IntelliTwin addresses this gap directly through a pre-registered, empirical evaluation framework:
1. **Decision-Aware Asymmetric Nonconformity**: Implementing an asymmetric nonconformity score parameterized by scaling $\gamma$ and asymmetry $\beta$ that modulates interval shape as a function of point prediction $p$:
   $$\sigma(p) = \left(1 + \frac{p}{125}\right)^\gamma, \quad z(p) = \exp\left(-\frac{p}{20}\right)$$
   $$a(p) = \sigma(p)\exp(\beta z(p)), \quad b(p) = \sigma(p)\exp(-\beta z(p))$$
2. **Hierarchical Engine-Weighted Quantiles**: Computing exact finite-sample thresholds following Lee et al. (2023) to eliminate survivor bias and respect engine clustering.
3. **Frozen Multiplicity-Controlled Inference**: Evaluating four research questions (RQ1: Maintenance Utility; RQ2: Subgroup Reliability; RQ3: Decision-Value Attribution vs. Matched Controls; RQ4: Generalization) using 10,000-draw stratified cluster bootstrap decision intervals at 98.75% confidence (Bonferroni FWER $\alpha = 0.0125$) and intersection-union testing.
4. **Three-Way Pre-registered Decisions**: Structuring all findings into immutable `Supported`, `Unsupported`, or `Inconclusive` classifications under frozen practical-effect margins ($\Delta_{\text{cost}} > 0.20$ SCU, $\Delta_{\text{error}} > 0.01$, coverage ceiling $E < 0.05$).
