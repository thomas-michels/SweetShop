import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.response import build_response, build_list_response
from app.api.dependencies.pagination_parameters import pagination_parameters
from app.api.dependencies.paginator import Paginator
from app.crud.fast_orders.schemas import FastOrderInDB, StoredProduct
from app.core.utils.utc_datetime import UTCDateTime

# Stub dependency modules
async def decode_jwt(*args, **kwargs):
    return {}

fake_dep = types.ModuleType("app.api.dependencies")
fake_dep.build_response = build_response
fake_dep.build_list_response = build_list_response
fake_dep.decode_jwt = decode_jwt
fake_dep.pagination_parameters = pagination_parameters
fake_dep.Paginator = Paginator
sys.modules["app.api.dependencies"] = fake_dep

async def fast_order_composer():
    return None

fake_composers = types.ModuleType("app.api.composers")
fake_composers.fast_order_composer = fast_order_composer
sys.modules["app.api.composers"] = fake_composers

from app.api.routers.fast_orders.command_routers import router as command_router
from app.api.routers.fast_orders.query_routers import router as query_router

app = FastAPI()
app.include_router(command_router, prefix="/api")
app.include_router(query_router, prefix="/api")


class TestFastOrdersCommandRouter(unittest.TestCase):
    def setUp(self):
        def override_dependency(mock):
            def _dependency():
                return mock
            return _dependency

        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)

        self.test_client = TestClient(app)

        self.fast_order = FastOrderInDB(
            id="fo1",
            organization_id="org_123",
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
            total_amount=10,
            payments=[],
            is_active=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

        self.service = SimpleNamespace(
            create=AsyncMock(return_value=self.fast_order),
            update=AsyncMock(return_value=self.fast_order),
            delete_by_id=AsyncMock(return_value=self.fast_order),
        )

        app.dependency_overrides[decode_jwt] = override_dependency({})
        app.dependency_overrides[fast_order_composer] = override_dependency(self.service)

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def test_post_fast_order_success(self):
        response = self.test_client.post(
            "/api/fast-orders",
            json={
                "products": [{"productId": "p1", "quantity": 1}],
                "orderDate": str(UTCDateTime.now()),
                "additional": 0,
                "discount": 0,
            },
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Fast Order created with success")

    def test_post_fast_order_failure(self):
        self.service.create.return_value = None
        response = self.test_client.post(
            "/api/fast-orders",
            json={
                "products": [{"productId": "p1", "quantity": 1}],
                "orderDate": str(UTCDateTime.now()),
                "additional": 0,
                "discount": 0,
            },
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Some error happened on create a fast order",
        )

    def test_post_fast_order_invalid_payload_returns_422(self):
        response = self.test_client.post(
            "/api/fast-orders",
            json={"products": []},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_fast_order_success(self):
        response = self.test_client.put(
            "/api/fast-orders/fo1",
            json={"description": "new"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Fast Order updated with success")

    def test_put_fast_order_failure(self):
        self.service.update.return_value = None
        response = self.test_client.put(
            "/api/fast-orders/fo1",
            json={"description": "new"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Some error happened on update a fast order",
        )

    def test_put_fast_order_invalid_payload_returns_422(self):
        response = self.test_client.put(
            "/api/fast-orders/fo1",
            json={"additional": -1},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

    def test_delete_fast_order_success(self):
        response = self.test_client.delete(
            "/api/fast-orders/fo1",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Fast Order deleted with success")

    def test_delete_fast_order_not_found(self):
        self.service.delete_by_id.return_value = None
        response = self.test_client.delete(
            "/api/fast-orders/fo1",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["message"],
            "Fast Order fo1 not found",
        )
