from fastapi import APIRouter, Depends, Security

from app.api.composers import order_composer
from app.api.composers.pre_order_composite import pre_order_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.shared_schemas.responses import MessageResponse
from app.crud.orders import OrderServices, RequestOrder, UpdateOrder
from app.crud.orders.schemas import OrderStatus
from app.crud.pre_orders.schemas import PreOrderStatus
from app.crud.pre_orders.services import PreOrderServices
from app.crud.users import UserInDB

from .schemas import CreateOrderResponse, DeleteOrderResponse, UpdateOrderResponse

router = APIRouter(tags=["Orders"])


@router.post(
    "/orders",
    responses={
        201: {"model": CreateOrderResponse},
        400: {"model": MessageResponse},
    },
)
async def create_orders(
    order: RequestOrder,
    current_user: UserInDB = Security(decode_jwt, scopes=["order:create"]),
    order_services: OrderServices = Depends(order_composer),
):
    order_in_db = await order_services.create(order=order)

    if order_in_db:
        return build_response(
            status_code=201, message="Order created with success", data=order_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao criar pedido", data=None
        )


@router.put(
    "/orders/{order_id}",
    responses={
        200: {"model": UpdateOrderResponse},
        400: {"model": MessageResponse},
    },
)
async def update_order(
    order_id: str,
    order: UpdateOrder,
    current_user: UserInDB = Security(decode_jwt, scopes=["order:create"]),
    order_services: OrderServices = Depends(order_composer),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
):
    order_in_db = await order_services.update(id=order_id, updated_order=order)

    if order_in_db:
        if order.status is not None and order.status in [
            OrderStatus.READY_FOR_DELIVERY,
            OrderStatus.DONE,
        ]:
            pre_order_in_db = await pre_order_services.search_by_order_id(
                order_id=order_in_db.id
            )

            if pre_order_in_db:
                await pre_order_services.update_status(
                    pre_order_id=pre_order_in_db.id,
                    order_id=order_in_db.id,
                    new_status=PreOrderStatus(order_in_db.status.value),
                )

        return build_response(
            status_code=200, message="Order updated with success", data=order_in_db
        )

    else:
        return build_response(
            status_code=400, message="Erro ao atualizar pedido", data=None
        )


@router.delete(
    "/orders/{order_id}",
    responses={
        200: {"model": DeleteOrderResponse},
        404: {"model": MessageResponse},
    },
)
async def delete_order(
    order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["order:delete"]),
    order_services: OrderServices = Depends(order_composer),
):
    order_in_db = await order_services.delete_by_id(id=order_id)

    if order_in_db:
        return build_response(
            status_code=200, message="Order deleted with success", data=order_in_db
        )
    else:
        return build_response(
            status_code=404, message=f"Pedido {order_id} não encontrado", data=None
        )
