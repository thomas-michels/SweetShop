from typing import List

from app.crud.organization_plans.repositories import OrganizationPlanRepository

from .schemas import Invoice, InvoiceInDB, UpdateInvoice
from .repositories import InvoiceRepository


class InvoiceServices:

    def __init__(
            self,
            invoice_repository: InvoiceRepository,
            organization_plan_repository: OrganizationPlanRepository,
        ) -> None:
        self.__invoice_repository = invoice_repository
        self.__organization_plan_repository = organization_plan_repository

    async def create(self, invoice: Invoice, organization_id: str) -> InvoiceInDB:
        await self.__organization_plan_repository.select_by_id(
            id=invoice.organization_plan_id,
            organization_id=organization_id
        )

        invoice_in_db = await self.__invoice_repository.create(invoice=invoice)

        return invoice_in_db

    async def update(self, id: str, updated_invoice: UpdateInvoice) -> InvoiceInDB:
        invoice_in_db = await self.search_by_id(id=id)

        is_updated = invoice_in_db.validate_updated_fields(update_invoice=updated_invoice)

        if is_updated:
            invoice_in_db = await self.__invoice_repository.update(invoice=invoice_in_db)

        return invoice_in_db

    async def search_by_id(self, id: str) -> InvoiceInDB:
        invoice_in_db = await self.__invoice_repository.select_by_id(id=id)
        return invoice_in_db

    async def search_by_organization_plan_id(self, organization_plan_id: str) -> InvoiceInDB:
        invoice_in_db = await self.__invoice_repository.select_by_organization_plan_id(
            organization_plan_id=organization_plan_id
        )
        return invoice_in_db

    async def search_all(self) -> List[InvoiceInDB]:
        invoices = await self.__invoice_repository.select_all()
        return invoices

    async def delete_by_id(self, id: str) -> InvoiceInDB:
        invoice_in_db = await self.__invoice_repository.delete_by_id(id=id)
        return invoice_in_db
