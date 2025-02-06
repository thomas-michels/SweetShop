from datetime import datetime
from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import InvoiceModel
from .schemas import Invoice, InvoiceInDB

_logger = get_logger(__name__)


class InvoiceRepository(Repository):
    async def create(self, invoice: Invoice) -> InvoiceInDB:
        try:
            plan_model = InvoiceModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **invoice.model_dump()
            )

            plan_model.save()

            return InvoiceInDB.model_validate(plan_model)

        except Exception as error:
            _logger.error(f"Error on create_invoice: {str(error)}")
            raise UnprocessableEntity(message="Error on create new Invoice")

    async def update(self, invoice: InvoiceInDB) -> InvoiceInDB:
        try:
            plan_model: InvoiceModel = InvoiceModel.objects(
                id=invoice.id,
                is_active=True,
            ).first()

            plan_model.update(**invoice.model_dump())

            return await self.select_by_id(id=invoice.id)

        except Exception as error:
            _logger.error(f"Error on update_invoice: {str(error)}")
            raise UnprocessableEntity(message="Error on update Invoice")

    async def select_by_id(self, id: str, raise_404: bool = True) -> InvoiceInDB:
        try:
            plan_model: InvoiceModel = InvoiceModel.objects(
                id=id,
                is_active=True,
            ).first()

            return InvoiceInDB.model_validate(plan_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Invoice #{id} not found")

    async def select_by_organization_plan_id(self, organization_plan_id: str, raise_404: bool = True) -> InvoiceInDB:
        try:
            plan_model: InvoiceModel = InvoiceModel.objects(
                organization_plan_id=organization_plan_id,
                is_active=True,
            ).first()

            return InvoiceInDB.model_validate(plan_model)

        except Exception as error:
            _logger.error(f"Error on select_by_organization_plan_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Invoice not found")

    async def select_all(self) -> List[InvoiceInDB]:
        try:
            plans = []

            objects = InvoiceModel.objects(is_active=True)

            for plan_model in objects:
                plans.append(InvoiceInDB.model_validate(plan_model))

            return plans

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Plans not found")

    async def delete_by_id(self, id: str) -> InvoiceInDB:
        try:
            plan_model: InvoiceModel = InvoiceModel.objects(
                id=id,
                is_active=True
            ).first()
            plan_model.delete()

            return InvoiceInDB.model_validate(plan_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Invoice #{id} not found")
