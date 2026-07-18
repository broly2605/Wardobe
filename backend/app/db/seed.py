"""Seed baseline reference data: categories, a starter color palette, tags.

Idempotent — running it repeatedly won't create duplicates (existing slugs /
names are skipped). Invoke via ``python -m app.db.seed`` after migrations.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.reference import Category, Color, Tag

# (slug, display name, default warmth 0-10, sort order)
CATEGORIES: list[tuple[str, str, int, int]] = [
    ("tops", "Tops", 4, 10),
    ("bottoms", "Bottoms", 4, 20),
    ("dresses", "Dresses", 3, 30),
    ("outerwear", "Outerwear", 8, 40),
    ("footwear", "Footwear", 3, 50),
    ("accessories", "Accessories", 1, 60),
]

# A compact, well-distributed starter palette (name, hex, family).
COLORS: list[tuple[str, str, str]] = [
    ("Black", "#111111", "black"),
    ("White", "#f5f5f5", "white"),
    ("Charcoal", "#36454f", "grey"),
    ("Grey", "#9098a1", "grey"),
    ("Navy", "#1f2a44", "blue"),
    ("Blue", "#2f6fed", "blue"),
    ("Teal", "#009688", "green"),
    ("Green", "#3f8f4f", "green"),
    ("Olive", "#6b7d3a", "green"),
    ("Beige", "#d8c3a5", "beige"),
    ("Brown", "#6f4e37", "brown"),
    ("Burgundy", "#7b1f2b", "red"),
    ("Red", "#d1414b", "red"),
    ("Orange", "#e07a3f", "orange"),
    ("Mustard", "#d4a017", "yellow"),
    ("Pink", "#e8a3b8", "pink"),
    ("Purple", "#7a5299", "purple"),
]

TAGS: list[str] = [
    "favorite",
    "everyday",
    "statement",
    "comfy",
    "layering",
    "vintage",
    "new",
    "workwear",
    "athleisure",
]


async def seed() -> None:
    async with SessionLocal() as session:
        # Categories
        existing_cats = {
            c for c in (await session.execute(select(Category.slug))).scalars()
        }
        for slug, name, warmth, order in CATEGORIES:
            if slug not in existing_cats:
                session.add(
                    Category(
                        slug=slug,
                        name=name,
                        default_warmth=warmth,
                        sort_order=order,
                    )
                )

        # Colors
        existing_colors = {
            n for n in (await session.execute(select(Color.name))).scalars()
        }
        for name, hex_, family in COLORS:
            if name not in existing_colors:
                session.add(Color(name=name, hex=hex_, family=family))

        # Tags
        existing_tags = {
            n for n in (await session.execute(select(Tag.name))).scalars()
        }
        for name in TAGS:
            if name not in existing_tags:
                session.add(Tag(name=name))

        await session.commit()
    print("Seed complete: categories, colors, and tags are in place.")


if __name__ == "__main__":
    asyncio.run(seed())
