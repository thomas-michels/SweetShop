from typing import List

from fastapi import APIRouter, Depends, Security, Response

from app.api.composers import organization_plan_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.organization_plans import OrganizationPlanServices, OrganizationPlanInDB

router = APIRouter(tags=["Organization Plans"])


@router.get("/organization_plans/{organization_plan_id}", responses={200: {"model": OrganizationPlanInDB}})
async def get_organization_plan_by_id(
    organization_plan_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["organization_plan:get"]),
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
):
    organization_plan_in_db = await organization_plan_services.search_by_id(id=organization_plan_id)

    if organization_plan_in_db:
        return build_response(
            status_code=200, message="Organization plan found with success", data=organization_plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Organization plan {organization_plan_id} not found", data=None
        )


@router.get("/organization_plans", responses={200: {"model": List[OrganizationPlanInDB]}})
async def get_organization_plans(
    current_user: UserInDB = Security(decode_jwt, scopes=["organization_plan:get"]),
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
):
    organization_plans = await organization_plan_services.search_all()

    if organization_plans:
        return build_response(
            status_code=200, message="Organization plans found with success", data=organization_plans
        )

    else:
        return Response(status_code=204)
