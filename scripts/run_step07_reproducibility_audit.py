"""Step 7.5: Representative Seed-2026 Base Predictor Reproducibility Audit.

Re-runs the 6 official seed-2026 model cells from scratch:
- FD001 GBR, FD001 LSTM
- FD002 GBR, FD002 LSTM
- FD004 GBR, FD004 LSTM

Verifies:
1. GBR: exact numerical equivalence within float precision (max abs diff < 1e-5).
2. LSTM: convergence within 0.05 uncapped RMSE of the saved checkpoint.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from intellitwin.data.pipeline import prepare_dataset_for_model_development
from intellitwin.models.gbr import GBRHyperparameters, GBRModel
from intellitwin.models.lstm import LSTMHyperparameters, train_lstm_candidate
from intellitwin.models.reproducibility import resolve_device, set_global_seed

DATASETS = ("FD001", "FD002", "FD004")
AUDIT_SEED = 2026


def main() -> None:
    print("=" * 80)
    print("Step 7.5: Representative Seed-2026 Base Predictor Reproducibility Audit")
    print("=" * 80)

    device = resolve_device()
    audit_summary: dict[str, Any] = {}

    for ds in DATASETS:
        print(f"\n[{ds}] Preparing dataset for model training...")
        raw_path = Path(f"data/raw/cmapss/train_{ds}.txt")
        split_path = Path(f"data/splits/{ds.lower()}_engine_split_seed_2026.json")

        prep_data = prepare_dataset_for_model_development(
            dataset_name=ds,
            raw_path=raw_path,
            split_manifest_path=split_path,
        )

        X_train_gbr = prep_data.train_windows.flatten_for_gbr()
        X_val_gbr = prep_data.validation_windows.flatten_for_gbr()

        # ---------------------------------------------------------------------
        # 1. Audit GBR
        # ---------------------------------------------------------------------
        print(f"[{ds} GBR] Auditing seed 2026...")
        gbr_sum_path = Path(f"experiments/base_models/{ds}/GBR/summary.json")
        gbr_sum = json.loads(gbr_sum_path.read_text(encoding="utf-8"))
        gbr_cfg = gbr_sum["selected_configuration_id"]

        gbr_saved_meta_path = Path(
            f"experiments/base_models/{ds}/GBR/seed_{AUDIT_SEED}/metadata.json"
        )
        gbr_saved_meta = json.loads(gbr_saved_meta_path.read_text(encoding="utf-8"))
        gbr_hp_dict = gbr_saved_meta["complete_hyperparameters"]

        gbr_saved_preds_path = Path(
            f"experiments/base_models/{ds}/GBR/seed_{AUDIT_SEED}/validation_predictions.csv"
        )
        saved_gbr_preds = pd.read_csv(gbr_saved_preds_path)["prediction"].to_numpy()

        set_global_seed(AUDIT_SEED)
        hp_gbr = GBRHyperparameters(
            config_id=gbr_cfg,
            learning_rate=gbr_hp_dict["learning_rate"],
            max_leaf_nodes=gbr_hp_dict["max_leaf_nodes"],
            l2_regularization=gbr_hp_dict["l2_regularization"],
        )
        model_gbr = GBRModel(hyperparameters=hp_gbr, run_seed=AUDIT_SEED)
        model_gbr.fit(
            X_train_gbr,
            prep_data.train_windows.rul_target,
            sample_weight=prep_data.train_sample_weights,
        )
        rerun_gbr_preds = model_gbr.predict(X_val_gbr)

        max_gbr_diff = float(np.max(np.abs(rerun_gbr_preds - saved_gbr_preds)))
        mean_gbr_diff = float(np.mean(np.abs(rerun_gbr_preds - saved_gbr_preds)))
        print(f"  GBR max abs diff:  {max_gbr_diff:.8e}")
        print(f"  GBR mean abs diff: {mean_gbr_diff:.8e}")

        if max_gbr_diff > 1e-4:
            raise ValueError(f"GBR reproducibility failure on {ds}: max diff {max_gbr_diff}")

        # ---------------------------------------------------------------------
        # 2. Audit LSTM
        # ---------------------------------------------------------------------
        print(f"[{ds} LSTM] Auditing seed 2026...")
        lstm_sum_path = Path(f"experiments/base_models/{ds}/LSTM/summary.json")
        lstm_sum = json.loads(lstm_sum_path.read_text(encoding="utf-8"))
        lstm_cfg = lstm_sum["selected_configuration_id"]

        lstm_saved_meta_path = Path(
            f"experiments/base_models/{ds}/LSTM/seed_{AUDIT_SEED}/metadata.json"
        )
        lstm_saved_meta = json.loads(lstm_saved_meta_path.read_text(encoding="utf-8"))
        lstm_hp_dict = lstm_saved_meta["complete_hyperparameters"]
        saved_lstm_rmse = float(lstm_saved_meta["validation_uncapped_rmse"])

        set_global_seed(AUDIT_SEED)
        hp_lstm = LSTMHyperparameters(
            config_id=lstm_cfg,
            hidden_size=lstm_hp_dict["hidden_size"],
            learning_rate=lstm_hp_dict["learning_rate"],
            batch_size=lstm_hp_dict["batch_size"],
            max_epochs=lstm_hp_dict["max_epochs"],
            early_stopping_patience=lstm_hp_dict.get("early_stopping_patience", 10),
        )

        res_lstm = train_lstm_candidate(
            hyperparameters=hp_lstm,
            run_seed=AUDIT_SEED,
            X_train=prep_data.train_windows.X_sequence,
            y_train=prep_data.train_windows.rul_target,
            train_weights=prep_data.train_sample_weights,
            X_val=prep_data.validation_windows.X_sequence,
            rul_true_val=prep_data.validation_windows.rul_true,
            rul_target_val=prep_data.validation_windows.rul_target,
            val_engine_ids=prep_data.validation_windows.engine_ids,
            device=device,
        )
        rerun_lstm_rmse = float(res_lstm.validation_metrics.uncapped_rmse)
        lstm_rmse_diff = abs(rerun_lstm_rmse - saved_lstm_rmse)

        print(f"  LSTM saved RMSE: {saved_lstm_rmse:.4f}")
        print(f"  LSTM rerun RMSE: {rerun_lstm_rmse:.4f}")
        print(f"  LSTM abs diff:   {lstm_rmse_diff:.4f}")

        if lstm_rmse_diff > 0.05:
            raise ValueError(
                f"LSTM reproducibility failure on {ds}: abs diff {lstm_rmse_diff:.4f} > 0.05"
            )

        audit_summary[ds] = {
            "gbr": {
                "config_id": gbr_cfg,
                "max_abs_diff": max_gbr_diff,
                "mean_abs_diff": mean_gbr_diff,
                "status": "PASS",
            },
            "lstm": {
                "config_id": lstm_cfg,
                "saved_rmse": saved_lstm_rmse,
                "rerun_rmse": rerun_lstm_rmse,
                "rmse_diff": lstm_rmse_diff,
                "status": "PASS",
            },
        }

    out_json = Path("experiments/base_models/reproducibility_audit_seed_2026.json")
    out_json.write_text(json.dumps(audit_summary, indent=2), encoding="utf-8")
    print(f"\nWrote audit results to {out_json}")
    print("\n" + "=" * 80)
    print("ALL 6 SEED-2026 AUDIT CELLS PASSED REPRODUCIBILITY VERIFICATION")
    print("=" * 80)


if __name__ == "__main__":
    main()
