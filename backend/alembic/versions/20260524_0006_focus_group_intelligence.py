"""focus group intelligence

Revision ID: 20260524_0006
Revises: 20260524_0005
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260524_0006"
down_revision = "20260524_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("weekly_predictions", sa.Column("predicted_range_low", sa.Float(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("predicted_range_high", sa.Float(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("bullish_probability", sa.Float(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("bearish_probability", sa.Float(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("key_drivers", sa.JSON(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("main_risks", sa.JSON(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("technical_setup", sa.Text(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("sentiment_impact", sa.Text(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("suggested_trade_plan", sa.Text(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("range_hit", sa.Boolean(), nullable=True))
    op.add_column("weekly_predictions", sa.Column("volume_confirmation", sa.String(length=40), nullable=True))
    op.add_column("weekly_predictions", sa.Column("sector_relative_behavior", sa.String(length=80), nullable=True))

    op.create_table(
        "focus_group_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("scan_run_id", sa.Integer(), nullable=True),
        sa.Column("scan_result_id", sa.Integer(), nullable=True),
        sa.Column("bias", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("current_technical_setup", sa.Text(), nullable=False),
        sa.Column("key_catalyst", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("suggested_watch_action", sa.Text(), nullable=False),
        sa.Column("entry_zone", sa.String(length=120), nullable=True),
        sa.Column("stop_loss_area", sa.String(length=120), nullable=True),
        sa.Column("target_zone", sa.String(length=120), nullable=True),
        sa.Column("daily_move_pct", sa.Float(), nullable=True),
        sa.Column("weekly_move_pct", sa.Float(), nullable=True),
        sa.Column("volume_spike", sa.Boolean(), nullable=False),
        sa.Column("relative_volume", sa.Float(), nullable=True),
        sa.Column("indicators", sa.JSON(), nullable=True),
        sa.Column("support_resistance", sa.JSON(), nullable=True),
        sa.Column("catalysts", sa.JSON(), nullable=True),
        sa.Column("relevance", sa.JSON(), nullable=True),
        sa.Column("news_sentiment_score", sa.Float(), nullable=True),
        sa.Column("news_sentiment_label", sa.String(length=20), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_result_id"], ["scan_results.id"]),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_date", "symbol", name="uq_focus_group_analyses_date_symbol"),
    )
    op.create_index(op.f("ix_focus_group_analyses_id"), "focus_group_analyses", ["id"], unique=False)
    op.create_index(op.f("ix_focus_group_analyses_analysis_date"), "focus_group_analyses", ["analysis_date"], unique=False)
    op.create_index(op.f("ix_focus_group_analyses_symbol"), "focus_group_analyses", ["symbol"], unique=False)

    op.create_table(
        "focus_stock_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("behavior_profile", sa.JSON(), nullable=True),
        sa.Column("indicator_weights", sa.JSON(), nullable=True),
        sa.Column("accuracy_stats", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index(op.f("ix_focus_stock_profiles_id"), "focus_stock_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_focus_stock_profiles_symbol"), "focus_stock_profiles", ["symbol"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_focus_stock_profiles_symbol"), table_name="focus_stock_profiles")
    op.drop_index(op.f("ix_focus_stock_profiles_id"), table_name="focus_stock_profiles")
    op.drop_table("focus_stock_profiles")
    op.drop_index(op.f("ix_focus_group_analyses_symbol"), table_name="focus_group_analyses")
    op.drop_index(op.f("ix_focus_group_analyses_analysis_date"), table_name="focus_group_analyses")
    op.drop_index(op.f("ix_focus_group_analyses_id"), table_name="focus_group_analyses")
    op.drop_table("focus_group_analyses")

    for column in [
        "sector_relative_behavior",
        "volume_confirmation",
        "range_hit",
        "suggested_trade_plan",
        "sentiment_impact",
        "technical_setup",
        "main_risks",
        "key_drivers",
        "bearish_probability",
        "bullish_probability",
        "predicted_range_high",
        "predicted_range_low",
    ]:
        op.drop_column("weekly_predictions", column)
