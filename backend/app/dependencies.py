from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.core.security import get_token_data

# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    token = credentials.credentials
    token_data = get_token_data(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure current user is an admin.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


def get_optional_user():
    """
    Optional authentication - returns None if not authenticated.
    Useful for public endpoints with enhanced features for logged-in users.
    """
    async def optional_auth(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
        db: AsyncSession = Depends(get_db),
    ) -> Optional[User]:
        if not credentials:
            return None
        
        try:
            token_data = get_token_data(credentials.credentials)
            if not token_data:
                return None
            
            result = await db.execute(
                select(User).where(User.id == token_data.user_id)
            )
            return result.scalar_one_or_none()
        except:
            return None
    
    return optional_auth
