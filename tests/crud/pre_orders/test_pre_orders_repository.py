import unittest
from mongoengine import connect, disconnect
import mongomock

from app.core.exceptions import NotFoundError
from app.crud.pre_orders.repositories import PreOrderRepository
from app.crud.pre_orders.models import PreOrderModel
from app.crud.pre_orders.schemas import PreOrderStatus


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

    def _pre_order_model(self, code="001", status=PreOrderStatus.PENDING):
        return PreOrderModel(
            organization_id="org1",
            code=code,
            menu_id="men1",
            payment_method="CASH",
            customer={"name": "Ted", "ddd": "047", "phone_number": "9988"},
            delivery={"delivery_type": "WITHDRAWAL"},
            observation="obs",
            offers=[{"offer_id": "off1", "quantity": 1}],
            products=[],
            status=status.value,
            tax=0,
            total_amount=10,
        )

    async def test_update_status(self):
        model = self._pre_order_model()
        model.save()
        updated = await self.repo.update_status(model.id, PreOrderStatus.ACCEPTED)
        self.assertEqual(updated.status, PreOrderStatus.ACCEPTED)

    async def test_select_count_and_all(self):
        self._pre_order_model(code="A").save()
        self._pre_order_model(code="B", status=PreOrderStatus.ACCEPTED).save()
        count = await self.repo.select_count(status=PreOrderStatus.PENDING)
        self.assertEqual(count, 1)
        all_orders = await self.repo.select_all(page=1, page_size=1)
        self.assertEqual(len(all_orders), 1)

    async def test_delete_by_id(self):
        model = self._pre_order_model()
        model.save()
        await self.repo.delete_by_id(id=model.id)
        self.assertEqual(PreOrderModel.objects(is_active=True).count(), 0)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")
