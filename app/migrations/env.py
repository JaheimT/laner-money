"""Alembic environment. The app passes its own connection in
(models.run_migrations); the `alembic` CLI uses LANER_DB_PATH instead."""

import os

from alembic import context
from sqlalchemy import create_engine

from app.models import Base

target_metadata = Base.metadata


def run(connection):
    # render_as_batch: SQLite can't ALTER most things in place, so Alembic
    # rebuilds the table instead. Needed for future column changes.
    context.configure(connection=connection, target_metadata=target_metadata,
                      render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


connection = context.config.attributes.get("connection")
if connection is not None:
    run(connection)
else:
    path = os.environ.get("LANER_DB_PATH", "data/laner.db")
    with create_engine(f"sqlite:///{path}").begin() as conn:
        run(conn)
