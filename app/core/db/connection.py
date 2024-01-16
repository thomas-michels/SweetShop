from typing import Callable, Type
from fastapi import Depends, Request
from psycopg import Connection

from app.core.repositories.base_repository import Repository
    
def _get_connection_from_pool(request: Request):
    with request.app.state.pool.connection() as conn:
        yield conn


def get_repository(
    repo_type: Type[Repository],
) -> Callable[[Connection], Repository]:
    def _get_repo(conn: Connection = Depends(_get_connection_from_pool)) -> Repository:
        return repo_type(conn)

    return _get_repo
