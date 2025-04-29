from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import section_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.sections import SectionInDB, SectionServices

router = APIRouter(tags=["Sections"])


@router.get("/sections/{section_id}", responses={200: {"model": SectionInDB}})
async def get_section_by_id(
    section_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["section:get"]),
    section_services: SectionServices = Depends(section_composer),
):
    section_in_db = await section_services.search_by_id(
        id=section_id,
        expand=expand
    )

    if section_in_db:
        return build_response(
            status_code=200, message="Section found with success", data=section_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Seção {section_id} não encontrada", data=None
        )


@router.get("/menus/{menu_id}/sections", tags=["Menus"], responses={200: {"model": List[SectionInDB]}})
async def get_sections(
    menu_id: str,
    is_visible: bool = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["section:get"]),
    section_services: SectionServices = Depends(section_composer),
):
    sections = await section_services.search_all(
        menu_id=menu_id,
        is_visible=is_visible,
        expand=expand
    )

    if sections:
        return build_response(
            status_code=200, message="Sections found with success", data=sections
        )

    else:
        return Response(status_code=204)
