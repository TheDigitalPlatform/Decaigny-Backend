from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSON

from app.models.base import Base


class VehicleSync(Base):
    __tablename__ = "vehicle_syncs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, default="n8n")  # ydd | n8n | manual
    status = Column(String(50), nullable=False, default="running")  # running | success | failed | partial
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    fetched_count = Column(Integer, default=0, nullable=False)
    created_count = Column(Integer, default=0, nullable=False)
    updated_count = Column(Integer, default=0, nullable=False)
    sold_count = Column(Integer, default=0, nullable=False)
    skipped_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
