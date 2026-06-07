from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
    device_id: str
    name: str
    type: Literal["esp32"] = "esp32"
    status: Literal["ON", "OFF"] = "OFF"
    location: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceResponse(DeviceBase):
    id: int
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ControlRequest(BaseModel):
    target: Literal["pump_fill", "pump_drain", "oxygen", "feeder", "relay", "esp32"]
    action: Literal["ON", "OFF", "FEED", "RESET", "CHANGE_WATER"]


class ControlResponse(BaseModel):
    device_id: str
    action: str
    status: str
    message: str
