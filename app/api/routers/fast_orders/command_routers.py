from fastapi import APIRouter, Depends, Security

from app.api.composers import fast_order_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.fast_orders.schemas import RequestFastOrder
from app.crud.users import UserInDB
from app.crud.fast_orders import UpdateFastOrder, FastOrderInDB, FastOrderServices

router = APIRouter(tags=["Fast Orders"])


@router.post("/fast-orders", responses={201: {"model": FastOrderInDB}})
async def create_fast_orders(
    fast_order: RequestFastOrder,
    current_user: UserInDB = Security(decode_jwt, scopes=["fast_order:create"]),
    fast_order_services: FastOrderServices = Depends(fast_order_composer),
):
    fast_order_in_db = await fast_order_services.create(
        fast_order=fast_order
    )

    if fast_order_in_db:
        return build_response(
            status_code=201, message="Fast Order created with success", data=fast_order_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a fast order", data=None
        )


@router.put("/fast-orders/{fast_order_id}", responses={200: {"model": FastOrderInDB}})
async def update_fast_order(
    fast_order_id: str,
    fast_order: UpdateFastOrder,
    current_user: UserInDB = Security(decode_jwt, scopes=["fast_order:create"]),
    fast_order_services: FastOrderServices = Depends(fast_order_composer),
):
    fast_order_in_db = await fast_order_services.update(id=fast_order_id, updated_fast_order=fast_order)

    if fast_order_in_db:
        return build_response(
            status_code=200, message="Fast Order updated with success", data=fast_order_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a fast order", data=None
        )


@router.delete("/fast-orders/{fast_order_id}", responses={200: {"model": FastOrderInDB}})
async def delete_fast_order(
    fast_order_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["fast_order:delete"]),
    fast_order_services: FastOrderServices = Depends(fast_order_composer),
):
    fast_order_in_db = await fast_order_services.delete_by_id(id=fast_order_id)

    if fast_order_in_db:
        return build_response(
            status_code=200, message="Fast Order deleted with success", data=fast_order_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Fast Order {fast_order_id} not found", data=None
        )
