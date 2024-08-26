from typing import List

from app.core.exceptions import NotFoundError, UnprocessableEntity
from .schemas import CompleteItem, CompleteOrder, Order, OrderInDB, UpdateOrder
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

    async def search_by_id(self, id: str) -> CompleteOrder:
        order_in_db = await self.__order_repository.select_by_id(id=id)

        return await self.__build_complete_order(order_in_db)

    async def search_all(self, query: str, user_id: str) -> List[CompleteOrder]:
        orders = await self.__order_repository.select_all(query=query, user_id=user_id)
        complete_orders = []

        for order in orders:
            complete_orders.append(await self.__build_complete_order(order))

        return complete_orders

    async def delete_by_id(self, id: str) -> OrderInDB:
        order_in_db = await self.__order_repository.delete_by_id(id=id)
        return order_in_db

    async def __build_complete_order(self, order_in_db: OrderInDB) -> CompleteOrder:
        complete_order = CompleteOrder(
            is_active=order_in_db.is_active,
            created_at=order_in_db.created_at,
            updated_at=order_in_db.updated_at,
            delivery=order_in_db.delivery,
            id=order_in_db.id,
            preparation_date=order_in_db.preparation_date,
            status=order_in_db.status,
            user_id=order_in_db.user_id,
            value=order_in_db.value,
        )
        complete_order.items = []

        for item in order_in_db.items:
            product_in_db = await self.__product_repository.select_by_id(
                id=item.product_id
            )

            complete_item = CompleteItem(
                product=product_in_db,
                quantity=item.quantity
            )

            complete_order.items.append(complete_item)

        return complete_order

    async def __calculate_order_value(self, order: Order) -> float:
        value = 0
        for item in order.items:
            try:
                product_in_db = await self.__product_repository.select_by_id(id=item.product_id)

                value += (product_in_db.unit_price * item.quantity)

            except NotFoundError:
                raise UnprocessableEntity(message=f"Product {item.product_id} is invalid!")

        return value
