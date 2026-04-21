"""add cache_lookup_log table

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-04-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cache_lookup_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("origin", sa.String(length=3), nullable=False),
        sa.Column("destination", sa.String(length=3), nullable=False),
        sa.Column("hit", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("looked_up_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cache_lookup_log_origin", "cache_lookup_log", ["origin"])
    op.create_index("ix_cache_lookup_log_destination", "cache_lookup_log", ["destination"])
    op.create_index("ix_cache_lookup_log_hit", "cache_lookup_log", ["hit"])
    op.create_index("ix_cache_lookup_log_looked_up_at", "cache_lookup_log", ["looked_up_at"])


def downgrade() -> None:
    op.drop_index("ix_cache_lookup_log_looked_up_at", table_name="cache_lookup_log")
    op.drop_index("ix_cache_lookup_log_hit", table_name="cache_lookup_log")
    op.drop_index("ix_cache_lookup_log_destination", table_name="cache_lookup_log")
    op.drop_index("ix_cache_lookup_log_origin", table_name="cache_lookup_log")
    op.drop_table("cache_lookup_log")
