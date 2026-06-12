"""add substance manufacturing analysis

Revision ID: 20260612_0002
Revises: 20260611_0001
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260612_0002"
down_revision = "20260611_0001"
branch_labels = None
depends_on = None


JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "substance_manufacturing_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "substance_id",
            sa.String(36),
            sa.ForeignKey("substances.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_quantity", sa.Text()),
        sa.Column("target_grade", sa.Text()),
        sa.Column("intended_use", sa.Text()),
        sa.Column("destination_country", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("route_type", sa.Text()),
        sa.Column("process_overview", sa.Text()),
        sa.Column("required_equipment", JSONB),
        sa.Column("input_materials", JSONB),
        sa.Column("cost_drivers", JSONB),
        sa.Column("cost_model", JSONB),
        sa.Column("sourcing_queries", JSONB),
        sa.Column("compliance_notes", JSONB),
        sa.Column("safety_notes", JSONB),
        sa.Column("blocked_reasons", JSONB),
        sa.Column("confidence", sa.Numeric()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_substance_manufacturing_analyses_substance_id",
        "substance_manufacturing_analyses",
        ["substance_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_substance_manufacturing_analyses_substance_id",
        table_name="substance_manufacturing_analyses",
    )
    op.drop_table("substance_manufacturing_analyses")
