"""weather intelligence metrics

Adds feels-like temperature, humidity, and UV index to the weather cache so
recommendations can reason about the full comfort picture, not just raw
temperature.

Revision ID: a1b2c3d4e5f6
Revises: d22c552b250b
Create Date: 2026-07-18 05:10:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = 'd22c552b250b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('weather_cache', sa.Column('feels_like_c', sa.Float(), nullable=True))
    op.add_column('weather_cache', sa.Column('humidity_pct', sa.Float(), nullable=True))
    op.add_column('weather_cache', sa.Column('uv_index', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('weather_cache', 'uv_index')
    op.drop_column('weather_cache', 'humidity_pct')
    op.drop_column('weather_cache', 'feels_like_c')
