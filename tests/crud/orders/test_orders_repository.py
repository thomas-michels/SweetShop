import unittest
from datetime import timedelta
from unittest.mock import patch
from mongoengine import connect, disconnect
import mongomock

from app.core.utils.utc_datetime import UTCDateTime
from app.core.exceptions import NotFoundError
from app.crud.orders.repositories import OrderRepository
from app.crud.orders.schemas import (
    Order,
    StoredProduct,
    Delivery,
    DeliveryType,
    OrderStatus,
    StoredAdditionalItem,
)
from app.crud.orders.models import OrderModel


class TestOrderRepository(unittest.IsolatedAsyncioTestCase):
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
        self.repo = OrderRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    def _order(self, order_date=None):
        prod = StoredProduct(
            product_id="p1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=1,
        )
        delivery = Delivery(delivery_type=DeliveryType.WITHDRAWAL)
        now = order_date or UTCDateTime.now()
        return Order(
            customer_id=None,
            status=OrderStatus.PENDING,
            products=[prod],
            tags=["tag1"],
            delivery=delivery,
            preparation_date=now,
            order_date=now,
            description="desc",
            additional=0,
            discount=0,
        )

    async def test_create_order(self):
        order = self._order()
        created = await self.repo.create(order=order, total_amount=2.0)
        self.assertEqual(created.total_amount, 2.0)
        self.assertEqual(OrderModel.objects.count(), 1)

    async def test_update_order(self):
        created = await self.repo.create(self._order(), total_amount=2.0)
        updated = await self.repo.update(created.id, {"status": OrderStatus.DONE.value})
        self.assertEqual(updated.status, OrderStatus.DONE)

    async def test_select_count(self):
        await self.repo.create(self._order(), total_amount=2.0)
        count = await self.repo.select_count(
            customer_id=None,
            status=OrderStatus.PENDING,
            payment_status=[],
            delivery_type=None,
            tags=None,
            start_date=None,
            end_date=None,
            min_total_amount=None,
            max_total_amount=None,
        )
        self.assertEqual(count, 1)

    async def test_select_all_pagination(self):
        day = UTCDateTime.now()
        await self.repo.create(self._order(order_date=day), total_amount=2.0)
        await self.repo.create(self._order(order_date=day - timedelta(days=1)), total_amount=2.0)
        results = await self.repo.select_all(
            customer_id=None,
            status=OrderStatus.PENDING,
            payment_status=[],
            delivery_type=None,
            tags=None,
            start_date=None,
            end_date=None,
            min_total_amount=None,
            max_total_amount=None,
            order_by=None,
            ignore_default_filters=True,
            page=1,
            page_size=1,
        )
        self.assertEqual(len(results), 1)

    async def test_delete_by_id(self):
        created = await self.repo.create(self._order(), total_amount=2.0)
        await self.repo.delete_by_id(id=created.id)
        self.assertEqual(OrderModel.objects(is_active=True).count(), 0)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_create_order_with_additionals(self):
        additional = StoredAdditionalItem(
            item_id="a1",
            quantity=1,
            label="Extra",
            unit_price=1.0,
            unit_cost=0.5,
            consumption_factor=1.0,
        )
        prod = StoredProduct(
            product_id="p1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=1,
            additionals=[additional],
        )
        delivery = Delivery(delivery_type=DeliveryType.WITHDRAWAL)
        now = UTCDateTime.now()
        order = Order(
            customer_id=None,
            status=OrderStatus.PENDING,
            products=[prod],
            tags=["tag1"],
            delivery=delivery,
            preparation_date=now,
            order_date=now,
            description="desc",
            additional=0,
            discount=0,
        )
        created = await self.repo.create(order=order, total_amount=3.0)
        self.assertEqual(created.products[0].additionals[0].label, "Extra")
