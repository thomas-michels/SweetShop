from fastapi import APIRouter, Depends, Security

from app.api.composers import order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.orders import Order, OrderInDB, UpdateOrder, OrderServices

router = APIRouter(tags=["Orders"])


@router.post("/orders", responses={201: {"model": OrderInDB}})
async def create_orders(
    order: Order,
    current_user: UserInDB = Security(decode_jwt, scopes=["order:create"]),
    order_services: OrderServices = Depends(order_composer),
):
    order_in_db = await order_services.create(
        order=order
    )

    return build_response(
        status_code=201, message="Order created with success", data=order_in_db
    )


@router.put("/order/{order_id}", responses={200: {"model": OrderInDB}})
async def update_order(
    order_id: str,
    order: UpdateOrder,
    current_user: UserInDB = Security(decode_jwt, scopes=["order:update"]),
    order_services: OrderServices = Depends(order_composer),
):
    order_in_db = await order_services.update(id=order_id, updated_order=order)

    return build_response(
        status_code=200, message="Order updated with success", data=order_in_db
    )


@router.delete("/order/{order_id}", responses={200: {"model": OrderInDB}})
async def delete_order(
    order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["order:delete"]),
    order_services: OrderServices = Depends(order_composer),
):
    order_in_db = await order_services.delete_by_id(id=order_id)

    return build_response(
        status_code=200, message="Order deleted with success", data=order_in_db
    )
