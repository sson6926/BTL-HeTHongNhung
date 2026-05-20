import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.sensor_data import SensorDataResponse, LatestSensorResponse
from app.services import sensor_service

logger = logging.getLogger(__name__)

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "/latest",
    response_model=list[LatestSensorResponse],
    summary="Get latest sensor values per metric for a device",
)
async def get_latest_sensors(
    db: DbDep,
    device_id: str = Query(..., description="The device_id to query latest readings for"),
):
    """
    Return the most recent reading per metric_type for the specified device.
    Returns an empty list if the device has no sensor data.
    """
    try:
        records = await sensor_service.get_latest_by_device(db, device_id)
        return records
    except Exception as exc:
        logger.exception("Failed to get latest sensors for device %s: %s", device_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest sensor data.",
        ) from exc


@router.get(
    "/history",
    response_model=list[SensorDataResponse],
    summary="Get time-series history for a metric type",
)
async def get_sensor_history(
    db: DbDep,
    metric_type: str = Query(..., description="Metric type to retrieve history for"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    """
    Return the most recent `limit` readings for the given metric_type across all devices,
    ordered by created_at descending.
    """
    try:
        records = await sensor_service.get_history_by_metric(db, metric_type, limit)
        return records
    except Exception as exc:
        logger.exception(
            "Failed to get sensor history for metric %s: %s", metric_type, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sensor history.",
        ) from exc
