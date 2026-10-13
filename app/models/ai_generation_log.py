from sqlalchemy import Column, ForeignKey, Integer, JSON, String, Text, TIMESTAMP, func

from app.models.base import Base


class AIGenerationLog(Base):
    __tablename__ = "ai_generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    generated_post_id = Column(Integer, ForeignKey("generated_posts.id", ondelete="SET NULL"), nullable=True)
    post_type = Column(String(30), nullable=True, index=True)
    tone_name = Column(String(100), nullable=True)
    language = Column(String(5), nullable=True)
    source = Column(String(30), nullable=False, default="manual", server_default="manual")
    status = Column(String(30), nullable=False, index=True)
    attempt = Column(Integer, nullable=False, default=1, server_default="1")
    ai_model = Column(String(100), nullable=True)
    system_prompt = Column(Text, nullable=True)
    user_prompt = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    request_id = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
