from fastapi import Depends
from app.api.dependencies.cache_users import get_cached_users
from app.api.dependencies.get_access_token import get_access_token
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.services import OrganizationServices
from app.crud.users.repositories import UserRepository


async def organization_composer(
    access_token = Depends(get_access_token),
    cached_users = Depends(get_cached_users)
) -> OrganizationServices:
    organization_repository = OrganizationRepository()
    user_repository = UserRepository(
        access_token=access_token,
        cached_users=cached_users
    )
    organization_services = OrganizationServices(
        organization_repository=organization_repository,
        user_repository=user_repository
    )
    return organization_services
