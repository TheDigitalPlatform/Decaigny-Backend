from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import crud_role as role_crud
from app.schemas.role import RoleCreate, RoleUpdate

router = APIRouter()


@router.get("")
def read_roles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    roles = role_crud.get_roles(db, skip=skip, limit=limit)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Roles fetched successfully",
            "data": jsonable_encoder(roles),
        },
    )


@router.get("/{role_id}")
def read_role(role_id: int, db: Session = Depends(get_db)):
    db_role = role_crud.get_role(db, role_id=role_id)
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Role fetched successfully",
            "data": jsonable_encoder(db_role),
        },
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_role(role_in: RoleCreate, db: Session = Depends(get_db)):
    existing_role = role_crud.get_role_by_name(db, name=role_in.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists",
        )
    created_role = role_crud.create_role(db, role_in=role_in)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Role created successfully",
            "data": jsonable_encoder(created_role),
        },
    )


@router.put("/{role_id}")
def update_role(role_id: int, role_in: RoleUpdate, db: Session = Depends(get_db)):
    db_role = role_crud.get_role(db, role_id=role_id)
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    if role_in.name and role_in.name != db_role.name:
        existing_role = role_crud.get_role_by_name(db, name=role_in.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists",
            )

    updated_role = role_crud.update_role(db, db_role=db_role, role_in=role_in)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Role updated successfully",
            "data": jsonable_encoder(updated_role),
        },
    )


@router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    db_role = role_crud.get_role(db, role_id=role_id)
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    deleted_role = role_crud.delete_role(db, db_role=db_role)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Role deleted successfully",
            "data": jsonable_encoder(deleted_role),
        },
    )
