"""Delivery calculation strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.crud.orders.schemas import DeliveryType

if False:  # pragma: no cover
    from .order import Order


class DeliveryStrategy(ABC):
    """Defines the interface for delivery calculation strategies."""

    @abstractmethod
    def calculate_delivery_value(self, order: "Order") -> float:
        """Return the delivery cost for the given order."""


class WithdrawalStrategy(DeliveryStrategy):
    """Strategy for on-site withdrawal orders."""

    def calculate_delivery_value(self, order: "Order") -> float:
        return 0.0


class DeliveryStrategyConcrete(DeliveryStrategy):
    """Strategy for regular delivery orders."""

    def calculate_delivery_value(self, order: "Order") -> float:
        delivery = order.delivery
        value = getattr(delivery, "delivery_value", None)

        delivery_value = float(value or 0.0)

        # Keep the domain entity in sync with the calculated delivery value so
        # callers can safely persist or reuse it.
        if hasattr(order.delivery, "delivery_value"):
            order.delivery.delivery_value = delivery_value

        return delivery_value


class FastOrderStrategy(DeliveryStrategy):
    """Strategy for fast orders that ignore delivery fields."""

    def calculate_delivery_value(self, order: "Order") -> float:
        # Fast orders never charge delivery.
        return 0.0


def select_delivery_strategy(order: "Order") -> DeliveryStrategy:
    """Return the appropriate delivery strategy for ``order``."""

    delivery_type = getattr(order.delivery, "delivery_type", DeliveryType.WITHDRAWAL)

    if delivery_type == DeliveryType.DELIVERY:
        return DeliveryStrategyConcrete()
    if delivery_type == DeliveryType.FAST_ORDER:
        return FastOrderStrategy()
    return WithdrawalStrategy()
