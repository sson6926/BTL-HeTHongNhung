from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class DeviceHistoryResponse(BaseModel):
    id: int
    device_id: str
    action: Literal["ON", "OFF", "FEED", "RESET", "CHANGE_WATER"]
    status: Literal["success", "failed"]
    source: Literal["manual", "api", "schedule"]
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
