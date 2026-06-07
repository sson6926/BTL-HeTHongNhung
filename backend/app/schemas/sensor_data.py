from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict


class SensorDataResponse(BaseModel):
    id: int
    device_id: str
    metric_type: str
    value: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LatestSensorResponse(BaseModel):
    device_id: str
    metric_type: str
    value: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WaterMetricsResponse(BaseModel):
    temperature: Optional[float] = None
    tds: Optional[float] = None
    ph: Optional[float] = None


# ---------------------------------------------------------------------------
# Water quality forecast schemas
# ---------------------------------------------------------------------------

class WaterQualityForecastPoint(BaseModel):
    """A single predicted time-step."""
    forecast_time: datetime
    water_pH: float
    TDS: float
    water_temp: float


class WaterQualityForecastResponse(BaseModel):
    """Full response returned by GET /sensors/predict."""
    device_id: str
    generated_at: datetime
    input_points: int           # number of historical data points used
    forecast_steps: int         # number of future steps predicted
    forecasts: list[WaterQualityForecastPoint]
