from psycopg import Connection


class Repository:

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    @property
    def conn(self) -> Connection:
        return self._conn
