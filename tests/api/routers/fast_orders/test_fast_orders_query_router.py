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


class TestFastOrdersQueryRouter(unittest.TestCase):
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
            search_all=AsyncMock(return_value=[self.fast_order]),
            search_count=AsyncMock(return_value=1),
            search_by_id=AsyncMock(return_value=self.fast_order),
        )

        app.dependency_overrides[decode_jwt] = override_dependency({})
        app.dependency_overrides[fast_order_composer] = override_dependency(self.service)

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def test_get_fast_orders_with_results(self):
        response = self.test_client.get(
            "/api/fast-orders",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Fast Orders found with success")
        self.assertEqual(len(response.json()["data"]), 1)

    def test_get_fast_orders_empty_returns_204(self):
        self.service.search_all.return_value = []
        self.service.search_count.return_value = 0
        response = self.test_client.get(
            "/api/fast-orders",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 204)

    def test_get_fast_order_by_id_success(self):
        response = self.test_client.get(
            "/api/fast-orders/fo1",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["id"], "fo1")
        self.assertEqual(response.json()["message"], "Fast Order found with success")

    def test_get_fast_order_by_id_not_found(self):
        self.service.search_by_id.return_value = None
        response = self.test_client.get(
            "/api/fast-orders/missing",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["message"],
            "Fast Order missing not found",
        )
