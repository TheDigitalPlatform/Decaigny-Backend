import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_from_db
from app.crud import crud_prompt as prompt_crud
from app.models.user import User as UserModel
from app.schemas.prompt import PromptCreate, PromptUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_prompt(
    prompt_in: PromptCreate,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    logger.info("Creating new prompt: %s", prompt_in.name)
    existing = prompt_crud.get_prompt_by_name(db, name=prompt_in.name)
    if existing:
        logger.warning("Prompt creation failed - name already exists: %s", prompt_in.name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt with this name already exists",
        )
    created = prompt_crud.create_prompt(db, prompt_in=prompt_in)
    logger.info("Prompt created successfully | id=%s, name=%s", created.id, created.name)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Prompt created successfully",
            "data": jsonable_encoder(created),
        },
    )


@router.get("")
def list_prompts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    active_only: bool = Query(default=False),
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    logger.info("Listing prompts | skip=%s, limit=%s, active_only=%s, search=%s", skip, limit, active_only, search)
    prompts = prompt_crud.get_prompts(
        db, skip=skip, limit=limit, active_only=active_only, search=search
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Prompts fetched successfully",
            "data": jsonable_encoder(prompts),
        },
    )


@router.get("/by-name/{name}")
def read_prompt_by_name(
    name: str,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    logger.info("Reading prompt by name: %s", name)
    db_prompt = prompt_crud.get_prompt_by_name(db, name=name)
    if not db_prompt:
        logger.warning("Prompt not found for name: %s", name)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Prompt fetched successfully",
            "data": jsonable_encoder(db_prompt),
        },
    )


@router.get("/{prompt_id}")
def read_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    logger.info("Reading prompt by id: %s", prompt_id)
    db_prompt = prompt_crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        logger.warning("Prompt not found for id: %s", prompt_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Prompt fetched successfully",
            "data": jsonable_encoder(db_prompt),
        },
    )


@router.put("/{prompt_id}")
def update_prompt(
    prompt_id: int,
    prompt_in: PromptUpdate,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    logger.info("Updating prompt id: %s", prompt_id)
    db_prompt = prompt_crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        logger.warning("Update failed - prompt not found for id: %s", prompt_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    if prompt_in.name and prompt_in.name != db_prompt.name:
        conflict = prompt_crud.get_prompt_by_name(db, name=prompt_in.name)
        if conflict:
            logger.warning("Update failed - prompt name conflict: %s", prompt_in.name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt with this name already exists",
            )

    updated = prompt_crud.update_prompt(db, db_prompt=db_prompt, prompt_in=prompt_in)
    logger.info("Prompt updated successfully | id=%s", updated.id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Prompt updated successfully",
            "data": jsonable_encoder(updated),
        },
    )


@router.delete("/{prompt_id}")
def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    _current_user: UserModel = Depends(get_current_user_from_db),
) -> Any:
    logger.info("Deleting prompt id: %s", prompt_id)
    db_prompt = prompt_crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        logger.warning("Delete failed - prompt not found for id: %s", prompt_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    deleted = prompt_crud.delete_prompt(db, db_prompt=db_prompt)
    logger.info("Prompt deleted successfully | id=%s", deleted.id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Prompt deleted successfully",
            "data": jsonable_encoder(deleted),
        },
    )
