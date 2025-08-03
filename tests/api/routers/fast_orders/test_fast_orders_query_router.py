import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from fastapi.responses import JSONResponse

from datetime import datetime


def build_response(status_code, message, data=None):
    return JSONResponse(status_code=status_code, content={"message": message, "data": data})


def build_list_response(status_code, message, pagination, data=None):
    return JSONResponse(
        status_code=status_code,
        content={"message": message, "pagination": pagination, "data": data},
    )


def pagination_parameters():
    return {"page": 1, "page_size": 10}


class Paginator:
    def __init__(self, request=None, pagination=None):
        self.pagination = pagination or {"page": 1, "page_size": 10}

    def set_total(self, total):
        self.pagination["total"] = total


class TestFastOrdersQueryRouter(unittest.TestCase):
    def setUp(self):
        def override_dependency(mock):
            def _dependency():
                return mock
            return _dependency

        self.original_dependencies = sys.modules.get("app.api.dependencies")
        self.original_composers = sys.modules.get("app.api.composers")
        self.original_app = sys.modules.get("app")

        async def decode_jwt(*args, **kwargs):
            return {}

        fake_dep = types.ModuleType("app.api.dependencies")
        fake_dep.__path__ = []
        fake_dep.build_response = build_response
        fake_dep.build_list_response = build_list_response
        fake_dep.decode_jwt = decode_jwt
        fake_dep.pagination_parameters = pagination_parameters
        fake_dep.Paginator = Paginator
        sys.modules["app.api.dependencies"] = fake_dep
        bucket = types.ModuleType("app.api.dependencies.bucket")
        bucket.S3BucketManager = type("S3BucketManager", (), {})
        sys.modules["app.api.dependencies.bucket"] = bucket
        response_module = types.ModuleType("app.api.dependencies.response")
        response_module.build_response = build_response
        response_module.build_list_response = build_list_response
        sys.modules["app.api.dependencies.response"] = response_module
        email_sender = types.ModuleType("app.api.dependencies.email_sender")
        email_sender.send_email = lambda *args, **kwargs: None
        sys.modules["app.api.dependencies.email_sender"] = email_sender
        plan_feature = types.ModuleType("app.api.dependencies.get_plan_feature")
        plan_feature.get_plan_feature = lambda *args, **kwargs: None
        sys.modules["app.api.dependencies.get_plan_feature"] = plan_feature
        pagination_module = types.ModuleType("app.api.dependencies.pagination_parameters")
        pagination_module.pagination_parameters = pagination_parameters
        sys.modules["app.api.dependencies.pagination_parameters"] = pagination_module
        paginator_module = types.ModuleType("app.api.dependencies.paginator")
        paginator_module.Paginator = Paginator
        sys.modules["app.api.dependencies.paginator"] = paginator_module

        fake_image_validator = types.ModuleType("app.core.utils.image_validator")
        fake_image_validator.validate_image_file = lambda *args, **kwargs: None
        sys.modules["app.core.utils.image_validator"] = fake_image_validator

        fake_resize_image = types.ModuleType("app.core.utils.resize_image")
        fake_resize_image.resize_image = lambda *args, **kwargs: None
        sys.modules["app.core.utils.resize_image"] = fake_resize_image

        async def fast_order_composer():
            return None

        fake_composers = types.ModuleType("app.api.composers")
        fake_composers.fast_order_composer = fast_order_composer
        sys.modules["app.api.composers"] = fake_composers

        fake_app = types.ModuleType("app")
        fake_app.__path__ = [str(Path("app").resolve())]
        sys.modules["app"] = fake_app

        import importlib.util

        spec_cmd = importlib.util.spec_from_file_location(
            "command_routers", "app/api/routers/fast_orders/command_routers.py"
        )
        command_module = importlib.util.module_from_spec(spec_cmd)
        spec_cmd.loader.exec_module(command_module)
        command_router = command_module.router

        spec_query = importlib.util.spec_from_file_location(
            "query_routers", "app/api/routers/fast_orders/query_routers.py"
        )
        query_module = importlib.util.module_from_spec(spec_query)
        spec_query.loader.exec_module(query_module)
        query_router = query_module.router

        self.app = FastAPI()
        self.app.include_router(command_router, prefix="/api")
        self.app.include_router(query_router, prefix="/api")

        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)
        self.test_client = TestClient(self.app)

        now = datetime.utcnow().isoformat()
        self.fast_order = {
            "id": "fo1",
            "organizationId": "org_123",
            "products": [
                {
                    "productId": "p1",
                    "name": "Cake",
                    "unitPrice": 2.0,
                    "unitCost": 1.0,
                    "quantity": 1,
                }
            ],
            "orderDate": now,
            "description": None,
            "additional": 0,
            "discount": 0,
            "totalAmount": 10,
            "payments": [],
            "isActive": True,
            "createdAt": now,
            "updatedAt": now,
        }

        self.service = SimpleNamespace(
            search_all=AsyncMock(return_value=[self.fast_order]),
            search_count=AsyncMock(return_value=1),
            search_by_id=AsyncMock(return_value=self.fast_order),
        )

        self.app.dependency_overrides[decode_jwt] = override_dependency({})
        self.app.dependency_overrides[fast_order_composer] = override_dependency(self.service)

    def tearDown(self) -> None:
        disconnect()
        self.app.dependency_overrides = {}
        if self.original_dependencies is not None:
            sys.modules["app.api.dependencies"] = self.original_dependencies
        else:
            del sys.modules["app.api.dependencies"]
        if "app.api.dependencies.bucket" in sys.modules:
            del sys.modules["app.api.dependencies.bucket"]
        if "app.api.dependencies.email_sender" in sys.modules:
            del sys.modules["app.api.dependencies.email_sender"]
        if "app.api.dependencies.get_plan_feature" in sys.modules:
            del sys.modules["app.api.dependencies.get_plan_feature"]
        if "app.api.dependencies.pagination_parameters" in sys.modules:
            del sys.modules["app.api.dependencies.pagination_parameters"]
        if "app.api.dependencies.paginator" in sys.modules:
            del sys.modules["app.api.dependencies.paginator"]
        if "app.api.dependencies.response" in sys.modules:
            del sys.modules["app.api.dependencies.response"]
        if "app.core.utils.image_validator" in sys.modules:
            del sys.modules["app.core.utils.image_validator"]
        if "app.core.utils.resize_image" in sys.modules:
            del sys.modules["app.core.utils.resize_image"]

        if self.original_composers is not None:
            sys.modules["app.api.composers"] = self.original_composers
        else:
            del sys.modules["app.api.composers"]

        if self.original_app is not None:
            sys.modules["app"] = self.original_app
        else:
            del sys.modules["app"]

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
