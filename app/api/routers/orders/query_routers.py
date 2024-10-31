from typing import List

from fastapi import APIRouter, Depends, Security, Query, Response

from app.api.composers import order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.orders.schemas import OrderStatus
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

    if user_in_db:
        return build_response(
            status_code=200, message="Order found with success", data=user_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Order {order_id} not found", data=None
        )


@router.get("/orders", responses={200: {"model": List[OrderInDB]}})
async def get_orders(
    status: OrderStatus = Query(default=None),
    customer_id: str = Query(default=None),
    current_user: UserInDB = Security(decode_jwt, scopes=["order:get"]),
    order_services: OrderServices = Depends(order_composer),
):
    orders = await order_services.search_all(
        status=status,
        customer_id=customer_id
    )

    if orders:
        return build_response(
            status_code=200, message="Orders found with success", data=orders
        )

    else:
        return Response(status_code=204)
