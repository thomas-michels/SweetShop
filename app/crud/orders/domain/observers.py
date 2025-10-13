"""Observer abstractions for order events."""
from __future__ import annotations

from typing import Iterable, List, Protocol

from .events import OrderEvent

if False:  # pragma: no cover
    from .order import Order


class OrderObserver(Protocol):
    """Protocol implemented by order observers."""

    async def update(
        self,
        order: "Order",
        event: OrderEvent,
        **context: object,
    ) -> None:
        """React to an ``event`` triggered by ``order``."""


class OrderObservable:
    """Mixin providing observer registration and notification."""

    def __init__(self) -> None:
        self._observers: List[OrderObserver] = []

    def attach(self, observer: OrderObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: OrderObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    async def notify(
        self,
        order: "Order",
        event: OrderEvent,
        **context: object,
    ) -> None:
        for observer in list(self._observers):
            await observer.update(order, event, **context)

    def attach_many(self, observers: Iterable[OrderObserver]) -> None:
        for observer in observers:
            self.attach(observer)
