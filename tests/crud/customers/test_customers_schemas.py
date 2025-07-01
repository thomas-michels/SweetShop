import unittest
from app.crud.customers.schemas import Customer, UpdateCustomer


class TestCustomerSchemas(unittest.TestCase):
    def test_customer_invalid_phone_raises(self):
        with self.assertRaises(ValueError):
            Customer(name="A", ddd="aa", phone_number="123")

    def test_customer_invalid_document_length_raises(self):
        with self.assertRaises(ValueError):
            Customer(name="B", document="123")

    def test_customer_invalid_email_raises(self):
        with self.assertRaises(ValueError):
            Customer(name="C", email="bad_email")

    def test_customer_blank_email_becomes_none(self):
        cust = Customer(name="D", email="")
        self.assertIsNone(cust.email)

    def test_update_customer_invalid_email(self):
        with self.assertRaises(ValueError):
            UpdateCustomer(email="bad")
