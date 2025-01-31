from typing import List

from fastapi import APIRouter, Depends, HTTPException, Security, Response, status

from app.api.composers import organization_plan_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import CompleteUserInDB
from app.crud.organization_plans import OrganizationPlanServices, OrganizationPlanInDB

router = APIRouter(tags=["Organization Plans"])


@router.get("/organizations/{organization_id}/plans/{organization_plan_id}", responses={200: {"model": OrganizationPlanInDB}})
async def get_organization_plan_by_id(
    organization_id: str,
    organization_plan_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=["organization_plan:get"]),
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
):
    if organization_id not in current_user.organizations_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this organization!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    organization_plan_in_db = await organization_plan_services.search_by_id(
        id=organization_plan_id,
        organization_id=organization_id
    )

    if organization_plan_in_db:
        return build_response(
            status_code=200, message="Organization plan found with success", data=organization_plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Organization plan {organization_plan_id} not found", data=None
        )


@router.get("/organizations/{organization_id}/plans", responses={200: {"model": List[OrganizationPlanInDB]}})
async def get_organization_plans(
    organization_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=["organization_plan:get"]),
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
):
    if organization_id not in current_user.organizations_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this organization!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    organization_plans = await organization_plan_services.search_all(organization_id=organization_id)

    if organization_plans:
        return build_response(
            status_code=200, message="Organization plans found with success", data=organization_plans
        )

    else:
        return Response(status_code=204)
