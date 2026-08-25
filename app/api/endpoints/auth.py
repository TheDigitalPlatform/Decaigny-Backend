from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.deps import authenticate_user, get_db
from app.auth.jwt import create_access_token, create_refresh_token, decode_token, get_password_hash
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.validation import validate_body_dict, validate_request_body


router = APIRouter()


@router.post("/register")
async def register_user(
    register_data: RegisterRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Register a new user account.
    Assigns the default 'user' role on creation.
    """
    errors = validate_body_dict(
        register_data.model_dump(),
        ["name", "email", "password"],
    )
    if errors:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"errors": [e.model_dump() for e in errors]},
        )

    existing_user = db.query(User).filter(User.email == register_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    default_role = db.query(Role).filter(Role.name == "user").first()
    if not default_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default role not found. Please contact the administrator.",
        )

    user = User(
        name=register_data.name,
        email=register_data.email,
        hashed_password=get_password_hash(register_data.password),
        role_id=default_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Registration successful",
            "data": jsonable_encoder({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role_id": user.role_id,
            }),
        },
    )


@router.post("/login")
async def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Authenticate a user and return access and refresh tokens.
    Returns 401 if the credentials are invalid.
    """
    errors = validate_body_dict(
        login_data.model_dump(),
        ["email", "password"],
    )
    if errors:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"errors": [e.model_dump() for e in errors]},
        )

    user = authenticate_user(login_data.email, login_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = {
        "sub": user.email,
        "user_id": str(user.id),
        "role": user.role.name if user.role else None,
    }
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Login successful",
            "data": jsonable_encoder({
                "access_token": access_token,
                "token_type": "bearer",
                "refresh_token": refresh_token,
            }),
        },
    )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Issue a new access token and refresh token using a valid refresh token.
    Returns 401 if the refresh token is invalid or the user no longer exists.
    """
    errors = await validate_request_body(request, ["refresh_token"])
    if errors:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"errors": [e.model_dump() for e in errors]},
        )

    body = await request.json()

    try:
        token_data = decode_token(body["refresh_token"])

        user = db.query(User).filter(User.email == token_data.email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_payload = {
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role.name if user.role else None,
        }
        access_token = create_access_token(data=token_payload)
        new_refresh_token = create_refresh_token(data=token_payload)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Token refreshed successfully",
                "data": jsonable_encoder({
                    "access_token": access_token,
                    "token_type": "bearer",
                    "refresh_token": new_refresh_token,
                }),
            },
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
