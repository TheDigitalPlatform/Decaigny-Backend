from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PromptBase(BaseModel):
    name: str
    content: str
    description: Optional[str] = None
    is_active: bool = True


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PromptInDBBase(PromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Prompt(PromptInDBBase):
    pass
