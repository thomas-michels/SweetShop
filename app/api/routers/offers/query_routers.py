from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response, Request

from app.api.composers import offer_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.crud.users import UserInDB
from app.crud.offers import OfferInDB
from app.crud.offers.services import OfferServices

router = APIRouter(tags=["Offers"])


@router.get("/offers", responses={200: {"model": List[OfferInDB]}})
async def get_offers_paginated(
    request: Request,
    query: str = Query(default=None),
    expand: List[str] = Query(default=[]),
    is_visible: bool = Query(default=None),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    offer_services: OfferServices = Depends(offer_composer),
):
    paginator = Paginator(request=request, pagination=pagination)

    total = await offer_services.search_count(query=query, is_visible=is_visible)
    offers = await offer_services.search_all_paginated(
        query=query,
        expand=expand,
        page=pagination["page"],
        page_size=pagination["page_size"],
        is_visible=is_visible,
    )

    paginator.set_total(total=total)

    if offers:
        return build_list_response(
            status_code=200,
            message="Offers found with success",
            pagination=paginator.pagination,
            data=offers,
        )

    else:
        return Response(status_code=204)


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
