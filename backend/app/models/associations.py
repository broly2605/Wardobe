"""Many-to-many association tables.

Defined separately from the ORM classes to avoid circular imports, since both
sides of each relationship reference these tables.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, Table

from app.db.base import Base

# Links clothing items to their colors (an item may have several colors).
item_colors = Table(
    "item_colors",
    Base.metadata,
    Column(
        "item_id",
        BigInteger,
        ForeignKey("clothing_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "color_id",
        BigInteger,
        ForeignKey("colors.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Links clothing items to free-form tags.
item_tags = Table(
    "item_tags",
    Base.metadata,
    Column(
        "item_id",
        BigInteger,
        ForeignKey("clothing_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        BigInteger,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
