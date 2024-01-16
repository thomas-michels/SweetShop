import aiosql
import pathlib
from psycopg import Connection

class UsersQueriesMixin:

    def create_user(
        self,
        conn: Connection,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
    ): ...

    def select_user_by_id(
        self,
        conn: Connection,
        id: int
    ): ...

    def select_users(
        self,
        conn: Connection
    ): ...

    def update_user_by_id(
        self,
        conn: Connection,
        id: int,
        first_name: str,
        last_name: str,
        email: str,
    ): ...

    def delete_user_by_id(
        self,
        conn: Connection,
        id: int
    ): ...

queries: UsersQueriesMixin = aiosql.from_path(pathlib.Path(__file__).parent / "queries.sql", driver_adapter="psycopg")
