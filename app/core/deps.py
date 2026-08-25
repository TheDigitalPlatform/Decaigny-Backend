from app.db.session import get_db
from app.models.user import User as UserModel

from datetime import datetime
from fastapi import Depends, HTTPException, status, Security, Path, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError
 

from app.auth.jwt import verify_password, decode_token
 

security = HTTPBearer()
 
 
def authenticate_user(
    email: str, password: str, db: Session
) -> Optional[UserModel]:
    """
    Authenticate a user by email and password.
    """
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
 
 
def get_current_user_from_db(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Dependency to get the current authenticated user from the database.
    Verifies the JWT token and returns the user.
    Raises HTTPException if authentication fails.
    """
    try:
        token_data = decode_token(credentials.credentials)
        
        # Check if token is expired
        if token_data.exp < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Get user from database
        user = db.query(UserModel).filter(UserModel.email == token_data.email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(
    current_user: UserModel = Depends(get_current_user_from_db),
) -> UserModel:
    """
    Dependency that allows access only to users with the admin role.
    Raises HTTP 403 if the current user is not an admin.
    """
    if not current_user.role or current_user.role.name.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have admin access",
        )
    return current_user

