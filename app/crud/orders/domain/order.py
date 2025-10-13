"""Domain entity representing an order."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.crud.orders.schemas import DeliveryType, OrderStatus, PaymentStatus

from .delivery_strategy import select_delivery_strategy
from .events import OrderEvent
from .observers import OrderObservable
from .order_state import OrderState


@dataclass
class DeliveryData:
    delivery_type: DeliveryType
    delivery_value: Optional[float] = None
    delivery_at: Optional[datetime] = None
    address: Optional[Dict[str, Any]] = None


@dataclass
class OrderData:
    id: str
    organization_id: str
    status: OrderStatus
    payment_status: PaymentStatus
    customer_id: Optional[str]
    products: List[Dict[str, Any]]
    delivery: DeliveryData
    additional: float
    discount: float
    tags: List[str]
    total_amount: float
    order_date: datetime
    preparation_date: datetime
    description: Optional[str] = None
    reason_id: Optional[str] = None
    payments: List[Dict[str, Any]] = field(default_factory=list)
    tax: Optional[float] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class Order(OrderObservable):
    """Aggregate root for orders."""

    def __init__(self, order_data: OrderData) -> None:
        super().__init__()
        self.id = order_data.id
        self.organization_id = order_data.organization_id
        self.customer_id = order_data.customer_id
        self.delivery = order_data.delivery
        self.products = order_data.products
        self.additional = float(order_data.additional or 0)
        self.discount = float(order_data.discount or 0)
        self.total_amount = float(order_data.total_amount or 0)
        self.tags = list(order_data.tags)
        self.description = order_data.description
        self.reason_id = order_data.reason_id
        self.payments = list(order_data.payments)
        self.payment_status = order_data.payment_status
        self.order_date = order_data.order_date
        self.preparation_date = order_data.preparation_date
        self.tax = order_data.tax
        self.is_active = order_data.is_active
        self.metadata = dict(order_data.metadata)

        self.status = OrderState(order_data.status)
        self.status_history: List[Tuple[OrderStatus, datetime]] = [
            (self.status.current_status, datetime.utcnow())
        ]

    def _get_delivery_strategy(self):
        return select_delivery_strategy(self)

    def calculate_total(self) -> float:
        """Calculate the total amount considering the delivery strategy."""

        strategy = self._get_delivery_strategy()
        delivery_value = strategy.calculate_delivery_value(self)

        subtotal = float(self.additional)
        for product in self.products:
            unit_price = float(product.get("unit_price", 0))
            quantity = int(product.get("quantity", 0))
            subtotal += unit_price * quantity

            for additional in product.get("additionals", []):
                add_price = float(additional.get("unit_price", 0))
                add_quantity = int(additional.get("quantity", 0))
                subtotal += add_price * add_quantity * quantity

        subtotal = max(subtotal - float(self.discount), 0)
        total = subtotal + delivery_value

        return round(total, 2)

    async def change_status(self, new_status: OrderStatus | str) -> None:
        """Change the order status and notify observers."""

        old_status = self.status.current_status
        status = await self.status.transition_to(new_status)

        if status != old_status:
            timestamp = self.status.last_transition or datetime.utcnow()
            self.status_history.append((status, timestamp))
            await self.notify(
                self,
                OrderEvent.STATUS_CHANGED,
                old_status=old_status,
                new_status=status,
                changed_at=timestamp,
            )
