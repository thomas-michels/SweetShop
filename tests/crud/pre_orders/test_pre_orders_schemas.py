import unittest

from app.crud.pre_orders.schemas import PreOrderCustomer


class TestPreOrderSchemas(unittest.TestCase):
    def test_preorder_customer_sets_default_international_code(self):
        customer = PreOrderCustomer(name="John", ddd="047", phone_number="999")
        self.assertEqual(customer.international_code, "55")
