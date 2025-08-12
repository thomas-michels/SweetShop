from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Request, Security, Query, Response

from app.api.composers import fast_order_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.api.shared_schemas.responses import MessageResponse
from app.crud.users import UserInDB
from app.crud.fast_orders import FastOrderServices
from .schemas import (
    GetFastOrderResponse,
    GetFastOrdersResponse,
)

router = APIRouter(tags=["Fast Orders"])


@router.get(
    "/fast-orders/{fast_order_id}",
    responses={200: {"model": GetFastOrderResponse}, 404: {"model": MessageResponse}},
)
async def get_fast_order_by_id(
    fast_order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["fast_order:get"]),
    fast_order_services: FastOrderServices = Depends(fast_order_composer),
):
    fast_order_in_db = await fast_order_services.search_by_id(id=fast_order_id)

    if fast_order_in_db:
        return build_response(
            status_code=200, message="Fast Order found with success", data=fast_order_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Fast Order {fast_order_id} not found", data=None
        )


@router.get(
    "/fast-orders",
    responses={
        200: {"model": GetFastOrdersResponse},
        204: {"description": "No Content"},
    },
)
async def get_fast_orders(
    request: Request,
    day: date | None = Query(default=None),
    expand: List[str] = Query(default=[]),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=["fast_order:get"]),
    fast_order_services: FastOrderServices = Depends(fast_order_composer),
):
    paginator = Paginator(
        request=request, pagination=pagination
    )

    total = await fast_order_services.search_count(day=day)
    fast_orders = await fast_order_services.search_all(
        day=day,
        expand=expand,
        page=pagination["page"],
        page_size=pagination["page_size"],
    )

    paginator.set_total(total=total)

    if fast_orders:
        return build_list_response(
            status_code=200,
            message="Fast Orders found with success",
            pagination=paginator.pagination,
            data=fast_orders
        )

    else:
        return Response(status_code=204)
