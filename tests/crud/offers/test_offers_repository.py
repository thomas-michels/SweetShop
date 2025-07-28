import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.offers.models import OfferModel
from app.crud.offers.repositories import OfferRepository
from app.crud.offers.schemas import Offer, OfferProduct, Additional
from app.core.exceptions import NotFoundError


class TestOfferRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = OfferRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _offer(self, name="Combo", additionals=None):
        prod = OfferProduct(
            product_id="p1",
            name="P1",
            description="d",
            unit_cost=1.0,
            unit_price=2.0,
            file_id=None,
        )
        return Offer(
            name=name,
            description="desc",
            products=[prod],
            additionals=additionals or [],
            unit_cost=1.0,
            unit_price=2.0,
        )

    async def test_create_offer(self):
        offer = await self._offer(name="Lunch")
        result = await self.repo.create(offer)
        self.assertEqual(result.name, "Lunch")
        self.assertEqual(OfferModel.objects.count(), 1)

    async def test_create_offer_title_cases_name(self):
        offer = await self._offer(name="dInner menu")
        result = await self.repo.create(offer)
        self.assertEqual(result.name, "Dinner Menu")

    async def test_update_offer(self):
        created = await self.repo.create(await self._offer(name="Old"))
        created.name = "New"
        created.additionals = [
            Additional(name="Cheese", unit_price=1.0, unit_cost=0.5, min_quantity=0, max_quantity=1)
        ]
        updated = await self.repo.update(created)
        self.assertEqual(updated.name, "New")
        self.assertEqual(len(updated.additionals), 1)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_delete_by_id_success(self):
        created = await self.repo.create(await self._offer(name="Del"))
        result = await self.repo.delete_by_id(id=created.id)
        self.assertEqual(result.id, created.id)
        self.assertEqual(OfferModel.objects(is_active=True).count(), 0)

