import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.mqtt.client import mqtt_client
from app.schemas.device import ControlRequest, ControlResponse, DeviceCreate, DeviceResponse
from app.services import device_service, threshold_service

logger = logging.getLogger(__name__)

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[DeviceResponse], summary="List all devices")
async def list_devices(db: DbDep):
    """Return all registered devices."""
    try:
        return await device_service.get_all_devices(db)
    except Exception as exc:
        logger.exception("Failed to list devices: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve devices.",
        ) from exc


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a device",
)
async def create_device(body: DeviceCreate, db: DbDep):
    """Create/update a device from the pond form and optionally seed default thresholds."""
    try:
        device = await device_service.create_or_update_device(db, body)
        if body.pond_type:
            await threshold_service.seed_default_thresholds(
                db, device.device_id, pond_type=body.pond_type
            )
        return device
    except Exception as exc:
        logger.exception("Failed to create device %s: %s", body.device_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create device '{body.device_id}'.",
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


@router.put("/{device_id}/pond_type", response_model=DeviceResponse, summary="Change pond type and reseed thresholds")
async def change_pond_type(device_id: str, body: dict, db: DbDep):
    """Cập nhật pond_type và ghi đè ngưỡng theo loại ao mới."""
    pond_type = body.get("pond_type", "generic")
    device = await device_service.get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device '{device_id}' not found.")
    device.pond_type = pond_type
    await db.flush()
    await threshold_service.reseed_thresholds(db, device_id, pond_type)
    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a device")
async def delete_device(device_id: str, db: DbDep):
    """Delete a device record when a pond is removed."""
    deleted = await device_service.delete_device(db, device_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found.",
        )


@router.post(
    "/{device_id}/control",
    response_model=ControlResponse,
    summary="Send a control command to a device",
)
async def control_device(device_id: str, body: ControlRequest, db: DbDep):
    """
    Publish a control command via MQTT, update device status for ON/OFF,
    and log the action to device_history.
    """
    await device_service.ensure_esp32_device(db, device_id)

    target = body.target
    action = body.action

    try:
        payload = {"target": target, "action": action}
        mqtt_client.publish(f"control/{device_id}", payload)
        logger.info("Published control command to control/%s: %s", device_id, payload)

        if action in ("ON", "OFF"):
            await device_service.update_device_status(db, device_id, action)

        await device_service.log_device_history(
            db=db,
            device_id=device_id,
            action=action,
            target=target,
            status="success",
            source="api",
            note=f"Action '{action}' triggered via REST API.",
        )

        return ControlResponse(
            device_id=device_id,
            action=action,
            status="success",
            message=f"Command '{action}' (target: {target}) sent to device '{device_id}' successfully.",
        )

    except Exception as exc:
        logger.exception("Failed to control device %s: %s", device_id, exc)
        try:
            await device_service.log_device_history(
                db=db,
                device_id=device_id,
                action=action,
                target=target,
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
