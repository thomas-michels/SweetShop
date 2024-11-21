from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import tag_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.tags import TagServices, TagInDB

router = APIRouter(tags=["Tags"])


@router.get("/tags/{tags_id}", responses={200: {"model": TagInDB}})
async def get_tags_by_id(
    tags_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["tags:get"]),
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


@router.get("/tags", responses={200: {"model": List[TagInDB]}})
async def get_tags(
    query: str = Query(default=None),
    current_tags: UserInDB = Security(decode_jwt, scopes=["tags:get"]),
    tags_services: TagServices = Depends(tag_composer),
):
    tagss = await tags_services.search_all(query=query)

    if tagss:
        return build_response(
            status_code=200, message="Tags found with success", data=tagss
        )

    else:
        return Response(status_code=204)
