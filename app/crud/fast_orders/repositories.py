from datetime import datetime
from typing import List

from pydantic_core import ValidationError

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.crud.orders.models import OrderModel
from app.crud.orders.schemas import (
    Delivery,
    DeliveryType,
    OrderInDB,
    OrderStatus,
    PaymentStatus,
)

from .schemas import FastOrder, FastOrderInDB

_logger = get_logger(__name__)


class FastOrderRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.__organization_id = organization_id

    async def create(
        self, fast_order: FastOrder, total_amount: float
    ) -> FastOrderInDB:
        try:
            order_model = self.__build_order_model(
                fast_order=fast_order,
                total_amount=round(total_amount, 2),
                payment_status=PaymentStatus.PENDING,
            )

            order_model.save()

            return await self.select_by_id(id=order_model.id)

        except Exception as error:
            _logger.error(f"Error on create_fast_order: {str(error)}")
            raise UnprocessableEntity(message="Error on create new fast order")

    async def update(self, fast_order_id: str, fast_order: dict) -> OrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=fast_order_id,
                is_active=True,
                is_fast_order=True,
                organization_id=self.__organization_id,
            ).first()

            for field, value in fast_order.items():
                if hasattr(order_model, field):
                    setattr(order_model, field, value)

            order_model.total_amount = round(order_model.total_amount, 2)
            order_model.save()

            return await self.select_by_id(id=fast_order_id)

        except Exception as error:
            _logger.error(f"Error on update_fast_order: {str(error)}")
            raise UnprocessableEntity(message="Error on update fast order")

    async def select_by_id(self, id: str) -> OrderInDB:
        try:
            order_model: OrderModel = list(OrderModel.objects(
                id=id,
                is_active=True,
                is_fast_order=True,
                organization_id=self.__organization_id,
            ).aggregate(OrderModel.get_payments()))

            if order_model:
                return self.__from_order_model(order_model=order_model[0])

            raise NotFoundError(message=f"FastOrder #{id} not found")

        except ValidationError:
            raise NotFoundError(message=f"FastOrder #{id} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"FastOrder #{id} not found")

    async def select_count(
        self,
        day: datetime = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> int:
        try:
            objects = OrderModel.objects(
                is_active=True,
                is_fast_order=True,
                organization_id=self.__organization_id,
            )

            if day:
                objects = objects(order_date=day)

            if start_date:
                objects = objects.filter(order_date__gte=start_date)

            if end_date:
                objects = objects.filter(order_date__lt=end_date)

            return max(objects.count(), 0)

        except Exception as error:
            _logger.error(f"Error on select_count: {str(error)}")
            return 0

    async def select_all(
        self,
        day: datetime = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = None,
        page_size: int = None
    ) -> List[OrderInDB]:
        try:
            fast_orders = []

            objects = OrderModel.objects(
                is_active=True,
                is_fast_order=True,
                organization_id=self.__organization_id,
            )

            if day:
                objects = objects(order_date=day)

            if start_date:
                objects = objects.filter(order_date__gte=start_date)

            if end_date:
                objects = objects.filter(order_date__lt=end_date)

            objects = objects.order_by("-order_date")

            if page and page_size:
                skip = (page - 1) * page_size
                objects = objects.skip(skip).limit(page_size)

            for order_model in objects.aggregate(
                OrderModel.get_payments()
            ):
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
                organization_id=self.__organization_id,
            ).first()

            if order_model:
                order_model.delete()

                return self.__from_order_model(order_model=order_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"FastOrder #{id} not found")

    def __build_order_model(
        self,
        fast_order: FastOrder,
        payment_status: PaymentStatus,
        total_amount: float,
    ) -> OrderModel:
        order_model = OrderModel(
            total_amount=total_amount,
            additional=fast_order.additional,
            discount=fast_order.discount,
            organization_id=self.__organization_id,
            status=OrderStatus.DONE,
            payment_status=payment_status,
            products=[product.model_dump() for product in fast_order.products],
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.FAST_ORDER).model_dump(),
            preparation_date=fast_order.order_date,
            order_date=fast_order.order_date,
            description=fast_order.description,
            is_fast_order=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return order_model

    def __from_order_model(self, order_model: dict | OrderModel) -> FastOrderInDB:
        try:
            fast_order_in_db = FastOrderInDB(
                additional=order_model["additional"],
                created_at=order_model["created_at"],
                description=order_model.get("description"),
                discount=order_model["discount"],
                id=order_model["id"],
                is_active=order_model["is_active"],
                order_date=order_model["order_date"],
                organization_id=order_model["organization_id"],
                payments=order_model["payments"],
                products=order_model["products"],
                total_amount=order_model["total_amount"],
                updated_at=order_model["updated_at"],
            )
            return fast_order_in_db

        except (TypeError, AttributeError):
            fast_order_in_db = FastOrderInDB(
                additional=order_model.additional,
                created_at=order_model.created_at,
                description=order_model.description,
                discount=order_model.discount,
                id=order_model.id,
                is_active=order_model.is_active,
                order_date=order_model.order_date,
                organization_id=order_model.organization_id,
                payments=order_model.payments if hasattr(order_model, "payments") else [],
                products=order_model.products,
                total_amount=order_model.total_amount,
                updated_at=order_model.updated_at,
            )
            return fast_order_in_db
