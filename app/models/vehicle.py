from sqlalchemy import Boolean, Column, Integer, Numeric, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    erp_id = Column(String(100), unique=True, index=True, nullable=False)
    vin = Column(String(50), nullable=True, index=True)
    stock_number = Column(String(100), nullable=True)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    trim = Column(String(150), nullable=True)
    price = Column(Numeric(12, 2), nullable=True)
    mileage = Column(Integer, nullable=True)
    fuel_type = Column(String(50), nullable=True)
    transmission = Column(String(50), nullable=True)
    color = Column(String(100), nullable=True)
    body_type = Column(String(100), nullable=True)
    features = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="available", index=True)  # available | sold | unknown
    erp_status_raw = Column(String(255), nullable=True)
    is_new_to_us = Column(Boolean, nullable=False, default=True)
    isonline = Column(Boolean, nullable=False, default=False)
    issold = Column(Boolean, nullable=False, default=False)
    isnewinstock = Column(Boolean, nullable=False, default=False)

    first_seen_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    sold_at = Column(TIMESTAMP(timezone=True), nullable=True)
    raw_payload = Column(JSON, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    images = relationship("VehicleImage", back_populates="vehicle", cascade="all, delete-orphan", order_by="VehicleImage.sort_order")
