"""Outfit endpoints: CRUD plus wear logging."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import OutfitServiceDep
from app.api.serialization import serialize_outfit
from app.schemas.common import Message, Page
from app.schemas.outfit import OutfitCreate, OutfitRead, OutfitUpdate
from app.schemas.wear import WearLogCreate, WearLogRead
from app.services.outfit_service import OutfitNotFoundError

router = APIRouter(prefix="/outfits", tags=["outfits"])


@router.get("", response_model=Page[OutfitRead])
async def list_outfits(
    service: OutfitServiceDep,
    limit: int = Query(default=60, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[OutfitRead]:
    outfits, total = await service.list(limit=limit, offset=offset)
    return Page(
        items=[serialize_outfit(o) for o in outfits],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=OutfitRead, status_code=status.HTTP_201_CREATED)
async def create_outfit(payload: OutfitCreate, service: OutfitServiceDep) -> OutfitRead:
    outfit = await service.create(payload)
    return serialize_outfit(outfit)


@router.get("/{outfit_id}", response_model=OutfitRead)
async def get_outfit(outfit_id: int, service: OutfitServiceDep) -> OutfitRead:
    try:
        outfit = await service.get(outfit_id)
    except OutfitNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return serialize_outfit(outfit)


@router.patch("/{outfit_id}", response_model=OutfitRead)
async def update_outfit(
    outfit_id: int, payload: OutfitUpdate, service: OutfitServiceDep
) -> OutfitRead:
    try:
        outfit = await service.update(outfit_id, payload)
    except OutfitNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return serialize_outfit(outfit)


@router.delete("/{outfit_id}", response_model=Message)
async def delete_outfit(outfit_id: int, service: OutfitServiceDep) -> Message:
    try:
        await service.delete(outfit_id)
    except OutfitNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return Message(detail="Outfit deleted.")


@router.post("/wear", response_model=WearLogRead, status_code=status.HTTP_201_CREATED)
async def log_wear(payload: WearLogCreate, service: OutfitServiceDep) -> WearLogRead:
    """Record that an outfit and/or item was worn on a date."""
    log = await service.log_wear(payload)
    return WearLogRead.model_validate(log)
