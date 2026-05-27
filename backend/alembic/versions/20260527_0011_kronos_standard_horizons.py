"""kronos standard horizons

Revision ID: 20260527_0011
Revises: 20260526_0010
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260527_0011"
down_revision = "20260526_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("kronos_prediction_evaluations")}
    if "horizon_key" not in columns:
        op.add_column("kronos_prediction_evaluations", sa.Column("horizon_key", sa.String(length=40), nullable=True))
        op.execute("UPDATE kronos_prediction_evaluations SET horizon_key = 'one_week' WHERE horizon_key IS NULL")
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("kronos_prediction_evaluations")}
    if op.f("ix_kronos_prediction_evaluations_horizon_key") not in indexes:
        op.create_index(op.f("ix_kronos_prediction_evaluations_horizon_key"), "kronos_prediction_evaluations", ["horizon_key"], unique=False)


def downgrade() -> None:
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("kronos_prediction_evaluations")}
    if op.f("ix_kronos_prediction_evaluations_horizon_key") in indexes:
        op.drop_index(op.f("ix_kronos_prediction_evaluations_horizon_key"), table_name="kronos_prediction_evaluations")
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("kronos_prediction_evaluations")}
    if "horizon_key" in columns:
        op.drop_column("kronos_prediction_evaluations", "horizon_key")
