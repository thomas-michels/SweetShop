import unittest

from mongoengine import connect, disconnect
import mongomock

from app.crud.fast_orders.repositories import FastOrderRepository
from app.crud.fast_orders.schemas import FastOrder, StoredProduct
from app.crud.orders.models import OrderModel
from app.crud.orders.schemas import DeliveryType, OrderStatus, PaymentStatus
from app.core.exceptions import NotFoundError
from app.core.utils.utc_datetime import UTCDateTime


class TestFastOrderRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = FastOrderRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _order_model(self, order_date: UTCDateTime = UTCDateTime.now()):
        order = OrderModel(
            organization_id="org1",
            status=OrderStatus.DONE.value,
            payment_status=PaymentStatus.PENDING.value,
            products=[
                {
                    "product_id": "p1",
                    "name": "Cake",
                    "unit_price": 2.0,
                    "unit_cost": 1.0,
                    "quantity": 1,
                }
            ],
            tags=[],
            delivery={"delivery_type": DeliveryType.FAST_ORDER.value},
            preparation_date=order_date,
            order_date=order_date,
            total_amount=10,
            additional=0,
            discount=0,
            tax=0,
            is_fast_order=True,
        )
        order.save()
        return order

    async def test_create(self):
        fast_order = FastOrder(
            products=[
                StoredProduct(
                    product_id="p1",
                    name="Cake",
                    unit_price=2.0,
                    unit_cost=1.0,
                    quantity=1,
                )
            ],
            order_date=UTCDateTime.now(),
            description=None,
            additional=0,
            discount=0,
        )
        result = await self.repo.create(fast_order=fast_order, total_amount=10)
        self.assertEqual(result.total_amount, 10)

    async def test_update(self):
        order = await self._order_model()
        updated = await self.repo.update(
            fast_order_id=str(order.id), fast_order={"description": "updated"}
        )
        self.assertEqual(updated.description, "updated")

    async def test_select_by_id_success(self):
        order = await self._order_model()
        result = await self.repo.select_by_id(id=str(order.id))
        self.assertEqual(result.id, str(order.id))

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_count_with_day_filter(self):
        day = UTCDateTime.now()
        await self._order_model(order_date=day)
        await self._order_model(order_date=UTCDateTime(year=2020, month=1, day=1))
        count = await self.repo.select_count(day=day)
        self.assertEqual(count, 1)

    async def test_select_all_with_pagination(self):
        await self._order_model()
        await self._order_model()
        await self._order_model()
        results = await self.repo.select_all(page=1, page_size=2)
        self.assertEqual(len(results), 2)
        results_p2 = await self.repo.select_all(page=2, page_size=2)
        self.assertEqual(len(results_p2), 1)

    async def test_delete_by_id_success(self):
        order = await self._order_model()
        deleted = await self.repo.delete_by_id(id=str(order.id))
        self.assertEqual(deleted.id, str(order.id))
        self.assertEqual(
            OrderModel.objects(is_active=True, is_fast_order=True).count(), 0
        )

    async def test_delete_by_id_not_found(self):
        result = await self.repo.delete_by_id(id="missing")
        self.assertIsNone(result)
