# Phase 8 Exploratory Ablation & Robustness Analysis: Scientific Synthesis

- **Protocol Version**: `phase08-v1`
- **Status**: Complete Exploratory Analysis
- **Scope**: 240 Ablation Cells, 1,620 Stress Evaluations across 122 Held-Out Engines
- **Scientific Status**: EXPLORATORY_POST_CONFIRMATORY (Original RQ1–RQ4 remain UNSUPPORTED)

---

## 1. Executive Summary

Phase 8 investigates the mechanics and sensitivity limits of the conformal prediction systems evaluated in Step 9.
Under controlled $2 \times 2 \times 2$ factorial component ablation and 7 predefined engineering stress probes:
1. **Scale Dilation ($\gamma=2$)**: Primary driver of operational maintenance cost reduction. By expanding uncertainty bounds as predicted RUL increases, scale dilation mitigates premature maintenance interventions during early and mid-life operational cycles.
2. **Asymmetry ($\beta=-\ln(2)$)**: Moderates catastrophic lower-tail coverage misses in late lifecycle stages. However, asymmetry alone does not fully resolve worst-stage coverage deficiencies on complex regimes.
3. **Regime-Adaptive Routing**: Yields localized threshold sharpening but exhibits vulnerability under measurement bias and sensor dropout.
4. **Engineering Stress Resilience**: All methods demonstrate gradual cost degradation under Gaussian sensor noise (up to $\sigma=0.20$), but causal sensor dropout ($p \ge 0.05$) induces coverage loss due to forward-fill staleness.

---

## 2. Component Ablation Findings (Experiment A)

| Factor | Contrast (On - Off) | Mean Cost Impact (SCU) | Primary Effect |
| :--- | :---: | :---: | :--- |
| Scale ($\gamma: 2 \text{ vs } 0$) | $\Delta_{\text{cost}}$ | $-1.42$ SCU | Favorable cost reduction across all matched settings |
| Asymmetry ($\beta: -\ln(2) \text{ vs } 0$) | $\Delta_{\text{cost}}$ | $+0.18$ SCU | Slight conservative cost penalty trading off tail coverage |
| Routing (`regime` vs `global`) | $\Delta_{\text{cost}}$ | $-0.09$ SCU | Modest localized cost improvement on multi-regime datasets |

> [!NOTE]
> Passing individual cost components or identifying dominant factors does not imply that every component is strictly necessary or that joint confirmatory hypotheses are supported.

---

## 3. Engineering Stress Test Findings (Experiment B)

- **Gaussian Sensor Noise**: Performance degrades smoothly across $\sigma \in [0.05, 0.20]$. No catastrophic failure or sudden threshold divergence occurs.
- **Causal Sensor Dropout**: Forward-fill imputation preserves sequential continuity, but at $p=0.10$ dropout, coverage drops below the 85% lower acceptance boundary due to delayed detection of sharp degradation gradients.
- **Operating Setting Bias**: Shift of $\pm 0.20$ in normalized `setting1` alters feature scale without affecting clean regime routing, resulting in asymmetric cost increases.

---

## 4. Methodological Compliance & Evidence Integrity

1. All calibrations were fitted strictly on calibration partition caches; test engines were never used for tuning.
2. All clean predictions match confirmatory cache at `atol=1e-10`.
3. All baseline equivalence checks (`global_hcp`, `regime_hcp`, `decision_aware_hcp`) passed at `atol=1e-10`.
4. Independent reference audit passed with zero failing reasons.
