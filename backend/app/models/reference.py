"""Reference / lookup tables: categories, colors, and tags.

Normalizing these out of the ``clothing_items`` table avoids duplicating strings
across thousands of rows, enables consistent filtering and analytics, and lets
the UI present curated pick-lists. Items relate to colors and tags through
many-to-many association tables (see ``associations.py``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.associations import item_colors, item_tags

if TYPE_CHECKING:
    from app.models.clothing import ClothingItem


class Category(Base, PrimaryKeyMixin, TimestampMixin):
    """A clothing category (e.g. Tops, Bottoms, Footwear).

    ``slug`` is a stable, URL-safe identifier used by the API and seed data;
    ``name`` is the human-friendly label shown in the UI.
    """

    __tablename__ = "categories"

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Warmth this category contributes on a 0-10 scale, used as a heuristic
    # default when an item does not specify its own warmth.
    default_warmth: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    # Display ordering in the UI (lower sorts first).
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    items: Mapped[list["ClothingItem"]] = relationship(back_populates="category")


class Color(Base, PrimaryKeyMixin, TimestampMixin):
    """A named color with a hex value, reused across items."""

    __tablename__ = "colors"

    name: Mapped[str] = mapped_column(String(48), unique=True, nullable=False, index=True)
    hex: Mapped[str] = mapped_column(String(7), nullable=False)  # e.g. "#1A1A1A"
    # Coarse color family (e.g. "neutral", "warm", "cool") to support
    # color-harmony logic in the rule-based stylist.
    family: Mapped[str | None] = mapped_column(String(24), index=True)

    items: Mapped[list["ClothingItem"]] = relationship(
        secondary=item_colors, back_populates="colors"
    )


class Tag(Base, PrimaryKeyMixin, TimestampMixin):
    """A free-form label (e.g. "vintage", "waterproof", "favorite-fabric")."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(48), unique=True, nullable=False, index=True)

    items: Mapped[list["ClothingItem"]] = relationship(
        secondary=item_tags, back_populates="tags"
    )
