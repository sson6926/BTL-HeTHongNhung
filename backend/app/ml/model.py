"""
app/ml/model.py
---------------
PyTorch LSTM architecture for water quality time-series forecasting.

This mirrors the model definition in water-quality-prediction/src/model.py
so the backend is self-contained and does not depend on the ML source tree.
"""

import torch
import torch.nn as nn


class WaterQualityLSTM(nn.Module):
    """
    Stacked LSTM model that predicts the next time-step values of
    [water_pH, TDS, water_temp] given a lookback sequence of the same 3 features.

    Architecture:
        - 2-layer LSTM with hidden_size=64 and inter-layer dropout=0.2
        - Regression head: Linear(64→32) → ReLU → Dropout(0.2) → Linear(32→3)
    """

    def __init__(
        self,
        input_size: int = 3,
        hidden_size: int = 64,
        num_layers: int = 2,
        output_size: int = 3,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, input_size)
        Returns:
            Tensor of shape (batch_size, output_size)
        """
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)

        out, _ = self.lstm(x, (h0, c0))          # (batch, seq, hidden)
        out_last = out[:, -1, :]                   # take last time-step
        return self.fc(out_last)                   # (batch, output_size)
