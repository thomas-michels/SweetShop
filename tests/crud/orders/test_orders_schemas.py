import unittest

from app.crud.orders.schemas import (
    Delivery,
    DeliveryType,
    RequestOrder,
    RequestedProduct,
)
from app.core.utils.utc_datetime import UTCDateTime


class TestOrderSchemas(unittest.TestCase):
    def test_delivery_requires_fields_for_delivery_type(self):
        with self.assertRaises(ValueError):
            Delivery(delivery_type=DeliveryType.DELIVERY)

    def test_delivery_withdrawal_disallows_extra_fields(self):
        with self.assertRaises(ValueError):
            Delivery(
                delivery_type=DeliveryType.WITHDRAWAL,
                delivery_at=UTCDateTime.now(),
            )

    def test_request_order_requires_unique_tags(self):
        with self.assertRaises(ValueError):
            RequestOrder(
                products=[RequestedProduct(product_id="p1", quantity=1)],
                tags=["a", "a"],
                delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
                preparation_date=UTCDateTime.now(),
                order_date=UTCDateTime.now(),
            )
