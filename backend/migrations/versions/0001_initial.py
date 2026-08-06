"""empty baseline migration to bootstrap the alembic version table

Revision ID: 0001
Revises:
Create Date: 2026-08-06 00:00:00

The baseline is intentionally empty: it seeds Alembic's version tracking so
subsequent ``alembic revision --autogenerate`` migrations chain cleanly. No
tables are created here.
"""

from typing import Sequence, Union

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: baseline revision only."""


def downgrade() -> None:
    """No-op: baseline revision only."""
