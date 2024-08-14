from typing import List

from fastapi import APIRouter, Depends, Security

from app.api.composers import product_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.products import ProductInDB, ProductServices

router = APIRouter(tags=["Products"])


@router.get("/products/{product_id}", responses={200: {"model": ProductInDB}})
async def get_product_by_id(
    product_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["product:get"]),
    product_services: ProductServices = Depends(product_composer),
):
    user_in_db = await product_services.search_by_id(id=product_id)

    return build_response(
        status_code=200, message="Product found with success", data=user_in_db
    )


@router.get("/products", responses={200: {"model": List[ProductInDB]}})
async def get_products(
    current_user: UserInDB = Security(decode_jwt, scopes=["product:get"]),
    product_services: ProductServices = Depends(product_composer),
):
    users = await product_services.search_all()

    return build_response(
        status_code=200, message="Products found with success", data=users
    )
