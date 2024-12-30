from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

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
    product_in_db = await product_services.search_by_id(id=product_id)

    if product_in_db:
        return build_response(
            status_code=200, message="Product found with success", data=product_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Product {product_id} not found", data=None
        )


@router.get("/products", responses={200: {"model": List[ProductInDB]}})
async def get_products(
    query: str = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["product:get"]),
    product_services: ProductServices = Depends(product_composer),
):
    products = await product_services.search_all(query=query, expand=expand)

    if products:
        return build_response(
            status_code=200, message="Products found with success", data=products
        )

    else:
        return Response(status_code=204)
