import unittest
from mongoengine import connect, disconnect
import mongomock

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.products.models import ProductModel
from app.crud.products.repositories import ProductRepository
from app.crud.products.schemas import Product
from app.core.exceptions import NotFoundError, UnprocessableEntity


class TestProductRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = ProductRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _product(self, name="Cake", tags=None):
        return Product(
            name=name,
            description="desc",
            unit_price=10.0,
            unit_cost=5.0,
            tags=tags or [],
        )

    async def test_create_product(self):
        prod = await self._product(name="Choco")
        result = await self.repo.create(prod)
        self.assertEqual(result.name, "Choco")
        self.assertEqual(ProductModel.objects.count(), 1)

    async def test_create_product_strips_and_capitalizes_name(self):
        prod = await self._product(name="  sweet ")
        result = await self.repo.create(prod)
        self.assertEqual(result.name, "Sweet")

    async def test_update_product(self):
        created = await self.repo.create(await self._product(name="Old"))
        created.name = "New"
        updated = await self.repo.update(created)
        self.assertEqual(updated.name, "New")

    async def test_select_by_id_success(self):
        created = await self.repo.create(await self._product())
        result = await self.repo.select_by_id(id=created.id)
        self.assertEqual(result.id, created.id)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_by_id_raise_false_returns_none(self):
        result = await self.repo.select_by_id(id="missing", raise_404=False)
        self.assertIsNone(result)

    async def test_select_count_with_query(self):
        await self.repo.create(await self._product(name="Apple"))
        await self.repo.create(await self._product(name="Banana"))
        await self.repo.create(await self._product(name="Apricot"))
        count = await self.repo.select_count(query="Ap")
        self.assertEqual(count, 2)

    async def test_select_all_with_pagination(self):
        await self.repo.create(await self._product(name="A"))
        await self.repo.create(await self._product(name="B"))
        await self.repo.create(await self._product(name="C"))
        results = await self.repo.select_all(query=None, page=1, page_size=2)
        self.assertEqual(len(results), 2)
        results_p2 = await self.repo.select_all(query=None, page=2, page_size=2)
        self.assertEqual(len(results_p2), 1)
        names = {r.name for r in results + results_p2}
        self.assertEqual(names, {"A", "B", "C"})

    async def test_select_all_filter_by_tags(self):
        await self.repo.create(await self._product(name="TaggedA", tags=["t1", "t2"]))
        await self.repo.create(await self._product(name="TaggedB", tags=["t2"]))
        results = await self.repo.select_all(query=None, tags=["t1"], page=None, page_size=None)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Taggeda")

    async def test_delete_by_id_success(self):
        created = await self.repo.create(await self._product(name="Del"))
        result = await self.repo.delete_by_id(id=created.id)
        self.assertEqual(ProductModel.objects(is_active=True).count(), 0)
        self.assertEqual(result.name, "Del")

    async def test_delete_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.delete_by_id(id="missing")

    async def test_update_nonexistent_product_raises_unprocessable(self):
        from app.crud.products.schemas import ProductInDB
        missing = ProductInDB(
            id="missing",
            name="Missing",
            description="D",
            unit_price=1.0,
            unit_cost=1.0,
            tags=[],
            organization_id="org1",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        with self.assertRaises(UnprocessableEntity):
            await self.repo.update(missing)
