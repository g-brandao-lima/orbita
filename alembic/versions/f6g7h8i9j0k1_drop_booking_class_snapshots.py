"""drop booking_class_snapshots table (legacy from v1.0 Amadeus integration)

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-04-20 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6g7h8i9j0k1"
down_revision: Union[str, None] = "e5f6g7h8i9j0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("booking_class_snapshots")


def downgrade() -> None:
    op.create_table(
        "booking_class_snapshots",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("flight_snapshot_id", sa.Integer(), nullable=False),
        sa.Column("class_code", sa.String(length=3), nullable=False),
        sa.Column("seats_available", sa.Integer(), nullable=False),
        sa.Column("segment_direction", sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(["flight_snapshot_id"], ["flight_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
