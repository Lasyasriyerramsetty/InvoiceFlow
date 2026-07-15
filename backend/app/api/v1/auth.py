import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_current_user
from backend.app.api.v1.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from backend.app.infrastructure.database.session import get_db_session
from backend.app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from backend.app.infrastructure.database.models import User, UserRole
from backend.app.infrastructure.database.repositories import UserRepository
from backend.app.infrastructure.database.session import get_db_session

router = APIRouter(tags=["Auth"])


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    payload: UserCreate,
):
    existing = await UserRepository(session).get_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=UserRole(payload.role),
        department=payload.department,
    )
    user = await UserRepository(session).create(user)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    payload: LoginRequest,
):
    user = await UserRepository(session).get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_me(
    user: Annotated[User, Depends(get_current_user)],
):
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        department=user.department,
        is_active=user.is_active,
    )