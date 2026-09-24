"""
Publication-Quality Visualization Suite for UQ-DT Research Paper.

Generates 300-DPI publication figures:
- Fig 1: RUL Degradation Trajectory with Calibrated Prediction Intervals
- Fig 2: Epistemic vs. Aleatoric Uncertainty Decomposition under Thermal Shock
- Fig 3: Reliability Calibration Curve (Nominal vs. Empirical Coverage)
- Fig 4: Pareto Trade-off Curve (Interval Width vs. Coverage)
- Fig 5: Decision Cost Comparison (Deterministic vs. Conservative vs. UQ-DT)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional


def set_academic_style():
    """Configures clean, publication-ready matplotlib styling."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "figure.dpi": 300,
        "lines.linewidth": 1.8,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "grid.linestyle": "--",
    })


def plot_rul_trajectory_with_intervals(
    timesteps: np.ndarray,
    true_rul: np.ndarray,
    mu_pred: np.ndarray,
    lower_cqr: np.ndarray,
    upper_cqr: np.ndarray,
    mu_point_baseline: np.ndarray,
    save_path: str,
    asset_id: int = 1,
):
    """
    Fig 1: Compares UQ-DT calibrated confidence bands with deterministic point baseline.
    """
    set_academic_style()
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)

    ax.plot(timesteps, true_rul, "k-", label="Ground Truth RUL", linewidth=2.2)
    ax.plot(timesteps, mu_pred, color="#1f77b4", linestyle="--", label=r"UQ-DT Mean Prediction $\hat{\mu}(t)$")
    ax.plot(timesteps, mu_point_baseline, color="#d62728", linestyle=":", label="Paper 14 GA-Ensemble (Point)")

    # Calibrated prediction interval ribbon
    ax.fill_between(
        timesteps,
        lower_cqr,
        upper_cqr,
        color="#1f77b4",
        alpha=0.25,
        label=r"Calibrated 90% CQR Interval $[\hat{q}_{lo}, \hat{q}_{hi}]$",
    )

    ax.axhline(0, color="gray", linestyle="-", linewidth=0.8)
    ax.set_xlabel("Operating Time (Cycles / Hours)")
    ax.set_ylabel("Remaining Useful Life (RUL)")
    ax.set_title(f"Figure 1: RUL Prognostics for Asset #{asset_id} with Calibrated UQ-DT Intervals")
    ax.legend(loc="upper right", framealpha=0.92)
    plt.tight_layout()

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()


def plot_uncertainty_decomposition(
    timesteps: np.ndarray,
    sigma_total: np.ndarray,
    sigma_aleatoric: np.ndarray,
    sigma_epistemic: np.ndarray,
    shock_start: Optional[int],
    save_path: str,
):
    """
    Fig 2: Decoupled Epistemic vs. Aleatoric Uncertainty under Thermal Shock and Wear.
    """
    set_academic_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6.2), dpi=300, sharex=True)

    # Upper panel: Uncertainty standard deviations
    ax1.plot(timesteps, sigma_total, color="#2ca02c", label=r"Total Predictive $\sigma_{total}$", linewidth=2.0)
    ax1.plot(timesteps, sigma_aleatoric, color="#ff7f0e", linestyle="--", label=r"Aleatoric Noise $\sigma_{a}(x)$")
    ax1.plot(timesteps, sigma_epistemic, color="#9467bd", linestyle="-.", label=r"Epistemic Model Ignorance $\sigma_{e}(x)$")

    if shock_start:
        ax1.axvspan(shock_start, shock_start + 30, color="red", alpha=0.15, label="OOD Thermal Shock Zone")
        ax2.axvspan(shock_start, shock_start + 30, color="red", alpha=0.15)

    ax1.set_ylabel(r"Uncertainty Standard Dev ($\sigma$)")
    ax1.set_title("Figure 2: Epistemic vs. Aleatoric Uncertainty Decoupling Under Operational Drift")
    ax1.legend(loc="upper left", framealpha=0.92)

    # Lower panel: Stacked variance contribution percentage
    var_a = sigma_aleatoric ** 2
    var_e = sigma_epistemic ** 2
    var_tot = np.maximum(var_a + var_e, 1e-6)

    pct_aleatoric = (var_a / var_tot) * 100.0
    pct_epistemic = (var_e / var_tot) * 100.0

    ax2.fill_between(timesteps, 0, pct_aleatoric, color="#ff7f0e", alpha=0.55, label="Aleatoric Variance Share (%)")
    ax2.fill_between(timesteps, pct_aleatoric, 100, color="#9467bd", alpha=0.55, label="Epistemic Variance Share (%)")

    ax2.set_xlabel("Operating Time (Cycles)")
    ax2.set_ylabel("Variance Share (%)")
    ax2.set_ylim(0, 100)
    ax2.legend(loc="lower left", framealpha=0.92)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()


def plot_reliability_calibration(
    nominal_levels: np.ndarray,
    empirical_cqr: np.ndarray,
    empirical_gaussian: np.ndarray,
    empirical_baseline: np.ndarray,
    save_path: str,
):
    """
    Fig 3: Reliability Calibration Diagram (Nominal vs. Empirical Coverage).
    """
    set_academic_style()
    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=300)

    # Ideal calibration line
    ax.plot([0, 1], [0, 1], "k--", label="Ideal Calibration ($y = x$)", linewidth=1.5)

    ax.plot(nominal_levels, empirical_cqr, "o-", color="#1f77b4", label="Proposed UQ-DT (CQR)", linewidth=2.0)
    ax.plot(nominal_levels, empirical_gaussian, "s--", color="#ff7f0e", label="Uncalibrated Gaussian Likelihood")
    ax.plot(nominal_levels, empirical_baseline, "^:", color="#d62728", label="Paper 14 Ad-hoc Interval")

    ax.set_xlim(0.45, 1.0)
    ax.set_ylim(0.45, 1.02)
    ax.set_xlabel("Target Nominal Coverage $(1 - \\alpha)$")
    ax.set_ylabel("Empirical Coverage Probability (PICP)")
    ax.set_title("Figure 3: Reliability Calibration Diagram across Methods")
    ax.legend(loc="lower right", framealpha=0.92)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()


def plot_pareto_coverage_width(
    methods: List[str],
    picp_values: List[float],
    nmpiw_values: List[float],
    target_coverage: float,
    save_path: str,
):
    """
    Fig 4: Pareto Trade-off Between Interval Sharpness (NMPIW) and Coverage (PICP).
    """
    set_academic_style()
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)

    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd"]

    for i, name in enumerate(methods):
        ax.scatter(
            nmpiw_values[i],
            picp_values[i],
            color=colors[i % len(colors)],
            s=120,
            label=name,
            edgecolor="black",
            zorder=4,
        )
        ax.annotate(
            name,
            (nmpiw_values[i], picp_values[i]),
            textcoords="offset points",
            xytext=(8, -4),
            fontsize=9.5,
        )

    ax.axhline(target_coverage, color="red", linestyle="--", linewidth=1.4, label=f"Target Coverage ({int(target_coverage*100)}%)")

    ax.set_xlabel("Normalized Mean Prediction Interval Width (NMPIW) $\\rightarrow$ Lower is Better")
    ax.set_ylabel("Prediction Interval Coverage (PICP) $\\rightarrow$ Higher is Better")
    ax.set_title("Figure 4: Sharpness vs. Calibration Coverage Trade-off")
    ax.legend(loc="lower right", framealpha=0.92)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()


def plot_decision_cost_comparison(
    policy_names: List[str],
    total_costs: List[float],
    catastrophic_counts: List[int],
    save_path: str,
):
    """
    Fig 5: Life-Cycle Maintenance Cost & Catastrophic Failure Reductions.
    """
    set_academic_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.2), dpi=300)

    bar_colors = ["#d62728", "#ff7f0e", "#1f77b4"]

    # Panel 1: Total Cost
    bars1 = ax1.bar(policy_names, [c / 1000.0 for c in total_costs], color=bar_colors, width=0.55, edgecolor="black")
    ax1.set_ylabel("Total Fleet Expenditure ($k USD)")
    ax1.set_title("Total Maintenance Cost")
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2.0, yval + 1.2, f"${yval:.1f}k", ha="center", va="bottom", fontsize=9.5)

    # Panel 2: Catastrophic Failures
    bars2 = ax2.bar(policy_names, catastrophic_counts, color=bar_colors, width=0.55, edgecolor="black")
    ax2.set_ylabel("Number of Catastrophic Failures")
    ax2.set_title("Catastrophic Risk Occurrences")
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.1, f"{int(yval)}", ha="center", va="bottom", fontsize=9.5)

    plt.suptitle("Figure 5: Operational Decision Cost & Safety Comparison", y=1.02)
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()
