"""Factory helpers for the order aggregate."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from app.crud.orders.schemas import DeliveryType, OrderStatus
from app.crud.shared_schemas.payment import PaymentStatus

from .order import DeliveryData, Order, OrderData
from .observers import OrderObserver


class OrderFactory:
    """Factory responsible for instantiating :class:`Order` objects."""

    @staticmethod
    def build(order_data: OrderData, observers: Iterable[OrderObserver] | None = None) -> Order:
        order = Order(order_data)
        if observers:
            order.attach_many(observers)
        return order

    @staticmethod
    def build_from_mapping(
        payload: Mapping[str, Any],
        observers: Sequence[OrderObserver] | None = None,
    ) -> Order:
        """Create an :class:`Order` from a plain mapping."""

        order_data = OrderFactory.order_data_from_mapping(payload)
        return OrderFactory.build(order_data, observers)

    @staticmethod
    def order_data_from_mapping(payload: Mapping[str, Any]) -> OrderData:
        delivery_payload = payload.get("delivery", {}) or {}
        delivery_type = delivery_payload.get("delivery_type", DeliveryType.WITHDRAWAL)
        if not isinstance(delivery_type, DeliveryType):
            delivery_type = DeliveryType(delivery_type)

        delivery = DeliveryData(
            delivery_type=delivery_type,
            delivery_value=delivery_payload.get("delivery_value"),
            delivery_at=delivery_payload.get("delivery_at"),
            address=delivery_payload.get("address"),
        )

        status = payload.get("status", OrderStatus.PENDING)
        if not isinstance(status, OrderStatus):
            status = OrderStatus(status)

        payment_status = payload.get("payment_status", PaymentStatus.PENDING)
        if not isinstance(payment_status, PaymentStatus):
            payment_status = PaymentStatus(payment_status)

        order_id = payload.get("id")
        organization_id = payload.get("organization_id")

        if order_id is None or organization_id is None:
            raise ValueError("Order payload must include 'id' and 'organization_id'.")

        return OrderData(
            id=str(order_id),
            organization_id=str(organization_id),
            status=status,
            payment_status=payment_status,
            customer_id=payload.get("customer_id"),
            products=list(payload.get("products", [])),
            delivery=delivery,
            additional=float(payload.get("additional", 0) or 0),
            discount=float(payload.get("discount", 0) or 0),
            tags=list(payload.get("tags", [])),
            total_amount=float(payload.get("total_amount", 0) or 0),
            order_date=payload.get("order_date"),
            preparation_date=payload.get("preparation_date"),
            description=payload.get("description"),
            reason_id=payload.get("reason_id"),
            payments=list(payload.get("payments", [])),
            tax=payload.get("tax"),
            is_active=payload.get("is_active", True),
            metadata=dict(payload.get("metadata", {})),
        )
