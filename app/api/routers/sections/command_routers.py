from fastapi import APIRouter, Depends, Security

from app.api.composers import section_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.shared_schemas.responses import MessageResponse
from app.crud.users import UserInDB
from app.crud.sections import Section, UpdateSection, SectionServices
from .schemas import (
    CreateSectionResponse,
    UpdateSectionResponse,
    DeleteSectionResponse,
)

router = APIRouter(tags=["Sections"])


@router.post(
    "/sections",
    responses={201: {"model": CreateSectionResponse}, 400: {"model": MessageResponse}},
)
async def create_sections(
    section: Section,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:create"]),
    section_services: SectionServices = Depends(section_composer),
):
    section_in_db = await section_services.create(
        section=section
    )

    if section_in_db:
        return build_response(
            status_code=201, message="Section created with success", data=section_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao criar seção", data=None
        )


@router.put(
    "/sections/{section_id}",
    responses={200: {"model": UpdateSectionResponse}, 400: {"model": MessageResponse}},
)
async def update_section(
    section_id: str,
    section: UpdateSection,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:create"]),
    section_services: SectionServices = Depends(section_composer),
):
    section_in_db = await section_services.update(id=section_id, updated_section=section)

    if section_in_db:
        return build_response(
            status_code=200, message="Section updated with success", data=section_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao atualizar seção", data=None
        )


@router.delete(
    "/sections/{section_id}",
    responses={200: {"model": DeleteSectionResponse}, 404: {"model": MessageResponse}},
)
async def delete_section(
    section_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:delete"]),
    section_services: SectionServices = Depends(section_composer),
):
    section_in_db = await section_services.delete_by_id(id=section_id)

    if section_in_db:
        return build_response(
            status_code=200, message="Section deleted with success", data=section_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Seção {section_id} não encontrada", data=None
        )
