import logging
from datetime import datetime, timezone

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


async def save_all_sensor_data(
    db: AsyncSession,
    device_id: str,
    metrics: dict[str, float],
) -> list[SensorData]:
    """
    Lưu tất cả metric từ 1 MQTT message vào DB với cùng timestamp.

    Tất cả SensorData row được tạo với cùng `created_at` để đảm bảo
    dữ liệu từ 1 lần đo có thể được ghép lại chính xác theo thời gian.
    """
    now = datetime.now(timezone.utc)
    records = [
        SensorData(
            device_id=device_id,
            metric_type=metric_type,
            value=value,
            created_at=now,
        )
        for metric_type, value in metrics.items()
    ]
    db.add_all(records)
    await db.flush()
    logger.debug(
        "Saved %d sensor metrics for device=%s at %s",
        len(records),
        device_id,
        now.isoformat(),
    )
    return records


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
    Trả về `limit` bản ghi ghép từ 3 metric (temperature, tds, ph).

    Cách ghép: lấy top-`limit` giá trị mới nhất cho từng metric, sau đó
    ghép theo thứ tự index (index 0 = cặp mới nhất). Nếu 1 metric ít dữ liệu
    hơn thì điền None cho các vị trí thiếu.
    """
    _METRICS = ["temperature", "tds", "ph"]
    data: dict[str, list[float]] = {}

    for metric in _METRICS:
        stmt = (
            select(SensorData.value)
            .where(
                (SensorData.device_id == device_id)
                & (SensorData.metric_type == metric)
            )
            .order_by(SensorData.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        data[metric] = [row[0] for row in result.all()]

    # Số điểm thực tế cần trả (bằng metric có nhiều dữ liệu nhất, không quá limit)
    n = min(max((len(v) for v in data.values()), default=0), limit)

    response = [
        {
            "temperature": data["temperature"][i] if i < len(data["temperature"]) else None,
            "tds": data["tds"][i] if i < len(data["tds"]) else None,
            "ph": data["ph"][i] if i < len(data["ph"]) else None,
        }
        for i in range(n)
    ]

    logger.debug(
        "Retrieved %d water metric records for device=%s", len(response), device_id
    )
    return response
