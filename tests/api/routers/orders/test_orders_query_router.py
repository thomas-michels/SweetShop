import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers.order_composite import order_composer
from app.application import app
from app.crud.orders.schemas import (
    Delivery,
    DeliveryType,
    OrderInDB,
    OrderStatus,
    StoredProduct,
)
from app.crud.shared_schemas.payment import PaymentStatus
from app.core.utils.utc_datetime import UTCDateTime


class TestOrdersQueryRouter(unittest.TestCase):
    def setUp(self):
        def override_dependency(mock):
            def _dependency():
                return mock
            return _dependency

        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)

        self.test_client = TestClient(app)

        self.order = OrderInDB(
            id="ord1",
            organization_id="org_123",
            customer_id="cus1",
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            products=[
                StoredProduct(
                    product_id="p1",
                    name="Cake",
                    unit_price=2.0,
                    unit_cost=1.0,
                    quantity=1,
                )
            ],
            tags=[],
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            preparation_date=UTCDateTime.now(),
            order_date=UTCDateTime.now(),
            total_amount=10,
            description=None,
            additional=0,
            discount=0,
            payments=[],
            tax=0,
            reason_id=None,
            is_active=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

        self.service = SimpleNamespace(
            search_all=AsyncMock(return_value=[self.order]),
            search_count=AsyncMock(return_value=1),
            search_by_id=AsyncMock(return_value=self.order),
        )

        app.dependency_overrides[decode_jwt] = override_dependency({})
        app.dependency_overrides[check_current_organization] = override_dependency("org_123")
        app.dependency_overrides[order_composer] = override_dependency(self.service)
        app.user_middleware.clear()

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def test_get_orders_with_results(self):
        response = self.test_client.get(
            "/api/orders",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Orders found with success")
        self.assertEqual(len(response.json()["data"]), 1)

    def test_get_orders_empty_returns_204(self):
        self.service.search_all.return_value = []
        self.service.search_count.return_value = 0
        response = self.test_client.get(
            "/api/orders",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 204)

    def test_get_order_by_id_success(self):
        response = self.test_client.get(
            "/api/orders/ord1",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["id"], "ord1")
        self.assertEqual(response.json()["message"], "Order found with success")

    def test_get_order_by_id_not_found(self):
        self.service.search_by_id.return_value = None
        response = self.test_client.get(
            "/api/orders/missing",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Pedido missing não encontrado")
