from typing import List

from fastapi import APIRouter, Depends, Security, Response

from app.api.composers import product_additional_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.product_additionals import ProductAdditionalInDB
from app.crud.product_additionals.services import ProductAdditionalServices

router = APIRouter(tags=["ProductAdditionals"])


@router.get("/products/{product_id}/additionals/{additional_id}", responses={200: {"model": ProductAdditionalInDB}})
async def get_product_additional_by_id(
    product_id: str,
    additional_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["product_additional:get"]),
    product_additional_services: ProductAdditionalServices = Depends(product_additional_composer),
):
    additional_in_db = await product_additional_services.search_by_id(id=additional_id)

    if additional_in_db:
        return build_response(status_code=200, message="ProductAdditional found with success", data=additional_in_db)

    else:
        return build_response(status_code=404, message=f"ProductAdditional {additional_id} not found", data=None)


@router.get("/products/{product_id}/additionals", responses={200: {"model": List[ProductAdditionalInDB]}})
async def get_product_additionals(
    product_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["product_additional:get"]),
    product_additional_services: ProductAdditionalServices = Depends(product_additional_composer),
):
    additionals = await product_additional_services.search_by_product_id(product_id=product_id)

    if additionals:
        return build_response(status_code=200, message="ProductAdditionals found with success", data=additionals)
    else:
        return Response(status_code=204)
