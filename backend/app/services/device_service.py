import logging
from datetime import datetime, timezone
from typing import Optional

# pyrefly: ignore [missing-import]
from sqlalchemy import select, update
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.device_history import DeviceHistory
from app.schemas.device import DeviceCreate

logger = logging.getLogger(__name__)


async def get_all_devices(db: AsyncSession) -> list[Device]:
    """Return all devices ordered by created_at descending."""
    result = await db.execute(select(Device).order_by(Device.created_at.desc()))
    return list(result.scalars().all())


async def get_device_by_id(db: AsyncSession, device_id: str) -> Optional[Device]:
    """Return a single device by its device_id string, or None if not found."""
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    return result.scalar_one_or_none()


<<<<<<< HEAD
async def ensure_esp32_device(db: AsyncSession, device_id: str) -> Device:
    """Return an ESP32 device, creating it if this device_id is seen for the first time."""
    device = await get_device_by_id(db, device_id)
    if device is not None:
        return device

    device = Device(
        device_id=device_id,
        name=f"ESP32 {device_id}",
        type="esp32",
        status="OFF",
    )
    db.add(device)
    await db.flush()
    await db.refresh(device)
    logger.info("Auto-registered ESP32 device %s", device_id)
    return device


async def create_or_update_device(db: AsyncSession, payload: DeviceCreate) -> Device:
    """Create a new device, or update its display metadata if it already exists."""
    device = await get_device_by_id(db, payload.device_id)
    if device is None:
        device = Device(
            device_id=payload.device_id,
            name=payload.name,
            type=payload.type,
            status=payload.status,
            location=payload.location,
        )
        db.add(device)
        await db.flush()
        await db.refresh(device)
        logger.info("Created device %s", payload.device_id)
        return device

    device.name = payload.name
    device.type = payload.type
    device.location = payload.location
    device.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(device)
    logger.info("Updated device metadata %s", payload.device_id)
    return device


async def delete_device(db: AsyncSession, device_id: str) -> bool:
    """Delete a device by device_id. Related sensor/history rows cascade in the DB."""
    device = await get_device_by_id(db, device_id)
    if device is None:
        return False

    await db.delete(device)
    await db.flush()
    logger.info("Deleted device %s", device_id)
    return True


=======
async def create_device(db: AsyncSession, data: dict) -> Device:
    """Tạo device mới và flush (chưa commit)."""
    device = Device(**data)
    db.add(device)
    await db.flush()
    await db.refresh(device)
    logger.info("Created device: device_id=%s pond_type=%s", device.device_id, device.pond_type)
    return device


>>>>>>> f3d18dd5ad90f0a6fa402a7de0f64107a251a204
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
    target: Optional[str] = None,
    note: Optional[str] = None,
) -> DeviceHistory:
    """Insert a new DeviceHistory record and return it."""
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
        device_id,
        action,
        status,
        source,
    )
    return history
