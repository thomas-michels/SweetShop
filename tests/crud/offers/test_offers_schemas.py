import unittest
from app.crud.offers.schemas import Offer, OfferProduct, Additional, UpdateOffer


class TestOfferSchemas(unittest.TestCase):
    def _offer(self, file_id=None):
        prod = OfferProduct(
            product_id="p1",
            name="P1",
            description="d",
            unit_cost=1.0,
            unit_price=2.0,
            file_id=None,
        )
        add = Additional(
            name="Bacon",
            unit_price=0.5,
            unit_cost=0.3,
            min_quantity=1,
            max_quantity=2,
        )
        return Offer(
            name="Combo",
            description="desc",
            products=[prod],
            additionals=[add],
            file_id=file_id,
            unit_cost=1.0,
            unit_price=2.0,
        )

    def test_additional_quantity_validation(self):
        with self.assertRaises(ValueError):
            Additional(
                name="Cheese",
                unit_price=1.0,
                unit_cost=0.5,
                min_quantity=2,
                max_quantity=1,
            )

    def test_validate_updated_fields_additionals(self):
        offer = self._offer()
        update = UpdateOffer(
            additionals=[
                Additional(
                    name="Cheese",
                    unit_price=1.0,
                    unit_cost=0.5,
                    min_quantity=1,
                    max_quantity=3,
                )
            ]
        )
        changed = offer.validate_updated_fields(update)
        self.assertTrue(changed)
        self.assertEqual(offer.additionals[0].name, "Cheese")

    def test_validate_updated_fields_file_id(self):
        offer = self._offer()
        update = UpdateOffer(file_id="file1")
        changed = offer.validate_updated_fields(update)
        self.assertTrue(changed)
        self.assertEqual(offer.file_id, "file1")

