"""prediction outcome reason

Revision ID: 20260524_0005
Revises: 20260523_0004
Create Date: 2026-05-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260524_0005"
down_revision: Union[str, None] = "20260523_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("weekly_predictions")}
    if "outcome_reason" not in columns:
        op.add_column("weekly_predictions", sa.Column("outcome_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("weekly_predictions")}
    if "outcome_reason" in columns:
        op.drop_column("weekly_predictions", "outcome_reason")
