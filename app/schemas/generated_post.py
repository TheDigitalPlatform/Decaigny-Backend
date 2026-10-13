from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PostType = Literal["new_vehicle", "sold_vehicle"]
Language = Literal["nl", "fr", "en"]


class GeneratePostRequest(BaseModel):
    vehicle_id: int
    post_type: Literal["auto", "new_vehicle", "sold_vehicle"] = "auto"
    tone: Optional[str] = Field(default=None, description="Tone name, e.g. 'Premium'")
    tone_id: Optional[int] = None
    language: Optional[Language] = None
    regenerate: bool = False
    dry_run: bool = False
    source: str = "manual"


class GeneratedPostRead(BaseModel):
    id: int
    vehicle_id: int
    post_type: str
    tone_prompt_id: Optional[int] = None
    tone_name: Optional[str] = None
    language: str
    headline: Optional[str] = None
    body: str
    call_to_action: Optional[str] = None
    hashtags: List[str] = []
    content: str
    status: str
    version: int
    is_current: bool
    ai_model: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIGenerationLogRead(BaseModel):
    id: int
    vehicle_id: Optional[int] = None
    generated_post_id: Optional[int] = None
    post_type: Optional[str] = None
    tone_name: Optional[str] = None
    language: Optional[str] = None
    source: str
    status: str
    attempt: int
    ai_model: Optional[str] = None
    validation_errors: Optional[List[str]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    request_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIGenerationLogDetail(AIGenerationLogRead):
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    raw_response: Optional[str] = None


class PostConfigUpdate(BaseModel):
    new_vehicle_tone: Optional[str] = None
    sold_vehicle_tone: Optional[str] = None


class DealershipProfileRead(BaseModel):
    id: int
    name: str
    tagline: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    default_language: str
    call_to_action: Optional[str] = None
    signature: Optional[str] = None
    hashtags: List[str] = []
    preferred_phrases: List[str] = []
    banned_phrases: List[str] = []
    use_emojis: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealershipProfileUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    default_language: Optional[Language] = None
    call_to_action: Optional[str] = None
    signature: Optional[str] = None
    hashtags: Optional[List[str]] = None
    preferred_phrases: Optional[List[str]] = None
    banned_phrases: Optional[List[str]] = None
    use_emojis: Optional[bool] = None
