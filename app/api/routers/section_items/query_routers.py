from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import section_item_composer
from app.api.dependencies.response import build_response
from app.api.dependencies.auth import decode_jwt
from app.crud.users import UserInDB
from app.crud.section_items.services import SectionItemServices
from .schemas import GetSectionItemsResponse

router = APIRouter(tags=["Section Items"])


@router.get(
    "/sections/{section_id}/items",
    responses={
        200: {"model": GetSectionItemsResponse},
        204: {"description": "No Content"},
    },
    tags=["Sections"]
)
async def get_section_items(
    section_id: str,
    is_visible: bool = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["section:get"]),
    section_item_services: SectionItemServices = Depends(section_item_composer),
):
    section_items = await section_item_services.search_all(
        section_id=section_id, is_visible=is_visible, expand=expand
    )

    if section_items:
        return build_response(
            status_code=200,
            message="Section items found with success",
            data=section_items,
        )

    else:
        return Response(status_code=204)
