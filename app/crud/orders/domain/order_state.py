"""State management for order status transitions."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.crud.orders.schemas import OrderStatus


class OrderState:
    """Represents the mutable state of an order."""

    def __init__(self, current_status: OrderStatus | str) -> None:
        self.current_status: OrderStatus = self._validate_status(current_status)
        self.last_transition: Optional[datetime] = None

    async def transition_to(self, new_status: OrderStatus | str) -> OrderStatus:
        """Transition the order to a new status.

        Any transition between valid ``OrderStatus`` values is accepted. An
        attempt to set the same status is ignored. Invalid statuses raise a
        ``ValueError``.
        """

        status = self._validate_status(new_status)

        if status == self.current_status:
            return self.current_status

        self.last_transition = datetime.utcnow()
        self.current_status = status
        return self.current_status

    @staticmethod
    def _validate_status(status: OrderStatus | str) -> OrderStatus:
        if isinstance(status, OrderStatus):
            return status
        if isinstance(status, str):
            try:
                return OrderStatus(status)
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError(f"Invalid order status: {status!r}") from exc
        raise ValueError(f"Invalid order status type: {type(status)!r}")
