"""weekly evaluation reports

Revision ID: 20260523_0004
Revises: 20260518_0003
Create Date: 2026-05-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260523_0004"
down_revision: Union[str, None] = "20260518_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    prediction_columns = {column["name"] for column in inspector.get_columns("weekly_predictions")}
    if "false_positive" not in prediction_columns:
        op.add_column("weekly_predictions", sa.Column("false_positive", sa.Boolean(), nullable=False, server_default=sa.false()))
    if "news_sentiment_score" not in prediction_columns:
        op.add_column("weekly_predictions", sa.Column("news_sentiment_score", sa.Float(), nullable=True))
    if "news_sentiment_label" not in prediction_columns:
        op.add_column("weekly_predictions", sa.Column("news_sentiment_label", sa.String(length=20), nullable=True))

    if "weekly_evaluation_reports" not in set(inspector.get_table_names()):
        op.create_table(
            "weekly_evaluation_reports",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("week_start", sa.Date(), nullable=False),
            sa.Column("week_end", sa.Date(), nullable=False),
            sa.Column("evaluated_count", sa.Integer(), nullable=False),
            sa.Column("accuracy", sa.Float(), nullable=False),
            sa.Column("wins", sa.Integer(), nullable=False),
            sa.Column("losses", sa.Integer(), nullable=False),
            sa.Column("win_loss_ratio", sa.Float(), nullable=True),
            sa.Column("false_positives", sa.Integer(), nullable=False),
            sa.Column("indicator_effectiveness", sa.JSON(), nullable=False),
            sa.Column("news_sentiment_correlation", sa.JSON(), nullable=False),
            sa.Column("market_conditions", sa.JSON(), nullable=False),
            sa.Column("weight_changes", sa.JSON(), nullable=False),
            sa.Column("confidence_notes", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("week_start", "week_end", name="uq_weekly_evaluation_reports_week"),
        )
        op.create_index(op.f("ix_weekly_evaluation_reports_id"), "weekly_evaluation_reports", ["id"])
        op.create_index(op.f("ix_weekly_evaluation_reports_week_start"), "weekly_evaluation_reports", ["week_start"])
        op.create_index(op.f("ix_weekly_evaluation_reports_week_end"), "weekly_evaluation_reports", ["week_end"])


def downgrade() -> None:
    op.drop_index(op.f("ix_weekly_evaluation_reports_week_end"), table_name="weekly_evaluation_reports")
    op.drop_index(op.f("ix_weekly_evaluation_reports_week_start"), table_name="weekly_evaluation_reports")
    op.drop_index(op.f("ix_weekly_evaluation_reports_id"), table_name="weekly_evaluation_reports")
    op.drop_table("weekly_evaluation_reports")
    op.drop_column("weekly_predictions", "news_sentiment_label")
    op.drop_column("weekly_predictions", "news_sentiment_score")
    op.drop_column("weekly_predictions", "false_positive")
