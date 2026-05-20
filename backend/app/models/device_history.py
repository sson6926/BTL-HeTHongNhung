from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Enum, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DeviceHistory(Base):
    __tablename__ = "device_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        Enum("ON", "OFF", "FEED", "RESET", "CHANGE_WATER", name="history_action_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("success", "failed", name="history_status_enum"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        Enum("manual", "api", "schedule", name="history_source_enum"),
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())

    # Relationship
    device: Mapped["Device"] = relationship(  # noqa: F821
        "Device", back_populates="history", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<DeviceHistory id={self.id} device_id={self.device_id} "
            f"action={self.action} status={self.status}>"
        )
