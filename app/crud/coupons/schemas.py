from datetime import datetime
from typing import Optional

from pydantic import Field, model_validator
from app.core.models.base_model import DatabaseModel
from app.core.models.base_schema import GenericModel


class Coupon(GenericModel):
    name: str = Field(example="DESCONTO10")
    value: float = Field(example=10, gt=0)
    is_percent: bool = Field(example=False)
    expires_at: datetime = Field(example=str(datetime.now()))
    limit: int = Field(gt=0, example=10)

    def calculate_discount(self, price: float) -> float:
        if price == 0:
            return 0

        if self.is_percent:
            part_price = price / 100
            discount = part_price * self.value

        else:
            discount = self.value

        return max(discount, 0)

    @model_validator(mode="after")
    def validate_model(self) -> "Coupon":
        if self.limit <= 0:
            raise ValueError("Limit should be grater than zero")

        return self

    def validate_updated_fields(self, update_coupon: "UpdateCoupon") -> bool:
        is_updated = False

        if update_coupon.name is not None:
            self.name = update_coupon.name
            is_updated = True

        if update_coupon.value is not None:
            self.value = update_coupon.value
            is_updated = True

        if update_coupon.is_percent is not None:
            self.is_percent = update_coupon.is_percent
            is_updated = True

        if update_coupon.expires_at is not None:
            self.expires_at = update_coupon.expires_at
            is_updated = True

        if update_coupon.limit is not None:
            self.limit = update_coupon.limit
            is_updated = True

        return is_updated


class UpdateCoupon(GenericModel):
    name: Optional[str] = Field(default=None, example="DESCONTO10")
    value: Optional[float] = Field(default=None, example=10)
    is_percent: Optional[bool] = Field(default=None, example=False)
    expires_at: Optional[datetime] = Field(default=None, example=str(datetime.now()))
    limit: Optional[int] = Field(default=None, example=10)

    @model_validator(mode="after")
    def validate_model(self) -> "Coupon":
        now = datetime.now()

        if self.expires_at is not None and self.expires_at <= now:
            raise ValueError("Expires at should be grater than now")

        if self.limit is not None and self.limit <= 0:
            raise ValueError("Limit should be grater than zero")

        return self


class CouponInDB(Coupon, DatabaseModel):
    usage_count: int = Field(example=10)
