from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import section_offer_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.section_offers import SectionOfferServices, SectionOfferInDB

router = APIRouter(tags=["Section Offers"])


@router.get(
    "/sections/{section_id}/offers",
    responses={200: {"model": List[SectionOfferInDB]}},
)
async def get_section_offers(
    section_id: str,
    is_visible: bool = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["section:get"]),
    section_offer_services: SectionOfferServices = Depends(section_offer_composer),
):
    section_offers = await section_offer_services.search_all(
        section_id=section_id, is_visible=is_visible, expand=expand
    )

    if section_offers:
        return build_response(
            status_code=200,
            message="Section offers found with success",
            data=section_offers,
        )

    else:
        return Response(status_code=204)
