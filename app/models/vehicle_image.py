from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.models.base import Base


class VehicleImage(Base):
    __tablename__ = "vehicle_images"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("vehicle_id", "url", name="uq_vehicle_images_vehicle_id_url"),
    )

    vehicle = relationship("Vehicle", back_populates="images")
