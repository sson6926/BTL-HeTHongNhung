from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorDataResponse(BaseModel):
    id: int
    device_id: str
    metric_type: str
    value: float
    unit: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LatestSensorResponse(BaseModel):
    device_id: str
    metric_type: str
    value: float
    unit: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
