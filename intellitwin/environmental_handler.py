"""
Environmental and Operating Condition Handler for IntelliTwin.
Quantifies operating regimes and computes condition-normalized residuals
to decouple operational shifts from genuine physical degradation.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge


class EnvironmentalConditionHandler:
    """Decouples operating conditions (speed, load, throttle, altitude) from sensor trends."""

    def __init__(self, n_regimes=6, random_state=42):
        self.n_regimes = n_regimes
        self.random_state = random_state
        self.regime_clusterer = KMeans(n_clusters=n_regimes, random_state=random_state, n_init=10)
        self.regime_models = {}  # Per-sensor baseline regression models given operating settings
        self.fitted = False

    def fit(self, settings_train, sensors_train):
        """Fit condition-to-sensor mapping using healthy baseline training cycles."""
        settings_train = np.asarray(settings_train)
        sensors_train = np.asarray(sensors_train)

        # 1. Cluster operating conditions into regimes
        self.regime_clusterer.fit(settings_train)

        # 2. Fit Ridge regression per sensor: sensor_baseline = f(operating_settings)
        n_sensors = sensors_train.shape[1]
        for s_idx in range(n_sensors):
            model = Ridge(alpha=1.0)
            model.fit(settings_train, sensors_train[:, s_idx])
            self.regime_models[s_idx] = model

        self.fitted = True
        return self

    def identify_regime(self, settings):
        """Return discrete operating regime cluster for given settings."""
        return self.regime_clusterer.predict(np.asarray(settings))

    def predict_expected_sensors(self, settings):
        """Predict expected nominal sensor readings for given operating settings."""
        settings = np.asarray(settings)
        n_samples = len(settings)
        n_sensors = len(self.regime_models)
        expected = np.zeros((n_samples, n_sensors))
        for s_idx, model in self.regime_models.items():
            expected[:, s_idx] = model.predict(settings)
        return expected

    def compute_condition_residuals(self, settings, sensors):
        """Compute condition-normalized residuals: r = actual_sensor - expected_nominal(settings).
        Removes operating point artifacts so residuals isolate mechanical degradation.
        """
        sensors = np.asarray(sensors)
        expected = self.predict_expected_sensors(settings)
        residuals = sensors - expected
        return residuals
