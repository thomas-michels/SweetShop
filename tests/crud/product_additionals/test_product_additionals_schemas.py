import unittest

from app.crud.product_additionals.schemas import ProductAdditional, UpdateProductAdditional, OptionKind


class TestProductAdditionalSchemas(unittest.TestCase):
    def test_validate_updated_fields(self):
        group = ProductAdditional(
            name="Group",
            selection_type=OptionKind.RADIO,
            min_quantity=0,
            max_quantity=1,
            position=1,
            items={},
        )
        update = UpdateProductAdditional(name="New")
        changed = group.validate_updated_fields(update=update)
        self.assertTrue(changed)
        self.assertEqual(group.name, "New")

