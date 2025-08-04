from typing import List

from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.builder.order_calculator import OrderCalculator
from app.core.configs import get_logger
from app.core.utils.features import Feature
from app.core.utils.get_start_and_end_day_of_month import get_start_and_end_day_of_month
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.customers.repositories import CustomerRepository
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.products.repositories import ProductRepository
from app.crud.shared_schemas.payment import PaymentStatus
from app.crud.tags.repositories import TagRepository
from app.crud.additional_items.repositories import AdditionalItemRepository

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
    StoredAdditionalItem,
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
        organization_repository: OrganizationRepository,
        additional_item_repository: AdditionalItemRepository,
    ) -> None:
        self.__order_repository = order_repository
        self.__product_repository = product_repository
        self.__tag_repository = tag_repository
        self.__customer_repository = customer_repository
        self.__organization_repository = organization_repository
        self.__additional_item_repository = additional_item_repository

        self.organization_id = self.__order_repository.organization_id

        self.__cache_tags = {}
        self.__cache_customers = {}

        self.__order_calculator = OrderCalculator(
            product_repository=self.__product_repository
        )

    async def create(self, order: RequestOrder) -> CompleteOrder:
        plan_feature = await get_plan_feature(
            organization_id=self.__order_repository.organization_id,
            feature_name=Feature.MAX_ORDERS,
        )

        start_date, end_date = get_start_and_end_day_of_month()

        quantity = await self.__order_repository.select_count_by_date(
            start_date=start_date, end_date=end_date
        )

        if not plan_feature or (
            plan_feature.value != "-" and (quantity + 1) >= int(plan_feature.value)
        ):
            raise UnauthorizedException(
                detail=f"Maximum number of orders reached, Max value: {plan_feature.value}"
            )

        for tag in order.tags:
            await self.__tag_repository.select_by_id(id=tag)

        if order.customer_id is not None:
            await self.__customer_repository.select_by_id(id=order.customer_id)

        products = await self.__validate_products(raw_products=order.products)

        organization = await self.__organization_repository.select_by_id(
            id=self.__order_repository.organization_id
        )

        total_amount = await self.__order_calculator.calculate(
            additional=order.additional,
            delivery_value=order.delivery.delivery_value if order.delivery.delivery_value is not None else 0,
            discount=order.discount,
            products=products
        )

        total_tax = 0

        if organization.tax:
            total_tax = round(total_amount * (organization.tax / 100), 2)
            total_amount += total_tax

        order.products = []
        order = Order.model_validate(order)
        order.products = products
        order.tax = total_tax

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
            updated_fields["products"] = await self.__validate_products(
                raw_products=updated_order.products
            )

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

        total_amount = await self.__order_calculator.calculate(
            products=(
                updated_fields["products"]
                if updated_fields.get("products") is not None
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
            delivery_value=delivery_value
        )

        is_updated = order_in_db.validate_updated_fields(update_order=updated_order)

        if is_updated or updated_fields.get("products"):
            if "products" in updated_fields:
                updated_fields["products"] = [
                    product.model_dump() for product in updated_fields["products"]
                ]

            updated_fields.update(updated_order.model_dump(exclude_none=True))

            organization = await self.__organization_repository.select_by_id(
                id=self.__order_repository.organization_id
            )

            if organization.tax:
                total_tax = round(total_amount * (organization.tax / 100), 2)
                total_amount += total_tax
                updated_fields["tax"] = total_tax

            updated_fields["total_amount"] = total_amount

            order_in_db = await self.__order_repository.update(
                order_id=order_in_db.id, order=updated_fields
            )

        return await self.__build_complete_order(order_in_db)

    async def search_by_id(self, id: str, expand: List[str] = []) -> CompleteOrder:
        order_in_db = await self.__order_repository.select_by_id(id=id)

        return await self.__build_complete_order(order_in_db=order_in_db, expand=expand)

    async def search_count(
        self,
        status: OrderStatus,
        payment_status: List[PaymentStatus],
        delivery_type: DeliveryType,
        customer_id: str,
        start_date: UTCDateTime,
        end_date: UTCDateTime,
        tags: List[str],
        min_total_amount: float,
        max_total_amount: float,
    ) -> int:
        quantity = await self.__order_repository.select_count(
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
        return quantity

    async def search_all(
        self,
        status: OrderStatus,
        payment_status: List[PaymentStatus],
        delivery_type: DeliveryType,
        customer_id: str,
        start_date: UTCDateTime,
        end_date: UTCDateTime,
        tags: List[str],
        min_total_amount: float,
        max_total_amount: float,
        expand: List[str],
        order_by: str = None,
        ignore_default_filters: bool = False,
        page: int = None,
        page_size: int = None
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
            order_by=order_by,
            ignore_default_filters=ignore_default_filters,
            page=page,
            page_size=page_size
        )

        complete_orders = []

        for order in orders:
            complete_orders.append(
                await self.__build_complete_order(order_in_db=order, expand=expand)
            )

        return complete_orders

    async def search_all_without_filters(
        self,
        start_date: UTCDateTime,
        end_date: UTCDateTime,
        expand: List[str] = [],
    ) -> List[CompleteOrder]:

        orders = await self.__order_repository.select_all_without_filters(
            start_date=start_date,
            end_date=end_date,
        )

        complete_orders = []

        for order in orders:
            complete_orders.append(
                await self.__build_complete_order(order_in_db=order, expand=expand)
            )

        return complete_orders

    async def search_recent(
        self, limit: int = 10, expand: List[str] = []
    ) -> List[CompleteOrder]:
        orders = await self.__order_repository.select_recent(limit=limit)

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
            tax=order_in_db.tax,
            is_active=order_in_db.is_active,
            created_at=order_in_db.created_at,
            updated_at=order_in_db.updated_at,
        )

        if "customers" in expand:
            if order_in_db.customer_id is not None:
                if order_in_db.customer_id not in self.__cache_customers:
                    customer = await self.__customer_repository.select_by_id(
                        id=order_in_db.customer_id, raise_404=False
                    )
                    self.__cache_customers[order_in_db.customer_id] = customer

                else:
                    customer = self.__cache_customers[order_in_db.customer_id]

                if customer:
                    complete_order.customer = customer

        if "tags" in expand:
            complete_order.tags = []

            for tag in order_in_db.tags:
                if tag not in self.__cache_tags:
                    tag_in_db = await self.__tag_repository.select_by_id(
                        id=tag, raise_404=False
                    )
                    self.__cache_tags[tag] = tag_in_db

                else:
                    tag_in_db = self.__cache_tags[tag]

                if tag_in_db:
                    complete_order.tags.append(tag_in_db)

        return complete_order

    async def __validate_products(self, raw_products: List[RequestedProduct]) -> List[StoredProduct]:
        products = []

        for product in raw_products:
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

            for additional in product.additionals:
                item_in_db = await self.__additional_item_repository.select_by_id(
                    id=additional.item_id
                )

                stored_product.additionals.append(
                    StoredAdditionalItem(
                        item_id=additional.item_id,
                        quantity=additional.quantity,
                        label=item_in_db.label,
                        unit_price=item_in_db.unit_price,
                        unit_cost=item_in_db.unit_cost,
                        consumption_factor=item_in_db.consumption_factor,
                    )
                )

            products.append(stored_product)

        return products
