"""add synthetic project corridor geometry

Revision ID: 5a8c1d2e3f40
Revises: 3e6d7f8a9b10
Create Date: 2026-09-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "5a8c1d2e3f40"
down_revision: Union[str, Sequence[str], None] = "3e6d7f8a9b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("corridor_geometry", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "corridor_geometry")
