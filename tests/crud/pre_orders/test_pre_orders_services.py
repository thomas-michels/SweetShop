import unittest
from unittest.mock import AsyncMock
from mongoengine import connect, disconnect
import mongomock

from app.crud.pre_orders.repositories import PreOrderRepository
from app.crud.pre_orders.services import PreOrderServices
from app.crud.pre_orders.schemas import PreOrderStatus


class DummyOrg:
    international_code = "55"
    ddd = "047"
    phone_number = "123456789"


class TestPreOrderServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = PreOrderRepository(organization_id="org1")
        self.customer_repo = AsyncMock()
        self.offer_repo = AsyncMock()
        self.organization_repo = AsyncMock()
        self.message_services = AsyncMock()
        self.service = PreOrderServices(
            pre_order_repository=repo,
            customer_repository=self.customer_repo,
            offer_repository=self.offer_repo,
            organization_repository=self.organization_repo,
            message_services=self.message_services,
        )

    def tearDown(self):
        disconnect()

    def _pre_order_model(self, code="001", status=PreOrderStatus.PENDING):
        return {
            "organization_id": "org1",
            "code": code,
            "menu_id": "men1",
            "payment_method": "CASH",
            "customer": {"name": "Ted", "ddd": "047", "phone_number": "9988"},
            "delivery": {"delivery_type": "WITHDRAWAL"},
            "offers": [{"offer_id": "off1", "quantity": 1}],
            "status": status.value,
            "tax": 0,
            "total_amount": 10,
        }

    async def test_update_status(self):
        from app.crud.pre_orders.models import PreOrderModel
        pre = PreOrderModel(**self._pre_order_model())
        pre.save()
        self.customer_repo.select_by_phone.return_value = None
        self.organization_repo.select_by_id.return_value = DummyOrg()
        updated = await self.service.update_status(pre.id, PreOrderStatus.ACCEPTED)
        self.assertEqual(updated.status, PreOrderStatus.ACCEPTED)
        self.message_services.create.assert_awaited()

    async def test_search_all(self):
        from app.crud.pre_orders.models import PreOrderModel
        PreOrderModel(**self._pre_order_model(code="A")).save()
        PreOrderModel(**self._pre_order_model(code="B")).save()
        self.customer_repo.select_by_phone.return_value = None
        result = await self.service.search_all()
        self.assertEqual(len(result), 2)

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 2
        service = PreOrderServices(
            pre_order_repository=mock_repo,
            customer_repository=AsyncMock(),
            offer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
            message_services=AsyncMock(),
        )
        count = await service.search_count()
        self.assertEqual(count, 2)
        mock_repo.select_count.assert_awaited()

    async def test_delete_by_id(self):
        from app.crud.pre_orders.models import PreOrderModel
        pre = PreOrderModel(**self._pre_order_model())
        pre.save()
        deleted = await self.service.delete_by_id(pre.id)
        self.assertEqual(deleted.id, pre.id)
