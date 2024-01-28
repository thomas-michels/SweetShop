import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import MetaData, engine_from_config, pool

sys.path.append(str(pathlib.Path(__file__).resolve().parents[4]))

from app.core.configs import get_environment

SETTINGS = get_environment()
DATABASE_URL = SETTINGS.DATABASE_URL

config = context.config

fileConfig(config.config_file_name)  # type: ignore

target_metadata = MetaData(schema=SETTINGS.ENVIRONMENT)

config.set_main_option("sqlalchemy.url", str(DATABASE_URL))


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_metadata.schema,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.execute(f"create schema if not exists {target_metadata.schema};")
            context.execute(f"set search_path to {target_metadata.schema}")
            context.run_migrations()


run_migrations_online()
