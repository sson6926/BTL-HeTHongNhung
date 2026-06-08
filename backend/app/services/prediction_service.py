"""
app/services/prediction_service.py
-----------------------------------
Singleton service that loads the trained LSTM model + MinMaxScaler once at
application startup and exposes a predict function used by the API layer.

Metric name mapping (DB -> model features):
    "ph"          -> water_pH   (index 0)
    "tds"         -> TDS        (index 1)
    "temperature" -> water_temp (index 2)
"""

from __future__ import annotations

import logging
import os
import pickle
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import torch

from app.core.config import settings
from app.ml.model import WaterQualityLSTM, WaterQualityGRU

logger = logging.getLogger(__name__)

# Feature order expected by the model
_FEATURES = ["water_pH", "TDS", "water_temp"]

# DB metric_type -> model feature name
_METRIC_MAP: dict[str, str] = {
    "ph": "water_pH",
    "tds": "TDS",
    "temperature": "water_temp",
}


class PredictionService:
    """
    Holds the trained LSTM model and scaler in memory.

    Usage:
        # at startup
        prediction_service = PredictionService()
        prediction_service.load()

        # at request time
        results = prediction_service.predict(recent_data, steps=12, last_timestamp=...)
    """

    def __init__(self) -> None:
        self._model: Any | None = None
        self._model_name: str = "lstm"
        self._scaler: Any | None = None
        self._device: torch.device = torch.device("cpu")
        self._loaded: bool = False
        self._lookback: int = settings.ML_LOOKBACK

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load(
        self,
        model_path: str | None = None,
        scaler_path: str | None = None,
        lookback: int | None = None,
    ) -> None:
        """
        Load model weights and scaler from disk.
        Falls back to settings values when paths are not provided.
        Safe to call multiple times (no-ops if already loaded).
        """
        if self._loaded:
            logger.debug("PredictionService already loaded — skipping.")
            return

        model_path  = model_path  or settings.ML_MODEL_PATH
        scaler_path = scaler_path or settings.ML_SCALER_PATH
        self._lookback = lookback or settings.ML_LOOKBACK

        if not os.path.exists(model_path):
            logger.error("LSTM model weights not found at: %s", model_path)
            return
        if not os.path.exists(scaler_path):
            logger.error("MinMaxScaler not found at: %s", scaler_path)
            return

        # Load scaler
        with open(scaler_path, "rb") as f:
            self._scaler = pickle.load(f)
        logger.info("MinMaxScaler loaded from %s", scaler_path)

        # Determine model type from file name
        model_name = "lstm"
        if "gru" in model_path.lower():
            model_name = "gru"
        self._model_name = model_name

        # Load model
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if model_name == "lstm":
            self._model = WaterQualityLSTM(
                input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2
            )
        else:
            self._model = WaterQualityGRU(
                input_size=3, hidden_size=64, num_layers=2, output_size=3, dropout=0.2
            )
        state_dict = torch.load(model_path, map_location=self._device)
        self._model.load_state_dict(state_dict)
        self._model.to(self._device)
        self._model.eval()
        logger.info(
            "%s model loaded from %s  (device=%s)", model_name.upper(), model_path, self._device
        )

        self._loaded = True

    @property
    def is_ready(self) -> bool:
        return self._loaded

    @property
    def lookback(self) -> int:
        return self._lookback

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(
        self,
        recent_data: list[dict[str, float]],
        steps: int = 12,
        last_timestamp: datetime | None = None,
    ) -> list[dict]:
        """
        Run autoregressive multi-step forecasting.

        Args:
            recent_data:    List of dicts with keys 'water_pH', 'TDS', 'water_temp',
                            ordered oldest → newest. Length must be >= lookback (24).
            steps:          Number of future hourly steps to forecast.
            last_timestamp: Timestamp of the last point in recent_data.
                            Defaults to now (UTC) if not provided.

        Returns:
            List of dicts: [{forecast_time, water_pH, TDS, water_temp}, ...]

        Raises:
            RuntimeError: if model is not loaded.
            ValueError:   if recent_data has fewer rows than lookback.
        """
        if not self._loaded or self._model is None or self._scaler is None:
            raise RuntimeError(
                "PredictionService is not ready. Model has not been loaded."
            )

        lookback = self._lookback

        if len(recent_data) < lookback:
            raise ValueError(
                f"Need at least {lookback} data points, got {len(recent_data)}."
            )

        # Use only the most recent `lookback` points
        window_data = recent_data[-lookback:]

        # Convert to numpy array (N, 3) in feature order
        raw = np.array(
            [[row["water_pH"], row["TDS"], row["water_temp"]] for row in window_data],
            dtype=np.float32,
        )

        # Scale using the pre-fit scaler (transform only, NOT fit)
        scaled_seq = self._scaler.transform(raw)     # (lookback, 3)
        current_seq = scaled_seq.copy()

        predictions: list[np.ndarray] = []

        with torch.no_grad():
            for _ in range(steps):
                # (1, lookback, 3)
                tensor = (
                    torch.tensor(current_seq, dtype=torch.float32)
                    .unsqueeze(0)
                    .to(self._device)
                )
                pred = self._model(tensor).cpu().numpy()[0]  # (3,)
                predictions.append(pred)

                # Slide window: drop oldest, append prediction
                current_seq = np.vstack([current_seq[1:], pred])

        # Inverse-transform to physical units
        preds_array = np.array(predictions)                   # (steps, 3)
        inv_preds   = self._scaler.inverse_transform(preds_array)  # (steps, 3)

        # Build timestamp sequence starting 1 hour after last input point
        base_ts = last_timestamp or datetime.now(timezone.utc)
        results = []
        for i, row in enumerate(inv_preds):
            results.append(
                {
                    "forecast_time": base_ts + timedelta(hours=i + 1),
                    "water_pH":   float(row[0]),
                    "TDS":        float(row[1]),
                    "water_temp": float(row[2]),
                }
            )

        return results


# ---------------------------------------------------------------------------
# Module-level singleton — imported by main.py and the API router
# ---------------------------------------------------------------------------
prediction_service = PredictionService()
