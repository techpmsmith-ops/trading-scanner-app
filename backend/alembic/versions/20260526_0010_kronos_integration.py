"""kronos integration

Revision ID: 20260526_0010
Revises: 20260525_0009
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260526_0010"
down_revision = "20260525_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    scan_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("scan_results")}
    additions = [
        ("score_kronos", sa.Column("score_kronos", sa.Integer(), nullable=True)),
        ("kronos_enabled", sa.Column("kronos_enabled", sa.Boolean(), nullable=True)),
        ("kronos_model_name", sa.Column("kronos_model_name", sa.String(length=120), nullable=True)),
        ("kronos_bias", sa.Column("kronos_bias", sa.String(length=20), nullable=True)),
        ("kronos_confidence", sa.Column("kronos_confidence", sa.Float(), nullable=True)),
        ("kronos_expected_range_low", sa.Column("kronos_expected_range_low", sa.Float(), nullable=True)),
        ("kronos_expected_range_high", sa.Column("kronos_expected_range_high", sa.Float(), nullable=True)),
        ("kronos_volatility_estimate", sa.Column("kronos_volatility_estimate", sa.Float(), nullable=True)),
        ("kronos_summary", sa.Column("kronos_summary", sa.Text(), nullable=True)),
        ("kronos_raw_output_json", sa.Column("kronos_raw_output_json", sa.JSON(), nullable=True)),
        ("kronos_error", sa.Column("kronos_error", sa.Text(), nullable=True)),
    ]
    for name, column in additions:
        if name not in scan_columns:
            op.add_column("scan_results", column)
    op.execute("UPDATE scan_results SET score_kronos = 0 WHERE score_kronos IS NULL")
    op.execute("UPDATE scan_results SET kronos_enabled = 0 WHERE kronos_enabled IS NULL")

    focus_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("focus_group_analyses")}
    if "kronos" not in focus_columns:
        op.add_column("focus_group_analyses", sa.Column("kronos", sa.JSON(), nullable=True))

    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "kronos_prediction_evaluations" not in tables:
        op.create_table(
            "kronos_prediction_evaluations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("scan_result_id", sa.Integer(), nullable=True),
            sa.Column("predicted_direction", sa.String(length=20), nullable=False),
            sa.Column("predicted_range_low", sa.Float(), nullable=True),
            sa.Column("predicted_range_high", sa.Float(), nullable=True),
            sa.Column("actual_close_after_horizon", sa.Float(), nullable=True),
            sa.Column("actual_direction", sa.String(length=20), nullable=True),
            sa.Column("direction_correct", sa.Boolean(), nullable=True),
            sa.Column("range_hit", sa.Boolean(), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=False),
            sa.Column("model_name", sa.String(length=120), nullable=False),
            sa.Column("symbol", sa.String(length=16), nullable=False),
            sa.Column("timeframe", sa.String(length=20), nullable=False),
            sa.Column("forecast_horizon", sa.Integer(), nullable=False),
            sa.Column("prediction_created_at", sa.DateTime(), nullable=False),
            sa.Column("evaluation_completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["scan_result_id"], ["scan_results.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("kronos_prediction_evaluations")}
    if op.f("ix_kronos_prediction_evaluations_id") not in indexes:
        op.create_index(op.f("ix_kronos_prediction_evaluations_id"), "kronos_prediction_evaluations", ["id"], unique=False)
    if op.f("ix_kronos_prediction_evaluations_scan_result_id") not in indexes:
        op.create_index(op.f("ix_kronos_prediction_evaluations_scan_result_id"), "kronos_prediction_evaluations", ["scan_result_id"], unique=False)
    if op.f("ix_kronos_prediction_evaluations_symbol") not in indexes:
        op.create_index(op.f("ix_kronos_prediction_evaluations_symbol"), "kronos_prediction_evaluations", ["symbol"], unique=False)
    if op.f("ix_kronos_prediction_evaluations_prediction_created_at") not in indexes:
        op.create_index(op.f("ix_kronos_prediction_evaluations_prediction_created_at"), "kronos_prediction_evaluations", ["prediction_created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_kronos_prediction_evaluations_prediction_created_at"), table_name="kronos_prediction_evaluations")
    op.drop_index(op.f("ix_kronos_prediction_evaluations_symbol"), table_name="kronos_prediction_evaluations")
    op.drop_index(op.f("ix_kronos_prediction_evaluations_scan_result_id"), table_name="kronos_prediction_evaluations")
    op.drop_index(op.f("ix_kronos_prediction_evaluations_id"), table_name="kronos_prediction_evaluations")
    op.drop_table("kronos_prediction_evaluations")
    focus_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("focus_group_analyses")}
    if "kronos" in focus_columns:
        op.drop_column("focus_group_analyses", "kronos")
    scan_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("scan_results")}
    for name in [
        "kronos_error",
        "kronos_raw_output_json",
        "kronos_summary",
        "kronos_volatility_estimate",
        "kronos_expected_range_high",
        "kronos_expected_range_low",
        "kronos_confidence",
        "kronos_bias",
        "kronos_model_name",
        "kronos_enabled",
        "score_kronos",
    ]:
        if name in scan_columns:
            op.drop_column("scan_results", name)
