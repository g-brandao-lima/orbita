"""add route_cache table

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-04-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, None] = "f6g7h8i9j0k1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "route_cache",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("origin", sa.String(length=3), nullable=False),
        sa.Column("destination", sa.String(length=3), nullable=False),
        sa.Column("departure_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("min_price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="BRL"),
        sa.Column("cached_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="travelpayouts"),
    )
    op.create_index("ix_route_cache_origin", "route_cache", ["origin"])
    op.create_index("ix_route_cache_destination", "route_cache", ["destination"])
    op.create_index("ix_route_cache_departure_date", "route_cache", ["departure_date"])
    op.create_index("ix_route_cache_return_date", "route_cache", ["return_date"])
    op.create_index(
        "ix_route_cache_lookup",
        "route_cache",
        ["origin", "destination", "departure_date", "return_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_route_cache_lookup", table_name="route_cache")
    op.drop_index("ix_route_cache_return_date", table_name="route_cache")
    op.drop_index("ix_route_cache_departure_date", table_name="route_cache")
    op.drop_index("ix_route_cache_destination", table_name="route_cache")
    op.drop_index("ix_route_cache_origin", table_name="route_cache")
    op.drop_table("route_cache")
