from typing import List, Optional

from sqlalchemy.orm import Session

from app.auth.jwt import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def get_users_count(db: Session) -> int:
    return db.query(User).count()



def create_user(db: Session, user_in: UserCreate) -> User:
    db_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role_id=user_in.role_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_obj: User, obj_in: UserUpdate) -> User:
    update_data = obj_in.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_user(db: Session, db_obj: User) -> User:
    db.delete(db_obj)
    db.commit()
    return db_obj