from app.crud.plans.repositories import PlanRepository
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.organization_plans.services import OrganizationPlanServices


async def organization_plan_composer() -> OrganizationPlanServices:
    organization_plan_repository = OrganizationPlanRepository()
    plan_repository = PlanRepository()

    organization_plan_services = OrganizationPlanServices(
        organization_plan_repository=organization_plan_repository,
        plan_repository=plan_repository
    )
    return organization_plan_services
