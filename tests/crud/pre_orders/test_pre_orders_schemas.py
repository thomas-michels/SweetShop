import unittest

from app.crud.pre_orders.schemas import (
    PreOrderCustomer,
    PreOrderInDB,
    PreOrderStatus,
    SelectedOffer,
    Delivery,
    DeliveryType,
)
from app.core.utils.utc_datetime import UTCDateTime


class TestPreOrderSchemas(unittest.TestCase):
    def test_pre_order_customer_default_international_code(self):
        customer = PreOrderCustomer(name="Ted", ddd="047", phone_number="9988")
        self.assertEqual(customer.international_code, "55")

    def test_delivery_validation(self):
        with self.assertRaises(ValueError):
            Delivery(delivery_type=DeliveryType.DELIVERY, delivery_value=5.0, delivery_at=None, address=None)

    def test_pre_order_in_db_creation(self):
        customer = PreOrderCustomer(name="Ted", ddd="047", phone_number="9988")
        delivery = Delivery(delivery_type=DeliveryType.WITHDRAWAL)
        offer = SelectedOffer(offer_id="off1", quantity=1)
        now = UTCDateTime.now()
        pre = PreOrderInDB(
            id="pre1",
            organization_id="org1",
            code="001",
            menu_id="men1",
            payment_method="CASH",
            customer=customer,
            delivery=delivery,
            offers=[offer],
            status=PreOrderStatus.PENDING,
            tax=0,
            total_amount=10,
            created_at=now,
            updated_at=now,
            is_active=True,
        )
        self.assertEqual(pre.code, "001")
