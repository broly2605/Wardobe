"""Shared schema building blocks."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base for schemas that are populated from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    """A generic paginated response envelope."""

    items: list[T]
    total: int = Field(description="Total number of matching rows.")
    limit: int
    offset: int


class Message(BaseModel):
    """A simple message response (used for deletes / acknowledgements)."""

    detail: str
