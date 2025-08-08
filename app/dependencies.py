"""
FastAPI dependencies for authentication and common functionality
"""
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.exceptions import UnauthorizedException

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current authenticated user"""
    auth_service = AuthService()
    user = await auth_service.get_current_user(credentials.credentials, session)
    if not user:
        raise UnauthorizedException("Invalid authentication credentials")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise UnauthorizedException("Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_current_user():
    """Get optional current user for public endpoints"""
    async def _get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        session: AsyncSession = Depends(get_async_session)
    ) -> Optional[User]:
        if not credentials:
            return None
        
        try:
            auth_service = AuthService()
            return await auth_service.get_current_user(credentials.credentials, session)
        except Exception:
            return None
    
    return _get_optional_user