from fastapi import Depends

from app.api.composers.organization_plan_composite import organization_plan_composer
from app.api.dependencies.cache_users import get_cached_complete_users, get_cached_users
from app.api.dependencies.get_access_token import get_access_token
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.users.repositories import UserRepository
from app.crud.users.services import UserServices


async def user_composer(
    access_token=Depends(get_access_token),
    cached_complete_users=Depends(get_cached_complete_users),
    cached_users=Depends(get_cached_users),
    organization_plan_services=Depends(organization_plan_composer),
) -> UserServices:
    user_repository = UserRepository(
        access_token=access_token,
        cache_users=cached_users
    )

    organization_repository = OrganizationRepository()

    user_services = UserServices(
        user_repository=user_repository,
        cached_complete_users=cached_complete_users,
        organization_plan_services=organization_plan_services,
        organization_repository=organization_repository,
    )
    return user_services
