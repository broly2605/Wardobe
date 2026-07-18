"""Schemas for reference data: categories, colors, tags."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# --- Category ---
class CategoryBase(BaseModel):
    slug: str = Field(max_length=64)
    name: str = Field(max_length=64)
    description: str | None = None
    default_warmth: int = Field(default=5, ge=0, le=10)
    sort_order: int = 100


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(ORMModel, CategoryBase):
    id: int


# --- Color ---
class ColorBase(BaseModel):
    name: str = Field(max_length=48)
    hex: str = Field(pattern=r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
    family: str | None = Field(default=None, max_length=24)


class ColorCreate(ColorBase):
    pass


class ColorRead(ORMModel, ColorBase):
    id: int


# --- Tag ---
class TagBase(BaseModel):
    name: str = Field(max_length=48)


class TagCreate(TagBase):
    pass


class TagRead(ORMModel, TagBase):
    id: int
