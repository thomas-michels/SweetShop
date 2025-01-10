from fastapi import Depends
from app.api.dependencies.get_current_organization import check_current_organization
from app.crud.invites.repositories import InviteRepository
from app.crud.invites.services import InviteServices


async def invite_composer(
    organization_id: str = Depends(check_current_organization)
) -> InviteServices:
    invite_repository = InviteRepository(organization_id=organization_id)

    invite_services = InviteServices(
        invite_repository=invite_repository,
    )
    return invite_services
