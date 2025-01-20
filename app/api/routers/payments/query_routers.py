from typing import List

from fastapi import APIRouter, Depends, Security, Response

from app.api.composers import payment_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.payments import PaymentServices, PaymentInDB

router = APIRouter(tags=["Payments"])


@router.get("/payments/{payment_id}", responses={200: {"model": PaymentInDB}})
async def get_payments_by_id(
    payment_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["payments:get"]),
    payments_services: PaymentServices = Depends(payment_composer),
):
    payments_in_db = await payments_services.search_by_id(id=payment_id)

    if payments_in_db:
        return build_response(
            status_code=200, message="Payment found with success", data=payments_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Payment {payment_id} not found", data=None
        )


@router.get("/orders/{order_id}/payments", tags=["Orders"], responses={200: {"model": List[PaymentInDB]}})
async def get_payments(
    order_id: str,
    current_payments: UserInDB = Security(decode_jwt, scopes=["payments:get"]),
    payments_services: PaymentServices = Depends(payment_composer),
):
    payments = await payments_services.search_all(order_id=order_id)

    if payments:
        return build_response(
            status_code=200, message="Payments found with success", data=payments
        )

    else:
        return Response(status_code=204)
