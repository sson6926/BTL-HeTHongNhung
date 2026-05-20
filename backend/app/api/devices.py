import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.mqtt.client import mqtt_client
from app.schemas.device import DeviceResponse, ControlRequest, ControlResponse
from app.services import device_service

logger = logging.getLogger(__name__)

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[DeviceResponse], summary="List all devices")
async def list_devices(db: DbDep):
    """Return all registered devices."""
    try:
        devices = await device_service.get_all_devices(db)
        return devices
    except Exception as exc:
        logger.exception("Failed to list devices: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve devices.",
        ) from exc


@router.get("/{device_id}", response_model=DeviceResponse, summary="Get a single device")
async def get_device(device_id: str, db: DbDep):
    """Return a device by its device_id."""
    device = await device_service.get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found.",
        )
    return device


@router.post(
    "/{device_id}/control",
    response_model=ControlResponse,
    summary="Send a control command to a device",
)
async def control_device(device_id: str, body: ControlRequest, db: DbDep):
    """
    Publish a control command via MQTT, update device status (for ON/OFF),
    and log the action to device_history.
    """
    # Verify device exists
    device = await device_service.get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found.",
        )

    action = body.action

    try:
        # Publish MQTT command
        mqtt_client.publish(f"control/{device_id}", {"action": action})
        logger.info("Published control command to control/%s: action=%s", device_id, action)

        # Update device status only for ON/OFF actions
        if action in ("ON", "OFF"):
            await device_service.update_device_status(db, device_id, action)

        # Log to device_history
        await device_service.log_device_history(
            db=db,
            device_id=device_id,
            action=action,
            status="success",
            source="api",
            note=f"Action '{action}' triggered via REST API.",
        )

        return ControlResponse(
            device_id=device_id,
            action=action,
            status="success",
            message=f"Command '{action}' sent to device '{device_id}' successfully.",
        )

    except Exception as exc:
        logger.exception("Failed to control device %s: %s", device_id, exc)
        # Attempt to log failure
        try:
            await device_service.log_device_history(
                db=db,
                device_id=device_id,
                action=action,
                status="failed",
                source="api",
                note=str(exc),
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send command '{action}' to device '{device_id}'.",
        ) from exc
