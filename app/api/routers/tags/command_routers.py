from fastapi import APIRouter, Depends, Security

from app.api.composers import tag_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.shared_schemas.responses import MessageResponse
from app.crud.tags import (
    Tag,
    UpdateTag,
    TagServices
)
from app.crud.users import UserInDB
from .schemas import (
    CreateTagResponse,
    UpdateTagResponse,
    DeleteTagResponse,
)

router = APIRouter(tags=["Tags"])


@router.post(
    "/tags",
    responses={
        201: {"model": CreateTagResponse},
        400: {"model": MessageResponse},
    },
)
async def create_tag(
    tag: Tag,
    tag_services: TagServices = Depends(tag_composer),
    current_user: UserInDB = Security(decode_jwt, scopes=["tag:create"]),
):
    tag_in_db = await tag_services.create(tag=tag)

    if tag_in_db:
        return build_response(
            status_code=201, message="Tag created with success", data=tag_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao criar tag", data=None
        )


@router.put(
    "/tags/{tag_id}",
    responses={
        200: {"model": UpdateTagResponse},
        400: {"model": MessageResponse},
    },
)
async def update_tag(
    tag_id: str,
    tag: UpdateTag,
    current_user: UserInDB = Security(decode_jwt, scopes=["tag:create"]),
    tag_services: TagServices = Depends(tag_composer),
):
    tag_in_db = await tag_services.update(id=tag_id, updated_tag=tag)

    if tag_in_db:
        return build_response(
            status_code=200, message="Tag updated with success", data=tag_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro atualizar tag", data=None
        )


@router.delete(
    "/tags/{tag_id}",
    responses={
        200: {"model": DeleteTagResponse},
        404: {"model": MessageResponse},
    },
)
async def delete_tag(
    tag_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["tag:delete"]),
    tag_services: TagServices = Depends(tag_composer),
):
    tag_in_db = await tag_services.delete_by_id(id=tag_id)

    if tag_in_db:
        return build_response(
            status_code=200, message="Tag deleted with success", data=tag_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Tag {tag_id} não encontrada", data=None
        )
