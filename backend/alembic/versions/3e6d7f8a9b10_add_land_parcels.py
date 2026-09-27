"""add prototype land parcels

Revision ID: 3e6d7f8a9b10
Revises: 7a474a39e45b
Create Date: 2026-09-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "3e6d7f8a9b10"
down_revision: Union[str, Sequence[str], None] = "7a474a39e45b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "land_parcels",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("parcel_id", sa.String(length=100), nullable=False),
        sa.Column("ownership_type", sa.String(length=20), nullable=False),
        sa.Column("acquisition_status", sa.String(length=20), nullable=False),
        sa.Column("area_acres", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("geometry", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "parcel_id", name="uq_land_parcels_project_parcel"),
    )
    op.add_column("acquisition_cases", sa.Column("parcel_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_acquisition_cases_parcel_id", "acquisition_cases", "land_parcels", ["parcel_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_acquisition_cases_parcel_id", "acquisition_cases", type_="foreignkey")
    op.drop_column("acquisition_cases", "parcel_id")
    op.drop_table("land_parcels")
