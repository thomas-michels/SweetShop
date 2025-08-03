import unittest

from app.crud.fast_orders.schemas import (
    RequestFastOrder,
    RequestedProduct,
    UpdateFastOrder,
)
from app.core.utils.utc_datetime import UTCDateTime


class TestFastOrderSchemas(unittest.TestCase):
    def test_request_fast_order_requires_unique_products(self):
        with self.assertRaises(ValueError):
            RequestFastOrder(
                products=[
                    RequestedProduct(product_id="p1", quantity=1),
                    RequestedProduct(product_id="p1", quantity=2),
                ],
                order_date=UTCDateTime.now(),
            )

    def test_request_fast_order_rounds_seconds(self):
        dt = UTCDateTime.now()
        order = RequestFastOrder(
            products=[RequestedProduct(product_id="p1", quantity=1)],
            order_date=UTCDateTime(
                year=dt.year,
                month=dt.month,
                day=dt.day,
                hour=dt.hour,
                minute=dt.minute,
                second=10,
            ),
        )
        self.assertEqual(order.order_date.second, 0)

    def test_update_fast_order_validates_non_negative_fields(self):
        with self.assertRaises(ValueError):
            UpdateFastOrder(additional=-1)
        with self.assertRaises(ValueError):
            UpdateFastOrder(discount=-1)

    def test_update_fast_order_requires_unique_products(self):
        with self.assertRaises(ValueError):
            UpdateFastOrder(
                products=[
                    RequestedProduct(product_id="p1", quantity=1),
                    RequestedProduct(product_id="p1", quantity=2),
                ]
            )

    def test_update_fast_order_rounds_seconds(self):
        dt = UTCDateTime.now()
        upd = UpdateFastOrder(
            order_date=UTCDateTime(
                year=dt.year,
                month=dt.month,
                day=dt.day,
                hour=dt.hour,
                minute=dt.minute,
                second=15,
            )
        )
        self.assertEqual(upd.order_date.second, 0)
