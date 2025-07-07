from fastapi import Depends

from app.api.dependencies.cache_plans import get_cached_plans
from app.api.dependencies.cache_users import get_cached_complete_users, get_cached_users
from app.api.dependencies.get_access_token import get_access_token
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.services import OrganizationServices
from app.crud.users.repositories import UserRepository


async def organization_composer(
    access_token=Depends(get_access_token),
    cached_complete_users=Depends(get_cached_complete_users),
    cached_users=Depends(get_cached_users),
    cache_plans=Depends(get_cached_plans),
) -> OrganizationServices:
    organization_repository = OrganizationRepository()
    user_repository = UserRepository(
        access_token=access_token,
        cache_users=cached_users
    )

    organization_plan_repository = OrganizationPlanRepository(
        cache_plans=cache_plans
    )

    organization_services = OrganizationServices(
        organization_repository=organization_repository,
        organization_plan_repository=organization_plan_repository,
        user_repository=user_repository,
        cached_complete_users=cached_complete_users,
    )
    return organization_services
