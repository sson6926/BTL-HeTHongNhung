from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from sqlalchemy import BigInteger, String, Float, Boolean, ForeignKey, UniqueConstraint, func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SensorThreshold(Base):
    __tablename__ = "sensor_thresholds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Ngưỡng: NULL = không áp dụng chiều đó
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Hành động khi vi phạm ngưỡng (NULL = chỉ cảnh báo)
    action_target: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action_command: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # FALSE (default) = chỉ log cảnh báo
    # TRUE            = tự động publish lệnh điều khiển qua MQTT
    auto_action: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    # Mỗi device chỉ có 1 ngưỡng cho mỗi metric
    __table_args__ = (
        UniqueConstraint("device_id", "metric_type", name="uq_threshold_device_metric"),
    )

    def __repr__(self) -> str:
        return (
            f"<SensorThreshold device={self.device_id} metric={self.metric_type} "
            f"min={self.min_value} max={self.max_value} auto_action={self.auto_action}>"
        )
