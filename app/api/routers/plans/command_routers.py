from fastapi import APIRouter, Depends, Security

from app.api.composers import plan_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.auth import verify_super_user
from app.crud.plans import (
    Plan,
    PlanInDB,
    UpdatePlan,
    PlanServices
)
from app.crud.users import CompleteUserInDB

router = APIRouter(tags=["Plans"])


@router.post("/plans", responses={201: {"model": PlanInDB}})
async def create_plan(
    plan: Plan,
    plan_services: PlanServices = Depends(plan_composer),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
):
    verify_super_user(current_user=current_user)

    plan_in_db = await plan_services.create(plan=plan)

    if plan_in_db:
        return build_response(
            status_code=201, message="Plan created with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a plan", data=None
        )


@router.put("/plans/{plan_id}", responses={200: {"model": PlanInDB}})
async def update_plan(
    plan_id: str,
    plan: UpdatePlan,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    plan_services: PlanServices = Depends(plan_composer),
):
    verify_super_user(current_user=current_user)

    plan_in_db = await plan_services.update(
        id=plan_id,
        updated_plan=plan
    )

    if plan_in_db:
        return build_response(
            status_code=200, message="Plan updated with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a plan", data=None
        )


@router.delete("/plans/{plan_id}", responses={200: {"model": PlanInDB}})
async def delete_plan(
    plan_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    plan_services: PlanServices = Depends(plan_composer),
):
    verify_super_user(current_user=current_user)

    plan_in_db = await plan_services.delete_by_id(id=plan_id)

    if plan_in_db:
        return build_response(
            status_code=200, message="Plan deleted with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Plan {plan_id} not found", data=None
        )
