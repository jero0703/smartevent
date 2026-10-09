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
