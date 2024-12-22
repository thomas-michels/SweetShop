from datetime import date
from typing import List

from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.api.exceptions.authentication_exceptions import BadRequestException
from app.crud.products.repositories import ProductRepository
from app.core.configs import get_logger
from .schemas import CompleteProduct, RequestedProduct, FastOrder, FastOrderInDB, UpdateFastOrder, CompleteFastOrder
from .repositories import FastOrderRepository

logger = get_logger(__name__)


class FastOrderServices:

    def __init__(
        self,
        fast_order_repository: FastOrderRepository,
        product_repository: ProductRepository,
    ) -> None:
        self.__fast_order_repository = fast_order_repository
        self.__product_repository = product_repository

    async def create(self, fast_order: FastOrder) -> CompleteFastOrder:
        already_exists = await self.search_all(day=fast_order.day)

        if already_exists:
            raise BadRequestException(detail="You cannot create two fast orders for the same day")

        value = await self.__calculate_fast_order_value(
            products=fast_order.products
        )

        for product in fast_order.products:
            await self.__product_repository.select_by_id(id=product.product_id)

        fast_order_in_db = await self.__fast_order_repository.create(
            fast_order=fast_order,
            value=value
        )

        return await self.__build_complete_fast_order(fast_order_in_db)

    async def update(self, id: str, updated_fast_order: UpdateFastOrder) -> CompleteFastOrder:
        fast_order_in_db = await self.search_by_id(id=id)

        if updated_fast_order.products is not None:
            for product in updated_fast_order.products:
                await self.__product_repository.select_by_id(id=product.product_id)

        if updated_fast_order.day is not None:
            already_exists = await self.search_all(day=updated_fast_order.day)

            if already_exists and already_exists[0].id != id:
                raise BadRequestException(detail="You cannot create two fast orders for the same day")

        value = await self.__calculate_fast_order_value(
            products=updated_fast_order.products if updated_fast_order.products is not None else fast_order_in_db.products
        )

        is_updated = fast_order_in_db.validate_updated_fields(update_fast_order=updated_fast_order)

        if is_updated:
            updated_fields = updated_fast_order.model_dump(exclude_none=True)
            updated_fields["value"] = value

            fast_order_in_db = await self.__fast_order_repository.update(
                fast_order_id=fast_order_in_db.id,
                fast_order=updated_fields
            )

        return await self.__build_complete_fast_order(fast_order_in_db)

    async def search_by_id(self, id: str) -> CompleteFastOrder:
        fast_order_in_db = await self.__fast_order_repository.select_by_id(id=id)

        return await self.__build_complete_fast_order(fast_order_in_db)

    async def search_all(self, expand: List[str] = [], day: date = None) -> List[CompleteFastOrder]:
        orders = await self.__fast_order_repository.select_all(day=day)
        complete_fast_orders = []

        for order in orders:
            complete_fast_orders.append(await self.__build_complete_fast_order(fast_order_in_db=order, expand=expand))

        return complete_fast_orders

    async def delete_by_id(self, id: str) -> CompleteFastOrder:
        fast_order_in_db = await self.__fast_order_repository.delete_by_id(id=id)
        return await self.__build_complete_fast_order(fast_order_in_db)

    async def __build_complete_fast_order(self, fast_order_in_db: FastOrderInDB, expand: List[str] = []) -> CompleteFastOrder:
        complete_fast_order = CompleteFastOrder(
            id=fast_order_in_db.id,
            organization_id=fast_order_in_db.organization_id,
            products=fast_order_in_db.products,
            value=fast_order_in_db.value,
            day=fast_order_in_db.day,
            description=fast_order_in_db.description,
            is_active=fast_order_in_db.is_active,
            created_at=fast_order_in_db.created_at,
            updated_at=fast_order_in_db.updated_at,
        )

        if "products" in expand:
            complete_fast_order.products = []

            for product in fast_order_in_db.products:
                product_in_db = await self.__product_repository.select_by_id(
                    id=product.product_id,
                    raise_404=False
                )

                if product_in_db:
                    complete_product = CompleteProduct(
                        product=product_in_db,
                        quantity=product.quantity
                    )

                    complete_fast_order.products.append(complete_product)

        return complete_fast_order

    async def __calculate_fast_order_value(self, products: List[RequestedProduct]) -> float:
        value = 0

        for product in products:
            try:
                product_in_db = await self.__product_repository.select_by_id(id=product.product_id)

                value += (product_in_db.unit_price * product.quantity)

            except NotFoundError:
                raise UnprocessableEntity(message=f"Product {product.product_id} is invalid!")

        return value
