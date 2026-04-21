import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.composers import order_composer
from app.api.composers.pre_order_composite import pre_order_composer
from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.orders.schemas import (
    Delivery,
    DeliveryType,
    OrderInDB,
    OrderStatus,
)
from app.crud.pre_orders.schemas import PreOrderStatus
from app.crud.shared_schemas.payment import PaymentStatus
from tests.payloads import USER_IN_DB


class TestOrdersCommandRouter(unittest.TestCase):
    def setUp(self):
        self.test_client = TestClient(app)
        app.dependency_overrides[decode_jwt] = lambda: USER_IN_DB
        app.dependency_overrides[check_current_organization] = lambda: "org_123"
        app.user_middleware.clear()

    def tearDown(self):
        app.dependency_overrides = {}

    def _order_in_db(self, status: OrderStatus) -> OrderInDB:
        now = UTCDateTime.now()
        return OrderInDB(
            id="ord_123",
            organization_id="org_123",
            customer_id="cus_123",
            status=status,
            payment_status=PaymentStatus.PENDING,
            products=[],
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=now,
            order_date=now,
            description=None,
            additional=0,
            discount=0,
            reason_id=None,
            tax=0,
            total_amount=10,
            payments=[],
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def test_put_order_prepared_syncs_pre_order_status(self):
        order_services = AsyncMock()
        pre_order_services = AsyncMock()
        order_services.update.return_value = self._order_in_db(OrderStatus.PREPARED)
        pre_order_services.search_by_order_id.return_value = SimpleNamespace(
            id="pre_123"
        )

        app.dependency_overrides[order_composer] = lambda: order_services
        app.dependency_overrides[pre_order_composer] = lambda: pre_order_services

        response = self.test_client.put(
            "/api/orders/ord_123",
            json={"status": "PREPARED"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "PREPARED")
        pre_order_services.search_by_order_id.assert_awaited_once_with(
            order_id="ord_123"
        )
        pre_order_services.update_status.assert_awaited_once_with(
            pre_order_id="pre_123",
            order_id="ord_123",
            new_status=PreOrderStatus.PREPARED,
        )

    def test_put_order_in_preparation_does_not_sync_pre_order_status(self):
        order_services = AsyncMock()
        pre_order_services = AsyncMock()
        order_services.update.return_value = self._order_in_db(
            OrderStatus.IN_PREPARATION
        )

        app.dependency_overrides[order_composer] = lambda: order_services
        app.dependency_overrides[pre_order_composer] = lambda: pre_order_services

        response = self.test_client.put(
            "/api/orders/ord_123",
            json={"status": "IN_PREPARATION"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "IN_PREPARATION")
        pre_order_services.search_by_order_id.assert_not_awaited()
        pre_order_services.update_status.assert_not_awaited()
