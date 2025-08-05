import unittest
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.offers.schemas import Offer, OfferProduct, UpdateOffer


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
        return Offer(
            name="Combo",
            description="desc",
            products=[prod],
            file_id=file_id,
            unit_cost=1.0,
            unit_price=2.0,
            starts_at=UTCDateTime.now(),
            ends_at=UTCDateTime.now(),
            is_visible=True,
        )

    def test_validate_updated_fields_visibility(self):
        offer = self._offer()
        update = UpdateOffer(is_visible=False)
        changed = offer.validate_updated_fields(update)
        self.assertTrue(changed)
        self.assertFalse(offer.is_visible)

    def test_validate_updated_fields_file_id(self):
        offer = self._offer()
        update = UpdateOffer(file_id="file1")
        changed = offer.validate_updated_fields(update)
        self.assertTrue(changed)
        self.assertEqual(offer.file_id, "file1")

