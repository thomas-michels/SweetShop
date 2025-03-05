from fastapi import APIRouter, Depends, Security

from app.api.composers import coupon_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.auth import verify_super_user
from app.crud.coupons import (
    Coupon,
    CouponInDB,
    UpdateCoupon,
    CouponServices
)
from app.crud.users.schemas import CompleteUserInDB

router = APIRouter(tags=["Coupons"])


@router.post("/coupons", responses={201: {"model": CouponInDB}})
async def create_coupon(
    coupon: Coupon,
    coupon_services: CouponServices = Depends(coupon_composer),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
):
    verify_super_user(current_user=current_user)

    coupon_in_db = await coupon_services.create(coupon=coupon)

    if coupon_in_db:
        return build_response(
            status_code=201, message="Coupon created with success", data=coupon_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create a coupon", data=None
        )


@router.put("/coupons/{coupon_id}", responses={200: {"model": CouponInDB}})
async def update_coupon(
    coupon_id: str,
    coupon: UpdateCoupon,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    coupon_services: CouponServices = Depends(coupon_composer),
):
    verify_super_user(current_user=current_user)

    coupon_in_db = await coupon_services.update(id=coupon_id, updated_coupon=coupon)

    if coupon_in_db:
        return build_response(
            status_code=200, message="Coupon updated with success", data=coupon_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update a coupon", data=None
        )


@router.delete("/coupons/{coupon_id}", responses={200: {"model": CouponInDB}})
async def delete_coupon(
    coupon_id: str,
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    coupon_services: CouponServices = Depends(coupon_composer),
):
    verify_super_user(current_user=current_user)

    coupon_in_db = await coupon_services.delete_by_id(id=coupon_id)

    if coupon_in_db:
        return build_response(
            status_code=200, message="Coupon deleted with success", data=coupon_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Coupon {coupon_id} not found", data=None
        )
