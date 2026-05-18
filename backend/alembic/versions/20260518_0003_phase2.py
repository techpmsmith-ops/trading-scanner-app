"""phase 2 signals alerts predictions

Revision ID: 20260518_0003
Revises: 20260516_0002
Create Date: 2026-05-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260518_0003"
down_revision: Union[str, None] = "20260516_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = set(inspect(op.get_bind()).get_table_names())
    if "daily_recommendations" not in existing:
        op.create_table(
            "daily_recommendations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("recommendation_date", sa.Date(), nullable=False),
            sa.Column("scan_run_id", sa.Integer(), nullable=False),
            sa.Column("scan_result_id", sa.Integer(), nullable=False),
            sa.Column("symbol", sa.String(length=16), nullable=False),
            sa.Column("rank", sa.Integer(), nullable=False),
            sa.Column("score_total", sa.Integer(), nullable=False),
            sa.Column("setup_types", sa.JSON(), nullable=False),
            sa.Column("risk_flags", sa.JSON(), nullable=False),
            sa.Column("rationale", sa.Text(), nullable=False),
            sa.Column("disclaimer", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
            sa.ForeignKeyConstraint(["scan_result_id"], ["scan_results.id"]),
            sa.UniqueConstraint("recommendation_date", "rank", name="uq_daily_recommendations_date_rank"),
        )
        op.create_index(op.f("ix_daily_recommendations_id"), "daily_recommendations", ["id"])
        op.create_index(op.f("ix_daily_recommendations_recommendation_date"), "daily_recommendations", ["recommendation_date"])
        op.create_index(op.f("ix_daily_recommendations_scan_run_id"), "daily_recommendations", ["scan_run_id"])
        op.create_index(op.f("ix_daily_recommendations_scan_result_id"), "daily_recommendations", ["scan_result_id"])
        op.create_index(op.f("ix_daily_recommendations_symbol"), "daily_recommendations", ["symbol"])

    if "weekly_predictions" not in existing:
        op.create_table(
            "weekly_predictions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("week_start", sa.Date(), nullable=False),
            sa.Column("week_end", sa.Date(), nullable=False),
            sa.Column("symbol", sa.String(length=16), nullable=False),
            sa.Column("scan_run_id", sa.Integer(), nullable=True),
            sa.Column("scan_result_id", sa.Integer(), nullable=True),
            sa.Column("direction", sa.String(length=20), nullable=False),
            sa.Column("predicted_return_pct", sa.Float(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("score_total", sa.Integer(), nullable=False),
            sa.Column("component_scores", sa.JSON(), nullable=False),
            sa.Column("rationale", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("start_price", sa.Float(), nullable=True),
            sa.Column("end_price", sa.Float(), nullable=True),
            sa.Column("actual_return_pct", sa.Float(), nullable=True),
            sa.Column("outcome", sa.String(length=20), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("evaluated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"]),
            sa.ForeignKeyConstraint(["scan_result_id"], ["scan_results.id"]),
            sa.UniqueConstraint("week_start", "symbol", name="uq_weekly_predictions_week_symbol"),
        )
        op.create_index(op.f("ix_weekly_predictions_id"), "weekly_predictions", ["id"])
        op.create_index(op.f("ix_weekly_predictions_week_start"), "weekly_predictions", ["week_start"])
        op.create_index(op.f("ix_weekly_predictions_week_end"), "weekly_predictions", ["week_end"])
        op.create_index(op.f("ix_weekly_predictions_symbol"), "weekly_predictions", ["symbol"])

    if "scoring_weights" not in existing:
        op.create_table(
            "scoring_weights",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("effective_date", sa.Date(), nullable=False),
            sa.Column("weights", sa.JSON(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index(op.f("ix_scoring_weights_id"), "scoring_weights", ["id"])
        op.create_index(op.f("ix_scoring_weights_effective_date"), "scoring_weights", ["effective_date"])

    if "alert_subscriptions" not in existing:
        op.create_table(
            "alert_subscriptions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("channel", sa.String(length=20), nullable=False),
            sa.Column("destination_label", sa.String(length=255), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("alert_types", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index(op.f("ix_alert_subscriptions_id"), "alert_subscriptions", ["id"])
        op.create_index(op.f("ix_alert_subscriptions_channel"), "alert_subscriptions", ["channel"])


def downgrade() -> None:
    op.drop_index(op.f("ix_alert_subscriptions_channel"), table_name="alert_subscriptions")
    op.drop_index(op.f("ix_alert_subscriptions_id"), table_name="alert_subscriptions")
    op.drop_table("alert_subscriptions")
    op.drop_index(op.f("ix_scoring_weights_effective_date"), table_name="scoring_weights")
    op.drop_index(op.f("ix_scoring_weights_id"), table_name="scoring_weights")
    op.drop_table("scoring_weights")
    op.drop_index(op.f("ix_weekly_predictions_symbol"), table_name="weekly_predictions")
    op.drop_index(op.f("ix_weekly_predictions_week_end"), table_name="weekly_predictions")
    op.drop_index(op.f("ix_weekly_predictions_week_start"), table_name="weekly_predictions")
    op.drop_index(op.f("ix_weekly_predictions_id"), table_name="weekly_predictions")
    op.drop_table("weekly_predictions")
    op.drop_index(op.f("ix_daily_recommendations_symbol"), table_name="daily_recommendations")
    op.drop_index(op.f("ix_daily_recommendations_scan_result_id"), table_name="daily_recommendations")
    op.drop_index(op.f("ix_daily_recommendations_scan_run_id"), table_name="daily_recommendations")
    op.drop_index(op.f("ix_daily_recommendations_recommendation_date"), table_name="daily_recommendations")
    op.drop_index(op.f("ix_daily_recommendations_id"), table_name="daily_recommendations")
    op.drop_table("daily_recommendations")
