from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.schemas.auth import TokenData
 
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
 
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
 
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
 
def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)  # Refresh token valid for 30 days
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
 
def decode_token(token: str) -> TokenData:
    """
    Decode and verify a JWT token, returning the token data.
    Raises JWTError if the token is invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))
        user_id: str = payload.get("user_id")
        
        if email is None:
            raise JWTError("Token missing email claim")
            
        token_data = TokenData(email=email, exp=exp, user_id=user_id)
        return token_data
    except JWTError:
        raise JWTError("Could not validate credentials")
