from fastapi import APIRouter, Depends, Security

from app.api.composers import offer_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.offers import RequestOffer, OfferInDB, UpdateOffer
from app.crud.offers.services import OfferServices

router = APIRouter(tags=["Offers"])


@router.post("/offers", responses={201: {"model": OfferInDB}})
async def create_offers(
    offer: RequestOffer,
    current_user: UserInDB = Security(decode_jwt, scopes=["offer:create"]),
    offer_services: OfferServices = Depends(offer_composer),
):
    offer_in_db = await offer_services.create(
        request_offer=offer
    )

    if offer_in_db:
        return build_response(
            status_code=201, message="Offer created with success", data=offer_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao criar oferta", data=None
        )


@router.put("/offers/{offer_id}", responses={200: {"model": OfferInDB}})
async def update_offer(
    offer_id: str,
    offer: UpdateOffer,
    current_user: UserInDB = Security(decode_jwt, scopes=["offer:create"]),
    offer_services: OfferServices = Depends(offer_composer),
):
    offer_in_db = await offer_services.update(id=offer_id, updated_offer=offer)

    if offer_in_db:
        return build_response(
            status_code=200, message="Offer updated with success", data=offer_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao atualizar oferta", data=None
        )


@router.delete("/offers/{offer_id}", responses={200: {"model": OfferInDB}})
async def delete_offer(
    offer_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["offer:delete"]),
    offer_services: OfferServices = Depends(offer_composer),
):
    offer_in_db = await offer_services.delete_by_id(id=offer_id)

    if offer_in_db:
        return build_response(
            status_code=200, message="Offer deleted with success", data=offer_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Oferta {offer_id} não encontrada", data=None
        )
