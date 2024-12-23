from datetime import datetime
from typing import List

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.crud.shared_schemas.payment import PaymentStatus

from .models import OrderModel
from .schemas import Order, OrderInDB, OrderStatus

_logger = get_logger(__name__)


class OrderRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.__organization_id = organization_id

    async def create(self, order: Order, total_amount: float, payment_status: PaymentStatus) -> OrderInDB:
        try:
            order_model = OrderModel(
                total_amount=total_amount,
                organization_id=self.__organization_id,
                payment_status=payment_status,
                is_fast_order=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **order.model_dump(),
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
                is_fast_order=False,
                organization_id=self.__organization_id,
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
                is_fast_order=False,
                organization_id=self.__organization_id,
            ).first()

            return OrderInDB.model_validate(order_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"Order #{id} not found")

    async def select_all(
        self, customer_id: str, status: OrderStatus
    ) -> List[OrderInDB]:
        try:
            orders = []

            objects = OrderModel.objects(
                is_active=True,
                is_fast_order=False,
                organization_id=self.__organization_id,
            )

            if customer_id:
                objects = objects(customer_id=customer_id)

            if status:
                objects = objects(status=status.total_amount)

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
                is_fast_order=False,
                organization_id=self.__organization_id,
            ).first()
            order_model.delete()

            return OrderInDB.model_validate(order_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Order #{id} not found")
