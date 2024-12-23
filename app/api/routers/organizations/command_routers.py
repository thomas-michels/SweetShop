from fastapi import APIRouter, Depends, Security

from app.api.composers import organization_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.shared_schemas.role import RequestRole
from app.crud.users import UserInDB
from app.crud.organizations import Organization, OrganizationInDB, UpdateOrganization, OrganizationServices

router = APIRouter(tags=["Organizations"])


@router.post("/organizations", responses={201: {"model": OrganizationInDB}})
async def create_organizations(
    organization: Organization,
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:create"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organization_in_db = await organization_services.create(
        organization=organization,
        owner=current_user
    )

    if organization_in_db:
        return build_response(
            status_code=201, message="Organization created with success", data=organization_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create an organization", data=None
        )


@router.put("/organizations/{organization_id}", responses={200: {"model": OrganizationInDB}})
async def update_organization(
    organization_id: str,
    organization: UpdateOrganization,
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:update"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organization_in_db = await organization_services.update(id=organization_id, updated_organization=organization)

    if organization_in_db:
        return build_response(
            status_code=200, message="Organization updated with success", data=organization_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update an organization", data=None
        )


@router.delete("/organizations/{organization_id}", responses={200: {"model": OrganizationInDB}})
async def delete_organization(
    organization_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:delete"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organization_in_db = await organization_services.delete_by_id(id=organization_id)

    if organization_in_db:
        return build_response(
            status_code=200, message="Organization deleted with success", data=organization_in_db
        )
    else:
        return build_response(
            status_code=404, message=f"Organization {organization_id} not found", data=None
        )


@router.post("/organizations/{organization_id}/members/{user_id}", responses={200: {"model": OrganizationInDB}})
async def add_user_in_organization(
    organization_id: str,
    user_id: str,
    request_role: RequestRole,
    current_user: UserInDB = Security(decode_jwt, scopes=["member:add"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    added = await organization_services.add_user(
        organization_id=organization_id,
        user_making_request=current_user.user_id,
        user_id=user_id,
        role=request_role.role
    )

    if added:
        return build_response(
            status_code=200, message="User added in Organization with success", data=None
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on add an user in an organization", data=None
        )


@router.delete("/organizations/{organization_id}/members/{user_id}", responses={200: {"model": OrganizationInDB}})
async def remove_user_from_organization(
    organization_id: str,
    user_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["member:remove"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    removed = await organization_services.remove_user(
        organization_id=organization_id,
        user_making_request=current_user.user_id,
        user_id=user_id,
    )

    if removed:
        return build_response(
            status_code=200, message="User removed from Organization with success", data=None
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on remove an user from organization", data=None
        )
