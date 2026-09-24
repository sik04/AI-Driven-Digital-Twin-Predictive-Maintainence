"""
Probabilistic Surrogate Models for Digital Twin Uncertainty Quantification.

Implements:
1. HeteroscedasticEnsemble: Decouples epistemic and aleatoric uncertainty via
   negative log-likelihood regression and ensemble diversity.
2. GradientBoostedQuantileModel: Pinball quantile regression estimating conditional quantiles.
3. MCDropoutNeuralNet: Deep neural surrogate using Monte Carlo Dropout to sample weight posteriors.
"""

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from typing import Tuple, List, Dict, Optional


class HeteroscedasticEnsemble:
    """
    Deep Heteroscedastic Ensemble.
    Learns input-dependent aleatoric variance sigma_a^2(x) and captures epistemic
    uncertainty sigma_e^2(x) via ensemble member dispersion.
    """

    def __init__(
        self,
        n_estimators: int = 5,
        hidden_layer_sizes: Tuple[int, ...] = (64, 32),
        max_iter: int = 350,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.hidden_layer_sizes = hidden_layer_sizes
        self.max_iter = max_iter
        self.random_state = random_state

        self.mean_models: List[MLPRegressor] = []
        self.var_models: List[MLPRegressor] = []
        self.scaler_x = StandardScaler()
        self.scaler_y = StandardScaler()
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "HeteroscedasticEnsemble":
        X = np.asarray(X)
        y = np.asarray(y).reshape(-1, 1)

        X_scaled = self.scaler_x.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y).ravel()

        self.mean_models = []
        self.var_models = []
        rng = np.random.RandomState(self.random_state)

        n_samples = len(X)
        for i in range(self.n_estimators):
            # Bootstrap subsample for diverse ensemble members (epistemic coverage)
            boot_idx = rng.choice(n_samples, size=int(0.85 * n_samples), replace=True)
            X_b = X_scaled[boot_idx]
            y_b = y_scaled[boot_idx]

            # 1. Fit mean model mu_m(x)
            mean_net = MLPRegressor(
                hidden_layer_sizes=self.hidden_layer_sizes,
                activation="relu",
                alpha=0.001,
                learning_rate_init=0.01,
                max_iter=self.max_iter,
                random_state=rng.randint(0, 10000),
                early_stopping=True,
                n_iter_no_change=15,
            )
            mean_net.fit(X_b, y_b)
            self.mean_models.append(mean_net)

            # 2. Fit auxiliary log-variance model for heteroscedastic noise: s_m(x) = ln(sigma^2)
            preds_scaled = mean_net.predict(X_b)
            squared_residuals = np.maximum((y_b - preds_scaled) ** 2, 1e-4)
            log_residuals = np.log(squared_residuals)

            var_net = MLPRegressor(
                hidden_layer_sizes=(32, 16),
                activation="relu",
                alpha=0.01,
                learning_rate_init=0.01,
                max_iter=self.max_iter,
                random_state=rng.randint(0, 10000),
                early_stopping=True,
                n_iter_no_change=15,
            )
            var_net.fit(X_b, log_residuals)
            self.var_models.append(var_net)

        self.is_fitted = True
        return self

    def predict_distribution(
        self, X: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns:
            mu_pred: Overall ensemble mean prediction
            sigma_total: Combined total standard deviation
            sigma_aleatoric: Data noise standard deviation
            sigma_epistemic: Model uncertainty standard deviation
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_distribution().")

        X_scaled = self.scaler_x.transform(X)
        M = self.n_estimators

        # Collect predictions from all ensemble members in original scale
        all_mu_scaled = np.zeros((M, len(X)))
        all_var_orig = np.zeros((M, len(X)))
        y_std = self.scaler_y.scale_[0]

        for m in range(M):
            mu_m_scaled = self.mean_models[m].predict(X_scaled)
            all_mu_scaled[m] = mu_m_scaled

            # Predict log-variance, clip to avoid numerical explosions
            log_var_m = np.clip(self.var_models[m].predict(X_scaled), -6.0, 4.0)
            var_m_scaled = np.exp(log_var_m)
            # Rescale variance to original y units: Var(Y) = y_std^2 * Var(Y_scaled)
            all_var_orig[m] = var_m_scaled * (y_std ** 2)

        # Invert scaling on ensemble means
        all_mu_orig = np.zeros_like(all_mu_scaled)
        for m in range(M):
            all_mu_orig[m] = self.scaler_y.inverse_transform(all_mu_scaled[m].reshape(-1, 1)).ravel()

        # Epistemic & Aleatoric decomposition:
        mu_pred = np.mean(all_mu_orig, axis=0)
        # Aleatoric variance = average of member predicted variances
        var_aleatoric = np.mean(all_var_orig, axis=0)
        # Epistemic variance = variance across member mean predictions
        var_epistemic = np.var(all_mu_orig, axis=0)

        sigma_aleatoric = np.sqrt(np.maximum(var_aleatoric, 1e-6))
        sigma_epistemic = np.sqrt(np.maximum(var_epistemic, 1e-6))
        sigma_total = np.sqrt(var_aleatoric + var_epistemic)

        return mu_pred, sigma_total, sigma_aleatoric, sigma_epistemic

    def predict_intervals(
        self, X: np.ndarray, confidence: float = 0.90
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes Gaussian asymptotic confidence intervals: mu +/- z * sigma_total.
        """
        from scipy.stats import norm
        mu, sigma_total, _, _ = self.predict_distribution(X)
        z = norm.ppf(1.0 - (1.0 - confidence) / 2.0)
        lower = np.maximum(0.0, mu - z * sigma_total)
        upper = mu + z * sigma_total
        return mu, lower, upper


class GradientBoostedQuantileModel:
    """
    Gradient Boosted Quantile Regressor estimating conditional quantiles
    q_lo, q_mid, q_hi directly via Pinball loss minimization.
    """

    def __init__(
        self,
        lower_quantile: float = 0.05,
        median_quantile: float = 0.50,
        upper_quantile: float = 0.95,
        n_estimators: int = 120,
        learning_rate: float = 0.08,
        max_depth: int = 4,
        random_state: int = 42,
    ):
        self.q_lo = lower_quantile
        self.q_mid = median_quantile
        self.q_hi = upper_quantile
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state

        self.model_lo = GradientBoostingRegressor(
            loss="quantile",
            alpha=self.q_lo,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            random_state=self.random_state,
        )
        self.model_mid = GradientBoostingRegressor(
            loss="quantile",
            alpha=self.q_mid,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            random_state=self.random_state + 1,
        )
        self.model_hi = GradientBoostingRegressor(
            loss="quantile",
            alpha=self.q_hi,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            random_state=self.random_state + 2,
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GradientBoostedQuantileModel":
        X = np.asarray(X)
        y = np.asarray(y).ravel()

        self.model_lo.fit(X, y)
        self.model_mid.fit(X, y)
        self.model_hi.fit(X, y)

        self.is_fitted = True
        return self

    def predict_quantiles(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predicts conditional quantiles: q_lo, q_mid, q_hi.
        Ensures non-crossing quantiles: q_lo <= q_mid <= q_hi.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_quantiles().")

        q_lo_pred = self.model_lo.predict(X)
        q_mid_pred = self.model_mid.predict(X)
        q_hi_pred = self.model_hi.predict(X)

        # Monotonic non-crossing correction
        q_mid_pred = np.maximum(q_lo_pred, q_mid_pred)
        q_hi_pred = np.maximum(q_mid_pred, q_hi_pred)

        return q_lo_pred, q_mid_pred, q_hi_pred


class MCDropoutNeuralNet:
    """
    Monte Carlo Dropout Neural Surrogate for epistemic uncertainty estimation.
    Applies test-time dropout to approximate variational inference over model weights.
    """

    def __init__(
        self,
        hidden_dim: int = 48,
        dropout_rate: float = 0.15,
        n_mc_samples: int = 50,
        learning_rate: float = 0.005,
        epochs: int = 150,
        random_state: int = 42,
    ):
        self.hidden_dim = hidden_dim
        self.dropout_rate = dropout_rate
        self.n_mc_samples = n_mc_samples
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.rng = np.random.RandomState(random_state)

        self.scaler_x = StandardScaler()
        self.scaler_y = StandardScaler()

        # Network weights
        self.W1: Optional[np.ndarray] = None
        self.b1: Optional[np.ndarray] = None
        self.W2: Optional[np.ndarray] = None
        self.b2: Optional[np.ndarray] = None
        self.W3: Optional[np.ndarray] = None
        self.b3: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MCDropoutNeuralNet":
        X = np.asarray(X)
        y = np.asarray(y).reshape(-1, 1)

        X_s = self.scaler_x.fit_transform(X)
        y_s = self.scaler_y.fit_transform(y)

        n_samples, in_dim = X_s.shape
        out_dim = 1

        # He initialization
        self.W1 = self.rng.randn(in_dim, self.hidden_dim) * np.sqrt(2.0 / in_dim)
        self.b1 = np.zeros((1, self.hidden_dim))
        self.W2 = self.rng.randn(self.hidden_dim, self.hidden_dim) * np.sqrt(2.0 / self.hidden_dim)
        self.b2 = np.zeros((1, self.hidden_dim))
        self.W3 = self.rng.randn(self.hidden_dim, out_dim) * np.sqrt(2.0 / self.hidden_dim)
        self.b3 = np.zeros((1, out_dim))

        batch_size = min(64, n_samples)
        n_batches = int(np.ceil(n_samples / batch_size))

        # Mini-batch gradient descent with dropout
        for epoch in range(self.epochs):
            indices = self.rng.permutation(n_samples)
            for b in range(n_batches):
                batch_idx = indices[b * batch_size : (b + 1) * batch_size]
                xb = X_s[batch_idx]
                yb = y_s[batch_idx]

                # Forward pass with inverted dropout
                z1 = np.dot(xb, self.W1) + self.b1
                a1 = np.maximum(0, z1)  # ReLU
                mask1 = (self.rng.rand(*a1.shape) >= self.dropout_rate) / (1.0 - self.dropout_rate)
                a1_drop = a1 * mask1

                z2 = np.dot(a1_drop, self.W2) + self.b2
                a2 = np.maximum(0, z2)
                mask2 = (self.rng.rand(*a2.shape) >= self.dropout_rate) / (1.0 - self.dropout_rate)
                a2_drop = a2 * mask2

                out = np.dot(a2_drop, self.W3) + self.b3

                # Backprop
                grad_out = (out - yb) / len(xb)

                grad_W3 = np.dot(a2_drop.T, grad_out)
                grad_b3 = np.sum(grad_out, axis=0, keepdims=True)

                grad_a2_drop = np.dot(grad_out, self.W3.T)
                grad_a2 = grad_a2_drop * mask2
                grad_z2 = grad_a2 * (z2 > 0)
                grad_W2 = np.dot(a1_drop.T, grad_z2)
                grad_b2 = np.sum(grad_z2, axis=0, keepdims=True)

                grad_a1_drop = np.dot(grad_z2, self.W2.T)
                grad_a1 = grad_a1_drop * mask1
                grad_z1 = grad_a1 * (z1 > 0)
                grad_W1 = np.dot(xb.T, grad_z1)
                grad_b1 = np.sum(grad_z1, axis=0, keepdims=True)

                # Parameter updates with weight decay
                self.W3 -= self.learning_rate * (grad_W3 + 1e-4 * self.W3)
                self.b3 -= self.learning_rate * grad_b3
                self.W2 -= self.learning_rate * (grad_W2 + 1e-4 * self.W2)
                self.b2 -= self.learning_rate * grad_b2
                self.W1 -= self.learning_rate * (grad_W1 + 1e-4 * self.W1)
                self.b1 -= self.learning_rate * grad_b1

        return self

    def predict_mc(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Performs T stochastic forward passes with dropout to estimate mean and epistemic variance.
        """
        X_s = self.scaler_x.transform(X)
        mc_preds = np.zeros((self.n_mc_samples, len(X)))

        for t in range(self.n_mc_samples):
            # Forward pass with active test-time dropout
            z1 = np.dot(X_s, self.W1) + self.b1
            a1 = np.maximum(0, z1)
            mask1 = (self.rng.rand(*a1.shape) >= self.dropout_rate) / (1.0 - self.dropout_rate)
            a1_drop = a1 * mask1

            z2 = np.dot(a1_drop, self.W2) + self.b2
            a2 = np.maximum(0, z2)
            mask2 = (self.rng.rand(*a2.shape) >= self.dropout_rate) / (1.0 - self.dropout_rate)
            a2_drop = a2 * mask2

            out_s = np.dot(a2_drop, self.W3) + self.b3
            # Invert scaling
            out_orig = self.scaler_y.inverse_transform(out_s).ravel()
            mc_preds[t] = out_orig

        mu = np.mean(mc_preds, axis=0)
        sigma_epistemic = np.std(mc_preds, axis=0)

        return mu, sigma_epistemic
