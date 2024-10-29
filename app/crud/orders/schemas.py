from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional, Type

from pydantic import BaseModel, Field, ValidationError

from app.core.models import DatabaseModel
from app.crud.products.schemas import ProductInDB


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PREPARATION = "IN_PREPARATION"
    DONE = "DONE"


class DeliveryType(str, Enum):
    WITHDRWAWAL = "WITHDRWAWAL"
    DELIVERY = "DELIVERY"


class Address(BaseModel):
    street: str = Field(example="Rua de Testes")
    number: str = Field(example="123")
    neighborhood: str = Field(example="Bairro")
    city: str = Field(example="Blumenau")


class Delivery(BaseModel):
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


class Item(BaseModel):
    product_id: str = Field()
    quantity: int = Field(gt=0, example=1)


class CompleteItem(BaseModel):
    product: ProductInDB = Field()
    quantity: int = Field(gt=0, example=1)


class Order(BaseModel):
    user_id: str = Field(example="66bae5c2e59a0787e2c903e3")
    status: OrderStatus = Field(default=OrderStatus.PENDING, example=OrderStatus.IN_PREPARATION)
    items: List[Item] = Field(default=[], min_length=1)
    delivery: Delivery = Field()
    preparation_date: date = Field(example=str(date.today()))

    def validate_updated_fields(self, update_order: Type["UpdateOrder"]) -> bool:
        is_updated = False

        if update_order.user_id:
            self.user_id = update_order.user_id
            is_updated = True

        if update_order.status:
            self.status = update_order.status
            is_updated = True

        if update_order.items:
            self.items = update_order.items
            is_updated = True

        if update_order.delivery:
            self.delivery = update_order.delivery
            is_updated = True

        if update_order.preparation_date:
            self.preparation_date = update_order.preparation_date
            is_updated = True

        return is_updated


class UpdateOrder(BaseModel):
    user_id: Optional[str] = Field(default=None, example="66bae5c2e59a0787e2c903e3")
    status: Optional[OrderStatus] = Field(default=None, example=OrderStatus.IN_PREPARATION)
    items: Optional[List[Item]] = Field(default=None, min_length=1)
    delivery: Optional[Delivery] = Field(default=None)
    preparation_date: Optional[date] = Field(default=None, example=str(date.today()))


class OrderInDB(Order, DatabaseModel):
    value: float = Field(example=12.2)
    is_active: bool = Field(example=True, exclude=True)


class CompleteOrder(OrderInDB):
    items: List[CompleteItem] = Field(default=[], min_length=1)
