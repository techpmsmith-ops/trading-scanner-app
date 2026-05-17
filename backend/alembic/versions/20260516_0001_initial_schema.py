"""initial schema

Revision ID: 20260516_0001
Revises:
Create Date: 2026-05-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260516_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(inspect(op.get_bind()).get_table_names())

    if "tickers" not in existing_tables:
        op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index(op.f("ix_tickers_id"), "tickers", ["id"])
        op.create_index(op.f("ix_tickers_symbol"), "tickers", ["symbol"], unique=True)

    if "users" not in existing_tables:
        op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index(op.f("ix_users_id"), "users", ["id"])
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    if "price_bars" not in existing_tables:
        op.create_table(
        "price_bars",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("adjusted_close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticker_id"], ["tickers.id"]),
        sa.UniqueConstraint("ticker_id", "date", name="uq_price_bars_ticker_date"),
        )
        op.create_index(op.f("ix_price_bars_id"), "price_bars", ["id"])
        op.create_index(op.f("ix_price_bars_ticker_id"), "price_bars", ["ticker_id"])
        op.create_index(op.f("ix_price_bars_date"), "price_bars", ["date"])

    if "scan_runs" not in existing_tables:
        op.create_table(
        "scan_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("universe_count", sa.Integer(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        )
        op.create_index(op.f("ix_scan_runs_id"), "scan_runs", ["id"])
        op.create_index(op.f("ix_scan_runs_run_date"), "scan_runs", ["run_date"])

    if "scan_results" not in existing_tables:
        op.create_table(
        "scan_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scan_run_id", sa.Integer(), nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("close_price", sa.Float(), nullable=False),
        sa.Column("score_total", sa.Integer(), nullable=False),
        sa.Column("score_trend", sa.Integer(), nullable=False),
        sa.Column("score_momentum", sa.Integer(), nullable=False),
        sa.Column("score_volume", sa.Integer(), nullable=False),
        sa.Column("score_risk", sa.Integer(), nullable=False),
        sa.Column("score_setup_quality", sa.Integer(), nullable=False),
        sa.Column("setup_types", sa.JSON(), nullable=False),
        sa.Column("risk_flags", sa.JSON(), nullable=False),
        sa.Column("indicators", sa.JSON(), nullable=False),
        sa.Column("entry_zone", sa.Float(), nullable=True),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("target_1", sa.Float(), nullable=True),
        sa.Column("target_2", sa.Float(), nullable=True),
        sa.Column("risk_reward", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.ForeignKeyConstraint(["ticker_id"], ["tickers.id"]),
        sa.UniqueConstraint("scan_run_id", "ticker_id", name="uq_scan_results_run_ticker"),
        )
        op.create_index(op.f("ix_scan_results_id"), "scan_results", ["id"])
        op.create_index(op.f("ix_scan_results_scan_run_id"), "scan_results", ["scan_run_id"])
        op.create_index(op.f("ix_scan_results_ticker_id"), "scan_results", ["ticker_id"])
        op.create_index(op.f("ix_scan_results_symbol"), "scan_results", ["symbol"])

    if "journal_entries" not in existing_tables:
        op.create_table(
        "journal_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("setup_type", sa.String(length=80), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("planned_entry", sa.Float(), nullable=True),
        sa.Column("actual_entry", sa.Float(), nullable=True),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("target_1", sa.Float(), nullable=True),
        sa.Column("target_2", sa.Float(), nullable=True),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("position_size", sa.Float(), nullable=True),
        sa.Column("risk_amount", sa.Float(), nullable=True),
        sa.Column("entry_date", sa.Date(), nullable=True),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("pnl_amount", sa.Float(), nullable=True),
        sa.Column("pnl_percent", sa.Float(), nullable=True),
        sa.Column("result", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("emotions", sa.Text(), nullable=True),
        sa.Column("mistake_tags", sa.JSON(), nullable=True),
        sa.Column("lesson_learned", sa.Text(), nullable=True),
        sa.Column("linked_scan_result_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["linked_scan_result_id"], ["scan_results.id"]),
        )
        op.create_index(op.f("ix_journal_entries_id"), "journal_entries", ["id"])
        op.create_index(op.f("ix_journal_entries_symbol"), "journal_entries", ["symbol"])


def downgrade() -> None:
    op.drop_index(op.f("ix_journal_entries_symbol"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_id"), table_name="journal_entries")
    op.drop_table("journal_entries")
    op.drop_index(op.f("ix_scan_results_symbol"), table_name="scan_results")
    op.drop_index(op.f("ix_scan_results_ticker_id"), table_name="scan_results")
    op.drop_index(op.f("ix_scan_results_scan_run_id"), table_name="scan_results")
    op.drop_index(op.f("ix_scan_results_id"), table_name="scan_results")
    op.drop_table("scan_results")
    op.drop_index(op.f("ix_scan_runs_run_date"), table_name="scan_runs")
    op.drop_index(op.f("ix_scan_runs_id"), table_name="scan_runs")
    op.drop_table("scan_runs")
    op.drop_index(op.f("ix_price_bars_date"), table_name="price_bars")
    op.drop_index(op.f("ix_price_bars_ticker_id"), table_name="price_bars")
    op.drop_index(op.f("ix_price_bars_id"), table_name="price_bars")
    op.drop_table("price_bars")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_tickers_symbol"), table_name="tickers")
    op.drop_index(op.f("ix_tickers_id"), table_name="tickers")
    op.drop_table("tickers")
