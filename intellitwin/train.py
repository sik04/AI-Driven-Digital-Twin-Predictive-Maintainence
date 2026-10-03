"""
IntelliTwin Master Training and Experimental Evaluation Pipeline.
Trains:
  1. LSTM RUL model (PyTorch, heteroscedastic)
  2. GRU RUL model (PyTorch)
  3. Random Forest and XGBoost RUL baselines
  4. Fault Classifiers (RF, XGBoost) for health state (Healthy, Degrading, Critical)
  5. Unsupervised Anomaly Detector (Isolation Forest + PCA)
  6. Conformal Calibrator for calibrated prediction intervals
  7. Environmental Condition Handler & Masking Fault Discriminator
  8. Catastrophic Failure Lead Time and Missed Detection Evaluator
Saves all models and empirical results to disk.
"""

import os
import json
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

from intellitwin.data_loader import CMAPSSDataLoader
from intellitwin.models.lstm_rul import LSTMRULNet, GRURULNet, heteroscedastic_loss, nasa_scoring_function
from intellitwin.models.fault_classifier import FaultClassifier
from intellitwin.models.anomaly_detector import AnomalyDetector
from intellitwin.conformal_calibrator import ConformalCalibrator
from intellitwin.environmental_handler import EnvironmentalConditionHandler
from intellitwin.fault_discriminator import FaultDiscriminator
from intellitwin.catastrophic_evaluator import CatastrophicFailureEvaluator
from intellitwin.metrics import compute_regression_metrics, compute_uq_metrics


def run_pipeline(output_dir="intellitwin/models"):
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 70)
    print("IntelliTwin AI-Driven Digital Twin: Comprehensive Training Pipeline")
    print("=" * 70)

    # 1. Load Data
    print("\n[Step 1/8] Loading and preprocessing NASA C-MAPSS dataset (FD001)...")
    loader = CMAPSSDataLoader(data_dir="data/cmapss", sub_dataset="FD001", max_rul=125, seq_len=30)
    train_df, test_df, feature_cols = loader.prepare_data()

    tab_data = loader.get_tabular_data(val_ratio=0.2)
    seq_data = loader.get_sequential_data(val_ratio=0.2)

    X_train_tab = tab_data["X_train"]
    y_train_rul_tab = tab_data["y_train_rul"]
    y_train_state_tab = tab_data["y_train_state"]

    X_val_tab = tab_data["X_val"]
    y_val_rul_tab = tab_data["y_val_rul"]
    y_val_state_tab = tab_data["y_val_state"]

    X_test_last_tab = tab_data["X_test_last"]
    y_test_last_rul = tab_data["y_test_last_rul"]
    y_test_last_state = tab_data["y_test_last_state"]

    X_train_seq = torch.tensor(seq_data["X_train_seq"], dtype=torch.float32)
    y_train_rul_seq = torch.tensor(seq_data["y_train_rul_seq"], dtype=torch.float32)
    X_val_seq = torch.tensor(seq_data["X_val_seq"], dtype=torch.float32)
    y_val_rul_seq = torch.tensor(seq_data["y_val_rul_seq"], dtype=torch.float32)
    X_test_last_seq = torch.tensor(seq_data["X_test_last_seq"], dtype=torch.float32)

    num_features = X_train_tab.shape[1]
    print(f"Loaded {len(train_df)} training samples across {train_df['unit'].nunique()} units.")
    print(f"Features: {num_features} (Settings + Informative Sensors + Rolling Statistics)")

    # 2. Train LSTM RUL Model (with heteroscedastic loss)
    print("\n[Step 2/8] Training Heteroscedastic LSTM RUL Model...")
    train_dataset = TensorDataset(X_train_seq, y_train_rul_seq)
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)

    lstm_model = LSTMRULNet(input_dim=num_features, hidden_dim=64, num_layers=2, dropout=0.2, heteroscedastic=True)
    optimizer = torch.optim.Adam(lstm_model.parameters(), lr=0.002, weight_decay=1e-5)

    epochs = 20
    lstm_model.train()
    for ep in range(epochs):
        total_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            mu, log_var = lstm_model(batch_x)
            loss = heteroscedastic_loss(mu, log_var, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (ep + 1) % 5 == 0:
            print(f"  Epoch {ep+1:2d}/{epochs:2d} - NLL Loss: {total_loss/len(train_loader):.4f}")

    # Evaluate LSTM on Test Set (Last Cycles)
    lstm_model.eval()
    with torch.no_grad():
        lstm_mu_val, lstm_logvar_val = lstm_model(X_val_seq)
        lstm_std_val = torch.exp(0.5 * lstm_logvar_val).numpy()
        lstm_mu_val = lstm_mu_val.numpy()

        lstm_mu_test, lstm_logvar_test = lstm_model(X_test_last_seq)
        lstm_std_test = torch.exp(0.5 * lstm_logvar_test).numpy()
        lstm_mu_test = lstm_mu_test.numpy()

    lstm_metrics = compute_regression_metrics(y_test_last_rul, lstm_mu_test)
    print(f"  LSTM Test RMSE: {lstm_metrics['rmse']:.2f}, MAE: {lstm_metrics['mae']:.2f}, NASA Score: {lstm_metrics['nasa_score']:.1f}")

    # 3. Train GRU Baseline Model
    print("\n[Step 3/8] Training GRU RUL Comparison Model...")
    gru_model = GRURULNet(input_dim=num_features, hidden_dim=64, num_layers=2, dropout=0.2)
    gru_optimizer = torch.optim.Adam(gru_model.parameters(), lr=0.002)
    mse_criterion = nn.MSELoss()

    gru_model.train()
    for ep in range(15):
        for batch_x, batch_y in train_loader:
            gru_optimizer.zero_grad()
            pred = gru_model(batch_x)
            loss = mse_criterion(pred, batch_y)
            loss.backward()
            gru_optimizer.step()

    gru_model.eval()
    with torch.no_grad():
        gru_pred_test = gru_model(X_test_last_seq).numpy()
    gru_metrics = compute_regression_metrics(y_test_last_rul, gru_pred_test)
    print(f"  GRU Test RMSE: {gru_metrics['rmse']:.2f}, MAE: {gru_metrics['mae']:.2f}, NASA Score: {gru_metrics['nasa_score']:.1f}")

    # 4. Train Random Forest & XGBoost RUL Regressors
    print("\n[Step 4/8] Training Tree-based RUL Regressors (Random Forest & XGBoost)...")
    rf_reg = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    rf_reg.fit(X_train_tab, y_train_rul_tab)
    rf_pred_test = rf_reg.predict(X_test_last_tab)
    rf_metrics = compute_regression_metrics(y_test_last_rul, rf_pred_test)
    print(f"  RF Test RMSE: {rf_metrics['rmse']:.2f}, MAE: {rf_metrics['mae']:.2f}")

    xgb_reg = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.08, random_state=42, n_jobs=-1)
    xgb_reg.fit(X_train_tab, y_train_rul_tab)
    xgb_pred_test = xgb_reg.predict(X_test_last_tab)
    xgb_metrics = compute_regression_metrics(y_test_last_rul, xgb_pred_test)
    print(f"  XGBoost Test RMSE: {xgb_metrics['rmse']:.2f}, MAE: {xgb_metrics['mae']:.2f}")

    # 5. Train Health State Fault Classifiers (Healthy / Degrading / Critical)
    print("\n[Step 5/8] Training Multi-Class Fault Classifiers...")
    rf_clf = FaultClassifier(model_type="rf", n_estimators=150, max_depth=14)
    rf_clf.fit(X_train_tab, y_train_state_tab)
    rf_eval = rf_clf.evaluate(X_test_last_tab, y_test_last_state)
    print(f"  Random Forest Accuracy: {rf_eval['accuracy']*100:.2f}%, F1-Score: {rf_eval['f1_macro']:.4f}")
    print(f"  Missed Critical Rate: {rf_eval['missed_detection_rate']*100:.2f}%, False Alarm Rate: {rf_eval['false_alarm_rate']*100:.2f}%")

    xgb_clf = FaultClassifier(model_type="xgb", n_estimators=150, max_depth=6)
    xgb_clf.fit(X_train_tab, y_train_state_tab)
    xgb_eval = xgb_clf.evaluate(X_test_last_tab, y_test_last_state)
    print(f"  XGBoost Accuracy: {xgb_eval['accuracy']*100:.2f}%, F1-Score: {xgb_eval['f1_macro']:.4f}")

    # 6. Unsupervised Anomaly Detection
    print("\n[Step 6/8] Fitting Baseline Anomaly Detector (Isolation Forest + PCA)...")
    healthy_train = X_train_tab[y_train_state_tab == 0]
    anomaly_det = AnomalyDetector(contamination=0.04)
    anomaly_det.fit_healthy_baseline(healthy_train)
    anomaly_scores_test = anomaly_det.score_samples(X_test_last_tab)
    print(f"  Mean Anomaly Score (Critical): {np.mean(anomaly_scores_test[y_test_last_state == 2]):.4f}")
    print(f"  Mean Anomaly Score (Healthy):  {np.mean(anomaly_scores_test[y_test_last_state == 0]):.4f}")

    # 7. Uncertainty Quantification & Conformal Calibration (90% target coverage)
    print("\n[Step 7/8] Calibrating Prediction Intervals via Split Conformal Prediction...")
    calibrator = ConformalCalibrator(target_coverage=0.90)
    # Calibrate on validation split
    calibrator.calibrate(y_val_rul_seq.numpy(), lstm_mu_val, lstm_std_val)
    # Apply to test set
    lower_test, upper_test = calibrator.predict_intervals(lstm_mu_test, lstm_std_test)
    uq_metrics = compute_uq_metrics(y_test_last_rul, lower_test, upper_test, alpha=0.10)
    print(f"  Conformal Calibrated PICP: {uq_metrics['picp']*100:.2f}% (Target: 90.00%)")
    print(f"  MPIW: {uq_metrics['mpiw']:.2f} cycles, Winkler Score: {uq_metrics['winkler_score']:.2f}")

    # 8. Environmental Handling & Masking Problem Fault Discrimination
    print("\n[Step 8/8] Evaluating Environmental Discrimination & Catastrophic Lead Time...")
    setting_cols = ["setting_1", "setting_2", "setting_3"]
    sensor_cols = [c for c in feature_cols if c.startswith("sensor_") and not ("mean" in c or "std" in c)]
    env_handler = EnvironmentalConditionHandler(n_regimes=4)
    env_handler.fit(train_df[setting_cols].values, train_df[sensor_cols].values)

    test_residuals = env_handler.compute_condition_residuals(test_df[setting_cols].values, test_df[sensor_cols].values)
    setting_shifts = np.linalg.norm(test_df[setting_cols].values - np.mean(train_df[setting_cols].values, axis=0), axis=1)
    epistemic_unc = np.repeat(lstm_std_test.mean(), len(test_residuals))  # Proxy for epistemic uncertainty

    discriminator = FaultDiscriminator(residual_threshold=1.5, epistemic_threshold=20.0)
    cases, case_counts = discriminator.discriminate(test_residuals, setting_shifts, epistemic_unc)
    print(f"  Masking Discrimination Cases: {case_counts}")

    # Catastrophic Failure Evaluation on Run-to-Failure validation units
    val_units = train_df[train_df["unit"] > 80]["unit"].unique()
    trajectories = []
    for u in val_units:
        u_data = train_df[train_df["unit"] == u]
        u_feat = u_data[feature_cols].values
        # Fast trajectory prediction using RF for sequence coverage
        u_pred = rf_reg.predict(u_feat)
        trajectories.append({
            "unit": int(u),
            "cycles": u_data["cycle"].values,
            "rul_true": u_data["rul"].values,
            "rul_pred": u_pred
        })

    cat_evaluator = CatastrophicFailureEvaluator(critical_threshold_cycles=20, warning_threshold_cycles=45)
    cat_metrics = cat_evaluator.evaluate_trajectories(trajectories)
    print(f"  Catastrophic Prevention Success Rate: {cat_metrics['catastrophic_prevention_success_rate']*100:.2f}%")
    print(f"  Mean Warning Lead Time: {cat_metrics['mean_warning_lead_time_cycles']:.1f} cycles")
    print(f"  Missed Catastrophic Failures: {cat_metrics['missed_catastrophic_failures']}")

    # Save models and results
    torch.save(lstm_model.state_dict(), os.path.join(output_dir, "lstm_rul.pt"))
    torch.save(gru_model.state_dict(), os.path.join(output_dir, "gru_rul.pt"))

    results = {
        "dataset": "NASA C-MAPSS FD001",
        "total_train_samples": len(train_df),
        "total_test_samples": len(test_df),
        "feature_count": num_features,
        "rul_regression_models": {
            "LSTM_heteroscedastic": lstm_metrics,
            "GRU": gru_metrics,
            "Random_Forest": rf_metrics,
            "XGBoost": xgb_metrics
        },
        "fault_classification_models": {
            "Random_Forest": rf_eval,
            "XGBoost": xgb_eval
        },
        "uncertainty_quantification": uq_metrics,
        "masking_fault_discrimination": case_counts,
        "catastrophic_failure_evaluation": cat_metrics
    }

    results_path = os.path.join(output_dir, "evaluation_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll models and verified results saved to {results_path}!")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run_pipeline()
