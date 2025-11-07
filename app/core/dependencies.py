"""Authentication and authorization dependencies."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.services.auth_service import AuthService

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """Get the current authenticated user."""
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.get_current_user(token)
        return user
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None."""
    if not token:
        return None
    
    auth_service = AuthService(db)
    try:
        user = await auth_service.get_current_user(token)
        return user if user.is_active else None
    except HTTPException:
        return None


def require_permission(permission: str):
    """Create a dependency that requires a specific permission."""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # For now, we'll use a simple role-based system
        # You can extend this to check specific permissions
        if permission == "admin" and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_checker


def require_roles(*roles: str):
    """Create a dependency that requires specific roles."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_roles = []
        if current_user.is_superuser:
            user_roles.append("admin")
        if current_user.is_active:
            user_roles.append("user")
        
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(roles)}"
            )
        return current_user
    
    return role_checker
