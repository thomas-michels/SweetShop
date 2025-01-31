from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.organization_plans.services import OrganizationPlanServices


async def organization_plan_composer(
    organization_id: str = Depends(check_current_organization)
) -> OrganizationPlanServices:
    organization_plan_repository = OrganizationPlanRepository(organization_id=organization_id)
    organization_plan_services = OrganizationPlanServices(
        organization_plan_repository=organization_plan_repository
    )
    return organization_plan_services
