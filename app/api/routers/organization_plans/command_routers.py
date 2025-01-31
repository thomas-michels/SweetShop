from fastapi import APIRouter, Depends, Security

from app.api.composers import organization_plan_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.organization_plans import (
    OrganizationPlan,
    OrganizationPlanInDB,
    UpdateOrganizationPlan,
    OrganizationPlanServices
)
from app.crud.users import UserInDB

router = APIRouter(tags=["Organization Plans"])


@router.post("/organization_plans", responses={201: {"model": OrganizationPlanInDB}})
async def create_organization_plan(
    organization_plan: OrganizationPlan,
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
    current_user: UserInDB = Security(decode_jwt, scopes=["organization_plan:create"]),
):
    organization_plan_in_db = await organization_plan_services.create(
        organization_plan=organization_plan
    )

    if organization_plan_in_db:
        return build_response(
            status_code=201, message="Organization Plan created with success", data=organization_plan_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a organization plan", data=None
        )


@router.put("/organization_plans/{organization_plan_id}", responses={200: {"model": OrganizationPlanInDB}})
async def update_organization_plan(
    organization_plan_id: str,
    organization_plan: UpdateOrganizationPlan,
    current_user: UserInDB = Security(decode_jwt, scopes=["organization_plan:create"]),
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
):
    organization_plan_in_db = await organization_plan_services.update(
        id=organization_plan_id,
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


@router.delete("/organization_plans/{organization_plan_id}", responses={200: {"model": OrganizationPlanInDB}})
async def delete_organization_plan(
    organization_plan_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["organization_plan:delete"]),
    organization_plan_services: OrganizationPlanServices = Depends(organization_plan_composer),
):
    organization_plan_in_db = await organization_plan_services.delete_by_id(id=organization_plan_id)

    if organization_plan_in_db:
        return build_response(
            status_code=200, message="Organization Plan deleted with success", data=organization_plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Organization Plan {organization_plan_id} not found", data=None
        )
