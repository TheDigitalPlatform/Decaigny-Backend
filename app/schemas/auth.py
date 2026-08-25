from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    email: Optional[str] = None
    exp: Optional[datetime] = None
    user_id: Optional[str] = None
    role: Optional[str] = None


class TokenPayload(BaseModel):
    sub: str
    exp: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
