import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user_from_db, get_db
from app.crud import crud_generated_post, crud_settings, crud_vehicle
from app.models.user import User as UserModel
from app.schemas.generated_post import GeneratePostRequest, GeneratedPostRead, PostConfigUpdate
from app.schemas.vehicle import VehicleRead
from app.services.post_generation_service import service as post_generation_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config", status_code=status.HTTP_200_OK)
def get_post_config(
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    profile = None
    try:
        from app.crud import crud_dealership_profile

        profile = crud_dealership_profile.get_active(db)
    except Exception:
        profile = None

    default_language = profile.default_language if profile else settings.AI_DEFAULT_LANGUAGE
    new_vehicle_tone = crud_settings.get_ai_tone_for_post_type(db, "new_vehicle")
    sold_vehicle_tone = crud_settings.get_ai_tone_for_post_type(db, "sold_vehicle")
    default_tone = crud_settings.get_default_communication_style(db)
    data = {
        "ai_enabled": True,
        "default_language": default_language,
        "new_vehicle_tone": new_vehicle_tone,
        "sold_vehicle_tone": sold_vehicle_tone,
        "default_communication_style": default_tone,
        "batch_limit": getattr(settings, "AI_PENDING_BATCH_LIMIT", 10),
        "pending_max_age_days": getattr(settings, "AI_PENDING_MAX_AGE_DAYS", 7),
        "max_failures_per_vehicle": getattr(settings, "AI_MAX_FAILURES_PER_VEHICLE", 6),
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "message": "AI post config fetched successfully", "data": data},
    )


@router.put("/config", status_code=status.HTTP_200_OK)
def update_post_config(
    payload: PostConfigUpdate,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    if payload.new_vehicle_tone:
        crud_settings.set_ai_tone_for_post_type(db, "new_vehicle", str(payload.new_vehicle_tone))
    if payload.sold_vehicle_tone:
        crud_settings.set_ai_tone_for_post_type(db, "sold_vehicle", str(payload.sold_vehicle_tone))
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "AI post config updated successfully",
            "data": {
                "new_vehicle_tone": crud_settings.get_ai_tone_for_post_type(db, "new_vehicle"),
                "sold_vehicle_tone": crud_settings.get_ai_tone_for_post_type(db, "sold_vehicle"),
            },
        },
    )


@router.get("/pending", status_code=status.HTTP_200_OK)
def list_pending_posts(
    post_type: str = Query(default="new_vehicle"),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    max_age = getattr(settings, "AI_PENDING_MAX_AGE_DAYS", 7)
    since = datetime.now(timezone.utc) - timedelta(days=max_age)
    vehicles = crud_vehicle.get_vehicles_pending_post(
        db,
        post_type=post_type,
        since=since,
        limit=limit,
        max_failures=getattr(settings, "AI_MAX_FAILURES_PER_VEHICLE", 6),
    )
    payload = [VehicleRead.model_validate(v).model_dump(mode="json") for v in vehicles]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "message": "Pending vehicles fetched successfully", "data": payload},
    )


@router.get("", status_code=status.HTTP_200_OK)
def list_posts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    vehicle_id: Optional[int] = Query(default=None),
    post_type: Optional[str] = Query(default=None),
    post_status: Optional[str] = Query(default=None, alias="status"),
    current_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    posts = crud_generated_post.get_posts(
        db,
        skip=skip,
        limit=limit,
        vehicle_id=vehicle_id,
        post_type=post_type,
        status=post_status,
        current_only=current_only,
    )
    data = [GeneratedPostRead.model_validate(post).model_dump(mode="json") for post in posts]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Generated posts fetched successfully",
            "data": data,
            "meta": {"total": crud_generated_post.get_posts_count(db, vehicle_id=vehicle_id, post_type=post_type, status=post_status, current_only=current_only), "skip": skip, "limit": limit},
        },
    )


@router.get("/{post_id}", status_code=status.HTTP_200_OK)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    post = crud_generated_post.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated post not found")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "message": "Generated post fetched successfully", "data": GeneratedPostRead.model_validate(post).model_dump(mode="json")},
    )


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_post(
    payload: GeneratePostRequest,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    vehicle = crud_vehicle.get_vehicle(db, payload.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    result = post_generation_service.generate_post_for_vehicle(
        db,
        vehicle,
        post_type=None if payload.post_type == "auto" else payload.post_type,
        tone=payload.tone,
        tone_id=payload.tone_id,
        language=payload.language,
        source=payload.source,
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"success": True, "message": "Post generated successfully", "data": result},
    )
