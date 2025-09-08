from typing import List
from fastapi import APIRouter, Depends, Query, Security

from app.api.composers import pre_order_composer, order_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.shared_schemas.responses import MessageResponse
from app.crud.users import UserInDB
from app.crud.pre_orders import PreOrderServices, UpdatePreOrder
from app.crud.orders import OrderServices
from .schemas import (
    UpdatePreOrderResponse,
    DeletePreOrderResponse,
    AcceptPreOrderResponse,
)

router = APIRouter(tags=["Pre-Orders"])


@router.put(
    "/pre_orders/{pre_order_id}",
    responses={200: {"model": UpdatePreOrderResponse}, 404: {"model": MessageResponse}},
)
async def update_pre_orders(
    pre_order_id: str,
    pre_order: UpdatePreOrder,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["pre-order:create"]),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
):
    pre_order_in_db = await pre_order_services.update_status(
        pre_order_id=pre_order_id,
        new_status=pre_order.status,
        expand=expand
    )

    if pre_order_in_db:
        return build_response(
            status_code=200, message="Pré pedido atualizado com sucesso", data=pre_order_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Pré pedido {pre_order_id} não encontrado", data=None
        )


@router.post(
    "/pre_orders/{pre_order_id}/reject",
    responses={200: {"model": UpdatePreOrderResponse}, 404: {"model": MessageResponse}},
)
async def reject_pre_order(
    pre_order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["pre-order:create"]),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
):
    pre_order_in_db = await pre_order_services.reject_pre_order(
        pre_order_id=pre_order_id,
    )

    if pre_order_in_db:
        return build_response(
            status_code=200, message="Pré pedido rejeitado com sucesso", data=pre_order_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Pré pedido {pre_order_id} não encontrado", data=None
        )


@router.post(
    "/pre_orders/{pre_order_id}/accept",
    responses={201: {"model": AcceptPreOrderResponse}, 404: {"model": MessageResponse}},
)
async def accept_pre_order(
    pre_order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["pre-order:create"]),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
    order_services: OrderServices = Depends(order_composer),
):
    order_in_db = await pre_order_services.accept_pre_order(
        pre_order_id=pre_order_id,
        order_services=order_services,
    )

    if order_in_db:
        return build_response(
            status_code=201,
            message="Pré pedido aceito com sucesso",
            data=order_in_db,
        )
    else:
        return build_response(
            status_code=404, message=f"Pré pedido {pre_order_id} não encontrado", data=None
        )



@router.delete(
    "/pre_orders/{pre_order_id}",
    responses={200: {"model": DeletePreOrderResponse}, 404: {"model": MessageResponse}},
)
async def delete_pre_order(
    pre_order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["pre-order:delete"]),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
):
    pre_order_in_db = await pre_order_services.delete_by_id(id=pre_order_id)

    if pre_order_in_db:
        return build_response(
            status_code=200, message="Pré pedido deletado com sucesso", data=pre_order_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Pré pedido {pre_order_id} não encontradp", data=None
        )
