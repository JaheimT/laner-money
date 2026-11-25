"""Baseline: the transactions table as it was in M0.

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("amount_pence", sa.Integer, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("note", sa.String(200), nullable=True),
        sa.Column("date", sa.Date, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("transactions")
