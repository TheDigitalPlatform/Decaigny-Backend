from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.generated_post import GeneratedPost


def get_post(db: Session, post_id: int) -> Optional[GeneratedPost]:
    return db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()


def get_current_post(db: Session, vehicle_id: int, post_type: str) -> Optional[GeneratedPost]:
    return (
        db.query(GeneratedPost)
        .filter(
            GeneratedPost.vehicle_id == vehicle_id,
            GeneratedPost.post_type == post_type,
            GeneratedPost.is_current.is_(True),
        )
        .first()
    )


def _filtered(query, vehicle_id, post_type, status, current_only):
    if vehicle_id is not None:
        query = query.filter(GeneratedPost.vehicle_id == vehicle_id)
    if post_type:
        query = query.filter(GeneratedPost.post_type == post_type)
    if status:
        query = query.filter(GeneratedPost.status == status)
    if current_only:
        query = query.filter(GeneratedPost.is_current.is_(True))
    return query


def get_posts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    vehicle_id: Optional[int] = None,
    post_type: Optional[str] = None,
    status: Optional[str] = None,
    current_only: bool = True,
) -> List[GeneratedPost]:
    query = _filtered(db.query(GeneratedPost), vehicle_id, post_type, status, current_only)
    return query.order_by(GeneratedPost.created_at.desc(), GeneratedPost.id.desc()).offset(skip).limit(limit).all()


def get_posts_count(
    db: Session,
    vehicle_id: Optional[int] = None,
    post_type: Optional[str] = None,
    status: Optional[str] = None,
    current_only: bool = True,
) -> int:
    query = _filtered(db.query(func.count(GeneratedPost.id)), vehicle_id, post_type, status, current_only)
    return query.scalar() or 0


def create_post_version(db: Session, *, vehicle_id: int, post_type: str, values: Dict[str, Any]) -> GeneratedPost:
    previous = get_current_post(db, vehicle_id, post_type)
    version = 1
    if previous:
        previous.is_current = False
        db.add(previous)
        version = previous.version + 1
        db.flush()

    post = GeneratedPost(vehicle_id=vehicle_id, post_type=post_type, version=version, is_current=True, **values)
    db.add(post)
    db.flush()
    return post
