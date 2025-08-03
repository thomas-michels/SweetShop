import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers.pre_order_composite import pre_order_composer
from app.application import app
from app.crud.pre_orders.schemas import PreOrderInDB, PreOrderStatus, PreOrderCustomer, SelectedOffer
from app.crud.orders.schemas import Delivery, DeliveryType
from app.crud.shared_schemas.payment import PaymentMethod
from app.core.utils.utc_datetime import UTCDateTime


class TestPreOrdersQueryRouter(unittest.TestCase):
    def setUp(self):
        def override_dependency(mock):
            def _dependency():
                return mock
            return _dependency

        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)

        self.test_client = TestClient(app)

        self.pre_order = PreOrderInDB(
            id="pre1",
            organization_id="org_123",
            code="001",
            menu_id="men1",
            payment_method=PaymentMethod.CASH,
            customer=PreOrderCustomer(name="John", ddd="047", phone_number="999"),
            delivery=Delivery(delivery_type=DeliveryType.WITHDRAWAL),
            observation=None,
            offers=[SelectedOffer(offer_id="off1", quantity=1)],
            status=PreOrderStatus.PENDING,
            tax=0,
            total_amount=10,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )

        self.service = SimpleNamespace(
            search_all=AsyncMock(return_value=[self.pre_order]),
            search_count=AsyncMock(return_value=1),
            search_by_id=AsyncMock(return_value=self.pre_order),
        )

        app.dependency_overrides[decode_jwt] = override_dependency({})
        app.dependency_overrides[check_current_organization] = override_dependency("org_123")
        app.dependency_overrides[pre_order_composer] = override_dependency(self.service)
        app.user_middleware.clear()

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def test_get_pre_orders_with_results(self):
        response = self.test_client.get(
            "/api/pre_orders",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Pré pedidos encontrados com sucesso")
        self.assertEqual(len(response.json()["data"]), 1)

    def test_get_pre_orders_empty_returns_204(self):
        self.service.search_all.return_value = []
        self.service.search_count.return_value = 0
        response = self.test_client.get(
            "/api/pre_orders",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 204)

    def test_get_pre_order_by_id_success(self):
        response = self.test_client.get(
            "/api/pre_orders/pre1",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["id"], "pre1")
        self.assertEqual(response.json()["message"], "Pré pedido encontrado com sucesso")

    def test_get_pre_order_by_id_not_found(self):
        self.service.search_by_id.return_value = None
        response = self.test_client.get(
            "/api/pre_orders/missing",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Pré pedido encontrado não encontrado")
