from fastapi import APIRouter, Depends, Security

from app.api.composers import pre_order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.pre_orders import PreOrderInDB, PreOrderServices, UpdatePreOrder

router = APIRouter(tags=["Pre-Orders"])


@router.put("/pre_orders/{pre_order_id}", responses={200: {"model": PreOrderInDB}})
async def update_pre_orders(
    pre_order_id: str,
    pre_order: UpdatePreOrder,
    current_user: UserInDB = Security(decode_jwt, scopes=["pre-order:create"]),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
):
    pre_order_in_db = await pre_order_services.update_status(
        pre_order_id=pre_order_id,
        new_status=pre_order.status
    )

    if pre_order_in_db:
        return build_response(
            status_code=200, message="Pré pedido atualizado com sucesso", data=pre_order_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Pré pedido {pre_order_id} não encontrado", data=None
        )



@router.delete("/pre_orders/{pre_order_id}", responses={200: {"model": PreOrderInDB}})
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
