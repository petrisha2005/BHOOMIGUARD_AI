"""Alembic environment configured from the application settings."""

from alembic import context

from app.db.session import engine
from app.models import Base


config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Configure Alembic without opening a database connection."""

    context.configure(
        url=engine.url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Configure Alembic with the application's SQLAlchemy engine."""

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
