from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Security, Query, Response

from app.api.composers import fast_order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.fast_orders import CompleteFastOrder, FastOrderServices

router = APIRouter(tags=["Fast Orders"])


@router.get("/fast-orders/{fast_order_id}", responses={200: {"model": CompleteFastOrder}})
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


@router.get("/fast-orders", responses={200: {"model": List[CompleteFastOrder]}})
async def get_fast_orders(
    day: date | None = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["fast_order:get"]),
    fast_order_services: FastOrderServices = Depends(fast_order_composer),
):
    fast_orders = await fast_order_services.search_all(
        day=day,
        expand=expand
    )

    if fast_orders:
        return build_response(
            status_code=200, message="Fast Orders found with success", data=fast_orders
        )

    else:
        return Response(status_code=204)
