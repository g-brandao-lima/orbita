"""cleanup snapshots with wrong currency (USD stored as BRL)

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-04-01 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All existing snapshots were collected with USD prices stored as BRL
    # due to fast-flights defaulting to US currency on Render servers.
    # Signals derived from those snapshots are also invalid.
    op.execute("DELETE FROM detected_signals")
    op.execute("DELETE FROM booking_class_snapshots")
    op.execute("DELETE FROM flight_snapshots")


def downgrade() -> None:
    # Data deletion is irreversible
    pass
