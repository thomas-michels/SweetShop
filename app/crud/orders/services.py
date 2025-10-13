"""Compatibility layer for legacy imports.

The business logic now lives in :mod:`app.crud.orders.services.order_facade`.
This module keeps the public API stable by re-exporting the new facade under
its previous name (``OrderServices``).
"""

from .services.order_facade import OrderFacade

OrderServices = OrderFacade

__all__ = ["OrderFacade", "OrderServices"]
