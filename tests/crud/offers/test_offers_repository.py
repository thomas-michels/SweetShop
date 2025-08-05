import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.offers.models import OfferModel
from app.crud.offers.repositories import OfferRepository
from app.crud.offers.schemas import Offer, OfferProduct
from app.core.exceptions import NotFoundError
from app.core.utils.utc_datetime import UTCDateTime


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

    async def _offer(
        self,
        name="Combo",
        file_id=None,
        starts_at=None,
        ends_at=None,
        is_visible=True,
    ):
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
            file_id=file_id,
            unit_cost=1.0,
            unit_price=2.0,
            starts_at=starts_at,
            ends_at=ends_at,
            is_visible=is_visible,
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
        created.is_visible = False
        updated = await self.repo.update(created)
        self.assertEqual(updated.name, "New")
        self.assertFalse(updated.is_visible)

    async def test_create_with_file_id(self):
        offer = await self._offer(name="WithFile", file_id="file1")
        result = await self.repo.create(offer)
        self.assertEqual(result.file_id, "file1")

    async def test_create_offer_with_dates_and_visibility(self):
        start = UTCDateTime.now()
        end = UTCDateTime.now()
        offer = await self._offer(starts_at=start, ends_at=end, is_visible=False)
        result = await self.repo.create(offer)
        self.assertEqual(result.starts_at, start)
        self.assertEqual(result.ends_at, end)
        self.assertFalse(result.is_visible)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_delete_by_id_success(self):
        created = await self.repo.create(await self._offer(name="Del"))
        result = await self.repo.delete_by_id(id=created.id)
        self.assertEqual(result.id, created.id)
        self.assertEqual(OfferModel.objects(is_active=True).count(), 0)

    async def test_select_count_with_query(self):
        await self.repo.create(await self._offer(name="Apple"))
        await self.repo.create(await self._offer(name="Banana"))
        await self.repo.create(await self._offer(name="Apricot"))

        count = await self.repo.select_count(query="Ap")

        self.assertEqual(count, 2)

    async def test_select_all_paginated(self):
        await self.repo.create(await self._offer(name="A"))
        await self.repo.create(await self._offer(name="B"))
        await self.repo.create(await self._offer(name="C"))

        results = await self.repo.select_all_paginated(query=None, page=1, page_size=2)
        self.assertEqual(len(results), 2)

        results_p2 = await self.repo.select_all_paginated(query=None, page=2, page_size=2)
        self.assertEqual(len(results_p2), 1)
        names = {r.name for r in results + results_p2}
        self.assertEqual(names, {"A", "B", "C"})

