from fastapi import FastAPI, Request
from psycopg_pool import ConnectionPool
from contextlib import asynccontextmanager
from app.core.configs import get_environment, get_logger

_env = get_environment()
_logger = get_logger(__name__)


def start_pool() -> ConnectionPool:
    return ConnectionPool(
        conninfo=(
            f"host={_env.DATABASE_HOST} "
            f"port={_env.DATABASE_PORT} "
            f"user={_env.DATABASE_USER} "
            f"password={_env.DATABASE_PASSWORD} "
            f"dbname={_env.DATABASE_NAME}"),
        min_size=_env.DATABASE_MIN_CONNECTIONS,
        max_size=_env.DATABASE_MAX_CONNECTIONS,
        name=_env.APPLICATION_NAME
    )

@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    _logger.info("Connecting to PostgreSQL")

    app.state.pool = start_pool()

    _logger.info("Connection established")

    yield

    close_db_connection(app=app)


def close_db_connection(app: FastAPI) -> None:
    _logger.info("Closing connection to database")

    app.state.pool.close()

    _logger.info("Connection closed")
