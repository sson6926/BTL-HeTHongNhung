from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, model_validator


class ThresholdCreate(BaseModel):
    """Tạo hoặc thay thế ngưỡng cho 1 metric."""

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = None
    action_target: Optional[str] = None
    action_command: Optional[str] = None
    auto_action: bool = False

    @model_validator(mode="after")
    def validate_action_pair(self) -> "ThresholdCreate":
        """action_target và action_command phải cùng có hoặc cùng None."""
        has_target = self.action_target is not None
        has_command = self.action_command is not None
        if has_target != has_command:
            raise ValueError(
                "action_target và action_command phải cùng được cung cấp hoặc cùng để trống."
            )
        if self.auto_action and not has_target:
            raise ValueError(
                "auto_action=True yêu cầu action_target và action_command."
            )
        return self


class ThresholdUpdate(BaseModel):
    """Cập nhật một phần ngưỡng (ví dụ: toggle auto_action)."""

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = None
    action_target: Optional[str] = None
    action_command: Optional[str] = None
    auto_action: Optional[bool] = None


class ThresholdResponse(BaseModel):
    id: int
    device_id: str
    metric_type: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = None
    action_target: Optional[str] = None
    action_command: Optional[str] = None
    auto_action: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
