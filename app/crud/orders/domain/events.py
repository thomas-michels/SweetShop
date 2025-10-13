"""Domain events for the order aggregate."""
from enum import Enum


class OrderEvent(str, Enum):
    """Events emitted by the order domain entity."""

    STATUS_CHANGED = "status_changed"
