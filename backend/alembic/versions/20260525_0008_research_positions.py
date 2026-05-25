"""research positions

Revision ID: 20260525_0008
Revises: 20260525_0007
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260525_0008"
down_revision = "20260525_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("research_positions"):
        return
    op.create_table(
        "research_positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("position_type", sa.String(length=20), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("theme", sa.String(length=120), nullable=True),
        sa.Column("thesis", sa.Text(), nullable=True),
        sa.Column("conviction", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("average_cost", sa.Float(), nullable=True),
        sa.Column("current_price", sa.Float(), nullable=True),
        sa.Column("contracts", sa.Integer(), nullable=True),
        sa.Column("strike_price", sa.Float(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("premium_paid", sa.Float(), nullable=True),
        sa.Column("current_contract_price", sa.Float(), nullable=True),
        sa.Column("break_even", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_positions_id"), "research_positions", ["id"], unique=False)
    op.create_index(op.f("ix_research_positions_symbol"), "research_positions", ["symbol"], unique=False)


def downgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("research_positions"):
        return
    op.drop_index(op.f("ix_research_positions_symbol"), table_name="research_positions")
    op.drop_index(op.f("ix_research_positions_id"), table_name="research_positions")
    op.drop_table("research_positions")
