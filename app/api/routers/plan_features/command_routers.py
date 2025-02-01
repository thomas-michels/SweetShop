from fastapi import APIRouter, Depends, Security

from app.api.composers import plan_feature_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.auth import verify_super_user
from app.crud.plan_features import (
    PlanFeature,
    PlanFeatureInDB,
    UpdatePlanFeature,
    PlanFeatureServices
)
from app.crud.users import CompleteUserInDB

router = APIRouter(tags=["Plan Features"])


@router.post("/plan_features", responses={201: {"model": PlanFeatureInDB}})
async def create_plan_feature(
    plan_feature: PlanFeature,
    plan_feature_services: PlanFeatureServices = Depends(plan_feature_composer),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
):
    verify_super_user(current_user=current_user)

    plan_in_db = await plan_feature_services.create(plan_feature=plan_feature)

    if plan_in_db:
        return build_response(
            status_code=201, message="Plan Feature created with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a plan feature", data=None
        )


@router.put("/plan_features/{plan_feature_id}", responses={200: {"model": PlanFeatureInDB}})
async def update_plan_feature(
    plan_feature_id: str,
    plan_feature: UpdatePlanFeature,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    plan_feature_services: PlanFeatureServices = Depends(plan_feature_composer),
):
    verify_super_user(current_user=current_user)

    plan_in_db = await plan_feature_services.update(
        id=plan_feature_id,
        updated_plan_feature=plan_feature
    )

    if plan_in_db:
        return build_response(
            status_code=200, message="Plan Feature updated with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a plan feature", data=None
        )


@router.delete("/plan_features/{plan_feature_id}", responses={200: {"model": PlanFeatureInDB}})
async def delete_plan_feature(
    plan_feature_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    plan_feature_services: PlanFeatureServices = Depends(plan_feature_composer),
):
    verify_super_user(current_user=current_user)

    plan_in_db = await plan_feature_services.delete_by_id(id=plan_feature_id)

    if plan_in_db:
        return build_response(
            status_code=200, message="Plan Feature deleted with success", data=plan_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Plan Feature {plan_feature_id} not found", data=None
        )
