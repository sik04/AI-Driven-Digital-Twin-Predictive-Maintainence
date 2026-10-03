"""
PyTorch-based LSTM and GRU Architectures for RUL Estimation in IntelliTwin.
Implements sequence-to-one recurrent neural networks with dropout regularization
and optional heteroscedastic uncertainty heads (mean and variance).
"""

import torch
import torch.nn as nn
import numpy as np


class LSTMRULNet(nn.Module):
    """LSTM Network for Remaining Useful Life (RUL) regression with uncertainty head."""

    def __init__(self, input_dim=54, hidden_dim=64, num_layers=2, dropout=0.2, heteroscedastic=True):
        super(LSTMRULNet, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.heteroscedastic = heteroscedastic

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        self.mu_head = nn.Linear(32, 1)
        if self.heteroscedastic:
            self.log_var_head = nn.Linear(32, 1)

    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        lstm_out, _ = self.lstm(x)
        # Take the output of the final time step
        last_step = lstm_out[:, -1, :]
        feat = self.fc(last_step)
        mu = self.mu_head(feat)

        if self.heteroscedastic:
            log_var = self.log_var_head(feat)
            # Clip log_var for numerical stability
            log_var = torch.clamp(log_var, min=-6.0, max=6.0)
            return mu.squeeze(-1), log_var.squeeze(-1)
        return mu.squeeze(-1)


class GRURULNet(nn.Module):
    """Gated Recurrent Unit (GRU) Network for RUL prediction."""

    def __init__(self, input_dim=54, hidden_dim=64, num_layers=2, dropout=0.2):
        super(GRURULNet, self).__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        gru_out, _ = self.gru(x)
        last_step = gru_out[:, -1, :]
        out = self.fc(last_step)
        return out.squeeze(-1)


def heteroscedastic_loss(mu, log_var, target):
    """Negative Log-Likelihood for Gaussian distribution with heteroscedastic variance:
    Loss = 0.5 * exp(-log_var) * (target - mu)^2 + 0.5 * log_var
    """
    precision = torch.exp(-log_var)
    mse = (target - mu) ** 2
    loss = 0.5 * precision * mse + 0.5 * log_var
    return torch.mean(loss)


def nasa_scoring_function(y_true, y_pred):
    """NASA C-MAPSS asymmetric evaluation metric.
    Penalizes late predictions (over-estimation) more severely than early predictions.
    """
    diff = y_pred - y_true
    score = np.where(diff < 0, np.exp(-diff / 13.0) - 1.0, np.exp(diff / 10.0) - 1.0)
    return float(np.sum(score))
