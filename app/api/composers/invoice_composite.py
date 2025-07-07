from fastapi import Depends
from app.api.dependencies.cache_plans import get_cached_plans
from app.crud.invoices.repositories import InvoiceRepository
from app.crud.invoices.services import InvoiceServices
from app.crud.organization_plans.repositories import OrganizationPlanRepository


async def invoice_composer(cache_plans=Depends(get_cached_plans)) -> InvoiceServices:
    invoice_repository = InvoiceRepository()
    organization_plan_repository = OrganizationPlanRepository(
        cache_plans=cache_plans
    )

    invoice_services = InvoiceServices(
        invoice_repository=invoice_repository,
        organization_plan_repository=organization_plan_repository
    )
    return invoice_services
