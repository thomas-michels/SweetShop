from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, Response, Security

from app.api.composers import order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.orders import OrderInDB, OrderServices
from app.crud.orders.schemas import DeliveryType, OrderStatus
from app.crud.shared_schemas.payment import PaymentStatus
from app.crud.users import UserInDB

router = APIRouter(tags=["Orders"])


@router.get("/orders/{order_id}", responses={200: {"model": OrderInDB}})
async def get_order_by_id(
    order_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["order:get"]),
    order_services: OrderServices = Depends(order_composer),
):
    order_in_db = await order_services.search_by_id(id=order_id, expand=expand)

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
    customer_id: str = Query(default=None, alias="customerId"),
    status: OrderStatus = Query(default=None),
    payment_status: List[PaymentStatus] = Query(default=[], alias="paymentStatus"),
    delivery_type: DeliveryType = Query(default=None, alias="deliveryType"),
    tags: List[str] = Query(default=[]),
    start_order_date: datetime = Query(default=None, alias="startOrderDate"),
    end_order_date: datetime = Query(default=None, alias="endOrderDate"),
    min_total_amount: float | None = Query(default=None, alias="minTotalAmount"),
    max_total_amount: float | None = Query(default=None, alias="maxTotalAmount"),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["order:get"]),
    order_services: OrderServices = Depends(order_composer),
):
    orders = await order_services.search_all(
        customer_id=customer_id,
        status=status,
        delivery_type=delivery_type,
        payment_status=payment_status,
        start_date=start_order_date,
        end_date=end_order_date,
        tags=tags,
        min_total_amount=min_total_amount,
        max_total_amount=max_total_amount,
        expand=expand,
    )

    if orders:
        return build_response(
            status_code=200, message="Orders found with success", data=orders
        )

    else:
        return Response(status_code=204)
