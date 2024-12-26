from datetime import datetime
from enum import Enum
from typing import List, Optional, Type

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.customers.schemas import CustomerInDB
from app.crud.products.schemas import ProductInDB
from app.crud.shared_schemas.address import Address
from app.crud.shared_schemas.payment import Payment, PaymentStatus
from app.crud.tags.schemas import TagInDB


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PREPARATION = "IN_PREPARATION"
    DONE = "DONE"
    CANCELED = "CANCELED"


class DeliveryType(str, Enum):
    WITHDRAWAL = "WITHDRAWAL"
    DELIVERY = "DELIVERY"


class Delivery(GenericModel):
    type: DeliveryType = Field(
        default=DeliveryType.WITHDRAWAL, example=DeliveryType.WITHDRAWAL
    )
    delivery_at: datetime | None = Field(default=None, example=str(datetime.now()))
    address: Address | None = Field(default=None)
    delivery_value: float | None = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "Delivery":
        if self.type == DeliveryType.DELIVERY:
            if not self.delivery_at:
                raise ValueError("`delivery_at` must be set for DELIVERY type")
            if not self.address:
                raise ValueError("`address` must be set for DELIVERY type")
            if not self.delivery_value:
                raise ValueError("`delivery_value` must be set for DELIVERY type")

        else:  # WITHDRAWAL
            if self.delivery_at or self.address or self.delivery_value:
                raise ValueError(
                    "`delivery_at`, `address`, and `delivery_value` must be None when type is WITHDRAWAL"
                )

        return self


class RequestedProduct(GenericModel):
    product_id: str = Field()
    quantity: int = Field(gt=0, example=1)


class CompleteProduct(GenericModel):
    product: ProductInDB = Field()
    quantity: int = Field(gt=0, example=1)


class Order(GenericModel):
    customer_id: str | None = Field(default=None, example="66bae5c2e59a0787e2c903e3")
    status: OrderStatus = Field(
        default=OrderStatus.PENDING, example=OrderStatus.IN_PREPARATION
    )
    products: List[RequestedProduct] = Field(default=[], min_length=1)
    tags: List[str] = Field(default=[])
    delivery: Delivery = Field()
    preparation_date: datetime = Field(example=str(datetime.now()))
    description: str | None = Field(default=None, example="Description")
    additional: float = Field(default=0, ge=0, example=12.2)
    discount: float | None = Field(default=0, ge=0, example=12.2)
    reason_id: str | None = Field(default=None, example="123")
    payment_details: List[Payment] = Field(default=[])

    @model_validator(mode="after")
    def validate_model(self) -> "Order":
        product_ids = [str(product.product_id) for product in self.products]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Products must contain unique items.")

        if len(self.tags) != len(set(self.tags)):
            raise ValueError("Tags must contain unique items.")

        return self

    def validate_updated_fields(self, update_order: Type["UpdateOrder"]) -> bool:
        is_updated = False

        if update_order.customer_id is not None:
            self.customer_id = update_order.customer_id
            is_updated = True

        if update_order.status is not None:
            self.status = update_order.status
            is_updated = True

        if update_order.products is not None:
            self.products = update_order.products
            is_updated = True

        if update_order.tags is not None:
            self.tags = update_order.tags
            is_updated = True

        if update_order.delivery is not None:
            self.delivery = update_order.delivery
            is_updated = True

        if update_order.preparation_date is not None:
            self.preparation_date = update_order.preparation_date
            is_updated = True

        if update_order.reason_id is not None:
            self.reason_id = update_order.reason_id
            is_updated = True

        if update_order.description is not None:
            self.description = update_order.description
            is_updated = True

        if update_order.additional is not None:
            self.additional = update_order.additional
            is_updated = True

        if update_order.discount is not None:
            self.discount = update_order.discount
            is_updated = True

        if update_order.payment_details is not None:
            self.payment_details = update_order.payment_details
            is_updated = True

        return is_updated


class UpdateOrder(GenericModel):
    customer_id: Optional[str] = Field(default=None, example="66bae5c2e59a0787e2c903e3")
    status: Optional[OrderStatus] = Field(
        default=None, example=OrderStatus.IN_PREPARATION
    )
    payment_details: Optional[List[Payment]] = Field(default=None)
    products: Optional[List[RequestedProduct]] = Field(default=None, min_length=1)
    delivery: Optional[Delivery] = Field(default=None)
    preparation_date: Optional[datetime] = Field(
        default=None, example=str(datetime.now())
    )
    description: Optional[str] = Field(default=None, example="Description")
    additional: Optional[float] = Field(default=None, example=12.2)
    discount: Optional[float] = Field(default=None, example=12.2)
    reason_id: Optional[str] = Field(default=None, example="123")
    tags: Optional[List[str]] = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdateOrder":
        if self.additional is not None:
            if self.additional < 0:
                raise ValueError("Additional must be grater than zero")

        if self.discount is not None:
            if self.discount < 0:
                raise ValueError("Discount must be grater than zero")

        if self.products is not None:
            product_ids = [str(product.product_id) for product in self.products]
            if len(product_ids) != len(set(product_ids)):
                raise ValueError("Products must contain unique items.")

        return self

class OrderInDB(Order, DatabaseModel):
    organization_id: str = Field(example="66bae5c2e59a0787e2c903e3")
    total_amount: float = Field(example=12.2)
    is_active: bool = Field(example=True, exclude=True)
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, example=PaymentStatus.PENDING
    )


class CompleteOrder(OrderInDB):
    customer: CustomerInDB | str | None = Field(default=None)
    products: List[CompleteProduct] | List[RequestedProduct] = Field(
        default=[], min_length=1
    )
    tags: List[TagInDB] | List[str] = Field(default=[])
