import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.section_items.models import SectionItemModel
from app.crud.section_items.repositories import SectionItemRepository
from app.crud.section_items.schemas import SectionItem, ItemType
from app.core.exceptions import NotFoundError


class TestSectionItemRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = SectionItemRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _section_item(self, position=1, is_visible=True, product=False):
        if product:
            return SectionItem(section_id="sec1", item_id="prod1", item_type=ItemType.PRODUCT, position=position, is_visible=is_visible)
        return SectionItem(section_id="sec1", item_id="off1", item_type=ItemType.OFFER, position=position, is_visible=is_visible)

    async def test_create_section_item(self):
        so = await self._section_item()
        result = await self.repo.create(so)
        self.assertEqual(result.position, 1)
        self.assertEqual(SectionItemModel.objects.count(), 1)

    async def test_create_section_item_with_product(self):
        so = await self._section_item(product=True)
        result = await self.repo.create(so)
        self.assertEqual(result.item_id, "prod1")
        self.assertEqual(SectionItemModel.objects.count(), 1)

    async def test_update_section_item(self):
        created = await self.repo.create(await self._section_item())
        created.position = 2
        updated = await self.repo.update(created)
        self.assertEqual(updated.position, 2)

    async def test_select_by_id_success(self):
        created = await self.repo.create(await self._section_item())
        result = await self.repo.select_by_id(id=created.id)
        self.assertEqual(result.id, created.id)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_all_filter_is_visible(self):
        await self.repo.create(await self._section_item(is_visible=True))
        await self.repo.create(await self._section_item(is_visible=False))
        visibles = await self.repo.select_all(section_id="sec1", is_visible=True)
        self.assertEqual(len(visibles), 1)
        self.assertTrue(visibles[0].is_visible)

    async def test_delete_by_id_success(self):
        created = await self.repo.create(await self._section_item())
        result = await self.repo.delete_by_id(id=created.id)
        self.assertEqual(result.id, created.id)
        self.assertEqual(SectionItemModel.objects(is_active=True).count(), 0)

    async def test_delete_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.delete_by_id(id="missing")
