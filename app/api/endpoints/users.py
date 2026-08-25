from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user_from_db, require_admin
from app.models.user import User as UserModel
from app.crud.crud_user import (
    create_user,
    get_user,
    get_user_by_email,
    get_users,
    get_users_count,
    update_user,
    delete_user,
)
from app.schemas.user import UserCreate, UserUpdate, UserProfileUpdate


router = APIRouter()


def _user_data(user: UserModel) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role_id": user.role_id,
        "role": jsonable_encoder(user.role),
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


# ---------------------------------------------------------------------------
# Admin-only CRUD
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED)
def create_user_admin(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> Any:
    existing = get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    new_user = create_user(db, user_in=user_in)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "User created successfully",
            "data": jsonable_encoder(_user_data(new_user)),
        },
    )


@router.get("")
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> Any:
    users = get_users(db, skip=skip, limit=limit)
    total = get_users_count(db)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Users fetched successfully",
            "data": {
                "items": jsonable_encoder([_user_data(u) for u in users]),
                "total": total,
            },
        },
    )



@router.get("/list")
def list_users_basic(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    users = get_users(db, skip=0, limit=10000)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Users fetched successfully",
            "data": [{"id": u.id, "name": u.name} for u in users],
        },
    )


@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    db_user = get_user(db, user_id=current_user.id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Profile fetched successfully",
            "data": jsonable_encoder(_user_data(db_user)),
        },
    )


@router.put("/profile")
def update_profile(
    user_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    db_user = get_user(db, user_id=current_user.id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user_in.email and user_in.email != db_user.email:
        existing = get_user_by_email(db, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
    updated_user = update_user(db, db_obj=db_user, obj_in=user_in)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Profile updated successfully",
            "data": jsonable_encoder(_user_data(updated_user)),
        },
    )


@router.get("/{user_id}")
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> Any:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "User fetched successfully",
            "data": jsonable_encoder(_user_data(db_user)),
        },
    )


@router.put("/{user_id}")
def update_user_admin(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> Any:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user_in.email and user_in.email != db_user.email:
        existing = get_user_by_email(db, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
    updated_user = update_user(db, db_obj=db_user, obj_in=user_in)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "User updated successfully",
            "data": jsonable_encoder(_user_data(updated_user)),
        },
    )


@router.delete("/{user_id}")
def delete_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> Any:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    data = jsonable_encoder(_user_data(db_user))
    delete_user(db, db_obj=db_user)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "User deleted successfully",
            "data": data,
        },
    )
