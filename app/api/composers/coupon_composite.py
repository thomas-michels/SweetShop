from app.crud.coupons.repositories import CouponRepository
from app.crud.coupons.services import CouponServices


async def coupon_composer(
) -> CouponServices:
    coupon_repository = CouponRepository()
    coupon_services = CouponServices(coupon_repository=coupon_repository)
    return coupon_services
