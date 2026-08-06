"""Primary health centre endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.container import get_phc_service
from app.api.deps.rbac import require_permissions
from app.domain.entities.facility import PrimaryHealthCentre
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse, Page
from app.schemas.phc import (
    PhcCreate,
    PhcQueryParams,
    PhcRead,
    PhcUpdate,
)
from app.services.phc_service import PhcService

router = APIRouter(prefix="/phcs", tags=["phcs"])

_ViewPhcs = Depends(require_permissions(Permission.FACILITY_VIEW))
_ManagePhcs = Depends(require_permissions(Permission.FACILITY_MANAGE))


def _read(entity: PrimaryHealthCentre) -> PhcRead:
    return PhcRead(
        id=entity.phc_id,
        name=entity.name,
        code=entity.code,
        district=entity.district,
        state=entity.state,
        latitude=entity.latitude,
        longitude=entity.longitude,
        contact=entity.contact,
        capacity=entity.capacity,
        priority_level=entity.priority_level,
        is_deleted=entity.is_deleted,
        created_at=entity.created_at,
    )


@router.get(
    "",
    response_model=ApiResponse[Page[PhcRead]],
    summary="List primary health centres (paginated and filtered)",
    dependencies=[_ViewPhcs],
)
async def list_phcs(
    params: Annotated[PhcQueryParams, Query()],
    service: Annotated[PhcService, Depends(get_phc_service)],
) -> ApiResponse[Page[PhcRead]]:
    items, total = await service.list(
        search=params.search,
        state=params.state,
        capacity_min=params.capacity_min,
        capacity_max=params.capacity_max,
        priority_level=params.priority_level,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[PhcRead](
            items=[_read(phc) for phc in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[PhcRead],
    status_code=201,
    summary="Create a primary health centre",
    dependencies=[_ManagePhcs],
)
async def create_phc(
    payload: PhcCreate,
    service: Annotated[PhcService, Depends(get_phc_service)],
) -> ApiResponse[PhcRead]:
    entity = await service.create(payload)
    return ApiResponse(data=_read(entity))


@router.get(
    "/{phc_id}",
    response_model=ApiResponse[PhcRead],
    summary="Get a primary health centre by id",
    dependencies=[_ViewPhcs],
)
async def get_phc(
    phc_id: UUID,
    service: Annotated[PhcService, Depends(get_phc_service)],
) -> ApiResponse[PhcRead]:
    entity = await service.get(phc_id)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{phc_id}",
    response_model=ApiResponse[PhcRead],
    summary="Update a primary health centre",
    dependencies=[_ManagePhcs],
)
async def update_phc(
    phc_id: UUID,
    payload: PhcUpdate,
    service: Annotated[PhcService, Depends(get_phc_service)],
) -> ApiResponse[PhcRead]:
    entity = await service.update(phc_id, payload)
    return ApiResponse(data=_read(entity))


@router.delete(
    "/{phc_id}",
    response_model=ApiResponse[PhcRead],
    summary="Soft-delete a primary health centre",
    dependencies=[_ManagePhcs],
)
async def delete_phc(
    phc_id: UUID,
    service: Annotated[PhcService, Depends(get_phc_service)],
) -> ApiResponse[PhcRead]:
    entity = await service.delete(phc_id)
    return ApiResponse(data=_read(entity))
