import logging
from typing import Optional

# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from app.models.sensor_threshold import SensorThreshold

logger = logging.getLogger(__name__)


async def get_by_device(db: AsyncSession, device_id: str) -> list[SensorThreshold]:
    """Trả về tất cả ngưỡng của 1 device."""
    result = await db.execute(
        select(SensorThreshold)
        .where(SensorThreshold.device_id == device_id)
        .order_by(SensorThreshold.metric_type)
    )
    return list(result.scalars().all())


async def get_by_metric(
    db: AsyncSession, device_id: str, metric_type: str
) -> Optional[SensorThreshold]:
    """Trả về ngưỡng của 1 metric cụ thể."""
    result = await db.execute(
        select(SensorThreshold)
        .where(SensorThreshold.device_id == device_id)
        .where(SensorThreshold.metric_type == metric_type)
    )
    return result.scalar_one_or_none()


async def upsert_threshold(
    db: AsyncSession,
    device_id: str,
    metric_type: str,
    data: dict,
) -> SensorThreshold:
    """Tạo mới hoặc thay thế toàn bộ ngưỡng cho 1 metric."""
    existing = await get_by_metric(db, device_id, metric_type)
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        await db.flush()
        await db.refresh(existing)
        logger.info("Updated threshold: device=%s metric=%s", device_id, metric_type)
        return existing

    threshold = SensorThreshold(device_id=device_id, metric_type=metric_type, **data)
    db.add(threshold)
    await db.flush()
    await db.refresh(threshold)
    logger.info("Created threshold: device=%s metric=%s", device_id, metric_type)
    return threshold


async def patch_threshold(
    db: AsyncSession,
    threshold: SensorThreshold,
    data: dict,
) -> SensorThreshold:
    """Cập nhật một phần các field của ngưỡng."""
    for key, value in data.items():
        if value is not None:
            setattr(threshold, key, value)
    await db.flush()
    await db.refresh(threshold)
    logger.info(
        "Patched threshold: device=%s metric=%s fields=%s",
        threshold.device_id, threshold.metric_type, list(data.keys()),
    )
    return threshold


async def delete_threshold(db: AsyncSession, threshold: SensorThreshold) -> None:
    """Xóa ngưỡng."""
    await db.delete(threshold)
    await db.flush()
    logger.info(
        "Deleted threshold: device=%s metric=%s",
        threshold.device_id, threshold.metric_type,
    )


async def seed_default_thresholds(
    db: AsyncSession,
    device_id: str,
    pond_type: str = "generic",
) -> list[SensorThreshold]:
    """
    Insert ngưỡng mặc định cho device mới theo loại ao.
    Nếu device đã có ngưỡng thì bỏ qua (không ghi đè).
    """
    from app.core.thresholds import DEFAULT_THRESHOLDS

    templates = DEFAULT_THRESHOLDS.get(pond_type, DEFAULT_THRESHOLDS["generic"])
    seeded = []

    for tpl in templates:
        existing = await get_by_metric(db, device_id, tpl.metric_type)
        if existing:
            continue  # không ghi đè ngưỡng đã có

        record = SensorThreshold(
            device_id=device_id,
            metric_type=tpl.metric_type,
            min_value=tpl.min_value,
            max_value=tpl.max_value,
            unit=tpl.unit,
            action_target=tpl.action_target,
            action_command=tpl.action_command,
            auto_action=tpl.auto_action,
        )
        db.add(record)
        seeded.append(record)

    if seeded:
        await db.flush()
        logger.info(
            "Seeded %d default thresholds for device=%s pond_type=%s",
            len(seeded), device_id, pond_type,
        )

    return seeded
