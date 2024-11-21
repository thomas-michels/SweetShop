from typing import List

from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.crud.customers.repositories import CustomerRepository
from app.crud.tags.repositories import TagRepository
from .schemas import CompleteProduct, CompleteOrder, Order, OrderInDB, OrderStatus, RequestedProduct, UpdateOrder
from .repositories import OrderRepository
from app.crud.products.repositories import ProductRepository
from app.core.configs import get_logger

logger = get_logger(__name__)


class OrderServices:

    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        tag_repository: TagRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self.__order_repository = order_repository
        self.__product_repository = product_repository
        self.__tag_repository = tag_repository
        self.__customer_repository = customer_repository

    async def create(self, order: Order) -> CompleteOrder:
        value = await self.__calculate_order_value(order.products)

        if order.customer_id is not None:
            await self.__customer_repository.select_by_id(id=order.customer_id)

        for product in order.products:
            await self.__product_repository.select_by_id(id=product.product_id)

        for tag in order.tags:
            await self.__tag_repository.select_by_id(id=tag)

        order_in_db = await self.__order_repository.create(order=order, value=value)

        return await self.__build_complete_order(order_in_db)

    async def update(self, id: str, updated_order: UpdateOrder) -> CompleteOrder:
        order_in_db = await self.search_by_id(id=id)

        if order_in_db.status == OrderStatus.DONE:
            logger.warning(f"Order cannot be updated if is done")
            return

        if updated_order.customer_id is not None:
            await self.__customer_repository.select_by_id(id=updated_order.customer_id)

        if updated_order.products is not None:
            for product in updated_order.products:
                await self.__product_repository.select_by_id(id=product.product_id)

            value = await self.__calculate_order_value(updated_order.products)
            order_in_db.value = value

        if updated_order.tags is not None:
            for tag in updated_order.tags:
                await self.__tag_repository.select_by_id(id=tag)

        is_updated = order_in_db.validate_updated_fields(update_order=updated_order)

        if is_updated:
            order_in_db = await self.__order_repository.update(
                order_id=order_in_db.id,
                order=updated_order.model_dump(exclude_none=True)
            )

        return await self.__build_complete_order(order_in_db)

    async def search_by_id(self, id: str) -> CompleteOrder:
        order_in_db = await self.__order_repository.select_by_id(id=id)

        return await self.__build_complete_order(order_in_db)

    async def search_all(self, status: OrderStatus, customer_id: str) -> List[CompleteOrder]:
        orders = await self.__order_repository.select_all(status=status, customer_id=customer_id)
        complete_orders = []

        for order in orders:
            complete_orders.append(await self.__build_complete_order(order))

        return complete_orders

    async def delete_by_id(self, id: str) -> CompleteOrder:
        order_in_db = await self.__order_repository.delete_by_id(id=id)
        return await self.__build_complete_order(order_in_db)

    async def __build_complete_order(self, order_in_db: OrderInDB) -> CompleteOrder:
        complete_order = CompleteOrder(
            is_active=order_in_db.is_active,
            created_at=order_in_db.created_at,
            updated_at=order_in_db.updated_at,
            delivery=order_in_db.delivery,
            id=order_in_db.id,
            preparation_date=order_in_db.preparation_date,
            status=order_in_db.status,
            value=order_in_db.value,
            reason_id=order_in_db.reason_id
        )
        complete_order.products = []

        if order_in_db.customer_id is not None:
            complete_order.customer = await self.__customer_repository.select_by_id(id=order_in_db.customer_id)

        for product in order_in_db.products:
            product_in_db = await self.__product_repository.select_by_id(
                id=product.product_id
            )

            complete_product = CompleteProduct(
                product=product_in_db,
                quantity=product.quantity
            )

            complete_order.products.append(complete_product)

        complete_order.tags = []

        for tag in order_in_db.tags:
            tag_in_db = await self.__tag_repository.select_by_id(id=tag)

            complete_order.tags.append(tag_in_db)

        return complete_order

    async def __calculate_order_value(self, products: List[RequestedProduct]) -> float:
        value = 0
        for product in products:
            try:
                product_in_db = await self.__product_repository.select_by_id(id=product.product_id)

                value += (product_in_db.unit_price * product.quantity)

            except NotFoundError:
                raise UnprocessableEntity(message=f"Product {product.product_id} is invalid!")

        return value
