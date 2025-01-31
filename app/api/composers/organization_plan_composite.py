from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.organization_plans.services import OrganizationPlanServices


async def organization_plan_composer() -> OrganizationPlanServices:
    organization_plan_repository = OrganizationPlanRepository()
    organization_plan_services = OrganizationPlanServices(
        organization_plan_repository=organization_plan_repository
    )
    return organization_plan_services
