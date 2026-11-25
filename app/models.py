"""The database tables, as Python classes.

No side effects on import (the Alembic command line imports this file).
Connecting and migrating live in app/db.py.

The schema is owned by Alembic migrations (app/migrations), not by
create_all: every change to a model here needs a new migration file.
"""

import datetime

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Shared limits: used by the column definitions here and by validation.py,
# so the database and the form can never disagree.
CATEGORY_MAX = 50
NOTE_MAX = 200


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Whole pence, never a float. Negative = money out, positive = money in.
    amount_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(CATEGORY_MAX), nullable=False)
    note: Mapped[str | None] = mapped_column(String(NOTE_MAX), nullable=True)
    # Stored by SQLite as ISO 8601 text ("2026-11-22").
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)


PERIODS = ("week", "month")   # a budget's home period; weeks run Monday-Sunday


class SpendingBudget(Base):
    """The overall budget for day-to-day spending. At most one row (id=1);
    no row means none is set. The amount is whatever the user chooses."""
    __tablename__ = "spending_budget"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String(5), nullable=False)


class CategoryBudget(Base):
    """A limit for one category, e.g. Eating out £30 a week."""
    __tablename__ = "category_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(CATEGORY_MAX), nullable=False, unique=True)
    amount_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String(5), nullable=False)


class ExcludedCategory(Base):
    """A category that does NOT count toward the overall spending budget
    (e.g. Rent). Every category counts unless it's listed here."""
    __tablename__ = "excluded_categories"

    category: Mapped[str] = mapped_column(String(CATEGORY_MAX), primary_key=True)


class User(Base):
    """The single user. Only ever one row (id=1); holds the password hash."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Argon2id hash in PHC format ("$argon2id$v=19$m=...$salt$hash").
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)


class LoginSession(Base):
    """A logged-in browser. The cookie holds a random token; only its SHA-256
    is stored, so a leaked database (or backup) can't be used to log in."""
    __tablename__ = "login_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
