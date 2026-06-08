import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.device_history import DeviceHistory
from app.schemas.device import DeviceCreate

logger = logging.getLogger(__name__)


async def get_all_devices(db: AsyncSession) -> list[Device]:
    result = await db.execute(select(Device).order_by(Device.created_at.desc()))
    return list(result.scalars().all())


async def get_device_by_id(db: AsyncSession, device_id: str) -> Optional[Device]:
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    return result.scalar_one_or_none()


async def ensure_esp32_device(db: AsyncSession, device_id: str) -> Device:
    """Return device or raise ValueError if not found."""
    device = await get_device_by_id(db, device_id)
    if device is None:
        raise ValueError(f"Device '{device_id}' not found.")
    return device


async def create_or_update_device(db: AsyncSession, body: DeviceCreate) -> Device:
    device = await get_device_by_id(db, body.device_id)
    if device:
        device.name = body.name
        device.location = body.location
        device.type = body.type
        if body.pond_type is not None:
            device.pond_type = body.pond_type
        device.updated_at = datetime.now(timezone.utc)
    else:
        device = Device(
            device_id=body.device_id,
            name=body.name,
            type=body.type,
            status="OFF",
            location=body.location,
            pond_type=body.pond_type,
        )
        db.add(device)
    await db.flush()
    await db.refresh(device)
    await db.commit()
    return device


async def delete_device(db: AsyncSession, device_id: str) -> bool:
    result = await db.execute(delete(Device).where(Device.device_id == device_id))
    await db.commit()
    return result.rowcount > 0


async def update_device_status(db: AsyncSession, device_id: str, status: str) -> Device:
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
    target: Optional[str] = None,
    note: Optional[str] = None,
) -> DeviceHistory:
    history = DeviceHistory(
        device_id=device_id,
        action=action,
        target=target,
        status=status,
        source=source,
        note=note,
    )
    db.add(history)
    await db.flush()
    await db.refresh(history)
    logger.info(
        "Logged history for device %s: action=%s status=%s source=%s",
        device_id, action, status, source,
    )
    return history
