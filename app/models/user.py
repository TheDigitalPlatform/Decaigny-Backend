from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    role = relationship("Role", back_populates="users")