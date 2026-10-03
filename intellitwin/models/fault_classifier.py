"""
Fault Classification and Health State Identification Module for IntelliTwin.
Classifies asset condition into Healthy (0), Degrading (1), and Critical (2).
Calculates Accuracy, Precision, Recall, F1, Confusion Matrix, False Alarm Rate,
and Missed Critical Detection Rate.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import xgboost as xgb


class FaultClassifier:
    """Multi-class fault classifier for asset health state assessment."""

    def __init__(self, model_type="rf", n_estimators=100, max_depth=12, random_state=42):
        self.model_type = model_type
        self.random_state = random_state
        if model_type == "rf":
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                class_weight="balanced",
                random_state=random_state,
                n_jobs=-1
            )
        elif model_type == "xgb":
            self.model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=0.08,
                random_state=random_state,
                n_jobs=-1,
                eval_metric="mlogloss"
            )
        elif model_type == "gb":
            self.model = GradientBoostingClassifier(
                n_estimators=n_estimators,
                max_depth=6,
                random_state=random_state
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    def fit(self, X_train, y_train):
        self.model.fit(X_train, y_train)
        return self

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def evaluate(self, X_test, y_test):
        """Compute comprehensive evaluation metrics across health state classes."""
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
        f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
        cm = confusion_matrix(y_test, y_pred)

        # Class 2 is Critical state (catastrophic failure risk)
        # False alarm: True is Healthy (0) or Degrading (1), but predicted Critical (2)
        true_non_crit = (y_test != 2)
        pred_crit = (y_pred == 2)
        false_alarms = np.sum(true_non_crit & pred_crit)
        false_alarm_rate = float(false_alarms / max(1, np.sum(true_non_crit)))

        # Missed detection: True is Critical (2), but predicted non-critical (< 2)
        true_crit = (y_test == 2)
        pred_non_crit = (y_pred != 2)
        missed_crit = np.sum(true_crit & pred_non_crit)
        missed_detection_rate = float(missed_crit / max(1, np.sum(true_crit)))

        per_class_rec = recall_score(y_test, y_pred, average=None, zero_division=0)
        per_class_prec = precision_score(y_test, y_pred, average=None, zero_division=0)
        per_class_f1 = f1_score(y_test, y_pred, average=None, zero_division=0)

        return {
            "model_type": self.model_type,
            "accuracy": float(acc),
            "precision_macro": float(prec_macro),
            "recall_macro": float(rec_macro),
            "f1_macro": float(f1_macro),
            "false_alarm_rate": float(false_alarm_rate),
            "missed_detection_rate": float(missed_detection_rate),
            "confusion_matrix": cm.tolist(),
            "per_class": {
                "Healthy": {"precision": float(per_class_prec[0]), "recall": float(per_class_rec[0]), "f1": float(per_class_f1[0])},
                "Degrading": {"precision": float(per_class_prec[1]), "recall": float(per_class_rec[1]), "f1": float(per_class_f1[1])},
                "Critical": {"precision": float(per_class_prec[2]), "recall": float(per_class_rec[2]), "f1": float(per_class_f1[2])},
            }
        }
