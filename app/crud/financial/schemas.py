from datetime import datetime

from pydantic import Field

from app.core.models.base_schema import GenericModel
from app.crud.orders.schemas import PaymentStatus


class Financial(GenericModel):
    order_id: str = Field(example="order_123")
    order_date: datetime = Field(example=str(datetime.now()))
    payment_status: PaymentStatus = Field(example=PaymentStatus.PENDING)
    total_amount: float = Field(example=12.2)
