import asyncio
import json
import logging
import threading
from typing import Any, Optional

import paho.mqtt.client as mqtt

from app.core.config import settings

logger = logging.getLogger(__name__)

_MAX_RECONNECT_RETRIES = 10


class MQTTClient:
    """
    Wraps paho-mqtt with:
    - Background loop thread (loop_start / loop_stop)
    - Automatic reconnect with exponential back-off (capped at 5 s)
    - Bridge to async DB services via asyncio.run_coroutine_threadsafe
    """

    def __init__(self) -> None:
        self._client = mqtt.Client(client_id="iot-backend", clean_session=True)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._reconnect_count: int = 0
        self._reconnect_timer: Optional[threading.Timer] = None
        self._connected: bool = False

        # Wire up callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Store the running asyncio event loop so callbacks can schedule coroutines."""
        self._loop = loop

    def connect(self) -> None:
        """Connect to the MQTT broker and start the background network loop."""
        logger.info(
            "Connecting to MQTT broker at %s:%s", settings.MQTT_HOST, settings.MQTT_PORT
        )
        self._client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        self._client.loop_start()

    def disconnect(self) -> None:
        """Stop the background loop and disconnect cleanly."""
        if self._reconnect_timer is not None:
            self._reconnect_timer.cancel()
            self._reconnect_timer = None
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False
        logger.info("MQTT client disconnected.")

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish a JSON-encoded payload to the given topic."""
        message = json.dumps(payload)
        result = self._client.publish(topic, message, qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(
                "Failed to publish to topic '%s': rc=%s", topic, result.rc
            )
        else:
            logger.debug("Published to '%s': %s", topic, message)

    # ------------------------------------------------------------------
    # Paho callbacks (run in the paho network thread)
    # ------------------------------------------------------------------

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict,
        rc: int,
    ) -> None:
        if rc == 0:
            self._connected = True
            self._reconnect_count = 0
            logger.info("MQTT connected successfully.")
            # Subscribe to all sensor topics: sensor/{device_id}/{metric_type}
            client.subscribe("sensor/+/+", qos=1)
            logger.info("Subscribed to sensor/+/+")
        else:
            logger.error("MQTT connection failed with return code %s", rc)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
    ) -> None:
        self._connected = False
        if rc != 0:
            logger.warning("Unexpected MQTT disconnect (rc=%s). Scheduling reconnect…", rc)
            self._schedule_reconnect()
        else:
            logger.info("MQTT disconnected cleanly.")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """
        Handle incoming sensor messages.

        Topic format: sensor/{device_id}/{metric_type}
        Payload:      {"value": <float>, "unit": "<str>"}
        """
        topic = msg.topic
        try:
            parts = topic.split("/")
            if len(parts) != 3 or parts[0] != "sensor":
                logger.warning("Unexpected topic format: %s", topic)
                return

            _, device_id, metric_type = parts

            payload = json.loads(msg.payload.decode("utf-8"))
            value: float = float(payload["value"])
            unit: str = str(payload.get("unit", ""))

            logger.debug(
                "Received sensor data: device=%s metric=%s value=%s %s",
                device_id,
                metric_type,
                value,
                unit,
            )

            if self._loop is None:
                logger.error("Event loop not set; cannot persist sensor data.")
                return

            # Schedule async DB writes on the FastAPI event loop
            asyncio.run_coroutine_threadsafe(
                self._persist_sensor_data(device_id, metric_type, value, unit),
                self._loop,
            )

        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            logger.error("Failed to parse MQTT message on topic '%s': %s", topic, exc)
        except Exception as exc:
            logger.exception("Unexpected error in on_message for topic '%s': %s", topic, exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _persist_sensor_data(
        self,
        device_id: str,
        metric_type: str,
        value: float,
        unit: str,
    ) -> None:
        """Save sensor reading and update device last_seen inside an async DB session."""
        from app.db.session import AsyncSessionLocal
        from app.services import sensor_service, device_service

        async with AsyncSessionLocal() as db:
            try:
                await sensor_service.save_sensor_data(db, device_id, metric_type, value, unit)
                await device_service.update_last_seen(db, device_id)
                await db.commit()
            except Exception as exc:
                await db.rollback()
                logger.error(
                    "DB error persisting sensor data for device=%s metric=%s: %s",
                    device_id,
                    metric_type,
                    exc,
                )

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnect attempt with a 5-second delay."""
        if self._reconnect_count >= _MAX_RECONNECT_RETRIES:
            logger.error(
                "Max MQTT reconnect retries (%s) reached. Giving up.", _MAX_RECONNECT_RETRIES
            )
            return

        self._reconnect_count += 1
        delay = 5.0
        logger.info(
            "Reconnect attempt %s/%s in %.0fs…",
            self._reconnect_count,
            _MAX_RECONNECT_RETRIES,
            delay,
        )
        self._reconnect_timer = threading.Timer(delay, self._do_reconnect)
        self._reconnect_timer.daemon = True
        self._reconnect_timer.start()

    def _do_reconnect(self) -> None:
        try:
            self._client.reconnect()
            logger.info("MQTT reconnect initiated.")
        except Exception as exc:
            logger.error("MQTT reconnect failed: %s", exc)
            self._schedule_reconnect()


# Global singleton used by the FastAPI app and API routes
mqtt_client = MQTTClient()
