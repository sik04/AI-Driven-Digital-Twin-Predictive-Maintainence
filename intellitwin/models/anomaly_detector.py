"""
Anomaly Detection Module for IntelliTwin.
Detects early deviations from baseline normal operating behavior using
Isolation Forest and Reconstruction Error residuals.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA


class AnomalyDetector:
    """Unsupervised anomaly detector trained on baseline healthy operating cycles."""

    def __init__(self, contamination=0.05, n_estimators=150, random_state=42):
        self.contamination = contamination
        self.random_state = random_state
        self.iso_forest = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        self.pca = PCA(n_components=0.95, random_state=random_state)
        self.reconstruction_threshold = None

    def fit_healthy_baseline(self, X_healthy):
        """Fit detector strictly on normal/healthy operational profiles."""
        self.iso_forest.fit(X_healthy)
        self.pca.fit(X_healthy)

        # Compute reconstruction error on healthy training data
        X_proj = self.pca.inverse_transform(self.pca.transform(X_healthy))
        rec_errors = np.mean((X_healthy - X_proj) ** 2, axis=1)
        # Threshold at (1 - contamination) percentile
        self.reconstruction_threshold = float(np.percentile(rec_errors, 100 * (1 - self.contamination)))
        return self

    def score_samples(self, X):
        """Return combined anomaly score between [0, 1]. Higher score = more anomalous."""
        # Isolation Forest decision function: negative values indicate outliers
        iso_scores = -self.iso_forest.score_samples(X)
        iso_norm = (iso_scores - iso_scores.min()) / (iso_scores.max() - iso_scores.min() + 1e-8)

        # Reconstruction error
        X_proj = self.pca.inverse_transform(self.pca.transform(X))
        rec_errors = np.mean((X - X_proj) ** 2, axis=1)
        rec_norm = np.clip(rec_errors / (self.reconstruction_threshold * 2.0 + 1e-8), 0.0, 1.0)

        # Combined anomaly score
        combined_score = 0.5 * iso_norm + 0.5 * rec_norm
        return combined_score

    def predict_anomalies(self, X, threshold=0.5):
        """Binary anomaly prediction: 1 = Anomaly, 0 = Normal."""
        scores = self.score_samples(X)
        return (scores > threshold).astype(int)
