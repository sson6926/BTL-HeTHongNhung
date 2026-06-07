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
