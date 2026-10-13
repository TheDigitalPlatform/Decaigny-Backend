from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict

PromptType = Literal["tone", "system", "new_vehicle_template", "sold_vehicle_template"]


class PromptBase(BaseModel):
    name: str
    content: str
    description: Optional[str] = None
    is_active: bool = True
    prompt_type: PromptType = "tone"


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    prompt_type: Optional[PromptType] = None


class PromptInDBBase(PromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Prompt(PromptInDBBase):
    pass
