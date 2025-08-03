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


class TestOrdersCommandRouter(unittest.TestCase):
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
            create=AsyncMock(return_value=self.order),
            update=AsyncMock(return_value=self.order),
            delete_by_id=AsyncMock(return_value=self.order),
        )

        app.dependency_overrides[decode_jwt] = override_dependency({})
        app.dependency_overrides[check_current_organization] = override_dependency("org_123")
        app.dependency_overrides[order_composer] = override_dependency(self.service)
        app.user_middleware.clear()

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def test_post_order_success(self):
        response = self.test_client.post(
            "/api/orders",
            json={
                "products": [{"productId": "p1", "quantity": 1}],
                "tags": [],
                "delivery": {"deliveryType": "WITHDRAWAL"},
                "preparationDate": str(UTCDateTime.now()),
                "orderDate": str(UTCDateTime.now())
            },
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Order created with success")

    def test_post_order_failure(self):
        self.service.create.return_value = None
        response = self.test_client.post(
            "/api/orders",
            json={
                "products": [{"productId": "p1", "quantity": 1}],
                "tags": [],
                "delivery": {"deliveryType": "WITHDRAWAL"},
                "preparationDate": str(UTCDateTime.now()),
                "orderDate": str(UTCDateTime.now())
            },
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Erro ao criar pedido")

    def test_post_order_invalid_payload_returns_422(self):
        response = self.test_client.post(
            "/api/orders",
            json={"products": []},
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 422)

    def test_put_order_success(self):
        response = self.test_client.put(
            "/api/orders/ord1",
            json={"status": "DONE"},
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Order updated with success")

    def test_put_order_failure(self):
        self.service.update.return_value = None
        response = self.test_client.put(
            "/api/orders/ord1",
            json={"status": "DONE"},
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Erro ao atualizar pedido")

    def test_put_order_invalid_payload_returns_422(self):
        response = self.test_client.put(
            "/api/orders/ord1",
            json={"additional": -1},
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 422)

    def test_delete_order_success(self):
        response = self.test_client.delete(
            "/api/orders/ord1",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Order deleted with success")

    def test_delete_order_not_found(self):
        self.service.delete_by_id.return_value = None
        response = self.test_client.delete(
            "/api/orders/ord1",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Pedido ord1 não encontrado")
