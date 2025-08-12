from typing import List

from fastapi import APIRouter, Depends, Query, Request, Security, Response

from app.api.composers import product_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.api.shared_schemas.responses import MessageResponse
from .schemas import (
    GetProductResponse,
    GetProductsResponse,
    GetProductsCountResponse,
)
from app.crud.users import UserInDB
from app.crud.products import ProductServices

router = APIRouter(tags=["Products"])


@router.get(
    "/products/{product_id}",
    responses={
        200: {"model": GetProductResponse},
        404: {"model": MessageResponse},
    },
)
async def get_product_by_id(
    product_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["product:get"]),
    product_services: ProductServices = Depends(product_composer),
):
    product_in_db = await product_services.search_by_id(
        id=product_id,
        expand=expand
    )

    if product_in_db:
        return build_response(
            status_code=200, message="Product found with success", data=product_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Produto {product_id} não encontrado", data=None
        )


@router.get(
    "/products",
    responses={
        200: {"model": GetProductsResponse},
        204: {"description": "No Content"},
    },
)
async def get_products(
    request: Request,
    query: str = Query(default=None),
    tags: List[str] = Query(default=[]),
    expand: List[str] = Query(default=[]),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=["product:get"]),
    product_services: ProductServices = Depends(product_composer),
):
    paginator = Paginator(
        request=request, pagination=pagination
    )

    total = await product_services.search_count(
        query=query,
        tags=tags
    )
    products = await product_services.search_all(
        query=query,
        tags=tags,
        expand=expand,
        page=pagination["page"],
        page_size=pagination["page_size"]
    )

    paginator.set_total(total=total)

    if products:
        return build_list_response(
            status_code=200,
            message="Products found with success",
            pagination=paginator.pagination,
            data=products
        )

    else:
        return Response(status_code=204)


@router.get(
    "/products/metrics/count",
    responses={
        200: {"model": GetProductsCountResponse},
        204: {"description": "No Content"},
    },
)
async def get_products_count(
    current_user: UserInDB = Security(decode_jwt, scopes=["product:get"]),
    product_services: ProductServices = Depends(product_composer),
):
    quantity = await product_services.search_count()

    if quantity:
        return build_response(
            status_code=200, message="Products count found with success", data=quantity
        )

    else:
        return Response(status_code=204)
