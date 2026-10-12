from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Vehicle Images ---
class VehicleImageBase(BaseModel):
    url: str
    is_primary: bool = False
    sort_order: int = 0


class VehicleImageCreate(VehicleImageBase):
    vehicle_id: int


class VehicleImageRead(VehicleImageBase):
    id: int
    vehicle_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Vehicles ---
class VehicleBase(BaseModel):
    erp_id: str
    vin: Optional[str] = None
    stock_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    trim: Optional[str] = None
    price: Optional[Decimal] = None
    mileage: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    color: Optional[str] = None
    body_type: Optional[str] = None
    features: Optional[Any] = None
    status: str = "available"
    erp_status_raw: Optional[str] = None
    is_new_to_us: bool = True
    isonline: bool = False
    issold: bool = False
    isnewinstock: bool = False


class VehicleCreate(VehicleBase):
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None
    raw_payload: Optional[Dict[str, Any]] = None


class VehicleUpdate(BaseModel):
    vin: Optional[str] = None
    stock_number: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    trim: Optional[str] = None
    price: Optional[Decimal] = None
    mileage: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    color: Optional[str] = None
    body_type: Optional[str] = None
    features: Optional[Any] = None
    status: Optional[str] = None
    erp_status_raw: Optional[str] = None
    is_new_to_us: Optional[bool] = None
    isonline: Optional[bool] = None
    issold: Optional[bool] = None
    isnewinstock: Optional[bool] = None
    last_seen_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None
    raw_payload: Optional[Dict[str, Any]] = None


class VehicleRead(VehicleBase):
    id: int
    first_seen_at: datetime
    last_seen_at: datetime
    sold_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    images: List[VehicleImageRead] = []

    model_config = ConfigDict(from_attributes=True)


class VehicleDetailRead(VehicleRead):
    raw_payload: Optional[Dict[str, Any]] = None


# --- Vehicle Syncs ---
class VehicleSyncPullRequest(BaseModel):
    mark_missing_as_sold: bool = True
    filter: Optional[str] = None
    source: Optional[str] = "n8n"


class VehicleSyncResult(BaseModel):
    sync_id: int
    fetched: int
    created: int
    updated: int
    sold: int
    skipped: int


class VehicleSyncRead(BaseModel):
    id: int
    source: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    fetched_count: int
    created_count: int
    updated_count: int
    sold_count: int
    skipped_count: int
    error_message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
