import unittest

from mongoengine import connect, disconnect
import mongomock

from app.crud.pre_orders.models import PreOrderModel
from app.crud.pre_orders.repositories import PreOrderRepository
from app.crud.pre_orders.schemas import PreOrderStatus
from app.crud.shared_schemas.payment import PaymentMethod
from app.core.exceptions import NotFoundError


class TestPreOrderRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = PreOrderRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _pre_order_model(self, code="001", status=PreOrderStatus.PENDING):
        pre_order = PreOrderModel(
            organization_id="org1",
            code=code,
            menu_id="men1",
            payment_method=PaymentMethod.CASH.value,
            customer={
                "name": "John",
                "ddd": "047",
                "international_code": "55",
                "phone_number": "999",
            },
            delivery={"delivery_type": "WITHDRAWAL"},
            offers=[{"offer_id": "off1", "quantity": 1}],
            status=status.value,
            tax=0,
            total_amount=10,
        )
        pre_order.save()
        return pre_order

    async def test_update_status(self):
        pre_order = await self._pre_order_model()
        result = await self.repo.update_status(
            pre_order_id=str(pre_order.id), new_status=PreOrderStatus.ACCEPTED
        )
        self.assertEqual(result.status, PreOrderStatus.ACCEPTED)

    async def test_select_by_id_success(self):
        pre_order = await self._pre_order_model(code="123")
        result = await self.repo.select_by_id(id=str(pre_order.id))
        self.assertEqual(result.code, "123")

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_count_with_filters(self):
        await self._pre_order_model(status=PreOrderStatus.PENDING)
        await self._pre_order_model(status=PreOrderStatus.ACCEPTED, code="ABC123")
        count_status = await self.repo.select_count(status=PreOrderStatus.PENDING)
        self.assertEqual(count_status, 1)
        count_code = await self.repo.select_count(code="ABC")
        self.assertEqual(count_code, 1)

    async def test_select_all_with_pagination(self):
        await self._pre_order_model(code="A")
        await self._pre_order_model(code="B")
        await self._pre_order_model(code="C")
        results = await self.repo.select_all(page=1, page_size=2)
        self.assertEqual(len(results), 2)
        results_p2 = await self.repo.select_all(page=2, page_size=2)
        self.assertEqual(len(results_p2), 1)

    async def test_delete_by_id_success(self):
        pre_order = await self._pre_order_model()
        deleted = await self.repo.delete_by_id(id=str(pre_order.id))
        self.assertEqual(deleted.id, str(pre_order.id))
        self.assertEqual(PreOrderModel.objects(is_active=True).count(), 0)

    async def test_delete_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.delete_by_id(id="missing")
