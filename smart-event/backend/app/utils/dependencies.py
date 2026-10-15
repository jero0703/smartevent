from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole
from app.services.auth_service import get_current_user

def require_user(current_user: User = Depends(get_current_user)) -> User:
    # Actually, if they are authenticated, they have at least USER role.
    return current_user

def require_organizer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.ORGANIZER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return current_user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return current_user

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_optional_user(token: Optional[str] = Depends(optional_oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return db.query(User).filter(User.id == int(user_id)).first()
    except Exception:
        return None
