from pydantic import Field

from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType
from app.crud.orders.schemas import OrderStatus
from app.crud.shared_schemas.address import Address


class CalendarOrder(GenericModel):
    order_id: str = Field(example="ord_123")
    customer_name: str = Field(example="Ted Mosby")
    order_status: OrderStatus = Field(example=OrderStatus.PENDING.value)
    order_date: UTCDateTimeType = Field(example=str(UTCDateTime.now()))
    order_delivery_type: str = Field(example="DELIVERY")
    order_delivery_at: UTCDateTimeType | None = Field(default=None)
    address: Address | None = Field(default=None)
