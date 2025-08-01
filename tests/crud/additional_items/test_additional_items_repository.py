import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.product_additionals.repositories import ProductAdditionalRepository
from app.crud.product_additionals.schemas import ProductAdditional, OptionKind
from app.crud.additional_items.repositories import AdditionalItemRepository
from app.crud.additional_items.schemas import AdditionalItem
from app.core.exceptions import NotFoundError


class TestAdditionalItemRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.additional_repo = AdditionalItemRepository(organization_id="org1")
        self.group_repo = ProductAdditionalRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _group_id(self):
        group = ProductAdditional(
            name="G",
            selection_type=OptionKind.RADIO,
            min_quantity=0,
            max_quantity=1,
            position=1,
            items={},
        )
        created = await self.group_repo.create(group)
        return created.id

    async def test_create_additional_item(self):
        gid = await self._group_id()
        item = AdditionalItem(position=1, product_id="p1", label="X", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        created = await self.additional_repo.create(additional_id=gid, item=item)
        self.assertEqual(created.label, "X")

    async def test_update_additional_item(self):
        gid = await self._group_id()
        item = AdditionalItem(position=1, product_id="p1", label="A", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        created = await self.additional_repo.create(additional_id=gid, item=item)
        created.label = "B"
        updated = await self.additional_repo.update(created)
        self.assertEqual(updated.label, "B")

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.additional_repo.select_by_id(id="missing")

    async def test_delete_by_id(self):
        gid = await self._group_id()
        item = AdditionalItem(position=1, product_id="p1", label="D", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        created = await self.additional_repo.create(additional_id=gid, item=item)
        deleted = await self.additional_repo.delete_by_id(id=created.id)
        self.assertEqual(deleted.id, created.id)

    async def test_select_all(self):
        gid = await self._group_id()
        item1 = AdditionalItem(position=1, product_id="p1", label="A", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        item2 = AdditionalItem(position=2, product_id="p2", label="B", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        await self.additional_repo.create(additional_id=gid, item=item1)
        await self.additional_repo.create(additional_id=gid, item=item2)
        items = await self.additional_repo.select_all(additional_id=gid)
        self.assertEqual(len(items), 2)

    async def test_select_all_for_additionals(self):
        gid1 = await self._group_id()
        gid2 = await self._group_id()
        item1 = AdditionalItem(position=1, product_id="p1", label="A", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        item2 = AdditionalItem(position=1, product_id="p2", label="B", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        await self.additional_repo.create(additional_id=gid1, item=item1)
        await self.additional_repo.create(additional_id=gid2, item=item2)
        mapping = await self.additional_repo.select_all_for_additionals([gid1, gid2])
        self.assertEqual(len(mapping[gid1]), 1)
        self.assertEqual(mapping[gid1][0].label, "A")
        self.assertEqual(len(mapping), 2)
