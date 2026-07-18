"""Reference-data endpoints: categories, colors, tags.

These power the UI's pick-lists. Categories are seeded, but colors and tags can
be created on the fly as the wardrobe grows.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import CategoryRepoDep, ColorRepoDep, TagRepoDep
from app.models.reference import Color, Tag
from app.schemas.reference import (
    CategoryRead,
    ColorCreate,
    ColorRead,
    TagCreate,
    TagRead,
)

router = APIRouter(tags=["reference"])


@router.get("/categories", response_model=list[CategoryRead])
async def list_categories(repo: CategoryRepoDep) -> list[CategoryRead]:
    return [CategoryRead.model_validate(c) for c in await repo.list_ordered()]


@router.get("/colors", response_model=list[ColorRead])
async def list_colors(repo: ColorRepoDep) -> list[ColorRead]:
    return [ColorRead.model_validate(c) for c in await repo.list_ordered()]


@router.post("/colors", response_model=ColorRead, status_code=status.HTTP_201_CREATED)
async def create_color(payload: ColorCreate, repo: ColorRepoDep) -> ColorRead:
    color = await repo.add(Color(**payload.model_dump()))
    return ColorRead.model_validate(color)


@router.get("/tags", response_model=list[TagRead])
async def list_tags(repo: TagRepoDep) -> list[TagRead]:
    return [TagRead.model_validate(t) for t in await repo.list_ordered()]


@router.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate, repo: TagRepoDep) -> TagRead:
    tag = await repo.add(Tag(**payload.model_dump()))
    return TagRead.model_validate(tag)
