from typing import List

from app.core.exceptions import NotFoundError, UnprocessableEntity
from .schemas import Order, OrderInDB, UpdateOrder
from .repositories import OrderRepository
from app.crud.products.repositories import ProductRepository


class OrderServices:

    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository
    ) -> None:
        self.__order_repository = order_repository
        self.__product_repository = product_repository

    async def create(self, order: Order) -> OrderInDB:
        value = await self.__calculate_order_value(order)

        order_in_db = await self.__order_repository.create(order=order, value=value)

        return order_in_db

    async def update(self, id: str, updated_order: UpdateOrder) -> OrderInDB:
        order_in_db = await self.search_by_id(id=id)

        is_updated = order_in_db.validate_updated_fields(update_order=updated_order)

        if order_in_db.items:
            value = await self.__calculate_order_value(order=order_in_db)
            order_in_db.value = value

        if is_updated:
            order_in_db = await self.__order_repository.update(order=order_in_db)

        return order_in_db

    async def search_by_id(self, id: str) -> OrderInDB:
        order_in_db = await self.__order_repository.select_by_id(id=id)
        return order_in_db

    async def search_all(self, query: str, user_id: str) -> List[OrderInDB]:
        orders = await self.__order_repository.select_all(query=query, user_id=user_id)
        return orders

    async def delete_by_id(self, id: str) -> OrderInDB:
        order_in_db = await self.__order_repository.delete_by_id(id=id)
        return order_in_db

    async def __calculate_order_value(self, order: Order) -> float:
        value = 0
        for item in order.items:
            try:
                product_in_db = await self.__product_repository.select_by_id(id=item.product_id)

                value += (product_in_db.unit_price * item.quantity)

            except NotFoundError:
                raise UnprocessableEntity(message=f"Product {item.product_id} is invalid!")

        return value