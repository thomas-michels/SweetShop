from typing import List
from pydantic import Field

from app.core.models.base_schema import GenericModel


class RecentOrder(GenericModel):
    order_id: str = Field(example="ord_123")
    customer_name: str = Field(example="Ted Mosby")
    total_amount: float = Field(example=123)


class HomeMetric(GenericModel):
    recent_orders: List[RecentOrder] = Field(default=[])
    customers_count: int = Field(default=0, example=10)
    products_count: int = Field(default=0, example=10)
    total_amount: float = Field(default=0, example=123)
    orders_today: int = Field(default=0, example=0)
