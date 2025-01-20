from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import invite_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.invites import InviteInDB, InviteServices

router = APIRouter(tags=["Invites"])


@router.get("/invites/{invite_id}", responses={200: {"model": InviteInDB}})
async def get_invites_by_id(
    invite_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    invites_services: InviteServices = Depends(invite_composer),
):
    invites_in_db = await invites_services.search_by_id(id=invite_id)

    if invites_in_db:
        return build_response(
            status_code=200, message="Invite found with success", data=invites_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Invite {invite_id} not found", data=None
        )


@router.get("/organizations/{organization_id}/invites", responses={200: {"model": List[InviteInDB]}})
async def get_invites_by_organization_id(
    organization_id: str,
    accepted: bool = Query(default=False),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["invite:get"]),
    invites_services: InviteServices = Depends(invite_composer),
):
    invites = await invites_services.search_all(
        organization_id=organization_id,
        accepted=accepted,
        expand=expand
    )

    if invites:
        return build_response(
            status_code=200, message="Invites found with success", data=invites
        )

    else:
        return Response(status_code=204)


@router.get("/users/{user_id}/invites", responses={200: {"model": List[InviteInDB]}})
async def get_user_invites(
    user_id: str,
    accepted: bool = Query(default=False),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    invites_services: InviteServices = Depends(invite_composer),
):
    invites_in_db = await invites_services.search_by_user_id(
        user_id=user_id,
        accepted=accepted,
        expand=expand
    )

    if invites_in_db:
        return build_response(
            status_code=200, message="Invites found with success", data=invites_in_db
        )

    else:
        return Response(status_code=204)
