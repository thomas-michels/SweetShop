from typing import List

from fastapi import APIRouter, Depends, Query, Request, Security, Response

from app.api.composers import tag_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.api.shared_schemas.responses import MessageResponse
from app.crud.users import UserInDB
from app.crud.tags import TagServices
from .schemas import GetTagResponse, GetTagsResponse

router = APIRouter(tags=["Tags"])


@router.get(
    "/tags/{tags_id}",
    responses={
        200: {"model": GetTagResponse},
        404: {"model": MessageResponse},
    },
)
async def get_tags_by_id(
    tags_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["tag:get"]),
    tags_services: TagServices = Depends(tag_composer),
):
    tags_in_db = await tags_services.search_by_id(id=tags_id)

    if tags_in_db:
        return build_response(
            status_code=200, message="Tag found with success", data=tags_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Tag {tags_id} not found", data=None
        )


@router.get(
    "/tags",
    responses={
        200: {"model": GetTagsResponse},
        204: {"description": "No Content"},
    },
)
async def get_tags(
    request: Request,
    query: str = Query(default=None),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=["tag:get"]),
    tags_services: TagServices = Depends(tag_composer),
):
    paginator = Paginator(
        request=request, pagination=pagination
    )

    total = await tags_services.count_all(query=query)
    tags = await tags_services.search_all(
        query=query,
        page=pagination["page"],
        page_size=pagination["page_size"],
    )

    paginator.set_total(total=total)

    if tags:
        return build_list_response(
            status_code=200,
            message="Tags found with success",
            pagination=paginator.pagination,
            data=tags
        )

    else:
        return Response(status_code=204)
