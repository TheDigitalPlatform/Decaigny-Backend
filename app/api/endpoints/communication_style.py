import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_from_db, get_db
from app.crud import crud_prompt, crud_settings
from app.schemas.communication_style import (
    CommunicationStyleItem,
    DefaultCommunicationStyleResponse,
    SetDefaultCommunicationStyleRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
def list_communication_styles(
    active_only: bool = Query(default=False),
    prompt_type: Optional[str] = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user_from_db),
) -> Any:
    """List tone prompts available for draft generation."""
    logger.info("Listing communication styles | active_only=%s | prompt_type=%s", active_only, prompt_type)
    prompts = crud_prompt.get_prompts(db, active_only=active_only, prompt_type=prompt_type)

    default_val = crud_settings.get_default_communication_style(db)

    items = []
    for prompt in prompts:
        is_def = False
        if default_val:
            if default_val.isdigit() and int(default_val) == prompt.id:
                is_def = True
            elif default_val.strip().lower() == prompt.name.strip().lower():
                is_def = True

        item = CommunicationStyleItem(
            id=prompt.id,
            name=prompt.name,
            description=prompt.description,
            is_active=prompt.is_active,
            is_default=is_def,
        )
        items.append(item)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Communication styles fetched successfully",
            "data": jsonable_encoder(items),
        },
    )


@router.get("/default", status_code=status.HTTP_200_OK)
def get_default_communication_style(
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user_from_db),
) -> Any:
    """Get the current standard tone setting."""
    default_val = crud_settings.get_default_communication_style(db)
    prompt_id = None
    name = None

    if default_val:
        if default_val.isdigit():
            p = crud_prompt.get_prompt(db, int(default_val))
            if p and p.is_active:
                prompt_id = p.id
                name = p.name
        else:
            p = crud_prompt.get_prompt_by_name(db, default_val)
            if p and p.is_active:
                prompt_id = p.id
                name = p.name

    payload = DefaultCommunicationStyleResponse(prompt_id=prompt_id, name=name)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Default communication style fetched successfully",
            "data": jsonable_encoder(payload),
        },
    )


@router.put("/default", status_code=status.HTTP_200_OK)
def set_default_communication_style(
    payload: SetDefaultCommunicationStyleRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user_from_db),
) -> Any:
    """Set the standard tone setting (requires valid active prompt)."""
    target_prompt = None
    if payload.prompt_id is not None:
        target_prompt = crud_prompt.get_prompt(db, payload.prompt_id)
    elif payload.name:
        target_prompt = crud_prompt.get_prompt_by_name(db, payload.name)

    if not target_prompt or not target_prompt.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected tone prompt does not exist or is inactive",
        )

    crud_settings.set_default_communication_style(db, str(target_prompt.id))
    logger.info("Updated default communication style to prompt_id=%s (%s)", target_prompt.id, target_prompt.name)

    res = DefaultCommunicationStyleResponse(
        prompt_id=target_prompt.id, name=target_prompt.name
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": f"Default communication style set to '{target_prompt.name}'",
            "data": jsonable_encoder(res),
        },
    )
