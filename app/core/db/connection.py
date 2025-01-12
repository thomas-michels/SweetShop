from contextlib import asynccontextmanager
from fastapi import FastAPI
from mongoengine import connect

from app.core.configs import get_environment, get_logger


_env = get_environment()
_logger = get_logger(__name__)


def start_database():
    connetion = connect(
        host=_env.DATABASE_HOST
    )
    connetion.server_info()


@asynccontextmanager
async def lifespan(app: FastAPI) -> None: # type: ignore
    _logger.info("Connecting to MongoDB")

    start_database()
    app.state.access_token = None
    app.state.cached_users = {}

    _logger.info("Connection established")

    yield
