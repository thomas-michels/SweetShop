from typing import List

from fastapi import APIRouter, Depends, Query, Request, Response, Security

from app.api.composers import order_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.core.utils.utc_datetime import UTCDateTimeType, UTCDateTime
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
            status_code=404, message=f"Pedido {order_id} não encontrado", data=None
        )


@router.get("/orders", responses={200: {"model": List[OrderInDB]}})
async def get_orders(
    request: Request,
    customer_id: str = Query(default=None, alias="customerId"),
    status: OrderStatus = Query(default=None),
    payment_status: List[PaymentStatus] = Query(default=[], alias="paymentStatus"),
    delivery_type: DeliveryType = Query(default=None, alias="deliveryType"),
    tags: List[str] = Query(default=[]),
    start_order_date: UTCDateTimeType = Query(default=None, alias="startOrderDate"),
    end_order_date: UTCDateTimeType = Query(default=None, alias="endOrderDate"),
    min_total_amount: float | None = Query(default=None, alias="minTotalAmount"),
    max_total_amount: float | None = Query(default=None, alias="maxTotalAmount"),
    expand: List[str] = Query(default=[]),
    order_by: str | None = Query(default=None),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=["order:get"]),
    order_services: OrderServices = Depends(order_composer),
):
    if not start_order_date and not end_order_date and not status:
        today = UTCDateTime.today()

        start_order_date = UTCDateTime(
            year=today.year,
            month=today.month,
            day=1,
            hour=0,
            minute=0,
            second=0
        )

    paginator = Paginator(
        request=request, pagination=pagination
    )

    total = await order_services.search_count(
        customer_id=customer_id,
        status=status,
        delivery_type=delivery_type,
        payment_status=payment_status,
        start_date=start_order_date,
        end_date=end_order_date,
        tags=tags,
        min_total_amount=min_total_amount,
        max_total_amount=max_total_amount,
    )

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
        order_by=order_by,
        page=pagination["page"],
        page_size=pagination["page_size"]
    )

    paginator.set_total(total=total)

    if orders:
        return build_list_response(
            status_code=200,
            message="Orders found with success",
            pagination=paginator.pagination,
            data=orders
        )

    else:
        return Response(status_code=204)
