import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.device_history import DeviceHistory

logger = logging.getLogger(__name__)


async def get_all_devices(db: AsyncSession) -> list[Device]:
    """Return all devices ordered by created_at descending."""
    result = await db.execute(select(Device).order_by(Device.created_at.desc()))
    return list(result.scalars().all())


async def get_device_by_id(db: AsyncSession, device_id: str) -> Optional[Device]:
    """Return a single device by its device_id string, or None if not found."""
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    return result.scalar_one_or_none()


async def update_device_status(db: AsyncSession, device_id: str, status: str) -> Device:
    """Update the status field of a device and return the updated object."""
    await db.execute(
        update(Device)
        .where(Device.device_id == device_id)
        .values(status=status, updated_at=datetime.now(timezone.utc))
    )
    await db.flush()

    device = await get_device_by_id(db, device_id)
    if device is None:
        raise ValueError(f"Device '{device_id}' not found after status update.")
    logger.info("Device %s status updated to %s", device_id, status)
    return device


async def update_last_seen(db: AsyncSession, device_id: str) -> None:
    """Refresh the last_seen timestamp for a device."""
    await db.execute(
        update(Device)
        .where(Device.device_id == device_id)
        .values(last_seen=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    )
    await db.flush()
    logger.debug("Device %s last_seen updated.", device_id)


async def log_device_history(
    db: AsyncSession,
    device_id: str,
    action: str,
    status: str,
    source: str,
    note: Optional[str] = None,
) -> DeviceHistory:
    """Insert a new DeviceHistory record and return it."""
    history = DeviceHistory(
        device_id=device_id,
        action=action,
        status=status,
        source=source,
        note=note,
    )
    db.add(history)
    await db.flush()
    await db.refresh(history)
    logger.info(
        "Logged history for device %s: action=%s status=%s source=%s",
        device_id,
        action,
        status,
        source,
    )
    return history
