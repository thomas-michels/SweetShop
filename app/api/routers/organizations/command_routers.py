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
            status_code=400, message="Erro ao criar organização", data=None
        )


@router.put("/organizations/{organization_id}", responses={200: {"model": OrganizationInDB}})
async def update_organization(
    organization_id: str,
    organization: UpdateOrganization,
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:update"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organization_in_db = await organization_services.update(
        id=organization_id,
        updated_organization=organization,
        user_making_request=current_user.user_id
    )

    if organization_in_db:
        return build_response(
            status_code=200, message="Organization updated with success", data=organization_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao atualizar organização", data=None
        )


@router.delete("/organizations/{organization_id}", responses={200: {"model": OrganizationInDB}})
async def delete_organization(
    organization_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:delete"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organization_in_db = await organization_services.delete_by_id(
        id=organization_id,
        user_making_request=current_user.user_id
    )

    if organization_in_db:
        return build_response(
            status_code=200, message="Organization deleted with success", data=organization_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Organização {organization_id} não encontrada", data=None
        )


@router.patch("/organizations/{organization_id}/members/{user_id}", responses={200: {"model": OrganizationInDB}})
async def update_user_in_organization(
    organization_id: str,
    user_id: str,
    request_role: RequestRole,
    current_user: UserInDB = Security(decode_jwt, scopes=["member:add"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    added = await organization_services.update_user_role(
        organization_id=organization_id,
        user_making_request=current_user.user_id,
        user_id=user_id,
        role=request_role.role
    )

    if added:
        return build_response(
            status_code=200, message="User's role updated with success", data=None
        )

    else:
        return build_response(
            status_code=400, message="Erro ao atualizar usuário na organização", data=None
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
            status_code=400, message="Erro ao remover usuário da organização", data=None
        )


@router.post("/organizations/{organization_id}/members/{user_id}/transfer_ownership", responses={200: {"model": OrganizationInDB}})
async def transfer_organization_ownership(
    organization_id: str,
    user_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["member:add"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    transfered = await organization_services.transfer_ownership(
        organization_id=organization_id,
        user_making_request=current_user.user_id,
        user_id=user_id
    )

    if transfered:
        return build_response(
            status_code=200, message="New organization owner set with success", data=None
        )

    else:
        return build_response(
            status_code=400, message="Erro ao transferir dono da organização", data=None
        )


@router.post("/organizations/{organization_id}/leave", responses={200: {"model": OrganizationInDB}})
async def leave_the_organization(
    organization_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    left = await organization_services.leave_the_organization(
        organization_id=organization_id,
        user_id=current_user.user_id
    )

    if left:
        return build_response(
            status_code=200, message="You left the organization", data=None
        )

    else:
        return build_response(
            status_code=400, message="Erro ao sair da organização", data=None
        )
