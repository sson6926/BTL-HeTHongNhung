import logging

# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import threshold_service, device_service

logger = logging.getLogger(__name__)


async def evaluate_rules(
    db: AsyncSession,
    device_id: str,
    metrics: dict[str, float],
) -> None:
    """
    Kiểm tra từng metric trong `metrics` với ngưỡng lưu trong DB.

    - Nếu vi phạm + auto_action=False → chỉ log WARNING (chế độ cảnh báo)
    - Nếu vi phạm + auto_action=True  → publish MQTT command + ghi device_history
    """
    # Lazy import để tránh circular dependency (mqtt_client import services)
    from app.mqtt.client import mqtt_client

    thresholds = await threshold_service.get_by_device(db, device_id)
    if not thresholds:
        return

    for threshold in thresholds:
        value = metrics.get(threshold.metric_type)
        if value is None:
            continue

        # Kiểm tra vi phạm ngưỡng
        min_violated = threshold.min_value is not None and value < threshold.min_value
        max_violated = threshold.max_value is not None and value > threshold.max_value
        violated = min_violated or max_violated

        if not violated:
            continue

        direction = f"< {threshold.min_value}" if min_violated else f"> {threshold.max_value}"
        note = (
            f"Auto-triggered: {threshold.metric_type}={value} {direction}"
            f" {threshold.unit or ''}"
        ).strip()

        if threshold.auto_action and threshold.action_target and threshold.action_command:
            # ── Chế độ tự động ──────────────────────────────────────────────
            mqtt_client.publish(
                f"control/{device_id}",
                {"target": threshold.action_target, "action": threshold.action_command},
            )
            await device_service.log_device_history(
                db=db,
                device_id=device_id,
                action=threshold.action_command,
                target=threshold.action_target,
                status="success",
                source="schedule",
                note=note,
            )
            logger.info(
                "AUTO ACTION | device=%s metric=%s value=%s → %s %s",
                device_id,
                threshold.metric_type,
                value,
                threshold.action_target,
                threshold.action_command,
            )
        else:
            # ── Chế độ cảnh báo (mặc định) ──────────────────────────────────
            logger.warning(
                "THRESHOLD ALERT | device=%s %s=%s %s (unit: %s)",
                device_id,
                threshold.metric_type,
                value,
                direction,
                threshold.unit or "—",
            )
