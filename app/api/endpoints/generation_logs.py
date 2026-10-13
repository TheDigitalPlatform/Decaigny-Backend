import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_from_db, get_db
from app.crud.crud_ai_generation_log import get_log, get_logs, get_logs_count
from app.models.user import User as UserModel
from app.schemas.generated_post import AIGenerationLogDetail, AIGenerationLogRead

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
def list_generation_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    vehicle_id: Optional[int] = Query(default=None),
    log_status: Optional[str] = Query(default=None, alias="status"),
    post_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    logs = get_logs(db, skip=skip, limit=limit, vehicle_id=vehicle_id, status=log_status, post_type=post_type)
    data = [AIGenerationLogRead.model_validate(log).model_dump(mode="json") for log in logs]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "AI generation logs fetched successfully",
            "data": data,
            "meta": {"total": get_logs_count(db, vehicle_id=vehicle_id, status=log_status, post_type=post_type), "skip": skip, "limit": limit},
        },
    )


@router.get("/{log_id}", status_code=status.HTTP_200_OK)
def get_generation_log(
    log_id: int,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    log = get_log(db, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation log not found")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "message": "AI generation log fetched successfully", "data": AIGenerationLogDetail.model_validate(log).model_dump(mode="json")},
    )
