from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.vehicle_sync import VehicleSync


def get_sync(db: Session, sync_id: int) -> Optional[VehicleSync]:
    return db.query(VehicleSync).filter(VehicleSync.id == sync_id).first()


def get_syncs(db: Session, skip: int = 0, limit: int = 50) -> List[VehicleSync]:
    return (
        db.query(VehicleSync)
        .order_by(VehicleSync.started_at.desc(), VehicleSync.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_running(
    db: Session, source: str = "n8n", meta: Optional[Dict[str, Any]] = None
) -> VehicleSync:
    now = datetime.now(timezone.utc)
    sync_obj = VehicleSync(
        source=source,
        status="running",
        started_at=now,
        meta=meta or {},
    )
    db.add(sync_obj)
    db.commit()
    db.refresh(sync_obj)
    return sync_obj


def finish_success(
    db: Session,
    sync_obj: VehicleSync,
    fetched_count: int,
    created_count: int,
    updated_count: int,
    sold_count: int,
    skipped_count: int,
    meta: Optional[Dict[str, Any]] = None,
) -> VehicleSync:
    now = datetime.now(timezone.utc)
    sync_obj.status = "success"
    sync_obj.finished_at = now
    sync_obj.fetched_count = fetched_count
    sync_obj.created_count = created_count
    sync_obj.updated_count = updated_count
    sync_obj.sold_count = sold_count
    sync_obj.skipped_count = skipped_count
    if meta:
        existing_meta = sync_obj.meta or {}
        existing_meta.update(meta)
        sync_obj.meta = existing_meta
    db.add(sync_obj)
    db.commit()
    db.refresh(sync_obj)
    return sync_obj


def finish_failed(
    db: Session,
    sync_obj: VehicleSync,
    error_message: str,
    fetched_count: int = 0,
    created_count: int = 0,
    updated_count: int = 0,
    sold_count: int = 0,
    skipped_count: int = 0,
    meta: Optional[Dict[str, Any]] = None,
) -> VehicleSync:
    now = datetime.now(timezone.utc)
    sync_obj.status = "failed"
    sync_obj.finished_at = now
    sync_obj.error_message = error_message
    sync_obj.fetched_count = fetched_count
    sync_obj.created_count = created_count
    sync_obj.updated_count = updated_count
    sync_obj.sold_count = sold_count
    sync_obj.skipped_count = skipped_count
    if meta:
        existing_meta = sync_obj.meta or {}
        existing_meta.update(meta)
        sync_obj.meta = existing_meta
    db.add(sync_obj)
    db.commit()
    db.refresh(sync_obj)
    return sync_obj
