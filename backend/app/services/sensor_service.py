import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_data import SensorData

logger = logging.getLogger(__name__)


async def save_sensor_data(
    db: AsyncSession,
    device_id: str,
    metric_type: str,
    value: float,
    unit: str,
) -> SensorData:
    """Persist a new sensor reading and return the saved object."""
    record = SensorData(
        device_id=device_id,
        metric_type=metric_type,
        value=value,
        unit=unit,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    logger.debug(
        "Saved sensor data: device=%s metric=%s value=%s %s",
        device_id,
        metric_type,
        value,
        unit,
    )
    return record


async def get_latest_by_device(db: AsyncSession, device_id: str) -> list[SensorData]:
    """
    Return the most recent SensorData row per metric_type for a given device.

    Uses a subquery that finds the maximum created_at per metric_type, then
    joins back to sensor_data to retrieve the full rows.
    """
    # Subquery: max(created_at) per metric_type for this device
    subq = (
        select(
            SensorData.metric_type,
            func.max(SensorData.created_at).label("max_created_at"),
        )
        .where(SensorData.device_id == device_id)
        .group_by(SensorData.metric_type)
        .subquery()
    )

    stmt = select(SensorData).join(
        subq,
        (SensorData.metric_type == subq.c.metric_type)
        & (SensorData.created_at == subq.c.max_created_at)
        & (SensorData.device_id == device_id),
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_history_by_metric(
    db: AsyncSession,
    metric_type: str,
    limit: int = 100,
) -> list[SensorData]:
    """Return the most recent `limit` readings for a given metric_type across all devices."""
    stmt = (
        select(SensorData)
        .where(SensorData.metric_type == metric_type)
        .order_by(SensorData.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
