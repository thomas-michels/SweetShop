import aiosql
import pathlib
from psycopg import Connection

class ProductsQueriesMixin:

    def create_product(
        self,
        conn: Connection,
        name: str,
        unit_price: float,
        unit_cost: float
    ): ...

    def select_product_by_id(
        self,
        conn: Connection,
        id: int
    ): ...

    def select_products_by_query(
        self,
        conn: Connection,
        query: str
    ): ...

    def select_products(
        self,
        conn: Connection
    ): ...

    def update_product_by_id(
        self,
        conn: Connection,
        id: int,
        name: str,
        unit_price: float,
        unit_cost: float
    ): ...

    def delete_product_by_id(
        self,
        conn: Connection,
        id: int
    ): ...

queries: ProductsQueriesMixin = aiosql.from_path(pathlib.Path(__file__).parent / "queries.sql", driver_adapter="psycopg")
