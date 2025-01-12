from fastapi import Depends
from app.api.dependencies.cache_users import get_cached_users
from app.api.dependencies.get_access_token import get_access_token
from app.crud.invites.repositories import InviteRepository
from app.crud.invites.services import InviteServices
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.users.repositories import UserRepository


async def invite_composer(
    access_token = Depends(get_access_token),
    cached_users = Depends(get_cached_users)
) -> InviteServices:
    invite_repository = InviteRepository()
    user_repository = UserRepository(
        access_token=access_token,
        cached_users=cached_users
    )
    organization_repository = OrganizationRepository()

    invite_services = InviteServices(
        invite_repository=invite_repository,
        organization_repository=organization_repository,
        user_repository=user_repository
    )
    return invite_services
