from typing import List

from fastapi import APIRouter, Depends, Query, Request, Security, Response

from app.api.composers import pre_order_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.api.dependencies.response import build_list_response
from app.crud.users import UserInDB
from app.crud.pre_orders import PreOrderInDB, PreOrderServices, PreOrderStatus

router = APIRouter(tags=["Pre-Orders"])


@router.get("/pre_orders", responses={200: {"model": List[PreOrderInDB]}})
async def get_pre_orders(
    request: Request,
    status: PreOrderStatus = Query(default=None),
    expand: List[str] = Query(default=[]),
    pagination: dict = Depends(pagination_parameters),
    current_user: UserInDB = Security(decode_jwt, scopes=["pre-order:get"]),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
):
    paginator = Paginator(
        request=request, pagination=pagination
    )

    total = await pre_order_services.search_count(status=status)

    pre_orders = await pre_order_services.search_all(
        status=status,
        expand=expand,
        page=pagination["page"],
        page_size=pagination["page_size"]
    )

    paginator.set_total(total=total)

    if pre_orders:
        return build_list_response(
            status_code=200,
            message="Pré pedidos encontrados com sucesso",
            pagination=paginator.pagination,
            data=pre_orders
        )

    else:
        return Response(status_code=204)


@router.get("/pre_orders/{pre_order_id}", responses={200: {"model": PreOrderInDB}})
async def get_pre_order_by_id(
    pre_order_id: str,
    expand: List[str] = Query(default=[]),
    current_user: UserInDB = Security(decode_jwt, scopes=["pre-order:get"]),
    pre_order_services: PreOrderServices = Depends(pre_order_composer),
):
    pre_order_in_db = await pre_order_services.search_by_id(id=pre_order_id, expand=expand)

    if pre_order_in_db:
        return build_response(
            status_code=200, message="Pré pedido encontrado com sucesso", data=pre_order_in_db
        )

    else:
        return build_response(
            status_code=404, message="Pré pedido encontrado não encontrado"
        )
