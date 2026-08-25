from typing import Optional

from sqlalchemy.orm import Session

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


def get_role(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> list[Role]:
    return db.query(Role).offset(skip).limit(limit).all()


def create_role(db: Session, role_in: RoleCreate) -> Role:
    db_role = Role(name=role_in.name, description=role_in.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def update_role(db: Session, db_role: Role, role_in: RoleUpdate) -> Role:
    update_data = role_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_role, field, value)

    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def delete_role(db: Session, db_role: Role) -> Role:
    db.delete(db_role)
    db.commit()
    return db_role

