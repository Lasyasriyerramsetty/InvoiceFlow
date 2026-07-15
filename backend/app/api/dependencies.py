import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import decode_token
from backend.app.infrastructure.database.models import User, UserRole
from backend.app.infrastructure.database.repositories import UserRepository
from backend.app.infrastructure.database.session import get_db_session

security = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["*"],
    UserRole.CFO: ["approve", "view", "report", "escalate"],
    UserRole.DIRECTOR: ["approve", "view", "report"],
    UserRole.FINANCE_MANAGER: ["approve", "view", "process"],
    UserRole.PROCUREMENT: ["approve", "view", "process"],
    UserRole.LEGAL: ["approve", "view"],
    UserRole.AP_CLERK: ["process", "view"],
    UserRole.AUDITOR: ["view", "report", "audit"],
    UserRole.VIEWER: ["view"],
}


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = await UserRepository(session).get_by_id(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_permission(permission: str):
    async def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        allowed = ROLE_PERMISSIONS.get(user.role, [])
        if "*" not in allowed and permission not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission '{permission}' required")
        return user

    return checker
