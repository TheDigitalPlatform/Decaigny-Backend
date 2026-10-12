from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.vehicle import Vehicle


def get_vehicle(db: Session, vehicle_id: int) -> Optional[Vehicle]:
    return (
        db.query(Vehicle)
        .options(joinedload(Vehicle.images))
        .filter(Vehicle.id == vehicle_id)
        .first()
    )


def get_by_erp_id(db: Session, erp_id: str) -> Optional[Vehicle]:
    return (
        db.query(Vehicle)
        .options(joinedload(Vehicle.images))
        .filter(Vehicle.erp_id == erp_id)
        .first()
    )


def get_by_vin(db: Session, vin: str) -> Optional[Vehicle]:
    return (
        db.query(Vehicle)
        .options(joinedload(Vehicle.images))
        .filter(Vehicle.vin == vin)
        .first()
    )


def get_vehicles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    is_new_to_us: Optional[bool] = None,
    search: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
) -> List[Vehicle]:
    query = db.query(Vehicle).options(joinedload(Vehicle.images))
    if status:
        query = query.filter(Vehicle.status == status)
    if is_new_to_us is not None:
        query = query.filter(Vehicle.is_new_to_us.is_(is_new_to_us))
    if make:
        query = query.filter(Vehicle.make.ilike(f"%{make}%"))
    if model:
        query = query.filter(Vehicle.model.ilike(f"%{model}%"))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Vehicle.make.ilike(search_pattern))
            | (Vehicle.model.ilike(search_pattern))
            | (Vehicle.vin.ilike(search_pattern))
            | (Vehicle.stock_number.ilike(search_pattern))
            | (Vehicle.erp_id.ilike(search_pattern))
        )
    return (
        query.order_by(Vehicle.updated_at.desc(), Vehicle.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_vehicles_count(
    db: Session,
    status: Optional[str] = None,
    is_new_to_us: Optional[bool] = None,
    search: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
) -> int:
    query = db.query(func.count(Vehicle.id))
    if status:
        query = query.filter(Vehicle.status == status)
    if is_new_to_us is not None:
        query = query.filter(Vehicle.is_new_to_us.is_(is_new_to_us))
    if make:
        query = query.filter(Vehicle.make.ilike(f"%{make}%"))
    if model:
        query = query.filter(Vehicle.model.ilike(f"%{model}%"))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Vehicle.make.ilike(search_pattern))
            | (Vehicle.model.ilike(search_pattern))
            | (Vehicle.vin.ilike(search_pattern))
            | (Vehicle.stock_number.ilike(search_pattern))
            | (Vehicle.erp_id.ilike(search_pattern))
        )
    return query.scalar() or 0


def get_new_vehicles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[Vehicle]:
    return (
        db.query(Vehicle)
        .options(joinedload(Vehicle.images))
        .filter(Vehicle.is_new_to_us.is_(True))
        .order_by(Vehicle.created_at.desc(), Vehicle.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_sold_vehicles(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[Vehicle]:
    return (
        db.query(Vehicle)
        .options(joinedload(Vehicle.images))
        .filter(Vehicle.status == "sold")
        .order_by(Vehicle.sold_at.desc().nullslast(), Vehicle.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def upsert_vehicle(
    db: Session,
    vehicle_data: Dict[str, Any],
) -> Tuple[Vehicle, bool, bool]:
    """
    Upsert vehicle by erp_id.
    Returns (vehicle, is_created, is_marked_sold).
    """
    now = datetime.now(timezone.utc)
    erp_id = vehicle_data["erp_id"]
    existing = db.query(Vehicle).filter(Vehicle.erp_id == erp_id).first()

    if existing:
        was_sold = (existing.status == "sold")
        # Existing vehicle: update fields
        for field, value in vehicle_data.items():
            if field not in ("id", "first_seen_at", "created_at", "is_new_to_us"):
                setattr(existing, field, value)
        existing.last_seen_at = now
        is_marked_sold = False
        if vehicle_data.get("issold") or vehicle_data.get("status") == "sold":
            if not existing.sold_at:
                existing.sold_at = now
            existing.status = "sold"
            if not was_sold:
                is_marked_sold = True
        db.add(existing)
        db.flush()
        return existing, False, is_marked_sold
    else:
        # New vehicle
        data = dict(vehicle_data)
        data.setdefault("is_new_to_us", True)
        data.setdefault("first_seen_at", now)
        data.setdefault("last_seen_at", now)
        is_marked_sold = False
        if data.get("issold") or data.get("status") == "sold":
            data.setdefault("sold_at", now)
            data["status"] = "sold"
            is_marked_sold = True

        new_vehicle = Vehicle(**data)
        db.add(new_vehicle)
        db.flush()
        return new_vehicle, True, is_marked_sold


def mark_sold(db: Session, vehicle: Vehicle) -> Vehicle:
    now = datetime.now(timezone.utc)
    vehicle.status = "sold"
    vehicle.issold = True
    if not vehicle.sold_at:
        vehicle.sold_at = now
    vehicle.updated_at = now
    db.add(vehicle)
    db.flush()
    return vehicle


def mark_missing_as_sold(db: Session, seen_erp_ids: Set[str]) -> int:
    """
    Mark available vehicles missing from full sync as sold.
    Returns number of marked vehicles.
    """
    now = datetime.now(timezone.utc)
    if not seen_erp_ids:
        # Safety: avoid marking everything sold if sync returned empty set
        return 0

    query = (
        db.query(Vehicle)
        .filter(Vehicle.status == "available")
        .filter(Vehicle.erp_id.notin_(seen_erp_ids))
    )
    missing_vehicles = query.all()
    count = 0
    for v in missing_vehicles:
        v.status = "sold"
        v.issold = True
        v.sold_at = now
        v.updated_at = now
        db.add(v)
        count += 1

    if count > 0:
        db.flush()
    return count
