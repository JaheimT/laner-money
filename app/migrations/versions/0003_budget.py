"""Budget: overall spending budget, category limits, and categories that
don't count toward the spending budget.

Revision ID: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spending_budget",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("amount_pence", sa.Integer, nullable=False),
        sa.Column("period", sa.String(5), nullable=False),
    )
    op.create_table(
        "category_budgets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("category", sa.String(50), nullable=False, unique=True),
        sa.Column("amount_pence", sa.Integer, nullable=False),
        sa.Column("period", sa.String(5), nullable=False),
    )
    op.create_table(
        "excluded_categories",
        sa.Column("category", sa.String(50), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("excluded_categories")
    op.drop_table("category_budgets")
    op.drop_table("spending_budget")
