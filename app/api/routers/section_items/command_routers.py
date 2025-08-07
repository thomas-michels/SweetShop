from fastapi import APIRouter, Depends, Security

from app.api.composers import section_item_composer
from app.api.dependencies.response import build_response
from app.api.dependencies.auth import decode_jwt
from app.crud.users import UserInDB
from app.crud.section_items import (
    SectionItem,
    SectionItemInDB,
    UpdateSectionItem,
    SectionItemServices,
)

router = APIRouter(tags=["Section Items"])


@router.post("/section_items", responses={201: {"model": SectionItemInDB}})
async def create_section_item(
    section_item: SectionItem,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:create"]),
    section_item_services: SectionItemServices = Depends(section_item_composer),
):
    section_item_in_db = await section_item_services.create(section_item=section_item)

    if section_item_in_db:
        return build_response(
            status_code=201,
            message="Section item created with success",
            data=section_item_in_db,
        )
    else:
        return build_response(
            status_code=400,
            message="Erro ao criar section item",
            data=None,
        )


@router.put("/section_items/{section_item_id}", responses={200: {"model": SectionItemInDB}})
async def update_section_item(
    section_item_id: str,
    section_item: UpdateSectionItem,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:create"]),
    section_item_services: SectionItemServices = Depends(section_item_composer),
):
    section_item_in_db = await section_item_services.update(
        id=section_item_id,
        updated_section_item=section_item,
    )

    if section_item_in_db:
        return build_response(
            status_code=200,
            message="Section item updated with success",
            data=section_item_in_db,
        )

    else:
        return build_response(
            status_code=400,
            message="Erro ao atualizar section item",
            data=None,
        )


@router.delete("/section_items/{section_item_id}", responses={200: {"model": SectionItemInDB}})
async def delete_section_item(
    section_item_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:delete"]),
    section_item_services: SectionItemServices = Depends(section_item_composer),
):
    section_item_in_db = await section_item_services.delete_by_id(id=section_item_id)

    if section_item_in_db:
        return build_response(
            status_code=200,
            message="Section item deleted with success",
            data=section_item_in_db,
        )

    else:
        return build_response(
            status_code=404,
            message=f"SectionItem {section_item_id} not found",
            data=None,
        )
