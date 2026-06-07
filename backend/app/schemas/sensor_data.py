from datetime import datetime
from typing import Optional

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
    water_pH: Optional[float] = None
    TDS: Optional[float] = None
    water_temp: Optional[float] = None
    created_at: datetime
