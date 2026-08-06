"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps.auth import CurrentUser
from app.api.deps.container import get_auth_service
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=ApiResponse[UserRead],
    status_code=201,
    summary="Register a new user account",
)
async def register(
    payload: RegisterRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[UserRead]:
    user = await auth.register(
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=payload.role,
    )
    return ApiResponse(data=UserRead(id=user.user_id, email=user.email, full_name=user.full_name, role=user.role, is_active=user.is_active, created_at=user.created_at))


@router.post("/login", response_model=ApiResponse[TokenResponse], summary="Login and receive tokens")
async def login(
    payload: LoginRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[TokenResponse]:
    user = await auth.authenticate(email=payload.email, password=payload.password)
    tokens = await auth.issue_tokens(user)
    return ApiResponse(
        data=TokenResponse(
            **tokens,
            user=UserRead(
                id=user.user_id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
        )
    )


@router.post(
    "/token",
    response_model=ApiResponse[AccessTokenResponse],
    summary="OAuth2 password flow: exchange credentials for tokens",
)
async def token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[AccessTokenResponse]:
    user = await auth.authenticate(email=form.username, password=form.password)
    tokens = await auth.issue_tokens(user)
    return ApiResponse(
        data=AccessTokenResponse(
            access_token=tokens["access_token"],
            token_type="bearer",  # noqa: S106
            expires_in=tokens["expires_in"],
        )
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[AccessTokenResponse],
    summary="Rotate a refresh token for a new access token",
)
async def refresh(
    payload: RefreshRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[AccessTokenResponse]:
    tokens = await auth.refresh(payload.refresh_token)
    return ApiResponse(
        data=AccessTokenResponse(
            access_token=tokens["access_token"],
            token_type="bearer",  # noqa: S106
            expires_in=tokens["expires_in"],
        )
    )


@router.post("/logout", response_model=ApiResponse, summary="Revoke a refresh token")
async def logout(
    payload: RefreshRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse:
    await auth.logout(payload.refresh_token)
    return ApiResponse(data={"detail": "Logged out"})


@router.get("/me", response_model=ApiResponse[UserRead], summary="Get the current user")
async def me(user: CurrentUser) -> ApiResponse[UserRead]:
    return ApiResponse(
        data=UserRead(
            id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    )
