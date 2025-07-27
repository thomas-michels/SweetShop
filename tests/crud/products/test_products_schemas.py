import unittest
from app.crud.products.schemas import (
    Product,
    UpdateProduct,
)


class TestProductSchemas(unittest.TestCase):

    def test_product_validation_price(self):
        with self.assertRaises(ValueError):
            Product(name="A", description="d", unit_price=1, unit_cost=2)

    def test_product_validation_unique_tags(self):
        with self.assertRaises(ValueError):
            Product(name="A", description="d", unit_price=2, unit_cost=1, tags=["x", "x"])

    def test_validate_updated_fields(self):
        product = Product(name="A", description="d", unit_price=2, unit_cost=1)
        updated = UpdateProduct(name="B")
        changed = product.validate_updated_fields(updated)
        self.assertTrue(changed)
        self.assertEqual(product.name, "B")

    def test_update_product_validation(self):
        with self.assertRaises(ValueError):
            UpdateProduct(unit_price=1, unit_cost=2)
        with self.assertRaises(ValueError):
            UpdateProduct(tags=["a", "a"])
