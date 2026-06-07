import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.sensor_data import (
    LatestSensorResponse,
    SensorDataResponse,
    WaterMetricsResponse,
    WaterQualityForecastResponse,
)
from app.services import sensor_service
from app.services.prediction_service import prediction_service

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


@router.get(
    "/water-metrics",
    response_model=list[WaterMetricsResponse],
    summary="Get latest 24 water metrics (pH, TDS, temperature)",
)
async def get_water_metrics(
    db: DbDep,
    device_id: str = Query(..., description="The device_id to query water metrics for"),
    limit: int = Query(24, ge=1, le=100, description="Maximum number of records to return"),
):
    """
    Return the latest `limit` records grouped by timestamp, containing water_pH, TDS, and water_temp.
    Each object contains values for all 3 metrics at the same timestamp (nullable if not available).
    """
    try:
        records = await sensor_service.get_water_metrics_24(db, device_id, limit)
        return records
    except Exception as exc:
        logger.exception(
            "Failed to get water metrics for device %s: %s", device_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve water metrics.",
        ) from exc


@router.get(
    "/predict",
    response_model=WaterQualityForecastResponse,
    summary="Forecast future water quality using the LSTM model",
)
async def predict_water_quality(
    db: DbDep,
    device_id: str = Query(..., description="Device ID to forecast water quality for"),
    steps: int = Query(
        12, ge=1, le=48,
        description="Number of future hourly steps to forecast (1–48)",
    ),
):
    """
    Retrieve the last 24 sensor readings (water_pH, TDS, water_temp) for the
    given device from the database, then run the pre-trained LSTM model to
    forecast the next `steps` hourly values.

    **Requires** at least 24 historical data points per metric in the database.

    Returns a `WaterQualityForecastResponse` containing:
    - Metadata (device_id, generated_at, input_points, forecast_steps)
    - A list of `WaterQualityForecastPoint` objects with forecast_time, water_pH,
      TDS, and water_temp for each predicted hour.
    """
    # 1. Check that the model is loaded
    if not prediction_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "LSTM prediction model is not loaded. "
                "Check that model artifacts are mounted correctly and the server "
                "started without errors."
            ),
        )

    # 2. Fetch recent historical data from DB
    try:
        recent_data, last_timestamp = (
            await sensor_service.get_recent_water_metrics_for_prediction(
                db, device_id, lookback=settings.ML_LOOKBACK
            )
        )
    except ValueError as exc:
        logger.warning("Insufficient data for prediction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "DB error while fetching prediction data for device %s: %s",
            device_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sensor data for prediction.",
        ) from exc

    # 3. Run LSTM inference (CPU-bound but fast; no need for run_in_executor
    #    for a ~24-step sliding-window prediction)
    try:
        forecasts = prediction_service.predict(
            recent_data=recent_data,
            steps=steps,
            last_timestamp=last_timestamp,
        )
    except RuntimeError as exc:
        logger.error("Prediction service error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Unexpected error during LSTM inference for device %s: %s",
            device_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LSTM inference failed.",
        ) from exc

    # 4. Build and return response
    return WaterQualityForecastResponse(
        device_id=device_id,
        generated_at=datetime.now(timezone.utc),
        input_points=len(recent_data),
        forecast_steps=steps,
        forecasts=forecasts,
    )
