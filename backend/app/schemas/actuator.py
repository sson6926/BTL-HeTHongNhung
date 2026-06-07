# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class ActuatorInfo(BaseModel):
    key: str
    """Định danh actuator – dùng làm 'target' khi gọi POST /devices/{id}/control."""

    label: str
    """Tên hiển thị tiếng Việt trên UI."""

    category: str
    """Nhóm thiết bị: 'pump' | 'feeder' | 'system'."""

    icon: str
    """Tên icon theo lucide-react để FE render."""

    supported_actions: list[str]
    """Danh sách action hợp lệ với actuator này."""

    description: str
    """Mô tả ngắn, dùng cho tooltip hoặc sub-label trên card."""
