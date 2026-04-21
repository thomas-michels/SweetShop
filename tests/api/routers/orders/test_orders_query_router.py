import unittest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.composers import order_composer
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
from app.crud.shared_schemas.payment import PaymentStatus
from tests.payloads import USER_IN_DB


class TestOrdersQueryRouter(unittest.TestCase):
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

    def test_get_orders_accepts_prepared_status_filter(self):
        order_services = AsyncMock()
        order_services.search_count.return_value = 1
        order_services.search_all.return_value = [
            self._order_in_db(OrderStatus.PREPARED)
        ]

        app.dependency_overrides[order_composer] = lambda: order_services

        response = self.test_client.get(
            "/api/orders?status=PREPARED",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["status"], "PREPARED")
        self.assertEqual(
            order_services.search_count.await_args.kwargs["status"],
            OrderStatus.PREPARED,
        )
        self.assertEqual(
            order_services.search_all.await_args.kwargs["status"],
            OrderStatus.PREPARED,
        )
