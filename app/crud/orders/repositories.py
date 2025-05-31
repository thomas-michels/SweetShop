from typing import List

from mongoengine import Q
from pydantic_core import ValidationError

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.shared_schemas.payment import PaymentStatus

from .models import OrderModel
from .schemas import DeliveryType, Order, OrderInDB, OrderStatus

_logger = get_logger(__name__)


class OrderRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, order: Order, total_amount: float) -> OrderInDB:
        try:
            order_model = OrderModel(
                total_amount=round(total_amount, 2),
                organization_id=self.organization_id,
                payment_status=PaymentStatus.PENDING,
                is_fast_order=False,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                **order.model_dump(),
            )

            order_model.description = (
                order_model.description.strip() if order_model.description else None
            )
            order_model.save()

            return await self.select_by_id(id=order_model.id)

        except Exception as error:
            _logger.error(f"Error on create_order: {str(error)}")
            raise UnprocessableEntity(message="Error on create new order")

    async def update(self, order_id: str, order: dict) -> OrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=order_id,
                is_active=True,
                organization_id=self.organization_id,
            ).first()

            order_model.update(**order)
            order_model.description = (
                order_model.description.strip() if order_model.description else None
            )
            order_model.total_amount = round(order_model.total_amount, 2)

            order_model.save()

            return await self.select_by_id(id=order_id)

        except ValidationError:
            raise NotFoundError(message=f"Order #{order_id} not found")

        except Exception as error:
            _logger.error(f"Error on update_order: {error}")
            raise UnprocessableEntity(message="Error on update order")

    async def select_count_by_date(
        self, start_date: UTCDateTime, end_date: UTCDateTime
    ) -> int:
        try:
            count = OrderModel.objects(
                is_active=True,
                organization_id=self.organization_id,
                created_at__gte=start_date,
                created_at__lte=end_date,
            ).count()

            return count if count else 0

        except Exception as error:
            _logger.error(f"Error on select_count_by_date: {str(error)}")
            return 0

    async def select_count(
        self,
        customer_id: str,
        status: OrderStatus,
        payment_status: List[PaymentStatus],
        delivery_type: DeliveryType,
        tags: List[str],
        start_date: UTCDateTime,
        end_date: UTCDateTime,
        min_total_amount: float,
        max_total_amount: float,
    ) -> int:
        try:
            objects = OrderModel.objects(
                is_active=True,
                is_fast_order=False,
                organization_id=self.organization_id,
            )

            if customer_id:
                objects = objects.filter(customer_id=customer_id)

            if status:
                objects = objects.filter(status=status.value)

            else:
                objects = objects.filter(
                    Q(status__ne=OrderStatus.DONE.value)
                    | Q(payment_status__ne=PaymentStatus.PAID.value)
                )

            if payment_status:
                objects = objects.filter(payment_status__in=payment_status)

            if delivery_type:
                objects = objects.filter(delivery__delivery_type=delivery_type.value)

            if start_date:
                objects = objects.filter(order_date__gte=start_date)

            if end_date:
                objects = objects.filter(order_date__lt=end_date)

            if tags:
                objects = objects.filter(tags__in=tags)

            if min_total_amount:
                objects = objects.filter(total_amount__gte=min_total_amount)

            if max_total_amount:
                objects = objects.filter(total_amount__lte=max_total_amount)

            return max(objects.count(), 0)

        except Exception as error:
            _logger.error(f"Error on select_count_by_date: {str(error)}")
            return 0

    async def select_by_id(self, id: str, fast_order: bool = False) -> OrderInDB:
        try:
            objects = OrderModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id,
            )

            if fast_order is not None:
                objects = objects.filter(is_fast_order=fast_order)

            order_model = list(objects.aggregate(OrderModel.get_payments()))

            if order_model:
                return self.__from_order_model(order_model=order_model[0])

            raise NotFoundError(message=f"Order #{id} not found")

        except ValidationError:
            raise NotFoundError(message=f"Order #{id} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"Order #{id} not found")

    async def select_all(
        self,
        customer_id: str,
        status: OrderStatus,
        payment_status: List[PaymentStatus],
        delivery_type: DeliveryType,
        tags: List[str],
        start_date: UTCDateTime,
        end_date: UTCDateTime,
        min_total_amount: float,
        max_total_amount: float,
        order_by: str = None,
        ignore_default_filters: bool = False,
        page: int = None,
        page_size: int = None,
    ) -> List[OrderInDB]:
        try:
            orders = []

            objects = OrderModel.objects(
                is_active=True,
                is_fast_order=False,
                organization_id=self.organization_id,
            )

            if customer_id:
                objects = objects.filter(customer_id=customer_id)

            if status:
                objects = objects.filter(status=status.value)

            else:
                if not ignore_default_filters:
                    objects = objects.filter(
                        Q(status__ne=OrderStatus.DONE.value) |
                        Q(payment_status__ne=PaymentStatus.PAID.value)
                    )

            if payment_status:
                objects = objects.filter(payment_status__in=payment_status)

            if delivery_type:
                objects = objects.filter(delivery__delivery_type=delivery_type.value)

            if start_date:
                objects = objects.filter(order_date__gte=start_date)

            if end_date:
                objects = objects.filter(order_date__lt=end_date)

            if tags:
                objects = objects.filter(tags__in=tags)

            if min_total_amount:
                objects = objects.filter(total_amount__gte=min_total_amount)

            if max_total_amount:
                objects = objects.filter(total_amount__lte=max_total_amount)

            if not order_by:
                order_by = "order_date"

            objects = objects.order_by(f"-{order_by}")

            if page and page_size:
                skip = (page - 1) * page_size
                objects = objects.skip(skip).limit(page_size)

            objects = objects.aggregate(OrderModel.get_payments())

            for order_model in objects:
                orders.append(self.__from_order_model(order_model=order_model))

            return orders

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Orders not found")

    async def select_all_without_filters(
        self, start_date: UTCDateTime, end_date: UTCDateTime
    ) -> List[OrderInDB]:
        """
        Este metodo retorna todos os pedidos normais e rapidos
        """
        try:
            orders = []

            objects = OrderModel.objects(
                is_active=True,
                organization_id=self.organization_id,
            )

            if start_date:
                objects = objects.filter(order_date__gte=start_date)

            if end_date:
                objects = objects.filter(order_date__lt=end_date)

            order_by = "order_date"

            objects = objects.order_by(f"-{order_by}").aggregate(
                OrderModel.get_payments()
            )

            for order_model in objects:
                orders.append(self.__from_order_model(order_model=order_model))

            return orders

        except Exception as error:
            _logger.error(f"Error on select_all_without_filters: {str(error)}")
            raise NotFoundError(message=f"Orders not found")

    async def select_recent(self, limit: int) -> List[OrderInDB]:
        try:
            orders = []

            objects = OrderModel.objects(
                is_active=True,
                organization_id=self.organization_id,
                is_fast_order=False,
            )

            objects = objects.limit(limit)

            objects = objects.order_by(f"-created_at").aggregate(
                OrderModel.get_payments()
            )

            for order_model in objects:
                orders.append(self.__from_order_model(order_model=order_model))

            return orders

        except Exception as error:
            _logger.error(f"Error on select_recent: {str(error)}")
            raise NotFoundError(message=f"Orders not found")

    async def delete_by_id(self, id: str) -> OrderInDB:
        try:
            order_model: OrderModel = OrderModel.objects(
                id=id,
                is_active=True,
                is_fast_order=False,
                organization_id=self.organization_id,
            ).first()

            if order_model:
                order_model.delete()
                return self.__from_order_model(order_model=order_model)

        except ValidationError:
            raise NotFoundError(message=f"Pedido #{id} não encontrado")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Pedido #{id} não encontrado")

    def __from_order_model(self, order_model: dict | OrderModel) -> OrderInDB:
        try:
            order_in_db = OrderInDB(**order_model)
            return order_in_db

        except (TypeError, AttributeError):
            order_in_db = OrderInDB.model_validate(order_model)
            return order_in_db
