from typing import List

from fastapi import APIRouter, Depends, Header, Query, Security, Response

from app.api.composers import organization_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.shared_schemas.responses import MessageResponse
from app.core.configs import get_environment
from app.core.utils.features import Feature
from app.crud.users import UserInDB
from app.crud.organizations import OrganizationServices
from .schemas import (
    GetUsersOrganizationsResponse,
    GetOrganizationResponse,
    GetOrganizationsResponse,
    GetOrganizationFeatureResponse,
)

router = APIRouter(tags=["Organizations"])
_env = get_environment()


@router.get(
    "/users/{user_id}/organizations",
    responses={
        200: {"model": GetUsersOrganizationsResponse},
        204: {"description": "No Content"},
    },
)
async def get_users_organizations(
    user_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:get"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organizations = await organization_services.search_all(user_id=user_id, expand=expand)

    if organizations:
        return build_response(
            status_code=200, message="Organization found with success", data=organizations
        )

    else:
        return Response(status_code=204)


@router.get(
    "/organizations/{organization_id}",
    responses={
        200: {"model": GetOrganizationResponse},
        404: {"model": MessageResponse},
    },
)
async def get_organization_by_id(
    organization_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:get"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organization_in_db = await organization_services.search_by_id(
        id=organization_id,
        expand=expand
    )

    if organization_in_db:
        return build_response(
            status_code=200, message="Organization found with success", data=organization_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Organização {organization_id} não encontrada", data=None
        )


@router.get(
    "/organizations",
    responses={
        200: {"model": GetOrganizationsResponse},
        204: {"description": "No Content"},
    },
)
async def get_organizations(
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["organization:get"]),
    organization_services: OrganizationServices = Depends(organization_composer),
):
    organizations = await organization_services.search_all(expand=expand)

    if organizations:
        return build_response(
            status_code=200, message="Organizataions found with success", data=organizations
        )

    else:
        return Response(status_code=204)


@router.get(
    "/organizations/{organization_id}/features/{feature_name}",
    responses={
        200: {"model": GetOrganizationFeatureResponse},
        400: {"model": GetOrganizationFeatureResponse},
        401: {"model": MessageResponse},
    },
)
async def get_organization_features_by_id(
    organization_id: str,
    feature_name: Feature,
    token: str = Header(default=None, include_in_schema=False)
):
    if _env.API_TOKEN != token:
        return build_response(
            status_code=401, message="Unauthorized!", data=None
        )

    plan_feature = await get_plan_feature(
        organization_id=organization_id,
        feature_name=feature_name
    )

    if plan_feature and plan_feature.value.startswith("t"):
        return build_response(
            status_code=200, message="This organization have this feature", data=None
        )

    else:
        return build_response(
            status_code=400, message=f"This organization doesn't have this feature", data=None
        )
