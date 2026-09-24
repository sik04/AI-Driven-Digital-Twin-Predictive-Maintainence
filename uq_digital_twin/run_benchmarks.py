"""
Master Benchmark Execution Script for UQ-DT Research Paper.

Runs full comparative evaluations across all models and corpus baselines:
1. Heteroscedastic Deep Ensemble (Proposed)
2. Conformalized Quantile Regression (CQR - Proposed)
3. Conformalized Heteroscedastic Ensemble (Proposed)
4. Paper 14 GA-Ensemble Baseline (Wang et al., 2026)
5. Paper 6 Tree Baseline (Hosseinzadeh et al., 2023)
6. Homoscedastic Gaussian Process

Evaluates on both Nominal and Out-of-Distribution (OOD) test sets,
simulates operational maintenance decisions, and renders all 5 publication figures.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Any

from uq_digital_twin.data_generator import (
    InfrastructureDegradationSimulator,
    extract_feature_matrix,
)
from uq_digital_twin.probabilistic_models import (
    HeteroscedasticEnsemble,
    GradientBoostedQuantileModel,
    MCDropoutNeuralNet,
)
from uq_digital_twin.conformal_calibrator import (
    ConformalizedQuantileCalibrator,
    ConformalNormalizedResidualCalibrator,
)
from uq_digital_twin.baselines import (
    Paper14EnsembleBaseline,
    Paper6TreeBaseline,
    HomoscedasticGPBaseline,
)
from uq_digital_twin.metrics import evaluate_uq_benchmark, compute_picp
from uq_digital_twin.decision_engine import RiskSensitiveMaintenanceScheduler
from uq_digital_twin.visualize import (
    plot_rul_trajectory_with_intervals,
    plot_uncertainty_decomposition,
    plot_reliability_calibration,
    plot_pareto_coverage_width,
    plot_decision_cost_comparison,
)


def run_comprehensive_benchmarks():
    print("=" * 80)
    print("UQ-DT: BENCHMARK SUITE FOR RESEARCH GAP 3 (UNCERTAINTY QUANTIFICATION)")
    print("=" * 80)

    # 1. Generate Fleet Telemetry
    print("\n[Step 1/6] Synthesizing Multi-Asset Fleet Telemetry...")
    sim = InfrastructureDegradationSimulator(random_seed=42)
    fleet = sim.generate_fleet_dataset(
        num_train_assets=28,
        num_calib_assets=10,
        num_test_nominal=12,
        num_test_ood=8,
    )

    X_train, y_train = extract_feature_matrix(fleet["train"])
    X_calib, y_calib = extract_feature_matrix(fleet["calib"])
    X_test_nom, y_test_nom = extract_feature_matrix(fleet["test_nominal"])
    X_test_ood, y_test_ood = extract_feature_matrix(fleet["test_ood"])

    print(f"  Training samples:    {len(X_train)} across 28 assets")
    print(f"  Calibration samples: {len(X_calib)} across 10 assets")
    print(f"  Nominal Test:        {len(X_test_nom)} across 12 assets")
    print(f"  OOD Test (Stress):   {len(X_test_ood)} across 8 assets")

    target_coverage = 0.90  # 90% confidence intervals (alpha = 0.10)
    alpha = 1.0 - target_coverage

    # 2. Train Models
    print("\n[Step 2/6] Training Probabilistic Models and Corpus Baselines...")
    
    # Model A: Heteroscedastic Deep Ensemble
    print("  -> Training Heteroscedastic Deep Ensemble (5 members)...")
    het_ensemble = HeteroscedasticEnsemble(n_estimators=5, random_state=42)
    het_ensemble.fit(X_train, y_train)

    # Model B: Gradient Boosted Quantile Model
    print("  -> Training Gradient Boosted Quantile Model (Pinball Loss)...")
    gb_quant = GradientBoostedQuantileModel(
        lower_quantile=alpha / 2.0,
        median_quantile=0.50,
        upper_quantile=1.0 - (alpha / 2.0),
        n_estimators=100,
        random_state=42,
    )
    gb_quant.fit(X_train, y_train)

    # Baseline 1: Paper 14 GA-Ensemble
    print("  -> Training Paper 14 GA-Ensemble Baseline (Wang et al., 2026)...")
    p14_base = Paper14EnsembleBaseline(random_state=42)
    p14_base.fit(X_train, y_train)
    train_preds_p14 = p14_base.predict(X_train)
    p14_train_res_std = float(np.std(y_train - train_preds_p14))

    # Baseline 2: Paper 6 Tree Baseline
    print("  -> Training Paper 6 Decision Forest Baseline (Hosseinzadeh et al., 2023)...")
    p6_base = Paper6TreeBaseline(random_state=42)
    p6_base.fit(X_train, y_train)

    # Baseline 3: Homoscedastic Gaussian Process
    print("  -> Training Homoscedastic GP Baseline...")
    gp_base = HomoscedasticGPBaseline(random_state=42)
    gp_base.fit(X_train, y_train)

    # 3. Conformal Calibration on Held-out Calibration Fleet
    print("\n[Step 3/6] Executing Conformal Calibration on Held-out Fleet...")
    # CQR calibrator for Quantile model
    cqr_calibrator = ConformalizedQuantileCalibrator(target_coverage=target_coverage)
    q_lo_calib, _, q_hi_calib = gb_quant.predict_quantiles(X_calib)
    q_shift = cqr_calibrator.calibrate(y_calib, q_lo_calib, q_hi_calib)
    print(f"  -> Conformal Quantile Shift Q_hat: {q_shift:.3f} cycles")

    # Conformal normalized residual calibrator for Heteroscedastic Ensemble
    res_calibrator = ConformalNormalizedResidualCalibrator(target_coverage=target_coverage)
    mu_calib, sig_calib, _, _ = het_ensemble.predict_distribution(X_calib)
    c_mult = res_calibrator.calibrate(y_calib, mu_calib, sig_calib)
    print(f"  -> Conformal Residual Multiplier c_hat: {c_mult:.3f}")

    # 4. Evaluation on Nominal and OOD Test Sets
    print("\n[Step 4/6] Evaluating UQ and Prognostic Metrics...")
    
    def evaluate_all_on(X_eval, y_eval, dataset_tag="Nominal"):
        y_range = float(np.max(y_eval) - np.min(y_eval))
        records = {}

        # 1. Proposed UQ-DT (CQR)
        q_lo, q_mid, q_hi = gb_quant.predict_quantiles(X_eval)
        cqr_lo, cqr_hi = cqr_calibrator.predict_intervals(q_lo, q_hi)
        res_cqr = evaluate_uq_benchmark(
            y_eval, q_mid, cqr_lo, cqr_hi, nominal_coverage=target_coverage, y_range=y_range
        )
        records["Proposed UQ-DT (CQR)"] = res_cqr

        # 2. Proposed UQ-DT (Conformal Heteroscedastic)
        mu_ens, sig_tot, sig_a, sig_e = het_ensemble.predict_distribution(X_eval)
        conf_lo, conf_hi = res_calibrator.predict_intervals(mu_ens, sig_tot)
        res_conf_ens = evaluate_uq_benchmark(
            y_eval, mu_ens, conf_lo, conf_hi, sigma=sig_tot, nominal_coverage=target_coverage, y_range=y_range
        )
        records["Proposed UQ-DT (Conf-Ensemble)"] = res_conf_ens

        # 3. Uncalibrated Heteroscedastic Ensemble (Gaussian 90%)
        from scipy.stats import norm
        z = norm.ppf(1.0 - alpha / 2.0)
        uncal_lo = np.maximum(0.0, mu_ens - z * sig_tot)
        uncal_hi = mu_ens + z * sig_tot
        res_uncal = evaluate_uq_benchmark(
            y_eval, mu_ens, uncal_lo, uncal_hi, sigma=sig_tot, nominal_coverage=target_coverage, y_range=y_range
        )
        records["Uncalibrated Heteroscedastic"] = res_uncal

        # 4. Uncalibrated Quantile Model (Raw pinball)
        res_raw_q = evaluate_uq_benchmark(
            y_eval, q_mid, q_lo, q_hi, nominal_coverage=target_coverage, y_range=y_range
        )
        records["Uncalibrated Pinball Quantile"] = res_raw_q

        # 5. Paper 14 GA-Ensemble + Naive Constant Interval
        p14_preds, p14_lo, p14_hi = p14_base.predict_naive_intervals(
            X_eval, p14_train_res_std, confidence=target_coverage
        )
        res_p14 = evaluate_uq_benchmark(
            y_eval, p14_preds, p14_lo, p14_hi, nominal_coverage=target_coverage, y_range=y_range
        )
        records["Paper 14 GA-Ensemble (Naive Interval)"] = res_p14

        # 6. Paper 6 Tree Baseline (Point only, ad-hoc constant interval)
        p6_preds = p6_base.predict(X_eval)
        p6_lo = np.maximum(0.0, p6_preds - z * p14_train_res_std)
        p6_hi = p6_preds + z * p14_train_res_std
        res_p6 = evaluate_uq_benchmark(
            y_eval, p6_preds, p6_lo, p6_hi, nominal_coverage=target_coverage, y_range=y_range
        )
        records["Paper 6 Decision Forest (Ad-hoc)"] = res_p6

        # 7. Homoscedastic Gaussian Process
        gp_mu, gp_sig = gp_base.predict_distribution(X_eval)
        gp_lo = np.maximum(0.0, gp_mu - z * gp_sig)
        gp_hi = gp_mu + z * gp_sig
        res_gp = evaluate_uq_benchmark(
            y_eval, gp_mu, gp_lo, gp_hi, sigma=gp_sig, nominal_coverage=target_coverage, y_range=y_range
        )
        records["Homoscedastic GP"] = res_gp

        return records

    nominal_results = evaluate_all_on(X_test_nom, y_test_nom, "Nominal")
    ood_results = evaluate_all_on(X_test_ood, y_test_ood, "OOD")

    print("\n--- RESULTS SUMMARY: IN-DISTRIBUTION NOMINAL TEST SET (Target PICP >= 90.0%) ---")
    df_nom = pd.DataFrame(nominal_results).T[
        ["rmse", "mae", "picp", "nmpiw", "cwc", "winkler"]
    ]
    df_nom["picp"] = df_nom["picp"] * 100.0
    print(df_nom.to_string())

    print("\n--- RESULTS SUMMARY: OUT-OF-DISTRIBUTION (OOD) THERMAL SHOCK & OVERLOAD ---")
    df_ood = pd.DataFrame(ood_results).T[
        ["rmse", "mae", "picp", "nmpiw", "cwc", "winkler"]
    ]
    df_ood["picp"] = df_ood["picp"] * 100.0
    print(df_ood.to_string())

    # 5. Operational Maintenance Decision Simulation (Gap 3 -> Gap 1)
    print("\n[Step 5/6] Simulating Decision Support System (DSS) Life-Cycle Costs...")
    # Build per-asset trajectory records for DSS simulation
    test_ood_df = fleet["test_ood"]
    asset_ids = test_ood_df["asset_id"].unique()
    asset_trajs = []

    for a_id in asset_ids:
        sub = test_ood_df[test_ood_df["asset_id"] == a_id]
        X_sub, y_sub = extract_feature_matrix(sub)
        q_lo_s, q_mid_s, q_hi_s = gb_quant.predict_quantiles(X_sub)
        cqr_lo_s, cqr_hi_s = cqr_calibrator.predict_intervals(q_lo_s, q_hi_s)
        _, sig_tot_s, _, _ = het_ensemble.predict_distribution(X_sub)

        asset_trajs.append({
            "asset_id": a_id,
            "timesteps": sub["timestep"].values,
            "true_rul": y_sub,
            "mu_pred": q_mid_s,
            "lower_bound": cqr_lo_s,
            "upper_bound": cqr_hi_s,
            "sigma": sig_tot_s,
        })

    scheduler = RiskSensitiveMaintenanceScheduler(
        cost_preventive=1200.0,
        cost_unplanned_failure=12500.0,
        planning_horizon=15,
        risk_tolerance_prob=0.05,
    )

    dss_det = scheduler.evaluate_fleet_policy(asset_trajs, policy_type="deterministic")
    dss_cons = scheduler.evaluate_fleet_policy(asset_trajs, policy_type="conservative")
    dss_uq = scheduler.evaluate_fleet_policy(asset_trajs, policy_type="uq_dt")

    print("\n--- DECISION SUPPORT SYSTEM (DSS) ECONOMIC POLICY COMPARISON ---")
    dss_df = pd.DataFrame([dss_det, dss_cons, dss_uq])
    print(dss_df.to_string())

    # 6. Render All 5 Publication Figures
    print("\n[Step 6/6] Generating High-Resolution 300-DPI Publication Figures...")
    figures_dir = os.path.join(os.path.dirname(__file__), "..", "figures")
    os.makedirs(figures_dir, exist_ok=True)

    # Fig 1: Single Asset RUL trajectory with intervals
    demo_asset_sub = test_ood_df[test_ood_df["asset_id"] == asset_ids[0]]
    X_demo, y_demo = extract_feature_matrix(demo_asset_sub)
    q_lo_d, q_mid_d, q_hi_d = gb_quant.predict_quantiles(X_demo)
    cqr_lo_d, cqr_hi_d = cqr_calibrator.predict_intervals(q_lo_d, q_hi_d)
    p14_demo = p14_base.predict(X_demo)

    fig1_path = os.path.join(figures_dir, "fig1_rul_calibrated_intervals.png")
    plot_rul_trajectory_with_intervals(
        timesteps=demo_asset_sub["timestep"].values,
        true_rul=y_demo,
        mu_pred=q_mid_d,
        lower_cqr=cqr_lo_d,
        upper_cqr=cqr_hi_d,
        mu_point_baseline=p14_demo,
        save_path=fig1_path,
        asset_id=int(asset_ids[0]),
    )
    print(f"  -> Saved Fig 1 to {fig1_path}")

    # Fig 2: Epistemic vs Aleatoric Decomposition
    _, sig_tot_d, sig_a_d, sig_e_d = het_ensemble.predict_distribution(X_demo)
    fig2_path = os.path.join(figures_dir, "fig2_uncertainty_decomposition.png")
    plot_uncertainty_decomposition(
        timesteps=demo_asset_sub["timestep"].values,
        sigma_total=sig_tot_d,
        sigma_aleatoric=sig_a_d,
        sigma_epistemic=sig_e_d,
        shock_start=50,
        save_path=fig2_path,
    )
    print(f"  -> Saved Fig 2 to {fig2_path}")

    # Fig 3: Reliability Calibration Diagram across nominal levels
    nom_levels = np.array([0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95])
    emp_cqr = []
    emp_gauss = []
    emp_base = []

    q_lo_nom, _, q_hi_nom = gb_quant.predict_quantiles(X_test_nom)
    mu_ens_nom, sig_tot_nom, _, _ = het_ensemble.predict_distribution(X_test_nom)
    p14_preds_nom = p14_base.predict(X_test_nom)

    for lvl in nom_levels:
        c_temp = ConformalizedQuantileCalibrator(target_coverage=lvl)
        c_temp.calibrate(y_calib, q_lo_calib, q_hi_calib)
        lo_t, hi_t = c_temp.predict_intervals(q_lo_nom, q_hi_nom)
        emp_cqr.append(compute_picp(y_test_nom, lo_t, hi_t))

        # Gaussian
        z_t = norm.ppf(1.0 - (1.0 - lvl) / 2.0)
        emp_gauss.append(compute_picp(y_test_nom, mu_ens_nom - z_t * sig_tot_nom, mu_ens_nom + z_t * sig_tot_nom))

        # Baseline
        emp_base.append(compute_picp(y_test_nom, p14_preds_nom - z_t * p14_train_res_std, p14_preds_nom + z_t * p14_train_res_std))

    fig3_path = os.path.join(figures_dir, "fig3_reliability_calibration.png")
    plot_reliability_calibration(
        nominal_levels=nom_levels,
        empirical_cqr=np.array(emp_cqr),
        empirical_gaussian=np.array(emp_gauss),
        empirical_baseline=np.array(emp_base),
        save_path=fig3_path,
    )
    print(f"  -> Saved Fig 3 to {fig3_path}")

    # Fig 4: Pareto Sharpness vs Coverage
    fig4_path = os.path.join(figures_dir, "fig4_pareto_coverage_width.png")
    plot_pareto_coverage_width(
        methods=["UQ-DT (CQR)", "UQ-DT (Conf-Ens)", "Uncalibrated Pinball", "Paper 14 Baseline", "Homoscedastic GP"],
        picp_values=[
            nominal_results["Proposed UQ-DT (CQR)"]["picp"],
            nominal_results["Proposed UQ-DT (Conf-Ensemble)"]["picp"],
            nominal_results["Uncalibrated Pinball Quantile"]["picp"],
            nominal_results["Paper 14 GA-Ensemble (Naive Interval)"]["picp"],
            nominal_results["Homoscedastic GP"]["picp"],
        ],
        nmpiw_values=[
            nominal_results["Proposed UQ-DT (CQR)"]["nmpiw"],
            nominal_results["Proposed UQ-DT (Conf-Ensemble)"]["nmpiw"],
            nominal_results["Uncalibrated Pinball Quantile"]["nmpiw"],
            nominal_results["Paper 14 GA-Ensemble (Naive Interval)"]["nmpiw"],
            nominal_results["Homoscedastic GP"]["nmpiw"],
        ],
        target_coverage=target_coverage,
        save_path=fig4_path,
    )
    print(f"  -> Saved Fig 4 to {fig4_path}")

    # Fig 5: Decision Support Cost Comparison
    fig5_path = os.path.join(figures_dir, "fig5_dss_cost_comparison.png")
    plot_decision_cost_comparison(
        policy_names=["Deterministic\n(Paper 14 / Paper 6)", "Conservative\nHeuristic", "UQ-DT Risk-Sensitive\n(Proposed)"],
        total_costs=[dss_det["total_cost"], dss_cons["total_cost"], dss_uq["total_cost"]],
        catastrophic_counts=[dss_det["catastrophic_failures"], dss_cons["catastrophic_failures"], dss_uq["catastrophic_failures"]],
        save_path=fig5_path,
    )
    print(f"  -> Saved Fig 5 to {fig5_path}")

    # Save all numerical results to JSON artifact for exact embedding into research paper
    out_results_json = os.path.join(figures_dir, "benchmark_metrics_summary.json")
    with open(out_results_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "nominal_results": nominal_results,
                "ood_results": ood_results,
                "dss_results": {"deterministic": dss_det, "conservative": dss_cons, "uq_dt": dss_uq},
            },
            f,
            indent=2,
        )
    print(f"\nAll benchmark metrics saved to {out_results_json}")
    print("\nBENCHMARK SUITE COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    run_comprehensive_benchmarks()
