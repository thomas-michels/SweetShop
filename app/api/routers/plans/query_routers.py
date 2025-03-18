from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import plan_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.auth import verify_super_user
from app.crud.users import CompleteUserInDB
from app.crud.plans import PlanServices, PlanInDB

router = APIRouter(tags=["Plans"])


@router.get("/plans", responses={200: {"model": List[PlanInDB]}})
async def get_plans(
    expand: List[str] = Query(default=[]),
    plan_services: PlanServices = Depends(plan_composer),
):
    plans = await plan_services.search_all(expand=expand)

    if plans:
        return build_response(
            status_code=200, message="Plans found with success", data=plans
        )

    else:
        return Response(status_code=204)


@router.get("/plans/{plan_id}", responses={200: {"model": PlanInDB}})
async def get_plan_by_id(
    plan_id: str,
    expand: List[str] = Query(default=[]),
    plan_services: PlanServices = Depends(plan_composer),
):
    plan_in_db = await plan_services.search_by_id(
        id=plan_id,
        expand=expand
    )

    if plan_in_db:
        return build_response(
            status_code=200, message="Plan found with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Plan {plan_id} not found", data=None
        )


@router.get("/plans/name/{name}", responses={200: {"model": PlanInDB}})
async def get_plan_by_name(
    name: str,
    expand: List[str] = Query(default=[]),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    plan_services: PlanServices = Depends(plan_composer),
):
    verify_super_user(current_user=current_user)

    plan_in_db = await plan_services.search_by_name(
        name=name,
        expand=expand
    )

    if plan_in_db:
        return build_response(
            status_code=200, message="Plan found with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Plan with name {name} not found", data=None
        )
