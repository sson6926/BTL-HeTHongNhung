import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_data import SensorData

logger = logging.getLogger(__name__)


async def save_sensor_data(
    db: AsyncSession,
    device_id: str,
    metric_type: str,
    value: float,
) -> SensorData:
    """Persist a new sensor reading (value only) and return the saved object."""
    record = SensorData(
        device_id=device_id,
        metric_type=metric_type,
        value=value,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    logger.debug(
        "Saved sensor data: device=%s metric=%s value=%s",
        device_id,
        metric_type,
        value,
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


async def get_water_metrics_24(
    db: AsyncSession,
    device_id: str,
    limit: int = 24,
) -> list[dict]:
    """
    Return the latest `limit` records grouped by timestamp, containing water_pH, TDS, and water_temp.
    Returns a list of dicts: [{"water_pH": x, "TDS": y, "water_temp": z, "created_at": timestamp}, ...]
    """
    # Query top limit records for each of the 3 metrics
    metrics = ["water_pH", "TDS", "water_temp"]
    data_by_timestamp = defaultdict(dict)

    for metric in metrics:
        stmt = (
            select(SensorData)
            .where(
                (SensorData.device_id == device_id)
                & (SensorData.metric_type == metric)
            )
            .order_by(SensorData.created_at.desc())
            .limit(limit * 2)  # Get more to handle potential duplicates/gaps
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        for record in records:
            ts = record.created_at
            data_by_timestamp[ts][metric] = record.value

    # Sort by timestamp descending and limit to top `limit` timestamps
    sorted_timestamps = sorted(data_by_timestamp.keys(), reverse=True)[:limit]

    # Build response
    response = [
        {
            "water_pH": data_by_timestamp[ts].get("water_pH"),
            "TDS": data_by_timestamp[ts].get("TDS"),
            "water_temp": data_by_timestamp[ts].get("water_temp"),
            "created_at": ts,
        }
        for ts in sorted_timestamps
    ]

    logger.debug(
        "Retrieved %d water metric records for device=%s", len(response), device_id
    )
    return response
