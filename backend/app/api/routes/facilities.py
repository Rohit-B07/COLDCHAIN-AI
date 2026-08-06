"""Facility endpoints: warehouses and primary health centres."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps.auth import CurrentUser
from app.api.deps.container import get_phc_repository, get_warehouse_repository
from app.core.exceptions import NotFoundError
from app.domain.repositories import PhCentreRepository, WarehouseRepository
from app.schemas.common import ApiResponse
from app.schemas.facility import PhCentreCreate, PhCentreRead, WarehouseCreate, WarehouseRead

router = APIRouter(tags=["facilities"])

warehouse_router = APIRouter(prefix="/warehouses")
phc_router = APIRouter(prefix="/phcs")


@warehouse_router.get("", response_model=ApiResponse[list[WarehouseRead]], summary="List warehouses")
async def list_warehouses(
    repo: Annotated[WarehouseRepository, Depends(get_warehouse_repository)],
) -> ApiResponse[list[WarehouseRead]]:
    warehouses = await repo.list()
    return ApiResponse(
        data=[
            WarehouseRead(
                id=w.warehouse_id,
                name=w.name,
                code=w.code,
                latitude=w.latitude,
                longitude=w.longitude,
                address=w.address,
                capacity=w.capacity,
            )
            for w in warehouses
        ]
    )


@warehouse_router.post(
    "",
    response_model=ApiResponse[WarehouseRead],
    status_code=201,
    summary="Create a warehouse",
)
async def create_warehouse(
    payload: WarehouseCreate,
    repo: Annotated[WarehouseRepository, Depends(get_warehouse_repository)],
) -> ApiResponse[WarehouseRead]:
    from app.domain.entities.facility import Warehouse as WarehouseEntity

    entity = WarehouseEntity.create(
        name=payload.name,
        code=payload.code,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address=payload.address,
        capacity=payload.capacity,
    )
    saved = await repo.create(entity)
    return ApiResponse(data=WarehouseRead(id=saved.warehouse_id, name=saved.name, code=saved.code, latitude=saved.latitude, longitude=saved.longitude, address=saved.address, capacity=saved.capacity))


@warehouse_router.get("/{warehouse_id}", response_model=ApiResponse[WarehouseRead], summary="Get a warehouse")
async def get_warehouse(
    warehouse_id: UUID,
    repo: Annotated[WarehouseRepository, Depends(get_warehouse_repository)],
) -> ApiResponse[WarehouseRead]:
    warehouse = await repo.get(warehouse_id)
    if warehouse is None:
        raise NotFoundError("Warehouse not found")
    return ApiResponse(data=WarehouseRead(id=warehouse.warehouse_id, name=warehouse.name, code=warehouse.code, latitude=warehouse.latitude, longitude=warehouse.longitude, address=warehouse.address, capacity=warehouse.capacity))


@phc_router.get("", response_model=ApiResponse[list[PhCentreRead]], summary="List PHCs")
async def list_phcs(
    repo: Annotated[PhCentreRepository, Depends(get_phc_repository)],
) -> ApiResponse[list[PhCentreRead]]:
    phcs = await repo.list()
    return ApiResponse(
        data=[
            PhCentreRead(
                id=p.phc_id,
                name=p.name,
                code=p.code,
                district=p.district,
                state=p.state,
                latitude=p.latitude,
                longitude=p.longitude,
                contact=p.contact,
                capacity=p.capacity,
                priority_level=p.priority_level,
            )
            for p in phcs
        ]
    )


@phc_router.post("", response_model=ApiResponse[PhCentreRead], status_code=201, summary="Create a PHC")
async def create_phc(
    payload: PhCentreCreate,
    repo: Annotated[PhCentreRepository, Depends(get_phc_repository)],
) -> ApiResponse[PhCentreRead]:
    from app.domain.entities.facility import PrimaryHealthCentre as PhcEntity

    entity = PhcEntity.create(
        name=payload.name,
        code=payload.code,
        district=payload.district,
        state=payload.state,
        latitude=payload.latitude,
        longitude=payload.longitude,
        contact=payload.contact,
        capacity=payload.capacity,
        priority_level=payload.priority_level,
    )
    saved = await repo.create(entity)
    return ApiResponse(
        data=PhCentreRead(
            id=saved.phc_id,
            name=saved.name,
            code=saved.code,
            district=saved.district,
            state=saved.state,
            latitude=saved.latitude,
            longitude=saved.longitude,
            contact=saved.contact,
            capacity=saved.capacity,
            priority_level=saved.priority_level,
        )
    )


@phc_router.get("/{phc_id}", response_model=ApiResponse[PhCentreRead], summary="Get a PHC")
async def get_phc(
    phc_id: UUID,
    repo: Annotated[PhCentreRepository, Depends(get_phc_repository)],
) -> ApiResponse[PhCentreRead]:
    phc = await repo.get(phc_id)
    if phc is None:
        raise NotFoundError("Primary health centre not found")
    return ApiResponse(
        data=PhCentreRead(
            id=phc.phc_id,
            name=phc.name,
            code=phc.code,
            district=phc.district,
            state=phc.state,
            latitude=phc.latitude,
            longitude=phc.longitude,
            contact=phc.contact,
            capacity=phc.capacity,
            priority_level=phc.priority_level,
        )
    )