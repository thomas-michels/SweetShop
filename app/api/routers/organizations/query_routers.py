from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import organization_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.organizations import OrganizationInDB, OrganizationServices

router = APIRouter(tags=["Organizations"])


@router.get("/users/{user_id}/organizations", responses={200: {"model": OrganizationInDB}})
async def get_users_organizations(
    user_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:get"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organizations = await organization_services.search_all(user_id=user_id, expand=expand)

    if organizations:
        return build_response(
            status_code=200, message="Organization found with success", data=organizations
        )

    else:
        return Response(status_code=204)


@router.get("/organizations/{organization_id}", responses={200: {"model": OrganizationInDB}})
async def get_organization_by_id(
    organization_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:get"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    user_in_db = await organization_services.search_by_id(
        id=organization_id,
        expand=expand
    )

    if user_in_db:
        return build_response(
            status_code=200, message="Organization found with success", data=user_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Organization {organization_id} not found", data=None
        )


@router.get("/organizations", responses={200: {"model": List[OrganizationInDB]}})
async def get_organizations(
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:get"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organizations = await organization_services.search_all(expand=expand)

    if organizations:
        return build_response(
            status_code=200, message="Organizataions found with success", data=organizations
        )

    else:
        return Response(status_code=204)
