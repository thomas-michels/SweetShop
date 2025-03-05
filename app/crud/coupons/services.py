from datetime import datetime
from typing import List

from app.api.exceptions.authentication_exceptions import UnprocessableEntityException
from app.core.exceptions.users import UnprocessableEntity

from .schemas import Coupon, CouponInDB, UpdateCoupon
from .repositories import CouponRepository


class CouponServices:

    def __init__(self, coupon_repository: CouponRepository) -> None:
        self.__coupon_repository = coupon_repository

    async def create(self, coupon: Coupon) -> CouponInDB:
        now = datetime.now()

        if coupon.expires_at <= now:
            raise UnprocessableEntity("Expires at should be grater than now")

        coupon_in_db = await self.__coupon_repository.create(coupon=coupon)
        return coupon_in_db

    async def update(self, id: str, updated_coupon: UpdateCoupon) -> CouponInDB:
        coupon_in_db = await self.search_by_id(id=id)

        is_updated = coupon_in_db.validate_updated_fields(update_coupon=updated_coupon)

        if is_updated:
            if updated_coupon.limit is not None and updated_coupon.limit < coupon_in_db.usage_count:
                raise UnprocessableEntityException(detail="Limit should be grater than usage")

            coupon_in_db = await self.__coupon_repository.update(coupon=coupon_in_db)

        return coupon_in_db

    async def search_by_id(self, id: str) -> CouponInDB:
        coupon_in_db = await self.__coupon_repository.select_by_id(id=id)
        return coupon_in_db

    async def search_by_name(self, name: str) -> CouponInDB:
        coupon_in_db = await self.__coupon_repository.select_by_name(name=name)
        return coupon_in_db

    async def search_all(self, query: str) -> List[CouponInDB]:
        coupons = await self.__coupon_repository.select_all(query=query)
        return coupons

    async def delete_by_id(self, id: str) -> CouponInDB:
        coupon_in_db = await self.__coupon_repository.delete_by_id(id=id)
        return coupon_in_db
