import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_from_db, get_db
from app.crud import crud_dealership_profile
from app.models.user import User as UserModel
from app.schemas.generated_post import DealershipProfileRead, DealershipProfileUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
def get_dealership_profile(
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    profile = crud_dealership_profile.get_active(db)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dealership profile not found")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "message": "Dealership profile fetched successfully", "data": DealershipProfileRead.model_validate(profile).model_dump(mode="json")},
    )


@router.put("", status_code=status.HTTP_200_OK)
def update_dealership_profile(
    payload: DealershipProfileUpdate,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    profile = crud_dealership_profile.get_active(db)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dealership profile not found")
    values = payload.model_dump(exclude_unset=True)
    updated = crud_dealership_profile.update_profile(db, profile, values)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "message": "Dealership profile updated successfully", "data": DealershipProfileRead.model_validate(updated).model_dump(mode="json")},
    )
