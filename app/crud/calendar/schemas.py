from datetime import datetime
from typing import List
from pydantic import Field

from app.core.models.base_schema import GenericModel
from app.crud.orders.schemas import OrderStatus
from app.crud.shared_schemas.address import Address


class CalendarOrder(GenericModel):
    order_id: str = Field(example="ord_123")
    customer_name: str = Field(example="Ted Mosby")
    order_status: OrderStatus = Field(example=OrderStatus.PENDING.value)
    order_date: datetime = Field(example=str(datetime.now()))
    order_delivery_type: str = Field(example="DELIVERY")
    order_delivery_at: datetime | None = Field(default=None)
    address: Address | None = Field(default=None)
