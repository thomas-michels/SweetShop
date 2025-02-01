from typing import List

from fastapi import APIRouter, Depends, Security, Response

from app.api.composers import plan_feature_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.auth import verify_super_user
from app.crud.users import CompleteUserInDB
from app.crud.plan_features import PlanFeatureServices, PlanFeatureInDB

router = APIRouter(tags=["Plan Features"])


@router.get("/plan_features/{plan_feature_id}", responses={200: {"model": PlanFeatureInDB}})
async def get_plan_feature_by_id(
    plan_feature_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    plan_feature_services: PlanFeatureServices = Depends(plan_feature_composer),
):
    verify_super_user(current_user=current_user)

    plan_in_db = await plan_feature_services.search_by_id(id=plan_feature_id)

    if plan_in_db:
        return build_response(
            status_code=200, message="Plan feature found with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Plan feature {plan_feature_id} not found", data=None
        )


@router.get("/plans/{plan_id}/features", responses={200: {"model": List[PlanFeatureInDB]}})
async def get_plan_features(
    plan_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    plan_feature_services: PlanFeatureServices = Depends(plan_feature_composer),
):
    verify_super_user(current_user=current_user)

    plan_features = await plan_feature_services.search_all(plan_id=plan_id)

    if plan_features:
        return build_response(
            status_code=200, message="Plan features found with success", data=plan_features
        )

    else:
        return Response(status_code=204)
