"""
IntelliTwin Step 6: RUL Sequence Modeling Experiment
================================================================================
Empirical research-grade investigation comparing:
  1. GRU + MSE Loss
  2. Standard LSTM + MSE Loss
  3. Heteroscedastic LSTM + Gaussian Negative Log-Likelihood (NLL) Loss

With contextual comparison against Step 5 tabular baselines (Random Forest, XGBoost).
All models strictly evaluate under the Step-4 leakage-free engine-level isolation
protocol on the terminal cycles of the 100 NASA C-MAPSS FD001 test fleet.

Artifacts saved to:
  artifacts/experiments/step_06_rul/
Figures saved to:
  artifacts/figures/step_06/
"""

import os
import sys
import copy
import json
import subprocess
import platform
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

# Ensure repository root is in sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from intellitwin.data_loader import CMAPSSDataLoader
from intellitwin.models.lstm_rul import LSTMRULNet, GRURULNet, heteroscedastic_loss
from intellitwin.metrics import compute_regression_metrics, nasa_scoring_function

# Paths
EXP_DIR = os.path.join(REPO_ROOT, "artifacts", "experiments", "step_06_rul")
FIGS_DIR = os.path.join(REPO_ROOT, "artifacts", "figures", "step_06")

os.makedirs(EXP_DIR, exist_ok=True)
os.makedirs(FIGS_DIR, exist_ok=True)


def get_git_commit_hash() -> str:
    """Retrieve current Git commit SHA for provenance tracking."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT
        ).decode("ascii").strip()
        return commit
    except Exception:
        return "unknown"


def get_environment_metadata() -> Dict[str, str]:
    """Capture runtime environment metadata for reproducibility."""
    return {
        "python_version": platform.python_version(),
        "os": platform.platform(),
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "xgboost_version": xgb.__version__,
    }


# ----------------------------------------------------------------------
# Model Training Routines
# ----------------------------------------------------------------------

def train_gru(
    X_train_seq: np.ndarray,
    y_train_seq: np.ndarray,
    X_val_seq: np.ndarray,
    y_val_seq: np.ndarray,
    X_test_seq: np.ndarray,
    seed: int = 42,
    max_epochs: int = 20,
    batch_size: int = 128,
    patience: int = 8,
    lr: float = 2e-3
) -> np.ndarray:
    """Train GRU with MSE loss and validation checkpoint selection."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train_seq.shape[2]
    model = GRURULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)

    train_ds = TensorDataset(
        torch.tensor(X_train_seq, dtype=torch.float32),
        torch.tensor(y_train_seq, dtype=torch.float32)
    )
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    X_val_t = torch.tensor(X_val_seq, dtype=torch.float32)
    y_val_np = np.asarray(y_val_seq)

    best_val_rmse = float("inf")
    best_weights = copy.deepcopy(model.state_dict())
    patience_counter = 0

    model.train()
    for epoch in range(1, max_epochs + 1):
        for bx, by in train_loader:
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_preds = model(X_val_t).cpu().numpy()
            val_rmse = np.sqrt(np.mean((val_preds - y_val_np) ** 2))
        model.train()

        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_weights = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    model.load_state_dict(best_weights)
    model.eval()
    with torch.no_grad():
        X_test_t = torch.tensor(X_test_seq, dtype=torch.float32)
        test_preds = model(X_test_t).cpu().numpy()
    return np.clip(test_preds, 0.0, None)


def train_standard_lstm(
    X_train_seq: np.ndarray,
    y_train_seq: np.ndarray,
    X_val_seq: np.ndarray,
    y_val_seq: np.ndarray,
    X_test_seq: np.ndarray,
    seed: int = 42,
    max_epochs: int = 20,
    batch_size: int = 128,
    patience: int = 8,
    lr: float = 2e-3
) -> np.ndarray:
    """Train Standard LSTM with MSE loss and validation checkpoint selection."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train_seq.shape[2]
    model = LSTMRULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2, heteroscedastic=False)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)

    train_ds = TensorDataset(
        torch.tensor(X_train_seq, dtype=torch.float32),
        torch.tensor(y_train_seq, dtype=torch.float32)
    )
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    X_val_t = torch.tensor(X_val_seq, dtype=torch.float32)
    y_val_np = np.asarray(y_val_seq)

    best_val_rmse = float("inf")
    best_weights = copy.deepcopy(model.state_dict())
    patience_counter = 0

    model.train()
    for epoch in range(1, max_epochs + 1):
        for bx, by in train_loader:
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_preds = model(X_val_t).cpu().numpy()
            val_rmse = np.sqrt(np.mean((val_preds - y_val_np) ** 2))
        model.train()

        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_weights = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    model.load_state_dict(best_weights)
    model.eval()
    with torch.no_grad():
        X_test_t = torch.tensor(X_test_seq, dtype=torch.float32)
        test_preds = model(X_test_t).cpu().numpy()
    return np.clip(test_preds, 0.0, None)


def train_heteroscedastic_lstm(
    X_train_seq: np.ndarray,
    y_train_seq: np.ndarray,
    X_val_seq: np.ndarray,
    y_val_seq: np.ndarray,
    X_test_seq: np.ndarray,
    seed: int = 42,
    max_epochs: int = 20,
    batch_size: int = 128,
    patience: int = 8,
    lr: float = 2e-3
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Train Heteroscedastic LSTM optimizing Gaussian negative log-likelihood (NLL).
    
    Returns:
      test_mu: predicted mean RUL
      test_log_var: predicted log-variance
      test_std: predicted standard deviation (sigma = exp(0.5 * log_var))
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train_seq.shape[2]
    model = LSTMRULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2, heteroscedastic=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)

    train_ds = TensorDataset(
        torch.tensor(X_train_seq, dtype=torch.float32),
        torch.tensor(y_train_seq, dtype=torch.float32)
    )
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    X_val_t = torch.tensor(X_val_seq, dtype=torch.float32)
    y_val_np = np.asarray(y_val_seq)

    best_val_rmse = float("inf")
    best_weights = copy.deepcopy(model.state_dict())
    patience_counter = 0

    model.train()
    for epoch in range(1, max_epochs + 1):
        for bx, by in train_loader:
            optimizer.zero_grad()
            mu, log_var = model(bx)
            loss = heteroscedastic_loss(mu, log_var, by)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            mu_val, _ = model(X_val_t)
            val_preds = mu_val.cpu().numpy()
            val_rmse = np.sqrt(np.mean((val_preds - y_val_np) ** 2))
        model.train()

        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_weights = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    model.load_state_dict(best_weights)
    model.eval()
    with torch.no_grad():
        X_test_t = torch.tensor(X_test_seq, dtype=torch.float32)
        mu_test, logvar_test = model(X_test_t)
        test_mu = mu_test.cpu().numpy()
        test_logvar = logvar_test.cpu().numpy()
        test_std = np.exp(0.5 * test_logvar)

    test_mu_clipped = np.clip(test_mu, 0.0, None)
    return test_mu_clipped, test_logvar, test_std


# ----------------------------------------------------------------------
# Tabular Baseline Helper (for Contextual Comparison)
# ----------------------------------------------------------------------

def run_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test_last: np.ndarray,
    seed: int = 42
) -> np.ndarray:
    rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=seed, n_jobs=-1)
    rf.fit(X_train, y_train)
    return rf.predict(X_test_last)


def run_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test_last: np.ndarray,
    seed: int = 42
) -> np.ndarray:
    model = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=6,
        learning_rate=0.08,
        random_state=seed,
        n_jobs=-1
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return model.predict(X_test_last)


# ----------------------------------------------------------------------
# Master Experiment Runner
# ----------------------------------------------------------------------

def run_step06_experiment(
    seeds: Optional[List[int]] = None,
    mode: str = "full"
) -> Dict[str, Any]:
    """Execute complete Step 6 RUL sequence modeling experiment."""
    print("=" * 80)
    print(f"INTELLITWIN STEP 6: RUL SEQUENCE MODELING EXPERIMENT ({mode.upper()} MODE)")
    print("=" * 80)

    if seeds is None:
        seeds = [42] if mode == "smoke" else [42, 43, 44]

    primary_seed = seeds[0]
    git_commit = get_git_commit_hash()
    env_meta = get_environment_metadata()
    timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Load Data via Authoritative Step-4 Protocol
    print("\n[1/6] Loading C-MAPSS FD001 dataset via Step-4 isolated data protocol...")
    loader = CMAPSSDataLoader(random_state=primary_seed, val_ratio=0.20)
    train_df, test_df, feat_cols = loader.prepare_data(save_artifact=True)

    tab = loader.get_tabular_data()
    seq = loader.get_sequential_data()

    X_train_tab = tab["X_train"]
    y_train_rul = tab["y_train_rul"]
    X_val_tab = tab["X_val"]
    y_val_rul = tab["y_val_rul"]
    X_test_last_tab = tab["X_test_last"]
    y_test_last = tab["y_test_last_rul"]
    engine_ids = tab["test_last_unit_ids"]

    X_train_seq = seq["X_train_seq"]
    y_train_seq = seq["y_train_rul_seq"]
    X_val_seq = seq["X_val_seq"]
    y_val_seq = seq["y_val_rul_seq"]
    X_test_last_seq = seq["X_test_last_seq"]

    n_test = len(y_test_last)
    print(f"  Train: {len(X_train_seq)} sequence windows across 80 engines.")
    print(f"  Val:   {len(X_val_seq)} sequence windows across 20 engines.")
    print(f"  Test:  {n_test} terminal cycle engines.")

    max_epochs = 2 if mode == "smoke" else 20

    # 2. Execute Primary Experiments
    print("\n[2/6] Executing sequence models across seeds...")
    
    # Storage
    experiment_runs = []
    primary_predictions: Dict[str, np.ndarray] = {}
    primary_hetero_std: Optional[np.ndarray] = None
    primary_hetero_logvar: Optional[np.ndarray] = None

    # Model specifications
    models = [
        ("GRU + MSE", "gru", "Sequential", "MSELoss"),
        ("LSTM + MSE", "lstm_mse", "Sequential", "MSELoss"),
        ("Heteroscedastic LSTM + NLL", "heteroscedastic_lstm", "Sequential", "Gaussian_NLL"),
        ("Random Forest (Contextual)", "random_forest", "Tabular", "MSE"),
        ("XGBoost (Contextual)", "xgboost", "Tabular", "SquaredError"),
    ]

    for model_label, model_key, rep, loss_type in models:
        print(f"\n--- Model: {model_label} ({rep}, Loss: {loss_type}) ---")
        
        # In smoke mode, run primary seed; in full mode, run specified seeds
        model_seeds = seeds

        for s in model_seeds:
            if model_key == "gru":
                preds = train_gru(X_train_seq, y_train_seq, X_val_seq, y_val_seq, X_test_last_seq,
                                  seed=s, max_epochs=max_epochs)
            elif model_key == "lstm_mse":
                preds = train_standard_lstm(X_train_seq, y_train_seq, X_val_seq, y_val_seq, X_test_last_seq,
                                            seed=s, max_epochs=max_epochs)
            elif model_key == "heteroscedastic_lstm":
                preds, log_var, std = train_heteroscedastic_lstm(X_train_seq, y_train_seq, X_val_seq, y_val_seq, X_test_last_seq,
                                                                 seed=s, max_epochs=max_epochs)
                if s == primary_seed:
                    primary_hetero_std = std
                    primary_hetero_logvar = log_var
            elif model_key == "random_forest":
                preds = run_random_forest(X_train_tab, y_train_rul, X_test_last_tab, seed=s)
            elif model_key == "xgboost":
                preds = run_xgboost(X_train_tab, y_train_rul, X_val_tab, y_val_rul, X_test_last_tab, seed=s)
            else:
                raise ValueError(f"Unknown model_key: {model_key}")

            metrics = compute_regression_metrics(y_test_last, preds)
            err = preds - y_test_last

            rec = {
                "model_label": model_label,
                "model_key": model_key,
                "representation": rep,
                "loss_type": loss_type,
                "seed": s,
                "rmse": float(metrics["rmse"]),
                "mae": float(metrics["mae"]),
                "nasa_score": float(metrics["nasa_score"]),
                "mean_error": float(np.mean(err)),
                "median_error": float(np.median(err)),
                "std_error": float(np.std(err)),
                "underpredict_rate": float(np.mean(err < 0)),
                "overpredict_rate": float(np.mean(err > 0)),
                "n_test_samples": n_test,
                "git_commit": git_commit,
                "timestamp": timestamp,
            }
            experiment_runs.append(rec)

            if s == primary_seed:
                primary_predictions[model_key] = preds

            print(f"  [Seed {s}] RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}, NASA Score: {metrics['nasa_score']:.1f}, Bias: {np.mean(err):+.2f}")

    # 3. Model Comparison Summary Across Seeds
    print("\n[3/6] Computing multi-seed statistical summaries...")
    results_df = pd.DataFrame(experiment_runs)
    
    summary_records = []
    for model_label, model_key, rep, loss_type in models:
        sub = results_df[results_df["model_key"] == model_key]
        summary_records.append({
            "model_label": model_label,
            "model_key": model_key,
            "representation": rep,
            "loss_type": loss_type,
            "n_seeds": len(sub),
            "rmse_mean": float(sub["rmse"].mean()),
            "rmse_std": float(sub["rmse"].std() if len(sub) > 1 else 0.0),
            "mae_mean": float(sub["mae"].mean()),
            "mae_std": float(sub["mae"].std() if len(sub) > 1 else 0.0),
            "nasa_score_mean": float(sub["nasa_score"].mean()),
            "nasa_score_std": float(sub["nasa_score"].std() if len(sub) > 1 else 0.0),
            "mean_error_mean": float(sub["mean_error"].mean()),
            "primary_seed_rmse": float(sub[sub["seed"] == primary_seed]["rmse"].iloc[0]),
            "primary_seed_mae": float(sub[sub["seed"] == primary_seed]["mae"].iloc[0]),
            "primary_seed_nasa": float(sub[sub["seed"] == primary_seed]["nasa_score"].iloc[0]),
        })

    summary_df = pd.DataFrame(summary_records)

    # 4. Error Stratification Across Degradation Regimes
    print("\n[4/6] Conducting error stratification across operational regimes...")
    strat_records = []
    regimes = [
        ("Low (RUL <= 40)", y_test_last <= 40),
        ("Medium (40 < RUL <= 80)", (y_test_last > 40) & (y_test_last <= 80)),
        ("High (RUL > 80)", y_test_last > 80),
    ]

    for model_key in ["gru", "lstm_mse", "heteroscedastic_lstm", "random_forest", "xgboost"]:
        preds = primary_predictions[model_key]
        for reg_label, mask in regimes:
            y_sub = y_test_last[mask]
            p_sub = preds[mask]
            err_sub = p_sub - y_sub
            strat_records.append({
                "model_key": model_key,
                "regime": reg_label,
                "sample_count": int(np.sum(mask)),
                "rmse": float(np.sqrt(np.mean((p_sub - y_sub) ** 2))),
                "mae": float(np.mean(np.abs(p_sub - y_sub))),
                "nasa_score": float(nasa_scoring_function(y_sub, p_sub)),
                "mean_error": float(np.mean(err_sub)),
                "median_error": float(np.median(err_sub)),
            })

    strat_df = pd.DataFrame(strat_records)

    # 5. Heteroscedastic Predictive Uncertainty Analysis
    print("\n[5/6] Analyzing heteroscedastic uncertainty fidelity...")
    hetero_preds = primary_predictions["heteroscedastic_lstm"]
    abs_errors = np.abs(hetero_preds - y_test_last)

    assert primary_hetero_std is not None
    p_std = primary_hetero_std
    p_logvar = primary_hetero_logvar

    if (np.max(p_std) - np.min(p_std)) > 1e-3 and np.std(abs_errors) > 1e-3:
        try:
            pearson_r, pearson_p = stats.pearsonr(p_std, abs_errors)
            spearman_rho, spearman_p = stats.spearmanr(p_std, abs_errors)
        except Exception:
            pearson_r, pearson_p = 0.0, 1.0
            spearman_rho, spearman_p = 0.0, 1.0
    else:
        pearson_r, pearson_p = 0.0, 1.0
        spearman_rho, spearman_p = 0.0, 1.0

    uncertainty_metrics = {
        "mean_predicted_std": float(np.mean(p_std)),
        "median_predicted_std": float(np.median(p_std)),
        "std_of_predicted_std": float(np.std(p_std)),
        "min_predicted_std": float(np.min(p_std)),
        "max_predicted_std": float(np.max(p_std)),
        "pearson_correlation_std_vs_abs_error": float(pearson_r),
        "pearson_p_value": float(pearson_p),
        "spearman_correlation_std_vs_abs_error": float(spearman_rho),
        "spearman_p_value": float(spearman_p),
        "uncertainty_collapse_detected": bool(np.any(p_std < 1e-4)),
        "uncertainty_explosion_detected": bool(np.any(p_std > 1e4)),
        "data_dependent_aleatoric_interpretation": True,
    }

    # Per-engine predictions compilation
    per_engine_records = []
    for i, uid in enumerate(engine_ids):
        row = {
            "engine_id": int(uid),
            "actual_rul": float(y_test_last[i]),
            "gru_pred": float(primary_predictions["gru"][i]),
            "gru_error": float(primary_predictions["gru"][i] - y_test_last[i]),
            "lstm_mse_pred": float(primary_predictions["lstm_mse"][i]),
            "lstm_mse_error": float(primary_predictions["lstm_mse"][i] - y_test_last[i]),
            "heteroscedastic_lstm_pred": float(primary_predictions["heteroscedastic_lstm"][i]),
            "heteroscedastic_lstm_error": float(primary_predictions["heteroscedastic_lstm"][i] - y_test_last[i]),
            "heteroscedastic_lstm_std": float(p_std[i]),
            "random_forest_pred": float(primary_predictions["random_forest"][i]),
            "random_forest_error": float(primary_predictions["random_forest"][i] - y_test_last[i]),
            "xgboost_pred": float(primary_predictions["xgboost"][i]),
            "xgboost_error": float(primary_predictions["xgboost"][i] - y_test_last[i]),
        }
        per_engine_records.append(row)
    per_engine_df = pd.DataFrame(per_engine_records)

    # 6. Save Machine-Readable Artifacts
    print("\n[6/6] Persisting machine-readable experiment artifacts and figures...")

    # A. Result CSVs
    results_csv = os.path.join(EXP_DIR, "step06_rul_experiment_results.csv")
    results_df.to_csv(results_csv, index=False)

    summary_csv = os.path.join(EXP_DIR, "step06_rul_model_summary.csv")
    summary_df.to_csv(summary_csv, index=False)

    per_engine_csv = os.path.join(EXP_DIR, "step06_rul_per_engine_predictions.csv")
    per_engine_df.to_csv(per_engine_csv, index=False)

    strat_csv = os.path.join(EXP_DIR, "step06_rul_error_stratification.csv")
    strat_df.to_csv(strat_csv, index=False)

    # Heteroscedastic uncertainty table
    hetero_df = pd.DataFrame({
        "engine_id": engine_ids,
        "actual_rul": y_test_last,
        "predicted_mu": hetero_preds,
        "error": hetero_preds - y_test_last,
        "abs_error": abs_errors,
        "predicted_log_var": p_logvar,
        "predicted_std": p_std,
    })
    hetero_csv = os.path.join(EXP_DIR, "step06_heteroscedastic_uncertainty_analysis.csv")
    hetero_df.to_csv(hetero_csv, index=False)

    # Individual model prediction CSVs
    for m_key, fname in [
        ("gru", "predictions_gru.csv"),
        ("lstm_mse", "predictions_lstm_mse.csv"),
        ("heteroscedastic_lstm", "predictions_lstm_heteroscedastic.csv"),
    ]:
        sub_df = pd.DataFrame({
            "engine_id": engine_ids,
            "actual_rul": y_test_last,
            "predicted_rul": primary_predictions[m_key],
            "error": primary_predictions[m_key] - y_test_last,
            "absolute_error": np.abs(primary_predictions[m_key] - y_test_last),
        })
        if m_key == "heteroscedastic_lstm":
            sub_df["predicted_std"] = p_std
        sub_df.to_csv(os.path.join(EXP_DIR, fname), index=False)

    # Experiment Configuration & Summary JSON
    config_metadata = {
        "experiment_id": "step06_rul_modeling_experiment",
        "primary_research_question": "Does heteroscedastic sequence modeling improve Remaining Useful Life prediction compared with conventional sequence regression under the corrected, leakage-free experimental protocol?",
        "dataset": "NASA C-MAPSS FD001",
        "split_protocol": "Step 4 Authoritative Engine-Level Partition (80 train / 20 val / 100 test)",
        "split_artifact": "artifacts/splits/fd001_split.json",
        "git_commit": git_commit,
        "timestamp": timestamp,
        "environment": env_meta,
        "seeds": seeds,
        "primary_seed": primary_seed,
        "hyperparameters": {
            "sequence_length": 30,
            "features_count": 54,
            "hidden_dim": 64,
            "num_layers": 2,
            "dropout": 0.2,
            "learning_rate": 2e-3,
            "weight_decay": 1e-5,
            "batch_size": 128,
            "max_epochs": max_epochs,
            "patience": 8,
            "rul_cap": 125,
            "optimizer": "Adam",
        },
        "model_summary": summary_records,
        "uncertainty_analysis": uncertainty_metrics,
    }

    config_json_path = os.path.join(EXP_DIR, "step06_experiment_config.json")
    with open(config_json_path, "w") as f:
        json.dump(config_metadata, f, indent=2)

    summary_json_path = os.path.join(EXP_DIR, "step06_rul_experiment_summary.json")
    with open(summary_json_path, "w") as f:
        json.dump({
            "config": config_metadata,
            "all_runs": experiment_runs,
        }, f, indent=2)

    # 7. Generate Publication-Grade Figures (300 DPI)
    generate_step06_figures(
        summary_records=summary_records,
        per_engine_df=per_engine_df,
        hetero_df=hetero_df,
        uncertainty_metrics=uncertainty_metrics,
        y_test_last=y_test_last,
        engine_ids=engine_ids,
        primary_predictions=primary_predictions
    )

    print("=" * 80)
    print(f"STEP 6 RUL MODELING EXPERIMENT COMPLETE! Artifacts in: {EXP_DIR}")
    print("=" * 80)

    return config_metadata


# ----------------------------------------------------------------------
# Figure Generation
# ----------------------------------------------------------------------

def generate_step06_figures(
    summary_records: List[Dict[str, Any]],
    per_engine_df: pd.DataFrame,
    hetero_df: pd.DataFrame,
    uncertainty_metrics: Dict[str, Any],
    y_test_last: np.ndarray,
    engine_ids: np.ndarray,
    primary_predictions: Dict[str, np.ndarray]
) -> None:
    """Generate 5 focused research figures for Step 6."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams.update({"font.size": 9.5, "figure.dpi": 300})

    # ------------------------------------------------------------------
    # Figure 1: Actual vs Predicted RUL for Representative Test Engines
    # Deterministic sampling: Unit 31 (low), Unit 34 (medium), Unit 69 (high)
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    rep_units = [31, 34, 69]
    rep_indices = [np.where(engine_ids == u)[0][0] for u in rep_units]

    x = np.arange(len(rep_units))
    width = 0.16

    ax.bar(x - 2 * width, [y_test_last[i] for i in rep_indices], width, label="Ground Truth RUL", color="#2b2b2b")
    ax.bar(x - width, [primary_predictions["gru"][i] for i in rep_indices], width, label="GRU + MSE", color="#4daf4a")
    ax.bar(x, [primary_predictions["lstm_mse"][i] for i in rep_indices], width, label="LSTM + MSE", color="#377eb8")
    ax.bar(x + width, [primary_predictions["heteroscedastic_lstm"][i] for i in rep_indices], width, label="Hetero LSTM + NLL", color="#984ea3")
    ax.bar(x + 2 * width, [primary_predictions["xgboost"][i] for i in rep_indices], width, label="XGBoost (Tabular)", color="#ff7f00")

    ax.set_xticks(x)
    ax.set_xticklabels([f"Unit {u}\n(Actual: {y_test_last[i]:.0f}c)" for u, i in zip(rep_units, rep_indices)])
    ax.set_ylabel("Remaining Useful Life (cycles)")
    ax.set_title("Fig. 1. Terminal RUL Predictions on Representative Test Engines")
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), framealpha=0.95)
    plt.tight_layout()
    fig1_path = os.path.join(FIGS_DIR, "fig1_actual_vs_predicted_representative.png")
    fig.savefig(fig1_path, bbox_inches="tight")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Figure 2: Absolute Error Distribution by Model
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    plot_data = []
    model_order = ["gru", "lstm_mse", "heteroscedastic_lstm", "xgboost", "random_forest"]
    labels_order = ["GRU + MSE", "LSTM + MSE", "Hetero LSTM", "XGBoost", "Random Forest"]

    for m_key, m_label in zip(model_order, labels_order):
        col = f"{m_key}_error"
        errors = np.abs(per_engine_df[col])
        for e in errors:
            plot_data.append({"Model": m_label, "Absolute Error": e})

    plot_df = pd.DataFrame(plot_data)
    sns.boxplot(x="Model", y="Absolute Error", hue="Model", data=plot_df, ax=ax, palette="Set2", legend=False)
    ax.set_xticks(range(len(labels_order)))
    ax.set_xticklabels(labels_order, rotation=20, ha="right")
    ax.set_ylabel("Absolute Error |Predicted - Actual| (cycles)")
    ax.set_title("Fig. 2. Absolute Error Distribution Across Test Engines (N=100)")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    fig2_path = os.path.join(FIGS_DIR, "fig2_absolute_error_distribution.png")
    fig.savefig(fig2_path, bbox_inches="tight")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Figure 3: RMSE and MAE Comparison Across Models (Multi-Seed Bars)
    # ------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.8))
    m_labels = [s["model_label"].replace(" (Contextual)", "") for s in summary_records]
    rmse_means = [s["rmse_mean"] for s in summary_records]
    rmse_stds = [s["rmse_std"] for s in summary_records]
    mae_means = [s["mae_mean"] for s in summary_records]
    mae_stds = [s["mae_std"] for s in summary_records]

    bars1 = ax1.bar(range(len(m_labels)), rmse_means, yerr=rmse_stds, capsize=4, color="#3182bd", alpha=0.85)
    ax1.set_xticks(range(len(m_labels)))
    ax1.set_xticklabels(m_labels, rotation=35, ha="right")
    ax1.set_ylabel("RMSE (cycles) [Lower is Better]")
    ax1.set_title("RMSE Comparison (Mean ± Std)")
    ax1.grid(True, linestyle=":", alpha=0.6, axis="y")
    for b in bars1:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width()/2., h + 0.3, f"{h:.2f}", ha="center", va="bottom", fontsize=8.0)

    bars2 = ax2.bar(range(len(m_labels)), mae_means, yerr=mae_stds, capsize=4, color="#74c476", alpha=0.85)
    ax2.set_xticks(range(len(m_labels)))
    ax2.set_xticklabels(m_labels, rotation=35, ha="right")
    ax2.set_ylabel("MAE (cycles) [Lower is Better]")
    ax2.set_title("MAE Comparison (Mean ± Std)")
    ax2.grid(True, linestyle=":", alpha=0.6, axis="y")
    for b in bars2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width()/2., h + 0.3, f"{h:.2f}", ha="center", va="bottom", fontsize=8.0)

    plt.suptitle("Fig. 3. Multi-Seed Prognostic Accuracy Comparison on C-MAPSS FD001", y=1.02)
    plt.tight_layout()
    fig3_path = os.path.join(FIGS_DIR, "fig3_rmse_mae_comparison.png")
    fig.savefig(fig3_path, bbox_inches="tight")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Figure 4: Error vs Actual RUL (Highlighting Near-Failure Critical Regime)
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.scatter(y_test_last, per_engine_df["gru_error"], label="GRU + MSE", color="#4daf4a", alpha=0.7, s=28, marker="o")
    ax.scatter(y_test_last, per_engine_df["lstm_mse_error"], label="LSTM + MSE", color="#377eb8", alpha=0.7, s=28, marker="s")
    ax.scatter(y_test_last, per_engine_df["heteroscedastic_lstm_error"], label="Hetero LSTM + NLL", color="#984ea3", alpha=0.7, s=28, marker="^")

    ax.axhline(0, color="black", linestyle="-", linewidth=1.0)
    ax.axvspan(0, 40, color="#d62728", alpha=0.12, label="Critical Regime (RUL <= 40)")
    ax.set_xlabel("True Remaining Useful Life (cycles)")
    ax.set_ylabel("Prediction Error (Predicted - Actual) [cycles]")
    ax.set_title("Fig. 4. Prediction Error vs. Ground-Truth RUL Across Test Engines")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.95, fontsize=8.5)
    plt.tight_layout()
    fig4_path = os.path.join(FIGS_DIR, "fig4_error_vs_actual_rul.png")
    fig.savefig(fig4_path, bbox_inches="tight")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Figure 5: Heteroscedastic Predicted Std vs Absolute Prediction Error
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    p_std = hetero_df["predicted_std"]
    abs_err = hetero_df["abs_error"]

    ax.scatter(p_std, abs_err, color="#984ea3", alpha=0.75, s=32, edgecolors="none")

    # Fit linear regression trend line if variance exists
    has_valid_regression = False
    if (np.max(p_std) - np.min(p_std)) > 1e-3 and np.std(abs_err) > 1e-3:
        try:
            slope, intercept, r_val, p_val, std_err = stats.linregress(p_std, abs_err)
            x_vals = np.linspace(p_std.min(), p_std.max(), 100)
            ax.plot(x_vals, intercept + slope * x_vals, color="#e41a1c", linestyle="--", linewidth=1.5,
                    label=f"Linear Trend (r = {uncertainty_metrics['pearson_correlation_std_vs_abs_error']:.3f}, p = {uncertainty_metrics['pearson_p_value']:.4f})")
            has_valid_regression = True
        except Exception:
            has_valid_regression = False

    if not has_valid_regression:
        ax.axhline(float(np.mean(abs_err)), color="#e41a1c", linestyle="--", linewidth=1.5, label="Mean Absolute Error Baseline")

    ax.set_xlabel("Predicted Standard Deviation (cycles) [Aleatoric]")
    ax.set_ylabel("Absolute Prediction Error |Predicted - Actual| (cycles)")
    ax.set_title("Fig. 5. Heteroscedastic Uncertainty vs. Residual Magnitude")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", framealpha=0.95)
    plt.tight_layout()
    fig5_path = os.path.join(FIGS_DIR, "fig5_heteroscedastic_uncertainty_fidelity.png")
    fig.savefig(fig5_path, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------
# CLI Entrypoint
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Step 6 RUL Sequence Modeling Experiment")
    parser.add_argument("--smoke", action="store_true", help="Execute rapid smoke test run")
    parser.add_argument("--seeds", nargs="+", type=int, default=None, help="Random seeds to evaluate")
    args = parser.parse_args()

    mode = "smoke" if args.smoke else "full"
    run_step06_experiment(seeds=args.seeds, mode=mode)
