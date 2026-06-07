from fastapi import APIRouter

from app.schemas.actuator import ActuatorInfo

router = APIRouter()

# ---------------------------------------------------------------------------
# Danh sách actuator cố định theo phần cứng thực tế của hệ thống.
# Thiết bị không thay đổi runtime nên hardcode thay vì lưu DB.
# ---------------------------------------------------------------------------
_ACTUATORS: list[ActuatorInfo] = [
    ActuatorInfo(
        key="pump_fill",
        label="Bơm cấp nước",
        category="pump",
        icon="droplets",
        supported_actions=["ON", "OFF"],
        description="Máy bơm mini cấp nước vào bể qua relay kênh 1",
    ),
    ActuatorInfo(
        key="pump_drain",
        label="Bơm xả nước",
        category="pump",
        icon="arrow-down-to-dot",
        supported_actions=["ON", "OFF", "CHANGE_WATER"],
        description="Máy bơm mini xả nước ra ngoài qua relay kênh 2",
    ),
    ActuatorInfo(
        key="oxygen",
        label="Máy sục khí",
        category="pump",
        icon="wind",
        supported_actions=["ON", "OFF"],
        description="Hệ thống sục khí tăng oxy hòa tan, giả lập bằng LED",
    ),
    ActuatorInfo(
        key="feeder",
        label="Máy cho ăn",
        category="feeder",
        icon="fish",
        supported_actions=["FEED"],
        description="Hệ thống cho ăn tự động, giả lập bằng LED",
    ),
]


@router.get(
    "/",
    response_model=list[ActuatorInfo],
    summary="Danh sách actuator có thể điều khiển",
)
async def list_actuators() -> list[ActuatorInfo]:
    """
    Trả về danh sách tất cả actuator vật lý trong hệ thống.

    Mỗi actuator bao gồm:
    - `key`: dùng làm `target` khi gọi `POST /devices/{device_id}/control`
    - `supported_actions`: danh sách action hợp lệ với actuator này
    - `label`, `icon`, `category`, `description`: metadata cho UI
    """
    return _ACTUATORS
