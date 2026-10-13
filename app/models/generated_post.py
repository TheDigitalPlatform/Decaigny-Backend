from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, JSON, String, Text, TIMESTAMP, func, text

from app.models.base import Base


class GeneratedPost(Base):
    __tablename__ = "generated_posts"

    __table_args__ = (
        Index(
            "uq_generated_posts_current",
            "vehicle_id",
            "post_type",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    post_type = Column(String(30), nullable=False, index=True)
    tone_prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True)
    tone_name = Column(String(100), nullable=True)
    language = Column(String(5), nullable=False)
    headline = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    call_to_action = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)
    content = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="draft", server_default="draft", index=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    is_current = Column(Boolean, nullable=False, default=True, server_default="true", index=True)
    ai_model = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
