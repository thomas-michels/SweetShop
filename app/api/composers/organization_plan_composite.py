from fastapi import Depends
from app.api.dependencies.cache_plans import get_cached_plans
from app.crud.plans.repositories import PlanRepository
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.organization_plans.services import OrganizationPlanServices


async def organization_plan_composer(cache_plans=Depends(get_cached_plans)) -> OrganizationPlanServices:
    organization_plan_repository = OrganizationPlanRepository(cache_plans=cache_plans)
    plan_repository = PlanRepository()

    organization_plan_services = OrganizationPlanServices(
        organization_plan_repository=organization_plan_repository,
        plan_repository=plan_repository
    )
    return organization_plan_services
