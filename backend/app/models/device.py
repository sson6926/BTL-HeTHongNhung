from datetime import datetime
from typing import Optional

# pyrefly: ignore [missing-import]
from sqlalchemy import BigInteger, String, Enum, func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="esp32", nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("ON", "OFF", name="device_status_enum"),
        default="OFF",
        nullable=False,
    )
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pond_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    sensor_data: Mapped[list["SensorData"]] = relationship(  # noqa: F821
        "SensorData", back_populates="device", lazy="select"
    )
    history: Mapped[list["DeviceHistory"]] = relationship(  # noqa: F821
        "DeviceHistory", back_populates="device", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Device id={self.id} device_id={self.device_id} status={self.status}>"
