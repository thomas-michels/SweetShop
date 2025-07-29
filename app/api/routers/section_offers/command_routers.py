from fastapi import APIRouter, Depends, Security

from app.api.composers import section_offer_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.section_offers import (
    SectionOffer,
    SectionOfferInDB,
    UpdateSectionOffer,
    SectionOfferServices,
)

router = APIRouter(tags=["Section Offers"])


@router.post("/section_offers", responses={201: {"model": SectionOfferInDB}})
async def create_section_offer(
    section_offer: SectionOffer,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:create"]),
    section_offer_services: SectionOfferServices = Depends(section_offer_composer),
):
    section_offer_in_db = await section_offer_services.create(section_offer=section_offer)

    if section_offer_in_db:
        return build_response(
            status_code=201,
            message="Section offer created with success",
            data=section_offer_in_db,
        )
    else:
        return build_response(
            status_code=400,
            message="Erro ao criar section offer",
            data=None,
        )


@router.put("/section_offers/{section_offer_id}", responses={200: {"model": SectionOfferInDB}})
async def update_section_offer(
    section_offer_id: str,
    section_offer: UpdateSectionOffer,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:create"]),
    section_offer_services: SectionOfferServices = Depends(section_offer_composer),
):
    section_offer_in_db = await section_offer_services.update(
        id=section_offer_id,
        updated_section_offer=section_offer,
    )

    if section_offer_in_db:
        return build_response(
            status_code=200,
            message="Section offer updated with success",
            data=section_offer_in_db,
        )
    else:
        return build_response(
            status_code=400,
            message="Erro ao atualizar section offer",
            data=None,
        )


@router.delete("/section_offers/{section_offer_id}", responses={200: {"model": SectionOfferInDB}})
async def delete_section_offer(
    section_offer_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["section:delete"]),
    section_offer_services: SectionOfferServices = Depends(section_offer_composer),
):
    section_offer_in_db = await section_offer_services.delete_by_id(id=section_offer_id)

    if section_offer_in_db:
        return build_response(
            status_code=200,
            message="Section offer deleted with success",
            data=section_offer_in_db,
        )
    else:
        return build_response(
            status_code=404,
            message=f"SectionOffer {section_offer_id} not found",
            data=None,
        )
