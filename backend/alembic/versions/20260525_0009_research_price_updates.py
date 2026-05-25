"""research price updates

Revision ID: 20260525_0009
Revises: 20260525_0008
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260525_0009"
down_revision = "20260525_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("research_positions")}
    if "option_type" not in columns:
        op.add_column("research_positions", sa.Column("option_type", sa.String(length=10), nullable=True))
        op.execute("UPDATE research_positions SET option_type = 'call' WHERE option_type IS NULL")
    if "price_updated_at" not in columns:
        op.add_column("research_positions", sa.Column("price_updated_at", sa.DateTime(), nullable=True))
    if "price_update_source" not in columns:
        op.add_column("research_positions", sa.Column("price_update_source", sa.String(length=40), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("research_positions")}
    if "price_update_source" in columns:
        op.drop_column("research_positions", "price_update_source")
    if "price_updated_at" in columns:
        op.drop_column("research_positions", "price_updated_at")
    if "option_type" in columns:
        op.drop_column("research_positions", "option_type")
