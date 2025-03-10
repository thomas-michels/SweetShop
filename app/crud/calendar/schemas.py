from datetime import datetime
from typing import List
from pydantic import Field

from app.core.models.base_schema import GenericModel
from app.crud.orders.schemas import OrderStatus

class CalendarOrder(GenericModel):
    order_id: str = Field(example="ord_123")
    customer_name: str = Field(example="Ted Mosby")
    order_status: OrderStatus = Field(example=OrderStatus.PENDING.value)
    order_date: datetime = Field(example=str(datetime.now()))
    order_delivery_type: str = Field(example="DELIVERY")


class Calendar(GenericModel):
    month: int = Field(example=1, gt=0, lt=13)
    year: int = Field(example=1)
    day: int = Field(example=10, gt=0, lt=32)
    orders: List[CalendarOrder] = Field(default=[], example={
        "order_id": "ord_123",
        "customer_name": "Ted Mosby",
        "order_status": OrderStatus.PENDING.value,
        "order_date": str(datetime.now()),
    })
