import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_from_db
from app.crud import crud_vehicle
from app.models.user import User as UserModel
from app.schemas.vehicle import VehicleRead, VehicleDetailRead

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
def list_vehicles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    vehicle_status: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by status (available, sold, etc.)",
    ),
    is_new_to_us: Optional[bool] = Query(default=None, description="Filter by newly imported status"),
    search: Optional[str] = Query(default=None, description="Search term for make, model, VIN, or stock number"),
    make: Optional[str] = Query(default=None, description="Filter by make"),
    model: Optional[str] = Query(default=None, description="Filter by model"),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    """
    List vehicles with optional filtering and pagination.
    """
    vehicles = crud_vehicle.get_vehicles(
        db=db,
        skip=skip,
        limit=limit,
        status=vehicle_status,
        is_new_to_us=is_new_to_us,
        search=search,
        make=make,
        model=model,
    )
    total = crud_vehicle.get_vehicles_count(
        db=db,
        status=vehicle_status,
        is_new_to_us=is_new_to_us,
        search=search,
        make=make,
        model=model,
    )
    data = [VehicleRead.model_validate(v).model_dump(mode="json") for v in vehicles]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Vehicles fetched successfully",
            "data": data,
            "meta": {
                "total": total,
                "skip": skip,
                "limit": limit,
            },
        },
    )


@router.get("/new", status_code=status.HTTP_200_OK)
def list_new_vehicles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    """
    List vehicles newly introduced to stock (is_new_to_us=true).
    Used by n8n workflow for post generation / hooks.
    """
    new_vehicles = crud_vehicle.get_new_vehicles(db=db, skip=skip, limit=limit)
    data = [VehicleRead.model_validate(v).model_dump(mode="json") for v in new_vehicles]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "New vehicles fetched successfully",
            "data": data,
        },
    )


@router.get("/sold", status_code=status.HTTP_200_OK)
def list_sold_vehicles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    """
    List vehicles marked as sold (status=sold).
    Used by n8n workflow for sold hooks.
    """
    sold_vehicles = crud_vehicle.get_sold_vehicles(db=db, skip=skip, limit=limit)
    data = [VehicleRead.model_validate(v).model_dump(mode="json") for v in sold_vehicles]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Sold vehicles fetched successfully",
            "data": data,
        },
    )


@router.get("/{id}", status_code=status.HTTP_200_OK)
def get_vehicle_detail(
    id: int,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    """
    Retrieve single vehicle details including image URLs.
    """
    vehicle = crud_vehicle.get_vehicle(db=db, vehicle_id=id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    data = VehicleDetailRead.model_validate(vehicle).model_dump(mode="json")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Vehicle retrieved successfully",
            "data": data,
        },
    )

