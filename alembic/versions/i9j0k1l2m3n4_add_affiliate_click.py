"""add affiliate_click table

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-04-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "affiliate_click",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("origin", sa.String(length=3), nullable=False),
        sa.Column("destination", sa.String(length=3), nullable=False),
        sa.Column("departure_date", sa.Date(), nullable=True),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("referer", sa.String(length=500), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="public_route"),
        sa.Column("clicked_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_affiliate_click_origin", "affiliate_click", ["origin"])
    op.create_index("ix_affiliate_click_destination", "affiliate_click", ["destination"])
    op.create_index("ix_affiliate_click_user_id", "affiliate_click", ["user_id"])
    op.create_index("ix_affiliate_click_clicked_at", "affiliate_click", ["clicked_at"])


def downgrade() -> None:
    op.drop_index("ix_affiliate_click_clicked_at", table_name="affiliate_click")
    op.drop_index("ix_affiliate_click_user_id", table_name="affiliate_click")
    op.drop_index("ix_affiliate_click_destination", table_name="affiliate_click")
    op.drop_index("ix_affiliate_click_origin", table_name="affiliate_click")
    op.drop_table("affiliate_click")
