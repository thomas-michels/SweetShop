from fastapi import APIRouter, Depends, Security

from app.api.composers import invite_composer
from app.api.composers.organization_composite import organization_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.invites import (
    Invite,
    InviteInDB,
    InviteServices
)
from app.crud.organizations.services import OrganizationServices
from app.crud.users import UserInDB

router = APIRouter(tags=["Invites"])


@router.post("/invites", responses={201: {"model": InviteInDB}})
async def create_invite(
    invite: Invite,
    invite_services: InviteServices = Depends(invite_composer),
    current_user: UserInDB = Security(decode_jwt, scopes=["invite:create"]),
):
    invite_in_db = await invite_services.create(invite=invite, user_making_request=current_user.user_id)

    if invite_in_db:
        return build_response(
            status_code=201, message="Invite created with success", data=invite_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a invite", data=None
        )


@router.post("/invites/{invite_id}/accept", responses={200: {"model": InviteInDB}})
async def accept_invite(
    invite_id: str,
    invite_services: InviteServices = Depends(invite_composer),
    organization_services: OrganizationServices = Depends(organization_composer),
    current_user: UserInDB = Security(decode_jwt, scopes=["invite:create"]),
):
    invite_in_db = await invite_services.accept(id=invite_id, user_making_request=current_user.user_id)

    if invite_in_db and invite_in_db.is_accepted:
        await organization_services.add_user(
            user_id=current_user.user_id,
            organization_id=invite_in_db.organization_id,
            role=invite_in_db.role,
            user_making_request=current_user.user_id
        )

        return build_response(
            status_code=200, message="Invite accepted with success", data=invite_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on acept an invite", data=None
        )


@router.delete("/invites/{invite_id}", responses={200: {"model": InviteInDB}})
async def delete_invite(
    invite_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["invite:create"]),
    invite_services: InviteServices = Depends(invite_composer),
):
    invite_in_db = await invite_services.delete_by_id(id=invite_id)

    if invite_in_db:
        return build_response(
            status_code=200, message="Invite deleted with success", data=invite_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Invite {invite_id} not found", data=None
        )
