from typing import List

from fastapi import APIRouter, Depends, Security, Query

from app.api.composers import order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.orders import OrderInDB, OrderServices

router = APIRouter(tags=["Orders"])


@router.get("/orders/{order_id}", responses={200: {"model": OrderInDB}})
async def get_order_by_id(
    order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["order:get"]),
    order_services: OrderServices = Depends(order_composer),
):
    user_in_db = await order_services.search_by_id(id=order_id)

    return build_response(
        status_code=200, message="Order found with success", data=user_in_db
    )


@router.get("/orders", responses={200: {"model": List[OrderInDB]}})
async def get_orders(
    query: str = Query(default=None),
    user_id: str = Query(default=None),
    current_user: UserInDB = Security(decode_jwt, scopes=["order:get"]),
    order_services: OrderServices = Depends(order_composer),
):
    orders = await order_services.search_all(
        query=query,
        user_id=user_id
    )

    return build_response(
        status_code=200, message="Orders found with success", data=orders
    )
