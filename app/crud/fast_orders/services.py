from datetime import datetime
from typing import List

from app.api.exceptions.authentication_exceptions import (
    BadRequestException,
    UnprocessableEntityException,
)
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.crud.products.repositories import ProductRepository
from app.crud.shared_schemas.payment import Payment, PaymentStatus

from .repositories import FastOrderRepository
from .schemas import (
    FastOrder,
    FastOrderInDB,
    RequestedProduct,
    RequestFastOrder,
    StoredProduct,
    UpdateFastOrder,
)

logger = get_logger(__name__)


class FastOrderServices:

    def __init__(
        self,
        fast_order_repository: FastOrderRepository,
        product_repository: ProductRepository,
    ) -> None:
        self.__fast_order_repository = fast_order_repository
        self.__product_repository = product_repository

    async def create(self, fast_order: RequestFastOrder) -> FastOrderInDB:
        already_exists = await self.search_all(day=fast_order.order_date)

        if already_exists:
            raise BadRequestException(
                detail="You cannot create two fast orders for the same day"
            )

        fast_order = FastOrder.model_validate(fast_order)

        for product in fast_order.products:
            product_in_db = await self.__product_repository.select_by_id(
                id=product.product_id
            )
            product.name = product_in_db.name
            product.unit_cost = product_in_db.unit_cost
            product.unit_price = product_in_db.unit_price

        total_amount = await self.__calculate_fast_order_total_amount(
            products=fast_order.products,
            additional=fast_order.additional,
            discount=fast_order.discount,
        )

        if fast_order.discount > total_amount:
            raise UnprocessableEntityException(
                detail="Discount cannot be grater than total amount"
            )

        fast_order_in_db = await self.__fast_order_repository.create(
            fast_order=fast_order,
            total_amount=total_amount,
        )

        return fast_order_in_db

    async def update(
        self, id: str, updated_fast_order: UpdateFastOrder
    ) -> FastOrderInDB:
        fast_order_in_db = await self.search_by_id(id=id)
        updated_fields = {}

        if updated_fast_order.products is not None:
            updated_fields["products"] = []

            for product in updated_fast_order.products:
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
                updated_fields["products"].append(stored_product)

            updated_fast_order.products = None

        if updated_fast_order.order_date is not None:
            already_exists = await self.search_all(day=updated_fast_order.order_date)

            if already_exists and already_exists[0].id != id:
                raise BadRequestException(
                    detail="You cannot create two fast orders for the same day"
                )

        total_amount = await self.__calculate_fast_order_total_amount(
            products=(
                updated_fields["products"]
                if updated_fields.get("products") is not None
                else fast_order_in_db.products
            ),
            discount=(
                updated_fast_order.discount
                if updated_fast_order.discount is not None
                else fast_order_in_db.discount
            ),
            additional=(
                updated_fast_order.additional
                if updated_fast_order.additional is not None
                else fast_order_in_db.additional
            ),
        )

        is_updated = fast_order_in_db.validate_updated_fields(
            update_fast_order=updated_fast_order
        )

        if is_updated:
            if "products" in updated_fields:
                updated_fields["products"] = [product.model_dump() for product in updated_fields["products"]]

            updated_fields.update(updated_fast_order.model_dump(exclude_none=True))
            updated_fields["total_amount"] = total_amount

            if (
                updated_fast_order.discount is not None
                and updated_fast_order.discount > total_amount
            ):
                raise UnprocessableEntityException(
                    detail="Discount cannot be grater than total amount"
                )

            fast_order_in_db = await self.__fast_order_repository.update(
                fast_order_id=fast_order_in_db.id, fast_order=updated_fields
            )

        return fast_order_in_db

    async def search_by_id(self, id: str) -> FastOrderInDB:
        fast_order_in_db = await self.__fast_order_repository.select_by_id(id=id)

        return fast_order_in_db

    async def search_count(
        self,
        day: datetime = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> FastOrderInDB:
        quantity = await self.__fast_order_repository.select_count(
            day=day,
            start_date=start_date,
            end_date=end_date
        )

        return quantity

    async def search_all(
        self,
        expand: List[str] = [],
        day: datetime = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = None,
        page_size: int = None
    ) -> List[FastOrderInDB]:
        orders = await self.__fast_order_repository.select_all(
            day=day,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        return orders

    async def delete_by_id(self, id: str) -> FastOrderInDB:
        fast_order_in_db = await self.__fast_order_repository.delete_by_id(id=id)
        return fast_order_in_db

    async def __calculate_fast_order_total_amount(
        self, products: List[RequestedProduct], additional: float, discount: float
    ) -> float:
        total_amount = additional - discount

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
