import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.product_additionals.repositories import ProductAdditionalRepository
from app.crud.product_additionals.schemas import ProductAdditional, OptionKind
from app.crud.additional_items.repositories import AdditionalItemRepository
from app.crud.additional_items.schemas import AdditionalItem, UpdateAdditionalItem
from app.crud.additional_items.services import AdditionalItemServices


class TestAdditionalItemServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.item_repo = AdditionalItemRepository(organization_id="org1")
        self.group_repo = ProductAdditionalRepository(organization_id="org1")
        self.service = AdditionalItemServices(
            item_repository=self.item_repo,
            additional_repository=self.group_repo,
        )

    def tearDown(self):
        disconnect()

    async def _group_id(self):
        group = ProductAdditional(
            product_id="p0",
            name="G",
            selection_type=OptionKind.RADIO,
            min_quantity=0,
            max_quantity=1,
            position=1,
            items=[],
        )
        created = await self.group_repo.create(group)
        return created.id

    async def test_create_item(self):
        gid = await self._group_id()
        item = AdditionalItem(position=1, product_id="p1", label="X", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        created = await self.service.create(additional_id=gid, item=item)
        self.assertEqual(created.position, 1)

    async def test_update_item(self):
        gid = await self._group_id()
        item = AdditionalItem(position=1, product_id="p1", label="A", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        created = await self.service.create(additional_id=gid, item=item)
        update = UpdateAdditionalItem(label="B")
        updated = await self.service.update(id=created.id, updated_item=update)
        self.assertEqual(updated.label, "B")

    async def test_search_all(self):
        gid = await self._group_id()
        item = AdditionalItem(position=1, product_id="p1", label="A", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        await self.service.create(additional_id=gid, item=item)
        res = await self.service.search_all(additional_id=gid)
        self.assertEqual(len(res), 1)

    async def test_delete_item(self):
        gid = await self._group_id()
        item = AdditionalItem(position=1, product_id="p1", label="A", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        created = await self.service.create(additional_id=gid, item=item)
        deleted = await self.service.delete_by_id(id=created.id)
        self.assertEqual(deleted.id, created.id)
