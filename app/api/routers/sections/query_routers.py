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
    current_user: UserInDB = Security(decode_jwt, scopes=["section:get"]),
    section_services: SectionServices = Depends(section_composer),
):
    section_in_db = await section_services.search_by_id(id=section_id)

    if section_in_db:
        return build_response(
            status_code=200, message="Section found with success", data=section_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Section {section_id} not found", data=None
        )


@router.get("/sections", responses={200: {"model": List[SectionInDB]}})
async def get_sections(
    query: str = Query(default=None),
    tags: List[str] = Query(default=[]),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["section:get"]),
    section_services: SectionServices = Depends(section_composer),
):
    sections = await section_services.search_all(
        query=query,
        tags=tags,
        expand=expand
    )

    if sections:
        return build_response(
            status_code=200, message="Sections found with success", data=sections
        )

    else:
        return Response(status_code=204)
