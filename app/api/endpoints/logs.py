import logging

from fastapi import APIRouter, Depends, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.deps import get_current_user_from_db
from app.schemas.log import LogLinesResponse
from app.services.log_service import LogService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
def read_app_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    _current_user=Depends(get_current_user_from_db),
):
    logger.info("Fetching app log lines | skip=%s, limit=%s", skip, limit)
    lines, total = LogService.read_log_lines(skip=skip, limit=limit)

    payload = LogLinesResponse(
        lines=lines,
        total=total,
        skip=skip,
        limit=limit,
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Log lines fetched successfully",
            "data": jsonable_encoder(payload),
        },
    )
