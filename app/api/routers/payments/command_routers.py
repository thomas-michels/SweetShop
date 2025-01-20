from fastapi import APIRouter, Depends, Security

from app.api.composers import payment_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.payments import (
    Payment,
    PaymentInDB,
    UpdatePayment,
    PaymentServices
)
from app.crud.users import UserInDB

router = APIRouter(tags=["Payments"])


@router.post("/payments", responses={201: {"model": PaymentInDB}})
async def create_payment(
    payment: Payment,
    payment_services: PaymentServices = Depends(payment_composer),
    current_user: UserInDB = Security(decode_jwt, scopes=["payment:create"]),
):
    payment_in_db = await payment_services.create(payment=payment)

    if payment_in_db:
        return build_response(
            status_code=201, message="Payment created with success", data=payment_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a payment", data=None
        )


@router.put("/payments/{payment_id}", responses={200: {"model": PaymentInDB}})
async def update_payment(
    payment_id: str,
    payment: UpdatePayment,
    current_user: UserInDB = Security(decode_jwt, scopes=["payment:create"]),
    payment_services: PaymentServices = Depends(payment_composer),
):
    payment_in_db = await payment_services.update(id=payment_id, updated_payment=payment)

    if payment_in_db:
        return build_response(
            status_code=200, message="Payment updated with success", data=payment_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a payment", data=None
        )


@router.delete("/payments/{payment_id}", responses={200: {"model": PaymentInDB}})
async def delete_payment(
    payment_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["payment:delete"]),
    payment_services: PaymentServices = Depends(payment_composer),
):
    payment_in_db = await payment_services.delete_by_id(id=payment_id)

    if payment_in_db:
        return build_response(
            status_code=200, message="Payment deleted with success", data=payment_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Payment {payment_id} not found", data=None
        )
