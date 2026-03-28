from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.normalization import normalize_email
from app.core.security import create_access_token
from app.db.models.enums import UserRole
from app.db.models.user import User
from app.db.session import get_async_session
from app.modules.auth import service as auth_service
from app.modules.auth.constants import INACTIVE_USER_DETAIL
from app.modules.auth.deps import get_current_active_user, require_roles
from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> RegisterResponse:
    """Create an application login only. Does not create parish registry (``ChurchMember``) rows."""
    email_norm = normalize_email(str(body.email))
    existing = await auth_service.get_user_by_email(session, email_norm)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await auth_service.create_registered_user(
        session,
        full_name=body.full_name.strip(),
        email=email_norm,
        password=body.password,
    )
    token = create_access_token(user_id=user.id)
    return RegisterResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TokenResponse:
    email_norm = normalize_email(str(body.email))
    user = await auth_service.authenticate_user(
        session,
        email=email_norm,
        password=body.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=INACTIVE_USER_DETAIL,
        )

    token = create_access_token(user_id=user.id)
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=MeResponse)
async def me(
    user: Annotated[User, Depends(get_current_active_user)],
) -> MeResponse:
    return MeResponse.model_validate(user)


@router.get("/admin/ping")
async def admin_ping(
    _user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict[str, str]:
    """RBAC smoke endpoint — verifies `require_roles` wiring (admin only)."""
    return {"status": "ok"}
