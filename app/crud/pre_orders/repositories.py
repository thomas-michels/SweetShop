from typing import List

from pydantic import ValidationError
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import PreOrderModel
from .schemas import PreOrderInDB, PreOrderStatus

_logger = get_logger(__name__)


class PreOrderRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def update_status(self, pre_order_id: str, new_status: PreOrderStatus, order_id: str | None = None) -> PreOrderInDB:
        try:
            pre_order_model: PreOrderModel = PreOrderModel.objects(
                id=pre_order_id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            if new_status:
                pre_order_model.status = new_status

            if order_id is not None:
                pre_order_model.order_id = order_id

            if new_status or order_id is not None:
                pre_order_model.save()

            return await self.select_by_id(id=pre_order_id)

        except ValidationError:
            raise NotFoundError(message=f"PreOrder not found")

        except Exception as error:
            _logger.error(f"Error on update_pre_order: {error}")
            raise UnprocessableEntity(message="Error on update PreOrder")

    async def select_by_id(self, id: str, raise_404: bool = True) -> PreOrderInDB:
        try:
            pre_order_model: PreOrderModel = PreOrderModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            return PreOrderInDB.model_validate(pre_order_model)

        except ValidationError:
            if raise_404:
                raise NotFoundError(message=f"PreOrder #{id} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_id: {error}")
            if raise_404:
                raise NotFoundError(message=f"PreOrder #{id} not found")

    async def select_by_order_id(self, order_id: str, raise_404: bool = True) -> PreOrderInDB:
        try:
            pre_order_model: PreOrderModel = PreOrderModel.objects(
                order_id=order_id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            return PreOrderInDB.model_validate(pre_order_model)

        except ValidationError:
            if raise_404:
                raise NotFoundError(message=f"PreOrder for Order #{order_id} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_id: {error}")
            if raise_404:
                raise NotFoundError(message=f"PreOrder for Order #{order_id} not found")

    async def select_count(self, status: PreOrderStatus = None, code: str = None) -> int:
        try:
            objects = PreOrderModel.objects(
                is_active=True,
                organization_id=self.organization_id
            )

            if status is not None and not code:
                objects = objects.filter(status=status.value)

            if code is not None:
                objects = objects.filter(code__iregex=code)

            return max(objects.count(), 0)

        except Exception as error:
            _logger.error(f"Error on select_count: {str(error)}")
            return 0

    async def select_all(
        self,
        status: PreOrderStatus = None,
        code: str = None,
        page: int = None,
        page_size: int = None
        ) -> List[PreOrderInDB]:
        try:
            pre_orders = []

            objects = PreOrderModel.objects(
                is_active=True,
                organization_id=self.organization_id
            )

            if status is not None and not code:
                objects = objects.filter(status=status.value)

            if code is not None:
                objects = objects.filter(code__iregex=code)

            if page and page_size:
                skip = (page - 1) * page_size
                objects = objects.order_by("-created_at").skip(skip).limit(page_size)

            for pre_order_model in objects:
                pre_orders.append(PreOrderInDB.model_validate(pre_order_model))

            return pre_orders

        except Exception as error:
            _logger.error(f"Error on select_all: {error}")
            raise NotFoundError(message=f"PreOrders not found")

    async def delete_by_id(self, id: str) -> PreOrderInDB:
        try:
            pre_order_model: PreOrderModel = PreOrderModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            if pre_order_model:
                pre_order_model.delete()

                return PreOrderInDB.model_validate(pre_order_model)

            raise NotFoundError(message=f"PreOrder #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {error}")
            raise NotFoundError(message=f"PreOrder #{id} not found")
