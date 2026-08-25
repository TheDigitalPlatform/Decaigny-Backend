from typing import Optional
from pydantic import EmailStr
from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.role import Role as RoleSchema


# Shared properties
class UserBase(BaseSchema):
    name: str
    email: EmailStr
    role_id: int


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# Properties to receive via API on update
class UserUpdate(BaseSchema):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[int] = None


# Properties allowed for user profile update (name and email only)
class UserProfileUpdate(BaseSchema):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional properties to return via API
class User(UserInDBBase):
    role: Optional[RoleSchema] = None


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    password: str