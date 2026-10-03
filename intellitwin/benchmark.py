"""
IntelliTwin Step 5: Leakage-Free Baseline Benchmark Module.
Evaluates the 7-level RUL prognostic hierarchy under the authoritative Step-4 protocol:
  Level 0: Naive Mean Baseline
  Level 1: Classical Linear Regression
  Level 2: Random Forest Regressor
  Level 3: XGBoost Regressor
  Level 4: Gated Recurrent Unit (GRU)
  Level 5: Standard LSTM (Homoscedastic / MSE)
  Level 6: Heteroscedastic LSTM (Gaussian NLL)

Outputs generated:
  - artifacts/results/step05_baseline_results.csv
  - artifacts/results/step05_baseline_results.json
  - artifacts/results/step05_per_engine_results.csv
  - artifacts/results/step05_error_stratification.csv
  - artifacts/results/step05_prediction_bias.csv
  - artifacts/predictions/step05_<model>_test_predictions.csv
  - artifacts/figures/fig1_actual_vs_predicted_representative.png
  - artifacts/figures/fig2_model_comparison_rmse.png
  - artifacts/figures/fig3_model_comparison_mae.png
  - artifacts/figures/fig4_model_comparison_nasa_score.png
  - artifacts/figures/fig5_prediction_error_distribution.png
  - artifacts/figures/fig6_error_vs_actual_rul.png
"""

import os
import sys
import copy
import json
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

# Ensure repository root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
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
from intellitwin.config import get_default_data_config
from intellitwin.models.lstm_rul import LSTMRULNet, GRURULNet, heteroscedastic_loss
from intellitwin.metrics import compute_regression_metrics

# Output directories
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "artifacts", "results")
PREDS_DIR = os.path.join(REPO_ROOT, "artifacts", "predictions")
FIGS_DIR = os.path.join(REPO_ROOT, "artifacts", "figures")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(PREDS_DIR, exist_ok=True)
os.makedirs(FIGS_DIR, exist_ok=True)


def get_git_commit_hash() -> str:
    """Retrieve current Git commit SHA for provenance tracking."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT
        ).decode("utf-8").strip()
        return commit
    except Exception:
        return "unknown_commit"


# ----------------------------------------------------------------------
# Model Training & Inference Routines
# ----------------------------------------------------------------------

def run_naive_baseline(y_train: np.ndarray, n_test: int) -> np.ndarray:
    """Level 0: Constant mean prediction of training RUL."""
    mean_rul = float(np.mean(y_train))
    return np.full(n_test, mean_rul, dtype=np.float32)


def run_linear_regression(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray) -> np.ndarray:
    """Level 1: Ordinary Least Squares Linear Regression on tabular features."""
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    preds = lr.predict(X_test)
    return np.clip(preds, 0.0, None)


def run_random_forest(
    X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, seed: int = 42
) -> np.ndarray:
    """Level 2: Random Forest Regressor on tabular features."""
    rf = RandomForestRegressor(
        n_estimators=100, max_depth=15, random_state=seed, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    preds = rf.predict(X_test)
    return np.clip(preds, 0.0, None)


def run_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    seed: int = 42
) -> np.ndarray:
    """Level 3: XGBoost Regressor on tabular features with validation early stopping."""
    model = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=6,
        learning_rate=0.08,
        random_state=seed,
        n_jobs=-1,
        eval_metric="rmse"
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    preds = model.predict(X_test)
    return np.clip(preds, 0.0, None)


def train_gru(
    X_train_seq: np.ndarray,
    y_train_seq: np.ndarray,
    X_val_seq: np.ndarray,
    y_val_seq: np.ndarray,
    X_test_seq: np.ndarray,
    seed: int = 42,
    max_epochs: int = 20,
    batch_size: int = 128,
    patience: int = 8
) -> np.ndarray:
    """Level 4: GRU recurrent neural network with validation checkpoint selection."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train_seq.shape[2]
    model = GRURULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-3, weight_decay=1e-5)

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

        # Validation evaluation
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

    # Final inference on test set with best checkpoint
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
    patience: int = 8
) -> np.ndarray:
    """Level 5: Standard LSTM with scalar MSE loss and validation checkpoint selection."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train_seq.shape[2]
    model = LSTMRULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2, heteroscedastic=False)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-3, weight_decay=1e-5)

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
    patience: int = 8
) -> np.ndarray:
    """Level 6: Heteroscedastic LSTM optimizing Gaussian negative log likelihood."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    input_dim = X_train_seq.shape[2]
    model = LSTMRULNet(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2, heteroscedastic=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-3, weight_decay=1e-5)

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
        mu_test, _ = model(X_test_t)
        test_preds = mu_test.cpu().numpy()
    return np.clip(test_preds, 0.0, None)


# ----------------------------------------------------------------------
# Master Benchmark Execution Function
# ----------------------------------------------------------------------

def run_benchmark(
    seeds: Optional[List[int]] = None,
    mode: str = "full"
) -> Dict[str, Any]:
    """Execute complete Step 5 benchmark across all 7 model levels."""
    print("=" * 80)
    print(f"INTELLITWIN STEP 5: LEAKAGE-FREE BASELINE BENCHMARK ({mode.upper()} MODE)")
    print("=" * 80)

    if seeds is None:
        seeds = [42] if mode == "smoke" else [42, 43, 44]

    primary_seed = seeds[0]
    git_commit = get_git_commit_hash()
    timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Load Data using Authoritative Step-4 Protocol
    print("\n[1/5] Loading C-MAPSS FD001 via Step-4 isolated data protocol...")
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

    X_train_seq = seq["X_train_seq"]
    y_train_seq = seq["y_train_rul_seq"]
    X_val_seq = seq["X_val_seq"]
    y_val_seq = seq["y_val_rul_seq"]
    X_test_last_seq = seq["X_test_last_seq"]

    n_test = len(y_test_last)
    engine_ids = tab["test_last_unit_ids"]
    print(f"Data ready: {len(X_train_tab)} train tabular, {len(X_val_tab)} val tabular, {n_test} test engines.")

    max_epochs = 2 if mode == "smoke" else 20

    # Model Hierarchy Definition
    models_to_evaluate = [
        ("Level 0: Naive Mean", "naive", "None (Constant)"),
        ("Level 1: Linear Regression", "linear_regression", "Tabular"),
        ("Level 2: Random Forest", "random_forest", "Tabular"),
        ("Level 3: XGBoost", "xgboost", "Tabular"),
        ("Level 4: GRU", "gru", "Sequential"),
        ("Level 5: Standard LSTM", "standard_lstm", "Sequential"),
        ("Level 6: Heteroscedastic LSTM", "heteroscedastic_lstm", "Sequential"),
    ]

    benchmark_records = []
    primary_predictions: Dict[str, np.ndarray] = {}

    print("\n[2/5] Training and evaluating benchmark models...")
    for model_label, model_key, rep in models_to_evaluate:
        print(f"\n--- {model_label} ({rep}) ---")
        
        # Determine applicable seeds: Naive and Linear Regression are deterministic (1 run).
        # Random Forest, XGBoost, and neural networks can run multi-seed if provided.
        model_seeds = [primary_seed] if model_key in ["naive", "linear_regression"] else seeds

        seed_results = []
        for s in model_seeds:
            if model_key == "naive":
                preds = run_naive_baseline(y_train_rul, n_test)
            elif model_key == "linear_regression":
                preds = run_linear_regression(X_train_tab, y_train_rul, X_test_last_tab)
            elif model_key == "random_forest":
                preds = run_random_forest(X_train_tab, y_train_rul, X_test_last_tab, seed=s)
            elif model_key == "xgboost":
                preds = run_xgboost(X_train_tab, y_train_rul, X_val_tab, y_val_rul, X_test_last_tab, seed=s)
            elif model_key == "gru":
                preds = train_gru(X_train_seq, y_train_seq, X_val_seq, y_val_seq, X_test_last_seq, seed=s, max_epochs=max_epochs)
            elif model_key == "standard_lstm":
                preds = train_standard_lstm(X_train_seq, y_train_seq, X_val_seq, y_val_seq, X_test_last_seq, seed=s, max_epochs=max_epochs)
            elif model_key == "heteroscedastic_lstm":
                preds = train_heteroscedastic_lstm(X_train_seq, y_train_seq, X_val_seq, y_val_seq, X_test_last_seq, seed=s, max_epochs=max_epochs)
            else:
                raise ValueError(f"Unknown model key {model_key}")

            # Calculate primary metrics
            metrics = compute_regression_metrics(y_test_last, preds)
            err = preds - y_test_last

            rec = {
                "model_label": model_label,
                "model_key": model_key,
                "representation": rep,
                "seed": s,
                "rmse": metrics["rmse"],
                "mae": metrics["mae"],
                "nasa_score": metrics["nasa_score"],
                "mean_error": float(np.mean(err)),
                "median_error": float(np.median(err)),
                "std_error": float(np.std(err)),
                "underpredict_rate": float(np.mean(err < 0)),
                "overpredict_rate": float(np.mean(err > 0)),
                "n_test_samples": n_test,
                "git_commit": git_commit,
                "timestamp": timestamp,
            }
            seed_results.append(rec)
            benchmark_records.append(rec)

            if s == primary_seed:
                primary_predictions[model_key] = preds

            print(f"  [Seed {s}] RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}, NASA Score: {metrics['nasa_score']:.1f}, Bias: {np.mean(err):+.2f}")

    # 3. Create Primary Result DataFrames
    print("\n[3/5] Persisting machine-readable result artifacts...")
    results_df = pd.DataFrame(benchmark_records)
    results_csv_path = os.path.join(RESULTS_DIR, "step05_baseline_results.csv")
    results_df.to_csv(results_csv_path, index=False)
    print(f"  Saved benchmark runs: {results_csv_path}")

    # Compute summary across seeds
    summary_list = []
    for model_key in [m[1] for m in models_to_evaluate]:
        sub = results_df[results_df["model_key"] == model_key]
        rep = sub["representation"].iloc[0]
        label = sub["model_label"].iloc[0]
        summary_list.append({
            "model_label": label,
            "model_key": model_key,
            "representation": rep,
            "n_seeds": len(sub),
            "rmse_mean": float(sub["rmse"].mean()),
            "rmse_std": float(sub["rmse"].std()) if len(sub) > 1 else 0.0,
            "mae_mean": float(sub["mae"].mean()),
            "mae_std": float(sub["mae"].std()) if len(sub) > 1 else 0.0,
            "nasa_score_mean": float(sub["nasa_score"].mean()),
            "nasa_score_std": float(sub["nasa_score"].std()) if len(sub) > 1 else 0.0,
            "mean_error_mean": float(sub["mean_error"].mean()),
            "primary_rmse": float(sub[sub["seed"] == primary_seed]["rmse"].values[0]),
            "primary_mae": float(sub[sub["seed"] == primary_seed]["mae"].values[0]),
            "primary_nasa_score": float(sub[sub["seed"] == primary_seed]["nasa_score"].values[0]),
        })

    results_json_path = os.path.join(RESULTS_DIR, "step05_baseline_results.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "experiment_id": "step05_leakage_free_baseline_benchmark",
            "protocol": "Step 4 Authoritative Engine-Level Isolation",
            "dataset": "NASA C-MAPSS FD001",
            "split_artifact": "artifacts/splits/fd001_split.json",
            "git_commit": git_commit,
            "timestamp": timestamp,
            "seeds_evaluated": seeds,
            "primary_seed": primary_seed,
            "models_summary": summary_list,
            "all_runs": benchmark_records
        }, f, indent=2)
    print(f"  Saved JSON benchmark summary: {results_json_path}")

    # 4. Per-Engine and Prediction Artifacts
    per_engine_records = []
    for model_key, preds in primary_predictions.items():
        # Save individual prediction file
        pred_file = os.path.join(PREDS_DIR, f"step05_{model_key}_test_predictions.csv")
        pred_df = pd.DataFrame({
            "engine_id": engine_ids,
            "actual_rul": y_test_last,
            "predicted_rul": preds,
            "error": preds - y_test_last,
            "model": model_key,
            "split_id": "fd001_step04_authoritative"
        })
        pred_df.to_csv(pred_file, index=False)

        # Collect per-engine records
        for i in range(n_test):
            act = float(y_test_last[i])
            prd = float(preds[i])
            d = prd - act
            nasa = float(np.exp(-d / 13.0) - 1.0 if d < 0 else np.exp(d / 10.0) - 1.0)
            per_engine_records.append({
                "engine_id": int(engine_ids[i]),
                "actual_rul": act,
                "model_key": model_key,
                "predicted_rul": prd,
                "error": d,
                "abs_error": abs(d),
                "sq_error": d ** 2,
                "nasa_score": nasa
            })

    per_engine_df = pd.DataFrame(per_engine_records)
    per_engine_path = os.path.join(RESULTS_DIR, "step05_per_engine_results.csv")
    per_engine_df.to_csv(per_engine_path, index=False)
    print(f"  Saved per-engine results: {per_engine_path}")

    # 5. Error Stratification across RUL Regimes (Low <= 40, Med 41-80, High > 80)
    strat_records = []
    for model_key in primary_predictions.keys():
        sub = per_engine_df[per_engine_df["model_key"] == model_key]
        for regime_name, condition in [
            ("Low (RUL <= 40)", sub["actual_rul"] <= 40),
            ("Medium (40 < RUL <= 80)", (sub["actual_rul"] > 40) & (sub["actual_rul"] <= 80)),
            ("High (RUL > 80)", sub["actual_rul"] > 80),
        ]:
            reg_sub = sub[condition]
            if len(reg_sub) > 0:
                strat_records.append({
                    "model_key": model_key,
                    "rul_regime": regime_name,
                    "engine_count": len(reg_sub),
                    "rmse": float(np.sqrt(reg_sub["sq_error"].mean())),
                    "mae": float(reg_sub["abs_error"].mean()),
                    "nasa_score": float(reg_sub["nasa_score"].sum()),
                    "mean_error": float(reg_sub["error"].mean()),
                })

    strat_df = pd.DataFrame(strat_records)
    strat_path = os.path.join(RESULTS_DIR, "step05_error_stratification.csv")
    strat_df.to_csv(strat_path, index=False)
    print(f"  Saved error stratification: {strat_path}")

    # 6. Generate Publication Figures 1 to 6
    print("\n[4/5] Generating publication-grade benchmark figures...")
    generate_figures(primary_predictions, y_test_last, engine_ids, summary_list, per_engine_df)

    print("\n[5/5] Step 5 Baseline Benchmark Complete!")
    return {
        "summary": summary_list,
        "results_df": results_df,
        "primary_predictions": primary_predictions
    }


# ----------------------------------------------------------------------
# Publication Figure Generation
# ----------------------------------------------------------------------

def generate_figures(
    predictions: Dict[str, np.ndarray],
    y_true: np.ndarray,
    engine_ids: np.ndarray,
    summary_list: List[Dict[str, Any]],
    per_engine_df: pd.DataFrame
):
    """Generate publication figures 1 to 6 using Seaborn and Matplotlib."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "lines.linewidth": 1.6
    })

    # Figure 1: Actual vs Predicted RUL for 3 Representative Test Engines
    # Deterministic Selection: Unit with low true RUL (Unit 31), medium RUL (Unit 34), high RUL (Unit 69)
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    rep_units = [31, 34, 69]
    rep_indices = [np.where(engine_ids == u)[0][0] for u in rep_units]
    
    models_to_plot = ["naive", "random_forest", "xgboost", "gru", "heteroscedastic_lstm"]
    labels = ["Naive", "Random Forest", "XGBoost", "GRU", "Hetero LSTM"]
    colors = ["#7f7f7f", "#2ca02c", "#ff7f0e", "#9467bd", "#1f77b4"]

    x = np.arange(len(rep_units))
    width = 0.14

    # Ground truth bars
    ax.bar(x - 2.5 * width, [y_true[i] for i in rep_indices], width, label="Actual RUL", color="#d62728", hatch="//")

    for idx, (m_key, m_label, col) in enumerate(zip(models_to_plot, labels, colors)):
        preds_for_units = [predictions[m_key][i] for i in rep_indices]
        ax.bar(x + (idx - 1.5) * width, preds_for_units, width, label=m_label, color=col)

    ax.set_xticks(x)
    ax.set_xticklabels([f"Unit {u}\n(Actual={y_true[i]:.0f}c)" for u, i in zip(rep_units, rep_indices)])
    ax.set_ylabel("Remaining Useful Life (cycles)")
    ax.set_title("Fig. 1. Terminal RUL Predictions for Representative Test Engines")
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), framealpha=0.95)
    plt.tight_layout()
    fig1_path = os.path.join(FIGS_DIR, "fig1_actual_vs_predicted_representative.png")
    fig.savefig(fig1_path, bbox_inches="tight")
    plt.close(fig)

    # Figure 2: Model Comparison by RMSE
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    model_names = [s["model_key"].replace("_", " ").title() for s in summary_list]
    rmse_means = [s["rmse_mean"] for s in summary_list]
    rmse_stds = [s["rmse_std"] for s in summary_list]
    bars = ax.bar(range(len(model_names)), rmse_means, yerr=rmse_stds, capsize=4, color="#3182bd", alpha=0.85)
    ax.set_ylabel("RMSE (cycles) [Lower is Better]")
    ax.set_title("Fig. 2. Leakage-Free Prognostic Benchmark: RMSE on C-MAPSS FD001")
    ax.set_xticks(range(len(model_names)))
    ax.set_xticklabels(model_names, rotation=30, ha="right")
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f"{height:.2f}", ha="center", va="bottom", fontsize=8.5)
    plt.tight_layout()
    fig2_path = os.path.join(FIGS_DIR, "fig2_model_comparison_rmse.png")
    fig.savefig(fig2_path, bbox_inches="tight")
    plt.close(fig)

    # Figure 3: Model Comparison by MAE
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    mae_means = [s["mae_mean"] for s in summary_list]
    mae_stds = [s["mae_std"] for s in summary_list]
    bars = ax.bar(range(len(model_names)), mae_means, yerr=mae_stds, capsize=4, color="#74c476", alpha=0.85)
    ax.set_ylabel("MAE (cycles) [Lower is Better]")
    ax.set_title("Fig. 3. Leakage-Free Prognostic Benchmark: MAE on C-MAPSS FD001")
    ax.set_xticks(range(len(model_names)))
    ax.set_xticklabels(model_names, rotation=30, ha="right")
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.4, f"{height:.2f}", ha="center", va="bottom", fontsize=8.5)
    plt.tight_layout()
    fig3_path = os.path.join(FIGS_DIR, "fig3_model_comparison_mae.png")
    fig.savefig(fig3_path, bbox_inches="tight")
    plt.close(fig)

    # Figure 4: Model Comparison by NASA Asymmetric Score
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    nasa_means = [s["nasa_score_mean"] for s in summary_list]
    nasa_stds = [s["nasa_score_std"] for s in summary_list]
    bars = ax.bar(range(len(model_names)), nasa_means, yerr=nasa_stds, capsize=4, color="#e6550d", alpha=0.85)
    ax.set_ylabel("NASA Asymmetric Score [Lower is Better]")
    ax.set_title("Fig. 4. Leakage-Free Prognostic Benchmark: NASA Asymmetric Score")
    ax.set_xticks(range(len(model_names)))
    ax.set_xticklabels(model_names, rotation=30, ha="right")
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 20, f"{height:.0f}", ha="center", va="bottom", fontsize=8.5)
    plt.tight_layout()
    fig4_path = os.path.join(FIGS_DIR, "fig4_model_comparison_nasa_score.png")
    fig.savefig(fig4_path, bbox_inches="tight")
    plt.close(fig)

    # Figure 5: Prediction Error Distribution across Models
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    unique_models = list(per_engine_df["model_key"].unique())
    sns.boxplot(x="model_key", y="error", hue="model_key", data=per_engine_df, ax=ax, palette="Set2", legend=False)
    ax.axhline(0, color="red", linestyle="--", linewidth=1.2, label="Zero Error Line")
    ax.set_xticks(range(len(unique_models)))
    ax.set_xticklabels([m.replace("_", " ").title() for m in unique_models], rotation=30, ha="right")
    ax.set_ylabel("Error = Predicted RUL - Actual RUL (cycles)")
    ax.set_title("Fig. 5. Test Error Distributions Across All 100 Engine Fleets")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()
    fig5_path = os.path.join(FIGS_DIR, "fig5_prediction_error_distribution.png")
    fig.savefig(fig5_path, bbox_inches="tight")
    plt.close(fig)

    # Figure 6: Prediction Error vs Actual RUL (Overestimation in near-failure zone)
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    for m_key, color, mark in [
        ("random_forest", "#2ca02c", "o"),
        ("xgboost", "#ff7f0e", "^"),
        ("heteroscedastic_lstm", "#1f77b4", "s"),
    ]:
        sub = per_engine_df[per_engine_df["model_key"] == m_key]
        ax.scatter(sub["actual_rul"], sub["error"], label=m_key.replace("_", " ").title(),
                   alpha=0.65, s=28, color=color, marker=mark)

    ax.axhline(0, color="black", linestyle="-", linewidth=1.0)
    ax.axvspan(0, 40, color="#d62728", alpha=0.10, label="Near-Failure Critical Regime (RUL <= 40)")
    ax.set_xlabel("True Remaining Useful Life (cycles)")
    ax.set_ylabel("Prediction Error (cycles)")
    ax.set_title("Fig. 6. Prediction Error vs. Ground-Truth RUL on Test Engines")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.95, fontsize=8.5)
    plt.tight_layout()
    fig6_path = os.path.join(FIGS_DIR, "fig6_error_vs_actual_rul.png")
    fig.savefig(fig6_path, bbox_inches="tight")
    plt.close(fig)

    print(f"  All 6 benchmark figures generated and saved to {FIGS_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Step 5 Leakage-Free Baseline Benchmark")
    parser.add_argument("--smoke", action="store_true", help="Run quick 2-epoch smoke test")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44], help="Random seeds to evaluate")
    args = parser.parse_args()

    mode = "smoke" if args.smoke else "full"
    run_benchmark(seeds=args.seeds, mode=mode)
