from typing import List
from mongoengine.errors import NotUniqueError
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import CouponModel
from .schemas import Coupon, CouponInDB

_logger = get_logger(__name__)


class CouponRepository(Repository):
    async def create(self, coupon: Coupon) -> CouponInDB:
        try:
            coupon_model = CouponModel(
                usage_count=0,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                **coupon.model_dump(),
            )
            coupon_model.name = coupon_model.name.upper()

            coupon_model.save()

            return await self.select_by_id(id=coupon_model.id)

        except NotUniqueError:
            _logger.warning(f"Coupon with name {coupon.name} is not unique")
            return await self.select_by_name(name=coupon.name)

        except Exception as error:
            _logger.error(f"Error on create_coupon: {str(error)}")
            raise UnprocessableEntity(message="Error on create new Coupon")

    async def update(self, coupon: CouponInDB) -> CouponInDB:
        try:
            coupon_model: CouponModel = CouponModel.objects(
                id=coupon.id,
                is_active=True,
            ).first()
            coupon.name = coupon.name.upper()

            coupon_model.update(**coupon.model_dump())

            return await self.select_by_id(id=coupon.id)

        except Exception as error:
            _logger.error(f"Error on update_coupon: {str(error)}")
            raise UnprocessableEntity(message="Error on update Coupon")

    async def update_usage(self, coupon_id: str, quantity: int) -> CouponInDB:
        try:
            coupon_model: CouponModel = CouponModel.objects(
                id=coupon_id,
                is_active=True,
            ).first()

            now = UTCDateTime.now()

            if coupon_model.expires_at <= now:
                raise UnprocessableEntity(message="Coupon already expired")

            if (coupon_model.usage_count + quantity) <= coupon_model.limit:
                coupon_model.usage_count += quantity

                coupon_model.save()

                return await self.select_by_id(id=coupon_id)

            else:
                raise UnprocessableEntity(message="Coupon usage limit exceeded")

        except UnprocessableEntity as error:
            raise error

        except Exception as error:
            _logger.error(f"Error on update_usage: {str(error)}")
            raise NotFoundError(message=f"Coupon #{coupon_id} not found")

    async def select_by_id(self, id: str, raise_404: bool = True) -> CouponInDB:
        try:
            coupon_model: CouponModel = CouponModel.objects(
                id=id,
                is_active=True,
            ).first()

            return CouponInDB.model_validate(coupon_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Coupon #{id} not found")

    async def select_by_name(self, name: str) -> CouponInDB:
        try:
            name = name.upper()
            coupon_model: CouponModel = CouponModel.objects(
                name=name,
                is_active=True,
            ).first()

            return CouponInDB.model_validate(coupon_model)

        except Exception as error:
            _logger.error(f"Error on select_by_name: {str(error)}")
            raise NotFoundError(message=f"Coupon with name {name} not found")

    async def select_all(self, query: str) -> List[CouponInDB]:
        try:
            coupons = []

            objects = CouponModel.objects(is_active=True)

            if query:
                objects = objects.filter(name=query.upper())

            for coupon_model in objects.order_by("name"):
                coupons.append(CouponInDB.model_validate(coupon_model))

            return coupons

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Coupons not found")

    async def delete_by_id(self, id: str) -> CouponInDB:
        try:
            coupon_model: CouponModel = CouponModel.objects(
                id=id,
                is_active=True,
            ).first()
            coupon_model.delete()

            return CouponInDB.model_validate(coupon_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Coupon #{id} not found")
