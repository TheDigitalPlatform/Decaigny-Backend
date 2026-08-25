from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptUpdate


def get_prompt(db: Session, prompt_id: int) -> Optional[Prompt]:
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()


def get_prompt_by_name(db: Session, name: str) -> Optional[Prompt]:
    return db.query(Prompt).filter(Prompt.name == name).first()


def get_prompts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    search: Optional[str] = None,
) -> List[Prompt]:
    query = db.query(Prompt)
    if active_only:
        query = query.filter(Prompt.is_active.is_(True))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Prompt.name.ilike(search_pattern))
            | (Prompt.description.ilike(search_pattern))
            | (Prompt.content.ilike(search_pattern))
        )
    return query.order_by(Prompt.id).offset(skip).limit(limit).all()



def create_prompt(db: Session, prompt_in: PromptCreate) -> Prompt:
    db_obj = Prompt(
        name=prompt_in.name,
        content=prompt_in.content,
        description=prompt_in.description,
        is_active=prompt_in.is_active,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_prompt(
    db: Session, db_prompt: Prompt, prompt_in: PromptUpdate
) -> Prompt:
    update_data = prompt_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_prompt, field, value)
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def delete_prompt(db: Session, db_prompt: Prompt) -> Prompt:
    db.delete(db_prompt)
    db.commit()
    return db_prompt
