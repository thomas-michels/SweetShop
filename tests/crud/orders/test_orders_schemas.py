import unittest

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.orders.schemas import (
    Delivery,
    DeliveryType,
    RequestOrder,
    RequestedProduct,
    UpdateOrder,
    RequestedAdditionalItem,
)
from app.crud.shared_schemas.address import Address


class TestOrderSchemas(unittest.TestCase):
    def test_delivery_requires_fields_for_delivery(self):
        with self.assertRaises(ValueError):
            Delivery(delivery_type=DeliveryType.DELIVERY, address=None, delivery_value=None, delivery_at=None)

    def test_delivery_withdrawal_cannot_have_address(self):
        addr = Address(zip_code="89066-000", city="A", neighborhood="B", line_1="R", number="1")
        with self.assertRaises(ValueError):
            Delivery(delivery_type=DeliveryType.WITHDRAWAL, address=addr)

    def test_request_order_tags_unique(self):
        prod = RequestedProduct(product_id="p1", quantity=1)
        with self.assertRaises(ValueError):
            RequestOrder(
                products=[prod],
                tags=["a", "a"],
                delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
                preparation_date=UTCDateTime.now(),
                order_date=UTCDateTime.now(),
            )

    def test_update_order_negative_additional(self):
        with self.assertRaises(ValueError):
            UpdateOrder(additional=-1)

    def test_requested_additional_item_quantity_positive(self):
        with self.assertRaises(ValueError):
            RequestedAdditionalItem(item_id="a1", quantity=0)
