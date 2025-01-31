from fastapi import APIRouter, Depends, HTTPException, Security, status

from app.api.composers import organization_plan_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.auth import verify_scopes
from app.crud.organization_plans import (
    OrganizationPlan,
    OrganizationPlanInDB,
    UpdateOrganizationPlan,
    OrganizationPlanServices
)
from app.crud.users import CompleteUserInDB

router = APIRouter(tags=["Organization Plans"])


@router.post("/organizations/{organization_id}/plans", responses={201: {"model": OrganizationPlanInDB}})
async def create_organization_plan(
    organization_id: str,
    organization_plan: OrganizationPlan,
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=["organization_plan:create"]),
):
    if organization_id not in current_user.organizations_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this organization!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    verify_scopes(
        scopes_needed=["organization_plan:create"],
        user_role=current_user.organizations_roles[organization_id].role,
        current_user=current_user
    )

    organization_plan_in_db = await organization_plan_services.create(
        organization_plan=organization_plan,
        organization_id=organization_id
    )

    if organization_plan_in_db:
        return build_response(
            status_code=201, message="Organization Plan created with success", data=organization_plan_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a organization plan", data=None
        )


@router.put("/organizations/{organization_id}/plans/{organization_plan_id}", responses={200: {"model": OrganizationPlanInDB}})
async def update_organization_plan(
    organization_id: str,
    organization_plan_id: str,
    organization_plan: UpdateOrganizationPlan,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=["organization_plan:create"]),
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
):
    if organization_id not in current_user.organizations_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this organization!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    verify_scopes(
        scopes_needed=["organization_plan:create"],
        user_role=current_user.organizations_roles[organization_id].role,
        current_user=current_user
    )

    organization_plan_in_db = await organization_plan_services.update(
        id=organization_plan_id,
        organization_id=organization_id,
        updated_organization_plan=organization_plan
    )

    if organization_plan_in_db:
        return build_response(
            status_code=200, message="Organization Plan updated with success", data=organization_plan_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a organization plan", data=None
        )


@router.delete("/organizations/{organization_id}/plans/{organization_plan_id}", responses={200: {"model": OrganizationPlanInDB}})
async def delete_organization_plan(
    organization_plan_id: str,
    organization_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=["organization_plan:delete"]),
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
):
    if organization_id not in current_user.organizations_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this organization!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    verify_scopes(
        scopes_needed=["organization_plan:delete"],
        user_role=current_user.organizations_roles[organization_id].role,
        current_user=current_user
    )

    organization_plan_in_db = await organization_plan_services.delete_by_id(
        id=organization_plan_id,
        organization_id=organization_id
    )

    if organization_plan_in_db:
        return build_response(
            status_code=200, message="Organization Plan deleted with success", data=organization_plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Organization Plan {organization_plan_id} not found", data=None
        )
