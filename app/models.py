"""Database setup and the Transaction model.

All database access goes through SQLAlchemy's ORM, which always sends
values as bound parameters, so user input is never pasted into SQL text.
"""

import datetime
import os
from pathlib import Path

from sqlalchemy import Date, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

# Where the SQLite file lives. Configurable so the LXC deployment can put it
# somewhere like /var/lib/laner/laner.db. Relative paths resolve from the
# directory the app is started in (the repo root during development).
DB_PATH = Path(os.environ.get("LANER_DB_PATH", "data/laner.db"))

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
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)


def make_engine(path: Path = DB_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    # create_all only creates missing tables; it never alters existing ones.
    # Schema changes later will need a proper migration (e.g. Alembic).
    Base.metadata.create_all(engine)
    # The file holds financial data: owner read/write only.
    os.chmod(path, 0o600)
    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session():
    """FastAPI dependency: one session per request, always closed."""
    with SessionLocal() as session:
        yield session
