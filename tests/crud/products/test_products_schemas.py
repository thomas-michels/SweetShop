import unittest
from app.crud.products.schemas import (
    Item,
    ProductSection,
    Product,
    UpdateProduct,
)


class TestProductSchemas(unittest.TestCase):
    def test_item_auto_generates_id(self):
        item = Item(name="A", unit_price=1.0, unit_cost=0.5)
        self.assertIsNotNone(item.id)

    def test_product_section_requires_item(self):
        with self.assertRaises(ValueError):
            ProductSection(title="T", min_choices=1, max_choices=1, items=[])

    def test_product_section_auto_id(self):
        section = ProductSection(title="T", min_choices=1, max_choices=1, items=[Item(name="A", unit_price=1, unit_cost=1)])
        self.assertIsNotNone(section.id)

    def test_product_validation_price(self):
        with self.assertRaises(ValueError):
            Product(name="A", description="d", unit_price=1, unit_cost=2)

    def test_product_validation_unique_tags(self):
        with self.assertRaises(ValueError):
            Product(name="A", description="d", unit_price=2, unit_cost=1, tags=["x", "x"])

    def test_product_get_section_by_id(self):
        section = ProductSection(title="T", min_choices=1, max_choices=1, items=[Item(name="A", unit_price=1, unit_cost=1)])
        product = Product(name="A", description="d", unit_price=2, unit_cost=1, sections=[section])
        self.assertEqual(product.get_section_by_id(section.id).title, "T")

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
