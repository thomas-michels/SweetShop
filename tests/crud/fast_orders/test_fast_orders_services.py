import unittest
from unittest.mock import AsyncMock, patch
from mongoengine import connect, disconnect
import mongomock

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.fast_orders.repositories import FastOrderRepository
from app.crud.fast_orders.schemas import (
    RequestedProduct,
    RequestFastOrder,
    UpdateFastOrder,
)
from app.crud.fast_orders.services import FastOrderServices
from app.crud.products.schemas import ProductInDB


class TestFastOrderServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        pipeline = [{"$addFields": {"id": "$_id", "payments": []}}, {"$project": {"_id": 0}}]
        patcher = patch("app.crud.orders.models.OrderModel.get_payments", return_value=pipeline)
        self.addCleanup(patcher.stop)
        patcher.start()
        repo = FastOrderRepository(organization_id="org1")
        self.product_repo = AsyncMock()
        self.service = FastOrderServices(
            fast_order_repository=repo,
            product_repository=self.product_repo,
        )

    def tearDown(self):
        disconnect()

    async def _product_in_db(self):
        return ProductInDB(
            id="p1",
            name="Prod1",
            description="",
            unit_cost=1.0,
            unit_price=2.0,
            tags=[],
            file_id=None,
            organization_id="org1",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )

    async def _request_fast_order(self):
        return RequestFastOrder(
            products=[RequestedProduct(product_id="p1", quantity=1)],
            order_date=UTCDateTime.now(),
            description="fast",
            additional=0,
            discount=0,
        )

    async def test_create_fast_order(self):
        self.product_repo.select_by_id.return_value = await self._product_in_db()
        created = await self.service.create(await self._request_fast_order())
        self.assertEqual(created.products[0].name, "Prod1")
        self.product_repo.select_by_id.assert_awaited()

    async def test_update_fast_order_products(self):
        self.product_repo.select_by_id.return_value = await self._product_in_db()
        created = await self.service.create(await self._request_fast_order())
        self.product_repo.select_by_id.return_value = await self._product_in_db()
        update = UpdateFastOrder(products=[RequestedProduct(product_id="p1", quantity=2)], additional=1)
        updated = await self.service.update(id=created.id, updated_fast_order=update)
        self.assertEqual(updated.products[0].quantity, 2)

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 3
        service = FastOrderServices(
            fast_order_repository=mock_repo,
            product_repository=AsyncMock(),
        )
        count = await service.search_count(day=UTCDateTime.now())
        self.assertEqual(count, 3)
        mock_repo.select_count.assert_awaited()
