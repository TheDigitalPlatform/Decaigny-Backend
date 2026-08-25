from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator


class CommunicationStyleItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    is_default: bool = False

    model_config = ConfigDict(from_attributes=True)


class SetDefaultCommunicationStyleRequest(BaseModel):
    prompt_id: Optional[int] = None
    name: Optional[str] = None

    @model_validator(mode="after")
    def check_at_least_one(self):
        if self.prompt_id is None and (not self.name or not self.name.strip()):
            raise ValueError("Provide prompt_id or name")
        return self


class DefaultCommunicationStyleResponse(BaseModel):
    prompt_id: Optional[int] = None
    name: Optional[str] = None
