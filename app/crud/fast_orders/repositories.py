from datetime import date, datetime
from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from app.crud.orders.models import OrderModel
from app.crud.orders.schemas import (
    OrderInDB,
    OrderStatus,
    PaymentStatus,
    Delivery,
    DeliveryType
)
from .schemas import FastOrder, FastOrderInDB

_logger = get_logger(__name__)


class FastOrderRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.__organization_id = organization_id

    async def create(self, fast_order: FastOrder, value: float) -> FastOrderInDB:
        try:
            order_model = self.__build_order_model(
                fast_order=fast_order,
                value=value
            )

            order_model.save()

            return self.__from_order_model(order_model=order_model)

        except Exception as error:
            _logger.error(f"Error on create_order: {str(error)}")
            raise UnprocessableEntity(message="Error on create new fast order")

    async def update(self, fast_order_id: str, fast_order: dict) -> OrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=fast_order_id,
                is_active=True,
                is_fast_order=True,
                organization_id=self.__organization_id
            ).first()

            for field, value in fast_order.items():
                if hasattr(order_model, field):
                    setattr(order_model, field, value)

                elif field == "day":
                    order_model.preparation_date = value

            order_model.save()

            return await self.select_by_id(id=fast_order_id)

        except Exception as error:
            _logger.error(f"Error on update_fast_order: {str(error)}")
            raise UnprocessableEntity(message="Error on update fast order")

    async def select_by_id(self, id: str) -> OrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=id,
                is_active=True,
                is_fast_order=True,
                organization_id=self.__organization_id
            ).first()

            return self.__from_order_model(order_model=order_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"FastOrder #{id} not found")

    async def select_all(self, day: date) -> List[OrderInDB]:
        try:
            fast_orders = []

            objects = OrderModel.objects(
                is_active=True,
                is_fast_order=True,
                organization_id=self.__organization_id
            )

            if day:
                objects = objects(preparation_date=day)

            for order_model in objects.order_by("-preparation_date"):
                fast_orders.append(self.__from_order_model(order_model=order_model))

            return fast_orders

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Fast Orders not found")

    async def delete_by_id(self, id: str) -> FastOrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=id,
                is_active=True,
                is_fast_order=True,
                organization_id=self.__organization_id
            ).first()
            order_model.delete()

            return self.__from_order_model(order_model=order_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"FastOrder #{id} not found")

    def __build_order_model(self, fast_order: FastOrder, value: float) -> OrderModel:
        order_model = OrderModel(
            value=value,
            organization_id=self.__organization_id,
            status=OrderStatus.DONE,
            payment_status=PaymentStatus.PAID,
            products=[product.model_dump() for product in fast_order.products],
            tags=[],
            delivery=Delivery(type=DeliveryType.WITHDRAWAL).model_dump(),
            preparation_date=fast_order.day,
            description=fast_order.description,
            is_fast_order=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return order_model

    def __from_order_model(self, order_model: OrderModel) -> FastOrderInDB:
        fast_order_in_db = FastOrderInDB(
            id=order_model.pk,
            description=order_model.description,
            day=order_model.preparation_date,
            organization_id=order_model.organization_id,
            value=order_model.value,
            products=order_model.products,
            is_active=order_model.is_active,
            created_at=order_model.created_at,
            updated_at=order_model.updated_at
        )
        return fast_order_in_db
