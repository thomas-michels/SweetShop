from psycopg import Connection
from psycopg.rows import dict_row
from .base_connection import DBConnection
from app.core.configs import get_environment

_env = get_environment()


class PGConnection(DBConnection):

    def __init__(self, conn: Connection) -> None:
        self.conn = conn
        self.cursor = None

    def execute(self, sql_statement: str, values: dict = None, many: bool = False):
        sql = self.set_client(sql_statement)

        self.cursor = self.conn.cursor(row_factory=dict_row)
        self.cursor.execute(sql, values)
        return self.cursor.fetchall() if many else self.cursor.fetchone()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def set_client(self, sql_statement: str) -> str:
        return sql_statement.replace("public", _env.ENVIRONMENT)
