from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional, Type

from pydantic import Field, ValidationError

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.customers.schemas import CustomerInDB
from app.crud.products.schemas import ProductInDB
from app.crud.tags.schemas import TagInDB


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PREPARATION = "IN_PREPARATION"
    DONE = "DONE"

class PaymentStatus(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"


class DeliveryType(str, Enum):
    WITHDRWAWAL = "WITHDRWAWAL"
    DELIVERY = "DELIVERY"


class Address(GenericModel):
    street: str = Field(example="Rua de Testes")
    number: str = Field(example="123")
    neighborhood: str = Field(example="Bairro")
    city: str = Field(example="Blumenau")


class Delivery(GenericModel):
    type: DeliveryType = Field(default=DeliveryType.WITHDRWAWAL, example=DeliveryType.WITHDRWAWAL)
    delivery_at: datetime | None = Field(default=None, example=str(datetime.now()))
    address: Address | None = Field(default=None)

    def model_post_init(self, __context: Any) -> None:
        if self.type == DeliveryType.DELIVERY:
            if not self.delivery_at:
                raise ValidationError("Delivery_at must be set")

            if not self.address:
                raise ValidationError("Address must be set")

        return super().model_post_init(__context)


class RequestedProduct(GenericModel):
    product_id: str = Field()
    quantity: int = Field(gt=0, example=1)


class CompleteProduct(GenericModel):
    product: ProductInDB = Field()
    quantity: int = Field(gt=0, example=1)


class Order(GenericModel):
    customer_id: str | None = Field(default=None, example="66bae5c2e59a0787e2c903e3")
    status: OrderStatus = Field(default=OrderStatus.PENDING, example=OrderStatus.IN_PREPARATION)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, example=PaymentStatus.PENDING)
    products: List[RequestedProduct] = Field(default=[], min_length=1)
    tags: List[str] = Field(default=[])
    delivery: Delivery = Field()
    preparation_date: date = Field(example=str(date.today()))
    reason_id: str | None = Field(default=None, example="123")

    def validate_updated_fields(self, update_order: Type["UpdateOrder"]) -> bool:
        is_updated = False

        if update_order.customer_id:
            self.customer_id = update_order.customer_id
            is_updated = True

        if update_order.status:
            self.status = update_order.status
            is_updated = True

        if update_order.payment_status:
            self.payment_status = update_order.payment_status
            is_updated = True

        if update_order.products:
            self.products = update_order.products
            is_updated = True

        if update_order.delivery:
            self.delivery = update_order.delivery
            is_updated = True

        if update_order.preparation_date:
            self.preparation_date = update_order.preparation_date
            is_updated = True

        if update_order.reason_id:
            self.reason_id = update_order.reason_id
            is_updated = True

        return is_updated


class UpdateOrder(GenericModel):
    customer_id: Optional[str] = Field(default=None, example="66bae5c2e59a0787e2c903e3")
    status: Optional[OrderStatus] = Field(default=None, example=OrderStatus.IN_PREPARATION)
    payment_status: Optional[PaymentStatus] = Field(default=None, example=PaymentStatus.PENDING)
    products: Optional[List[RequestedProduct]] = Field(default=None, min_length=1)
    delivery: Optional[Delivery] = Field(default=None)
    preparation_date: Optional[date] = Field(default=None, example=str(date.today()))
    reason_id: Optional[str] = Field(default=None, example="123")


class OrderInDB(Order, DatabaseModel):
    value: float = Field(example=12.2)
    is_active: bool = Field(example=True, exclude=True)


class CompleteOrder(OrderInDB):
    customer: CustomerInDB | None = Field(default=None)
    products: List[CompleteProduct] = Field(default=[], min_length=1)
    tags: List[TagInDB] = Field(default=[])
