"""User management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import CurrentUser
from app.api.deps.container import get_user_service
from app.api.deps.rbac import require_permissions
from app.domain.entities.user import User
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse, Page
from app.schemas.user import (
    ChangePasswordRequest,
    UserProfileRead,
    UserQueryParams,
    UserSummaryRead,
    UserUpdateProfile,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

_ManageUsers = Depends(require_permissions(Permission.USER_MANAGE))


def _profile(user: User) -> UserProfileRead:
    return UserProfileRead(
        id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _summary(user: User) -> UserSummaryRead:
    return UserSummaryRead(
        id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserProfileRead],
    summary="Get the current user's profile",
)
async def get_profile(user: CurrentUser) -> ApiResponse[UserProfileRead]:
    return ApiResponse(data=_profile(user))


@router.patch(
    "/me",
    response_model=ApiResponse[UserProfileRead],
    summary="Update the current user's profile",
)
async def update_profile(
    payload: UserUpdateProfile,
    user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[UserProfileRead]:
    updated = await service.update_profile(
        user.user_id,
        full_name=payload.full_name,
        email=payload.email,
    )
    return ApiResponse(data=_profile(updated))


@router.post(
    "/me/change-password",
    response_model=ApiResponse,
    summary="Change the current user's password",
)
async def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse:
    await service.change_password(
        user.user_id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return ApiResponse(data={"detail": "Password changed"})


@router.get(
    "",
    response_model=ApiResponse[Page[UserSummaryRead]],
    summary="List users (paginated and filtered)",
    dependencies=[_ManageUsers],
)
async def list_users(
    params: Annotated[UserQueryParams, Query()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[Page[UserSummaryRead]]:
    items, total = await service.list_users(
        search=params.search,
        role=params.role,
        is_active=params.is_active,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[UserSummaryRead](
            items=[_summary(user) for user in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "/{user_id}/deactivate",
    response_model=ApiResponse[UserProfileRead],
    summary="Deactivate a user account",
    dependencies=[_ManageUsers],
)
async def deactivate_user(
    user_id: UUID,
    user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[UserProfileRead]:
    updated = await service.deactivate(user_id, actor_id=user.user_id)
    return ApiResponse(data=_profile(updated))


@router.post(
    "/{user_id}/activate",
    response_model=ApiResponse[UserProfileRead],
    summary="Activate a user account",
    dependencies=[_ManageUsers],
)
async def activate_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse[UserProfileRead]:
    updated = await service.activate(user_id)
    return ApiResponse(data=_profile(updated))
