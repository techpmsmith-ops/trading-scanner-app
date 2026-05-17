"""add scan duration

Revision ID: 20260516_0002
Revises: 20260516_0001
Create Date: 2026-05-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260516_0002"
down_revision: Union[str, None] = "20260516_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("scan_runs")}
    if "duration_seconds" not in columns:
        op.add_column("scan_runs", sa.Column("duration_seconds", sa.Float(), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("scan_runs")}
    if "duration_seconds" in columns:
        op.drop_column("scan_runs", "duration_seconds")
