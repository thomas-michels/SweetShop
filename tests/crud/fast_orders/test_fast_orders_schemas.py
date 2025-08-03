import unittest
from datetime import timedelta

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.fast_orders.schemas import (
    FastOrder,
    RequestedProduct,
    RequestFastOrder,
    UpdateFastOrder,
    StoredProduct,
)


class TestFastOrderSchemas(unittest.TestCase):
    def test_request_fast_order_unique_products(self):
        prod = RequestedProduct(product_id="p1", quantity=1)
        with self.assertRaises(ValueError):
            RequestFastOrder(products=[prod, prod], order_date=UTCDateTime.now())

    def test_update_fast_order_negative_additional(self):
        with self.assertRaises(ValueError):
            UpdateFastOrder(additional=-1)

    def test_validate_updated_fields(self):
        prod = StoredProduct(
            product_id="p1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=1,
        )
        fast_order = FastOrder(products=[prod], order_date=UTCDateTime.now())
        update = UpdateFastOrder(description="New")
        changed = fast_order.validate_updated_fields(update)
        self.assertTrue(changed)
        self.assertEqual(fast_order.description, "New")
