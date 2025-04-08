from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import offer_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.offers import OfferInDB, OfferServices

router = APIRouter(tags=["Offers"])


@router.get("/offers/{offer_id}", responses={200: {"model": OfferInDB}})
async def get_offer_by_id(
    offer_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    offer_services: OfferServices = Depends(offer_composer),
):
    offer_in_db = await offer_services.search_by_id(id=offer_id, expand=expand)

    if offer_in_db:
        return build_response(
            status_code=200, message="Offer found with success", data=offer_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Oferta {offer_id} não encontrada", data=None
        )


@router.get("/sections/{section_id}/offers", tags=["Sections"], responses={200: {"model": List[OfferInDB]}})
async def get_offers(
    section_id: str,
    is_visible: bool = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    offer_services: OfferServices = Depends(offer_composer),
):
    offers = await offer_services.search_all(
        section_id=section_id,
        is_visible=is_visible,
        expand=expand
    )

    if offers:
        return build_response(
            status_code=200, message="Offers found with success", data=offers
        )

    else:
        return Response(status_code=204)
