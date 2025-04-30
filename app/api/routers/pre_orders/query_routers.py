from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import pre_order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.pre_orders import PreOrderInDB, PreOrderServices, PreOrderStatus

router = APIRouter(tags=["Pre-Orders"])


@router.get("/pre_orders", responses={200: {"model": List[PreOrderInDB]}})
async def get_pre_orders(
    status: PreOrderStatus = Query(default=None),
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["pre-order:get"]),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
):
    pre_orders = await pre_order_services.search_all(status=status, expand=expand)

    if pre_orders:
        return build_response(
            status_code=200, message="Pré pedidos encontrados com sucesso", data=pre_orders
        )

    else:
        return Response(status_code=204)
