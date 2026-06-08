import logging
import time

# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import threshold_service, device_service

logger = logging.getLogger(__name__)

# Debounce: lưu thời điểm cuối cùng gửi từng action per device+metric
# key: (device_id, metric_type, action) → timestamp
_last_action_time: dict[tuple, float] = {}
DEBOUNCE_SECONDS = 120.0  # không gửi lại CHANGE_WATER trong 120s


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

    def to_comparable(metric_type: str, raw_value: float) -> float:
        """Convert giá trị thô sang đơn vị so sánh với ngưỡng trong DB.
        water_level: HC-SR04 trả về cm khoảng cách, DB lưu ngưỡng theo %
        Công thức: pct = (1 - (dist - 3) / 7) * 75, clamp 0-100
        """
        if metric_type == "water_level":
            pct = (1.0 - (raw_value - 3.0) / 7.0) * 75.0
            return max(0.0, min(100.0, pct))
        return raw_value

    for threshold in thresholds:
        value = metrics.get(threshold.metric_type)
        if value is None:
            continue

        # Convert sang đơn vị so sánh (ví dụ water_level: cm → %)
        cmp_value = to_comparable(threshold.metric_type, value)

        # Kiểm tra vi phạm ngưỡng
        min_violated = threshold.min_value is not None and cmp_value < threshold.min_value
        max_violated = threshold.max_value is not None and cmp_value > threshold.max_value
        violated = min_violated or max_violated

        if not violated:
            continue

        direction = f"< {threshold.min_value}" if min_violated else f"> {threshold.max_value}"
        note = (
            f"Auto-triggered: {threshold.metric_type}={cmp_value:.2f} {direction}"
            f" {threshold.unit or ''}"
        ).strip()

        if threshold.auto_action and threshold.action_target and threshold.action_command:
            # ── Chế độ tự động ──────────────────────────────────────────────
            # Với water_level: min vi phạm → pump_fill ON, max vi phạm → chỉ tắt pump_fill (không xả)
            if threshold.metric_type == "water_level" and max_violated:
                # Tắt bơm cấp nếu đang bật
                mqtt_client.publish(f"control/{device_id}", {"target": "pump_fill", "action": "OFF"})
                await device_service.log_device_history(db=db, device_id=device_id, action="OFF",
                    target="pump_fill", status="success", source="schedule", note=note)
                logger.info("AUTO STOP FILL | device=%s water_level=%s > max", device_id, cmp_value)
                continue

            act_target  = threshold.action_target
            act_command = threshold.action_command

            # Với CHANGE_WATER (nh3): truyền thêm ngưỡng water_level vào payload
            payload: dict = {"target": act_target, "action": act_command}
            if act_command == "CHANGE_WATER":
                # Debounce: không gửi lại trong DEBOUNCE_SECONDS
                debounce_key = (device_id, threshold.metric_type, act_command)
                now = time.time()
                last = _last_action_time.get(debounce_key, 0)
                if now - last < DEBOUNCE_SECONDS:
                    remaining = int(DEBOUNCE_SECONDS - (now - last))
                    logger.info("DEBOUNCE | device=%s %s skipped, cooldown %ds left",
                        device_id, act_command, remaining)
                    continue
                _last_action_time[debounce_key] = now

                wl_thresh = next((t for t in thresholds if t.metric_type == "water_level"), None)
                if wl_thresh and wl_thresh.auto_action:
                    payload["wl_drain_target"] = wl_thresh.min_value or 25.0
                    payload["wl_fill_target"]  = wl_thresh.max_value or 80.0
                else:
                    payload["wl_drain_target"] = 25.0
                    payload["wl_fill_target"]  = 80.0
                await device_service.log_device_history(db=db, device_id=device_id, action="ON",
                    target="pump_drain", status="success", source="schedule", note="CHANGE_WATER: draining")
                await device_service.log_device_history(db=db, device_id=device_id, action="ON",
                    target="pump_fill", status="success", source="schedule", note="CHANGE_WATER: will fill after drain")

            mqtt_client.publish(f"control/{device_id}", payload)
            await device_service.log_device_history(
                db=db, device_id=device_id,
                action=act_command, target=act_target,
                status="success", source="schedule", note=note,
            )
            logger.info(
                "AUTO ACTION | device=%s metric=%s value=%s(%s%%) → %s %s",
                device_id, threshold.metric_type, value, f"{cmp_value:.1f}", act_target, act_command,
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

    # ── Tắt thiết bị khi metric đã về mức an toàn ────────────────────────
    for threshold in thresholds:
        if not (threshold.auto_action and threshold.action_command == "ON" and threshold.action_target):
            continue
        value = metrics.get(threshold.metric_type)
        if value is None:
            continue
        cmp_value = to_comparable(threshold.metric_type, value)

        # Xác định thiết bị nào đang được bật và điều kiện dừng
        target = threshold.action_target
        should_off = False

        if threshold.metric_type == "water_level":
            # pump_fill bật khi thấp (min violated) → tắt khi đạt max
            if target == "pump_fill" and threshold.max_value is not None and cmp_value >= threshold.max_value:
                should_off = True
            # pump_drain: tắt khi nước đã xả xuống đến min_value
            if threshold.min_value is not None and cmp_value <= threshold.min_value:
                mqtt_client.publish(f"control/{device_id}", {"target": "pump_drain", "action": "OFF"})
                await device_service.log_device_history(db=db, device_id=device_id, action="OFF",
                    target="pump_drain", status="success", source="schedule",
                    note=f"Auto OFF pump_drain: water_level={cmp_value:.1f}% <= min {threshold.min_value}%")
                logger.info("AUTO OFF pump_drain | device=%s water_level=%.1f%% reached min", device_id, cmp_value)
        else:
            # Các metric khác: tắt khi đã về vùng an toàn hoàn toàn
            min_ok = threshold.min_value is None or cmp_value >= threshold.min_value
            max_ok = threshold.max_value is None or cmp_value <= threshold.max_value
            if min_ok and max_ok:
                should_off = True

        if not should_off:
            continue

        mqtt_client.publish(f"control/{device_id}", {"target": target, "action": "OFF"})
        await device_service.log_device_history(db=db, device_id=device_id, action="OFF",
            target=target, status="success", source="schedule",
            note=f"Auto OFF: {threshold.metric_type}={cmp_value:.2f} reached target")
        if threshold.metric_type == "water_level":
            other = "pump_drain" if target == "pump_fill" else "pump_fill"
            mqtt_client.publish(f"control/{device_id}", {"target": other, "action": "OFF"})
            await device_service.log_device_history(db=db, device_id=device_id, action="OFF",
                target=other, status="success", source="schedule",
                note=f"Auto OFF: {threshold.metric_type}={cmp_value:.2f} reached target")
        logger.info("AUTO OFF | device=%s metric=%s cmp=%.1f%% → %s OFF",
            device_id, threshold.metric_type, cmp_value, target)
