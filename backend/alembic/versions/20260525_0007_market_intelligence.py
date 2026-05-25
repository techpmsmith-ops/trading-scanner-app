"""market intelligence watchlist

Revision ID: 20260525_0007
Revises: 20260524_0006
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20260525_0007"
down_revision = "20260524_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intelligence_watchlist_symbols",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("themes", sa.JSON(), nullable=True),
        sa.Column("thesis", sa.Text(), nullable=True),
        sa.Column("data_sources", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", name="uq_intelligence_watchlist_symbols_symbol"),
    )
    op.create_index(op.f("ix_intelligence_watchlist_symbols_id"), "intelligence_watchlist_symbols", ["id"], unique=False)
    op.create_index(op.f("ix_intelligence_watchlist_symbols_symbol"), "intelligence_watchlist_symbols", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_intelligence_watchlist_symbols_symbol"), table_name="intelligence_watchlist_symbols")
    op.drop_index(op.f("ix_intelligence_watchlist_symbols_id"), table_name="intelligence_watchlist_symbols")
    op.drop_table("intelligence_watchlist_symbols")
