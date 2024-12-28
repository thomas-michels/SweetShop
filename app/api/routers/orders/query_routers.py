from typing import List

from fastapi import APIRouter, Depends, Security, Query, Response

from app.api.composers import order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.orders.schemas import DeliveryType, OrderStatus
from app.crud.shared_schemas.payment import PaymentStatus
from app.crud.users import UserInDB
from app.crud.orders import OrderInDB, OrderServices

router = APIRouter(tags=["Orders"])


@router.get("/orders/{order_id}", responses={200: {"model": OrderInDB}})
async def get_order_by_id(
    order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["order:get"]),
    order_services: OrderServices = Depends(order_composer),
):
    order_in_db = await order_services.search_by_id(id=order_id)

    if order_in_db:
        return build_response(
            status_code=200, message="Order found with success", data=order_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Order {order_id} not found", data=None
        )


@router.get("/orders", responses={200: {"model": List[OrderInDB]}})
async def get_orders(
    status: OrderStatus = Query(default=None),
    customer_id: str = Query(default=None),
    month: int = Query(default=None),
    payment_status: PaymentStatus = Query(default=None),
    delivery_type: DeliveryType = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["order:get"]),
    order_services: OrderServices = Depends(order_composer),
):
    orders = await order_services.search_all(
        status=status,
        customer_id=customer_id,
        month=month,
        delivery_type=delivery_type,
        payment_status=payment_status,
        expand=expand
    )

    if orders:
        return build_response(
            status_code=200, message="Orders found with success", data=orders
        )

    else:
        return Response(status_code=204)
