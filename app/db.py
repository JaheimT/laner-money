"""Database connection, migrations and sessions.

All database access goes through SQLAlchemy's ORM, which always sends
values as bound parameters, so user input is never pasted into SQL text.
"""

import datetime
import os
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Where the SQLite file lives. Configurable so Docker can put it in a volume
# (/data/laner.db). Relative paths resolve from the directory the app is
# started in (the repo root during development).
DB_PATH = Path(os.environ.get("LANER_DB_PATH", "data/laner.db"))
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def run_migrations(engine) -> None:
    """Bring the database schema up to date. Safe to run on every start."""
    from alembic import command
    from alembic.config import Config

    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        tables = inspect(conn).get_table_names()
        # Databases made before Alembic (M0) already have the transactions
        # table: mark them as being at the baseline instead of recreating it.
        if "transactions" in tables and "alembic_version" not in tables:
            command.stamp(cfg, "0001")
        command.upgrade(cfg, "head")


def make_engine(path: Path = DB_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    run_migrations(engine)
    # The file holds financial data: owner read/write only.
    os.chmod(path, 0o600)
    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session():
    """FastAPI dependency: one session per request, always closed."""
    with SessionLocal() as session:
        yield session


def utcnow() -> datetime.datetime:
    """Naive UTC 'now' (SQLite has no time zones; everything stored is UTC)."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
