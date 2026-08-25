from typing import Optional
from datetime import datetime

from app.schemas.base import BaseSchema


class RoleBase(BaseSchema):
    name: str
    description: str


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleInDBBase(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Role(RoleInDBBase):
    pass
