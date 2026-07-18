"""The core ``clothing_items`` model — a single wardrobe garment."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.associations import item_colors, item_tags
from app.models.enums import Formality, Season, string_enum

if TYPE_CHECKING:
    from app.models.outfit import OutfitItem
    from app.models.reference import Category, Color, Tag
    from app.models.wear import WearLog


class ClothingItem(Base, PrimaryKeyMixin, TimestampMixin):
    """A garment in the wardrobe.

    Descriptive attributes (brand, material, size…) are optional to honor the
    "minimal setup" requirement — only a name and category are needed. Styling
    signals (``warmth``, ``formality``, ``season``) drive recommendations.
    """

    __tablename__ = "clothing_items"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # --- Optional descriptive attributes ---
    brand: Mapped[str | None] = mapped_column(String(80))
    size: Mapped[str | None] = mapped_column(String(32))
    material: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)

    # --- Image (stored on local filesystem; DB keeps the relative path) ---
    image_path: Mapped[str | None] = mapped_column(String(255))

    # --- Styling signals ---
    season: Mapped[Season] = mapped_column(
        string_enum(Season, "season_enum"),
        default=Season.ALL_SEASON,
        nullable=False,
    )
    formality: Mapped[Formality] = mapped_column(
        string_enum(Formality, "formality_enum"),
        default=Formality.CASUAL,
        nullable=False,
    )
    # 0 (very light) .. 10 (very warm); powers weather-aware suggestions.
    warmth: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # --- Lifecycle / usage ---
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wear_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_worn_at: Mapped[date | None] = mapped_column(Date)
    purchase_date: Mapped[date | None] = mapped_column(Date)

    # --- AI enrichment ---
    # Free-form structured output from vision auto-tagging (labels, confidence,
    # detected attributes). JSONB keeps it queryable without schema churn.
    ai_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # --- Relationships ---
    category: Mapped["Category"] = relationship(back_populates="items", lazy="selectin")
    colors: Mapped[list["Color"]] = relationship(
        secondary=item_colors, back_populates="items", lazy="selectin"
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=item_tags, back_populates="items", lazy="selectin"
    )
    outfit_links: Mapped[list["OutfitItem"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    wear_logs: Mapped[list["WearLog"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
