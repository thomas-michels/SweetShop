from datetime import datetime
from typing import List
from fastapi.encoders import jsonable_encoder
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import OrderModel
from .schemas import Order, OrderInDB, OrderStatus

_logger = get_logger(__name__)


class OrderRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.__organization_id = organization_id

    async def create(self, order: Order, value: float) -> OrderInDB:
        try:
            order_model = OrderModel(
                value=value,
                organization_id=self.__organization_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **order.model_dump()
            )

            order_model.save()

            return OrderInDB.model_validate(order_model)

        except Exception as error:
            _logger.error(f"Error on create_order: {str(error)}")
            raise UnprocessableEntity(message="Error on create new order")

    async def update(self, order_id: str, order: dict) -> OrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=order_id,
                is_active=True,
                organization_id=self.__organization_id
            ).first()

            order_model.update(**order)
            order_model.save()

            return await self.select_by_id(id=order_id)

        except Exception as error:
            _logger.error(f"Error on update_order: {str(error)}")
            raise UnprocessableEntity(message="Error on update order")

    async def select_by_id(self, id: str) -> OrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=id,
                is_active=True,
                organization_id=self.__organization_id
            ).first()

            return OrderInDB.model_validate(order_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"Order #{id} not found")

    async def select_all(self, customer_id: str, status: OrderStatus) -> List[OrderInDB]:
        try:
            orders = []

            objects = OrderModel.objects(
                is_active=True,
                organization_id=self.__organization_id
            )

            if customer_id:
                objects = objects(customer_id=customer_id)

            if status:
                objects = objects(status=status.value)

            for order_model in objects.order_by("-preparation_date"):
                orders.append(OrderInDB.model_validate(order_model))

            return orders

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Orders not found")

    async def delete_by_id(self, id: str) -> OrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=id,
                is_active=True,
                organization_id=self.__organization_id
            ).first()
            order_model.delete()

            return OrderInDB.model_validate(order_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Order #{id} not found")
