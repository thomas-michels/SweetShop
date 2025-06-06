from typing import List

from pydantic_core import ValidationError

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import PaymentModel
from .schemas import Payment, PaymentInDB

_logger = get_logger(__name__)


class PaymentRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.__organization_id = organization_id

    async def create(self, payment: Payment) -> PaymentInDB:
        try:
            payment_model = PaymentModel(
                organization_id=self.__organization_id,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                **payment.model_dump(),
            )
            payment_model.save()

            return PaymentInDB.model_validate(payment_model)

        except Exception as error:
            _logger.error(f"Error on create_payment: {str(error)}")
            raise UnprocessableEntity(message="Error on create new Payment")

    async def update(self, payment: PaymentInDB) -> PaymentInDB:
        try:
            payment_model: PaymentModel = PaymentModel.objects(
                id=payment.id, is_active=True, organization_id=self.__organization_id
            ).first()

            payment_model.update(**payment.model_dump())

            return await self.select_by_id(id=payment.id)

        except Exception as error:
            _logger.error(f"Error on update_payment: {str(error)}")
            raise UnprocessableEntity(message="Error on update Payment")

    async def select_by_id(self, id: str, raise_404: bool = True) -> PaymentInDB:
        try:
            payment_model: PaymentModel = PaymentModel.objects(
                id=id, is_active=True, organization_id=self.__organization_id
            ).first()

            return PaymentInDB.model_validate(payment_model)

        except ValidationError:
            if raise_404:
                raise NotFoundError(message=f"Payment #{id} not found")

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Payment #{id} not found")

    async def select_all(self, order_id: str) -> List[PaymentInDB]:
        try:
            payments = []
            objects = PaymentModel.objects(
                order_id=order_id,
                is_active=True,
                organization_id=self.__organization_id,
            )

            for payment_model in objects.order_by("payment_date"):
                payment_in_db = PaymentInDB.model_validate(payment_model)

                payments.append(payment_in_db)

            return payments

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Payments not found")

    async def delete_by_id(self, id: str) -> PaymentInDB:
        try:
            payment_model: PaymentModel = PaymentModel.objects(
                id=id, is_active=True, organization_id=self.__organization_id
            ).first()
            if payment_model:
                payment_model.delete()

                return PaymentInDB.model_validate(payment_model)

            raise NotFoundError(message=f"Payment #{id} not found")

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Payment #{id} not found")
