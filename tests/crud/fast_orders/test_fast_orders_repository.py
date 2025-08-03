import unittest
from datetime import timedelta
from unittest.mock import patch

from mongoengine import connect, disconnect
import mongomock

from app.core.utils.utc_datetime import UTCDateTime
from app.core.exceptions import NotFoundError
from app.crud.fast_orders.repositories import FastOrderRepository
from app.crud.fast_orders.schemas import FastOrder, StoredProduct
from app.crud.orders.models import OrderModel


class TestFastOrderRepository(unittest.IsolatedAsyncioTestCase):
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
        self.repo = FastOrderRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    def _fast_order(self, order_date=None, description="Fast"):
        prod = StoredProduct(
            product_id="p1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=1,
        )
        return FastOrder(
            products=[prod],
            order_date=order_date or UTCDateTime.now(),
            description=description,
            additional=0,
            discount=0,
        )

    async def test_create_fast_order(self):
        fast_order = self._fast_order()
        created = await self.repo.create(fast_order=fast_order, total_amount=2.0)
        self.assertEqual(created.total_amount, 2.0)
        self.assertEqual(OrderModel.objects.count(), 1)

    async def test_update_fast_order(self):
        created = await self.repo.create(self._fast_order(), total_amount=2.0)
        updated = await self.repo.update(created.id, {"description": "Updated"})
        self.assertEqual(updated.description, "Updated")

    async def test_delete_by_id(self):
        created = await self.repo.create(self._fast_order(), total_amount=2.0)
        await self.repo.delete_by_id(id=created.id)
        self.assertEqual(OrderModel.objects(is_active=True).count(), 0)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")
