from typing import List

from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import Product, ProductInDB
from .queries import queries

_logger = get_logger(__name__)


class ProductRepository(Repository):
    def __init__(self, connection: Connection) -> None:
        super().__init__(connection)
        self.queries = queries

    async def create(self, product: Product) -> ProductInDB:
        try:
            raw_product = self.queries.create_product(
                conn=self.conn,
                name=product.name,
                unit_cost=product.unit_cost,
                unit_price=product.unit_price,
            )

            return self.__build_product(raw_product=raw_product)

        except UniqueViolation as error:
            raise UnprocessableEntity(message="Email already in use")

        except Exception as error:
            _logger.error(f"Error on create_user: {str(error)}")
            raise UnprocessableEntity(message="Error on create new user")

    async def update(self, user: UserInDB) -> UserInDB:
        try:
            raw_user = self.queries.update_user_by_id(
                conn=self.conn,
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
            )

            return self.__build_product(raw_user=raw_user)

        except UniqueViolation as error:
            raise UnprocessableEntity(message="Email already in use")

        except Exception as error:
            _logger.error(f"Error on update_user: {str(error)}")
            raise UnprocessableEntity(message="Error on update user")

    async def select_by_id(self, id: int) -> UserInDB:
        try:
            raw_user = self.queries.select_user_by_id(conn=self.conn, id=id)

            return self.__build_product(raw_user=raw_user)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"User #{id} not found")

    async def select_by_query(self, query: str) -> List[ProductInDB]:
        try:
            raw_products = self.queries.select_products_by_query(
                conn=self.conn, query=query
            )

            products = []

            for raw_product in raw_products:
                products.append(self.__build_product(raw_product=raw_product))

            return products

        except Exception as error:
            _logger.error(f"Error on select_by_query: {str(error)}")
            raise NotFoundError(message=f"User with email {email} not found")

    async def select_all(self) -> List[ProductInDB]:
        try:
            raw_products = self.queries.select_products(conn=self.conn)

            products = []

            for raw_product in raw_products:
                products.append(self.__build_product(raw_product=raw_product))

            return products

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Users not found")

    async def delete_by_id(self, id: int) -> ProductInDB:
        try:
            raw_product = self.queries.delete_product_by_id(conn=self.conn, id=id)

            return self.__build_product(raw_product=raw_product)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Product #{id} not found")

    def __build_product(self, raw_product: tuple) -> ProductInDB:
        return ProductInDB(
            id=raw_product[0],
            name=raw_product[1],
            unit_cost=raw_product[2],
            unit_price=raw_product[3],
            is_active=raw_product[5],
            created_at=raw_product[6],
            updated_at=raw_product[7],
        )
