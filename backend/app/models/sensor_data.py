from datetime import datetime

from sqlalchemy import BigInteger, String, Float, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())

    # Relationship
    device: Mapped["Device"] = relationship(  # noqa: F821
        "Device", back_populates="sensor_data", lazy="select"
    )

    __table_args__ = (
        Index("ix_sensor_data_device_created", "device_id", "created_at"),
        Index("ix_sensor_data_metric_created", "metric_type", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<SensorData id={self.id} device_id={self.device_id} "
            f"metric_type={self.metric_type} value={self.value}>"
        )
