import logging
from typing import Annotated

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]  
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.threshold import ThresholdCreate, ThresholdUpdate, ThresholdResponse
from app.services import threshold_service, device_service

logger = logging.getLogger(__name__)

router = APIRouter()

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "/{device_id}/thresholds",
    response_model=list[ThresholdResponse],
    summary="Lấy tất cả ngưỡng của 1 device",
)
async def list_thresholds(device_id: str, db: DbDep):
    """Trả về danh sách ngưỡng cảnh báo/tự động của device, sắp xếp theo metric_type."""
    device = await device_service.get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found.",
        )
    return await threshold_service.get_by_device(db, device_id)


@router.put(
    "/{device_id}/thresholds/{metric_type}",
    response_model=ThresholdResponse,
    summary="Tạo hoặc thay thế ngưỡng cho 1 metric",
)
async def upsert_threshold(
    device_id: str,
    metric_type: str,
    body: ThresholdCreate,
    db: DbDep,
):
    """
    Nếu ngưỡng cho `metric_type` chưa tồn tại → tạo mới.
    Nếu đã tồn tại → thay thế toàn bộ.
    """
    device = await device_service.get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found.",
        )
    threshold = await threshold_service.upsert_threshold(
        db, device_id, metric_type, body.model_dump()
    )
    return threshold


@router.patch(
    "/{device_id}/thresholds/{metric_type}",
    response_model=ThresholdResponse,
    summary="Cập nhật một phần ngưỡng (ví dụ: bật/tắt auto_action)",
)
async def patch_threshold(
    device_id: str,
    metric_type: str,
    body: ThresholdUpdate,
    db: DbDep,
):
    """Chỉ cập nhật các field được cung cấp, các field còn lại giữ nguyên."""
    threshold = await threshold_service.get_by_metric(db, device_id, metric_type)
    if threshold is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threshold for metric '{metric_type}' on device '{device_id}' not found.",
        )
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return await threshold_service.patch_threshold(db, threshold, data)


@router.delete(
    "/{device_id}/thresholds/{metric_type}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa ngưỡng của 1 metric",
)
async def delete_threshold(device_id: str, metric_type: str, db: DbDep):
    threshold = await threshold_service.get_by_metric(db, device_id, metric_type)
    if threshold is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threshold for metric '{metric_type}' on device '{device_id}' not found.",
        )
    await threshold_service.delete_threshold(db, threshold)
