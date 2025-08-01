import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.product_additionals.models import ProductAdditionalModel
from app.crud.product_additionals.repositories import ProductAdditionalRepository
from app.crud.product_additionals.schemas import ProductAdditional, OptionKind
from app.core.exceptions import NotFoundError


class TestProductAdditionalRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = ProductAdditionalRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _group(self, name="Toppings", product_id="prod1"):
        return ProductAdditional(
            product_id=product_id,
            name=name,
            selection_type=OptionKind.RADIO,
            min_quantity=0,
            max_quantity=1,
            position=1,
            items=[],
        )

    async def test_create_product_additional(self):
        group = await self._group(name="Extras")
        result = await self.repo.create(group)
        self.assertEqual(result.name, "Extras")
        self.assertEqual(ProductAdditionalModel.objects.count(), 1)

    async def test_update_product_additional(self):
        created = await self.repo.create(await self._group(name="Old"))
        created.name = "New"
        updated = await self.repo.update(created)
        self.assertEqual(updated.name, "New")

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_delete_by_id(self):
        created = await self.repo.create(await self._group(name="Del"))
        result = await self.repo.delete_by_id(id=created.id)
        self.assertEqual(result.id, created.id)
        self.assertEqual(ProductAdditionalModel.objects(is_active=True).count(), 0)

    async def test_select_all(self):
        await self.repo.create(await self._group(name="G1"))
        await self.repo.create(await self._group(name="G2"))
        results = await self.repo.select_all()
        self.assertEqual(len(results), 2)

    async def test_select_by_ids(self):
        g1 = await self.repo.create(await self._group(name="G1"))
        g2 = await self.repo.create(await self._group(name="G2"))
        results = await self.repo.select_by_ids([g1.id, g2.id])
        self.assertEqual({r.id for r in results}, {g1.id, g2.id})

    async def test_select_by_product_id(self):
        g1 = await self.repo.create(await self._group(name="G1", product_id="p1"))
        await self.repo.create(await self._group(name="G2", product_id="p2"))
        results = await self.repo.select_by_product_id("p1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, g1.id)
