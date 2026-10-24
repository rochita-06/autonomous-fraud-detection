"""initial schema — transaction_events, investigations

Revision ID: 0001
Revises:
Create Date: 2026-07-09
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transaction_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tx_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=16), nullable=False),
        sa.Column("receiver_id", sa.String(length=16), nullable=False, server_default=""),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("country", sa.String(length=8), nullable=False, server_default=""),
        sa.Column("device_id", sa.String(length=16), nullable=False, server_default=""),
        sa.Column("merchant_category", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("prefilter_risk", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="clean"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_transaction_events_tx_id", "transaction_events", ["tx_id"])
    op.create_index("ix_transaction_events_user_id", "transaction_events", ["user_id"])

    op.create_table(
        "investigations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tx_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("fraud_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.String(length=8), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("reasons", sa.Text(), nullable=False),
        sa.Column("reasoning_log", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("engine", sa.String(length=16), nullable=False, server_default="rules"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_investigations_tx_id", "investigations", ["tx_id"])
    op.create_index("ix_investigations_user_id", "investigations", ["user_id"])


def downgrade() -> None:
    op.drop_table("investigations")
    op.drop_table("transaction_events")
