import logging
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_from_db
from app.crud import crud_vehicle_sync
from app.models.user import User as UserModel
from app.schemas.vehicle import VehicleSyncPullRequest, VehicleSyncRead
from app.services.vehicle_sync_service import vehicle_sync_service
from app.services.ydd_client import YDDClientError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/pull", status_code=status.HTTP_200_OK)
def trigger_sync_pull(
    request_body: Optional[VehicleSyncPullRequest] = Body(default=None),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    """
    Trigger manual or n8n-scheduled sync from YDD ERP into Decaigny DB.
    Requires valid JWT token.
    """
    mark_missing_as_sold = True
    filter_param = None
    source = "n8n"
    if request_body:
        mark_missing_as_sold = request_body.mark_missing_as_sold
        filter_param = request_body.filter
        if request_body.source:
            source = request_body.source

    logger.info(
        "User %s initiated sync pull | source=%s, mark_missing_as_sold=%s, filter=%s",
        _current_user.email,
        source,
        mark_missing_as_sold,
        filter_param,
    )

    try:
        result = vehicle_sync_service.sync_inventory(
            db=db,
            source=source,
            mark_missing_as_sold=mark_missing_as_sold,
            filter_param=filter_param,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Sync completed",
                "data": jsonable_encoder(result),
            },
        )
    except YDDClientError as ydd_err:
        logger.error("YDD client error during sync pull: %s", ydd_err)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"YDD ERP synchronization failed: {ydd_err}",
                "data": {
                    "status_code": ydd_err.status_code or 500,
                    "response": ydd_err.response_text,
                },
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error during sync pull: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Sync process failed: {str(exc)}",
                "data": None,
            },
        )


@router.get("/health", status_code=status.HTTP_200_OK)
def check_sync_health(
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    """
    Check connectivity between Decaigny backend and Your Daily Drive API (/me, /stats).
    Requires valid JWT token.
    """
    logger.info("Sync health check requested by %s", _current_user.email)
    try:
        health_data = vehicle_sync_service.check_health()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "YDD connectivity healthy",
                "data": jsonable_encoder(health_data),
            },
        )
    except YDDClientError as ydd_err:
        logger.error("YDD connectivity check failed: %s", ydd_err)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "success": False,
                "message": f"YDD health check failed: {ydd_err}",
                "data": {
                    "status_code": ydd_err.status_code or 502,
                    "response": ydd_err.response_text,
                },
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error during sync health check: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": f"YDD connectivity check failed: {str(exc)}",
                "data": None,
            },
        )


@router.get("/runs", status_code=status.HTTP_200_OK)
def list_sync_runs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    """
    List sync history and runs.
    """
    runs = crud_vehicle_sync.get_syncs(db=db, skip=skip, limit=limit)
    data = [VehicleSyncRead.model_validate(r).model_dump(mode="json") for r in runs]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Sync runs retrieved successfully",
            "data": data,
        },
    )


@router.get("/runs/{id}", status_code=status.HTTP_200_OK)
def get_sync_run(
    id: int,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    """
    Retrieve single sync run detail by ID.
    """
    run = crud_vehicle_sync.get_sync(db=db, sync_id=id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync run not found",
        )
    data = VehicleSyncRead.model_validate(run).model_dump(mode="json")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Sync run detail retrieved successfully",
            "data": data,
        },
    )

