from sqlalchemy import Boolean, Column, Integer, JSON, String, Text, TIMESTAMP, func

from app.models.base import Base


class DealershipProfile(Base):
    __tablename__ = "dealership_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    tagline = Column(String(255), nullable=True)
    location = Column(String(150), nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    website = Column(String(255), nullable=True)
    default_language = Column(String(5), nullable=False, server_default="nl")
    call_to_action = Column(Text, nullable=True)
    signature = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)
    preferred_phrases = Column(JSON, nullable=True)
    banned_phrases = Column(JSON, nullable=True)
    use_emojis = Column(Boolean, nullable=False, default=True, server_default="true")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
