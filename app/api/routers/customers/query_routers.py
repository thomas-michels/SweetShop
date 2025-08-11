from typing import List

from fastapi import APIRouter, Depends, Query, Request, Response, Security

from app.api.composers import customer_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.api.shared_schemas.responses import MessageResponse
from .schemas import (
    GetCustomerResponse,
    GetCustomersResponse,
    GetCustomersCountResponse,
)
from app.crud.users import UserInDB
from app.crud.customers import CustomerServices

router = APIRouter(tags=["Customers"])


@router.get(
    "/customers/{customer_id}",
    responses={
        200: {"model": GetCustomerResponse},
        404: {"model": MessageResponse},
    },
)
async def get_customer_by_id(
    customer_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["customer:get"]),
    customer_services: CustomerServices = Depends(customer_composer),
):
    customer_in_db = await customer_services.search_by_id(
        id=customer_id,
        expand=expand
    )

    if customer_in_db:
        return build_response(
            status_code=200, message="Cliente encontrado", data=customer_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Cliente #{customer_id} não encontrado", data=None
        )


@router.get(
    "/customers",
    responses={
        200: {"model": GetCustomersResponse},
        204: {"description": "No Content"},
    },
)
async def get_customers(
    request: Request,
    query: str = Query(default=None),
    tags: List[str] = Query(default=[]),
    expand: List[str] = Query(default=[]),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=["customer:get"]),
    customer_services: CustomerServices = Depends(customer_composer),
):
    paginator = Paginator(
        request=request, pagination=pagination
    )

    total = await customer_services.search_count(
        query=query,
        tags=tags,
    )

    customers = await customer_services.search_all(
        query=query,
        tags=tags,
        page=pagination["page"],
        page_size=pagination["page_size"],
        expand=expand
    )

    paginator.set_total(total=total)

    if customers:
        return build_list_response(
            status_code=200,
            message="Clientes encontrados com sucesso",
            pagination=paginator.pagination,
            data=customers
        )

    else:
        return Response(status_code=204)


@router.get(
    "/customers/metrics/count",
    responses={
        200: {"model": GetCustomersCountResponse},
        204: {"description": "No Content"},
    },
)
async def get_customers_count(
    current_user: UserInDB = Security(decode_jwt, scopes=["customer:get"]),
    customer_services: CustomerServices = Depends(customer_composer),
):
    quantity = await customer_services.search_count()

    if quantity:
        return build_response(
            status_code=200, message="Contagem de clientes feita com sucesso", data=quantity
        )

    else:
        return Response(status_code=204)
