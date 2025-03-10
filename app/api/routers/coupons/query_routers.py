from typing import List

from fastapi import APIRouter, Depends, Query, Security, Response

from app.api.composers import coupon_composer
from app.api.dependencies import build_response, decode_jwt
from app.api.dependencies.auth import verify_super_user
from app.crud.users import UserInDB
from app.crud.coupons import CouponServices, CouponInDB
from app.crud.users.schemas import CompleteUserInDB

router = APIRouter(tags=["Coupons"])


@router.get("/coupons", responses={200: {"model": List[CouponInDB]}})
async def get_coupons(
    query: str = Query(default=None),
    current_user: CompleteUserInDB = Security(decode_jwt, scopes=[]),
    coupons_services: CouponServices = Depends(coupon_composer),
):
    verify_super_user(current_user=current_user)

    coupons = await coupons_services.search_all(query=query)

    if coupons:
        return build_response(
            status_code=200, message="Coupons found with success", data=coupons
        )

    else:
        return Response(status_code=204)


@router.get("/coupons/{coupon_id}", responses={200: {"model": CouponInDB}})
async def get_coupons_by_id(
    coupon_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=[]),
    coupons_services: CouponServices = Depends(coupon_composer),
):
    coupons_in_db = await coupons_services.search_by_id(id=coupon_id)

    if coupons_in_db:
        return build_response(
            status_code=200, message="Coupon found with success", data=coupons_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Coupon {coupon_id} not found", data=None
        )
