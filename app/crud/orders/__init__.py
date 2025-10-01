"""Order package exports.

This module intentionally avoids importing the services module at import time
to prevent circular dependencies when other modules (such as builders) depend
on the order schemas.
"""

from .schemas import (
    RequestOrder,
    Order,
    OrderInDB,
    UpdateOrder,
    CompleteOrder,
)

__all__ = [
    "RequestOrder",
    "Order",
    "OrderInDB",
    "UpdateOrder",
    "CompleteOrder",
    "OrderServices",
]


def __getattr__(name: str):  # pragma: no cover - thin wrapper
    """Lazily import services to avoid circular dependencies."""
    if name == "OrderServices":
        from .services import OrderServices

        return OrderServices
    raise AttributeError(f"module 'app.crud.orders' has no attribute {name!r}")

