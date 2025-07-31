import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.crud.product_additionals.repositories import ProductAdditionalRepository
from app.crud.product_additionals.schemas import (
    ProductAdditional,
    OptionKind,
    UpdateProductAdditional,
    AdditionalItem,
)
from app.crud.product_additionals.services import ProductAdditionalServices
from app.crud.additional_items.repositories import AdditionalItemRepository


class TestProductAdditionalServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = ProductAdditionalRepository(organization_id="org1")
        self.product_repo = AsyncMock()
        self.item_repo = AdditionalItemRepository(organization_id="org1")
        self.service = ProductAdditionalServices(
            additional_repository=self.repo,
            product_repository=self.product_repo,
            item_repository=self.item_repo,
        )

    def tearDown(self):
        disconnect()

    async def _group(self, with_item: bool = False):
        items = {}
        if with_item:
            items = {1: AdditionalItem(position=1, product_id="p1", label="x", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)}

        return ProductAdditional(
            name="Extras",
            selection_type=OptionKind.RADIO,
            min_quantity=0,
            max_quantity=1,
            position=1,
            items=items,
        )

    async def test_create_product_additional(self):
        self.product_repo.select_by_id.return_value = "prod"
        group = await self._group()
        result = await self.service.create(group)
        self.product_repo.select_by_id.assert_not_called()
        self.assertEqual(result.name, "Extras")

    async def test_create_with_items_validates_products(self):
        self.product_repo.select_by_id.return_value = "prod"
        group = await self._group(with_item=True)
        await self.service.create(group)
        self.product_repo.select_by_id.assert_awaited_with(id="p1")

    async def test_update_product_additional(self):
        self.product_repo.select_by_id.return_value = "prod"
        created = await self.service.create(await self._group())
        self.product_repo.select_by_id.return_value = "prod"
        update = UpdateProductAdditional(name="New")
        updated = await self.service.update(id=created.id, updated_product_additional=update)
        self.assertEqual(updated.name, "New")

    async def test_update_product_additional_with_items(self):
        self.product_repo.select_by_id.return_value = "prod"
        created = await self.service.create(await self._group())
        self.product_repo.select_by_id.return_value = "prod"
        update = UpdateProductAdditional(items={1: AdditionalItem(position=1, product_id="p1", label="X", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)})
        await self.service.update(id=created.id, updated_product_additional=update)
        self.product_repo.select_by_id.assert_awaited_with(id="p1")

    async def test_search_all(self):
        self.product_repo.select_by_id.return_value = "prod"
        await self.service.create(await self._group())
        res = await self.service.search_all()
        self.assertEqual(len(res), 1)

    async def test_add_update_delete_item(self):
        self.product_repo.select_by_id.return_value = "prod"
        created = await self.service.create(await self._group())
        item = AdditionalItem(position=1, product_id="p1", label="X", unit_price=0.0, unit_cost=0.0, consumption_factor=1.0)
        await self.service.add_item(additional_id=created.id, item=item)
        result = await self.service.search_by_id(created.id)
        self.assertIn(1, result.items)
        item_id = result.items[1].id
        item.label = "Y"
        await self.service.update_item(additional_id=created.id, item_id=item_id, item=item)
        self.assertEqual((await self.service.search_by_id(created.id)).items[1].label, "Y")
        await self.service.delete_item(additional_id=created.id, item_id=item_id)
        self.assertNotIn(1, (await self.service.search_by_id(created.id)).items)

