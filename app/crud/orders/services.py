from datetime import datetime
from typing import List

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.crud.customers.repositories import CustomerRepository
from app.crud.products.repositories import ProductRepository
from app.crud.shared_schemas.payment import PaymentStatus
from app.crud.tags.repositories import TagRepository

from .repositories import OrderRepository
from .schemas import (
    CompleteOrder,
    DeliveryType,
    Order,
    OrderInDB,
    OrderStatus,
    RequestedProduct,
    RequestOrder,
    StoredProduct,
    UpdateOrder,
)

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

    async def create(self, order: RequestOrder) -> CompleteOrder:
        products = []

        if order.customer_id is not None:
            await self.__customer_repository.select_by_id(id=order.customer_id)

        for product in order.products:
            product_in_db = await self.__product_repository.select_by_id(
                id=product.product_id
            )
            products.append(
                StoredProduct(
                    product_id=product.product_id,
                    quantity=product.quantity,
                    name=product_in_db.name,
                    unit_cost=product_in_db.unit_cost,
                    unit_price=product_in_db.unit_price,
                )
            )

        for tag in order.tags:
            await self.__tag_repository.select_by_id(id=tag)

        total_amount = await self.__calculate_order_total_amount(
            products=order.products,
            additional=order.additional,
            discount=order.discount,
            delivery_value=(
                order.delivery.delivery_value if order.delivery.delivery_value else 0
            ),
        )

        order.products = []
        order = Order.model_validate(order)
        order.products = products

        order_in_db = await self.__order_repository.create(
            order=order, total_amount=total_amount
        )

        return await self.__build_complete_order(order_in_db)

    async def update(self, id: str, updated_order: UpdateOrder) -> CompleteOrder:
        order_in_db = await self.search_by_id(id=id)
        updated_fields = {}

        if updated_order.customer_id is not None:
            await self.__customer_repository.select_by_id(id=updated_order.customer_id)

        if updated_order.products is not None:
            updated_fields["products"] = []

            for product in updated_order.products:
                product_in_db = await self.__product_repository.select_by_id(
                    id=product.product_id
                )
                stored_product = StoredProduct(
                    product_id=product.product_id,
                    quantity=product.quantity,
                    name=product_in_db.name,
                    unit_cost=product_in_db.unit_cost,
                    unit_price=product_in_db.unit_price,
                )
                updated_fields["products"].append(stored_product.model_dump())

            updated_order.products = None

        if updated_order.tags is not None:
            temp_tags = updated_order.tags
            for tag in temp_tags:
                if not await self.__tag_repository.select_by_id(
                    id=tag, raise_404=False
                ):
                    updated_order.tags.remove(tag)

        if updated_order.delivery is not None:
            if (
                order_in_db.delivery.delivery_type == DeliveryType.DELIVERY
                and updated_order.delivery.delivery_type == DeliveryType.WITHDRAWAL
            ):
                updated_order.delivery.delivery_value = 0
                updated_order.delivery.address = None

        delivery_value = (
            order_in_db.delivery.delivery_value
            if order_in_db.delivery.delivery_value is not None
            else 0
        )

        if updated_order.delivery and updated_order.delivery.delivery_value is not None:
            delivery_value = updated_order.delivery.delivery_value

        total_amount = await self.__calculate_order_total_amount(
            products=(
                updated_order.products
                if updated_order.products is not None
                else order_in_db.products
            ),
            additional=(
                updated_order.additional
                if updated_order.additional is not None
                else order_in_db.additional
            ),
            discount=(
                updated_order.discount
                if updated_order.discount is not None
                else order_in_db.discount
            ),
            delivery_value=delivery_value,
        )

        is_updated = order_in_db.validate_updated_fields(update_order=updated_order)

        if is_updated:
            updated_fields.update(updated_order.model_dump(exclude_none=True))
            updated_fields["total_amount"] = total_amount

            order_in_db = await self.__order_repository.update(
                order_id=order_in_db.id, order=updated_fields
            )

        return await self.__build_complete_order(order_in_db)

    async def search_by_id(self, id: str, expand: List[str] = []) -> CompleteOrder:
        order_in_db = await self.__order_repository.select_by_id(id=id)

        return await self.__build_complete_order(order_in_db=order_in_db, expand=expand)

    async def search_all(
        self,
        status: OrderStatus,
        payment_status: List[PaymentStatus],
        delivery_type: DeliveryType,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
        tags: List[str],
        min_total_amount: float,
        max_total_amount: float,
        expand: List[str],
    ) -> List[CompleteOrder]:

        orders = await self.__order_repository.select_all(
            customer_id=customer_id,
            status=status,
            payment_status=payment_status,
            delivery_type=delivery_type,
            start_date=start_date,
            end_date=end_date,
            min_total_amount=min_total_amount,
            max_total_amount=max_total_amount,
            tags=tags,
        )

        complete_orders = []

        for order in orders:
            complete_orders.append(
                await self.__build_complete_order(order_in_db=order, expand=expand)
            )

        return complete_orders

    async def delete_by_id(self, id: str) -> CompleteOrder:
        order_in_db = await self.__order_repository.delete_by_id(id=id)
        return await self.__build_complete_order(order_in_db)

    async def __build_complete_order(
        self, order_in_db: OrderInDB, expand: List[str] = []
    ) -> CompleteOrder:
        complete_order = CompleteOrder(
            id=order_in_db.id,
            organization_id=order_in_db.organization_id,
            customer_id=order_in_db.customer_id,
            customer=order_in_db.customer_id,
            status=order_in_db.status,
            payment_status=order_in_db.payment_status,
            products=order_in_db.products,
            tags=order_in_db.tags,
            delivery=order_in_db.delivery,
            preparation_date=order_in_db.preparation_date,
            order_date=order_in_db.order_date,
            reason_id=order_in_db.reason_id,
            total_amount=order_in_db.total_amount,
            description=order_in_db.description,
            additional=order_in_db.additional,
            discount=order_in_db.discount,
            payments=order_in_db.payments,
            is_active=order_in_db.is_active,
            created_at=order_in_db.created_at,
            updated_at=order_in_db.updated_at,
        )

        if "customers" in expand:
            if order_in_db.customer_id is not None:
                customer = await self.__customer_repository.select_by_id(
                    id=order_in_db.customer_id, raise_404=False
                )

                if customer:
                    complete_order.customer = customer

        if "tags" in expand:
            complete_order.tags = []

            for tag in order_in_db.tags:
                tag_in_db = await self.__tag_repository.select_by_id(
                    id=tag, raise_404=False
                )

                if tag_in_db:
                    complete_order.tags.append(tag_in_db)

        return complete_order

    async def __calculate_order_total_amount(
        self,
        products: List[RequestedProduct],
        delivery_value: float,
        additional: float,
        discount: float,
    ) -> float:
        total_amount = delivery_value + additional - discount

        for product in products:
            try:
                product_in_db = await self.__product_repository.select_by_id(
                    id=product.product_id
                )

                total_amount += product_in_db.unit_price * product.quantity

            except NotFoundError:
                raise UnprocessableEntity(
                    message=f"Product {product.product_id} is invalid!"
                )

        return total_amount
