"""Primary health centre management service.

Coordinates PHC CRUD, business rules (unique code, code format, capacity and
priority bounds, soft-delete semantics) and paginated/filtered listing.
Repository adapters are injected so the service stays free of persistence and
HTTP concerns.
"""

from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.entities.facility import PrimaryHealthCentre
from app.domain.repositories import PhCentreRepository
from app.schemas.phc import PhcCreate, PhcUpdate


class PhcService:
    def __init__(self, phc_repo: PhCentreRepository) -> None:
        self._repo = phc_repo

    async def create(self, payload: PhcCreate) -> PrimaryHealthCentre:
        try:
            entity = PrimaryHealthCentre.create(
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
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        existing = await self._repo.get_by_code(entity.code)
        if existing is not None:
            raise ConflictError(
                f"A primary health centre with code {entity.code!r} already exists"
            )
        return await self._repo.create(entity)

    async def get(self, phc_id: UUID) -> PrimaryHealthCentre:
        entity = await self._repo.get(phc_id)
        if entity is None:
            raise NotFoundError("Primary health centre not found")
        return entity

    async def list(
        self,
        *,
        search: str | None,
        state: str | None,
        capacity_min: int | None,
        capacity_max: int | None,
        priority_level: int | None,
        page: int,
        size: int,
    ) -> tuple[list[PrimaryHealthCentre], int]:
        offset = (page - 1) * size
        total = await self._repo.count(
            search=search,
            state=state,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
            priority_level=priority_level,
        )
        items = await self._repo.list_paginated(
            search=search,
            state=state,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
            priority_level=priority_level,
            offset=offset,
            limit=size,
        )
        return items, total

    async def update(self, phc_id: UUID, payload: PhcUpdate) -> PrimaryHealthCentre:
        entity = await self.get(phc_id)
        if payload.code is not None and payload.code.strip().upper() != entity.code:
            existing = await self._repo.get_by_code(payload.code)
            if existing is not None and existing.phc_id != phc_id:
                raise ConflictError(
                    f"A primary health centre with code {payload.code!r} already exists"
                )
        try:
            entity.update(
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
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._repo.update(entity)

    async def delete(self, phc_id: UUID) -> PrimaryHealthCentre:
        entity = await self.get(phc_id)
        entity.soft_delete()
        await self._repo.soft_delete(phc_id)
        return entity
