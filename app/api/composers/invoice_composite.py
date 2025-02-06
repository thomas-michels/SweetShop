from app.crud.invoices.repositories import InvoiceRepository
from app.crud.invoices.services import InvoiceServices
from app.crud.organization_plans.repositories import OrganizationPlanRepository


async def invoice_composer() -> InvoiceServices:
    invoice_repository = InvoiceRepository()
    organization_plan_repository = OrganizationPlanRepository()

    invoice_services = InvoiceServices(
        invoice_repository=invoice_repository,
        organization_plan_repository=organization_plan_repository
    )
    return invoice_services
