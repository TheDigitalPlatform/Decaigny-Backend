from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_generation_log import AIGenerationLog


def create_log(db: Session, **values) -> AIGenerationLog:
    log = AIGenerationLog(**values)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_log(db: Session, log_id: int) -> Optional[AIGenerationLog]:
    return db.query(AIGenerationLog).filter(AIGenerationLog.id == log_id).first()


def _filtered(query, vehicle_id, status, post_type):
    if vehicle_id is not None:
        query = query.filter(AIGenerationLog.vehicle_id == vehicle_id)
    if status:
        query = query.filter(AIGenerationLog.status == status)
    if post_type:
        query = query.filter(AIGenerationLog.post_type == post_type)
    return query


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    vehicle_id: Optional[int] = None,
    status: Optional[str] = None,
    post_type: Optional[str] = None,
) -> List[AIGenerationLog]:
    query = _filtered(db.query(AIGenerationLog), vehicle_id, status, post_type)
    return query.order_by(AIGenerationLog.created_at.desc(), AIGenerationLog.id.desc()).offset(skip).limit(limit).all()


def get_logs_count(
    db: Session,
    vehicle_id: Optional[int] = None,
    status: Optional[str] = None,
    post_type: Optional[str] = None,
) -> int:
    return _filtered(db.query(func.count(AIGenerationLog.id)), vehicle_id, status, post_type).scalar() or 0
