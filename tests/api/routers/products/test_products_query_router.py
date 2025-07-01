import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.crud.products.models import ProductModel
from app.crud.tags.models import TagModel
from app.core.utils.utc_datetime import UTCDateTime
from tests.payloads import USER_IN_DB


class TestProductsQueryRouter(unittest.TestCase):
    def setUp(self):
        def override_dependency(mock):
            def _dependency():
                return mock
            return _dependency

        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)
        self.test_client = TestClient(app)

        app.dependency_overrides[decode_jwt] = override_dependency(USER_IN_DB)
        app.dependency_overrides[check_current_organization] = override_dependency("org_123")
        app.user_middleware.clear()

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def insert_mock_product(self, name="Product"):
        product = ProductModel(
            name=name,
            description="desc",
            organization_id="org_123",
            unit_price=10.0,
            unit_cost=5.0,
            tags=[],
        )
        product.save()
        return str(product.id)

    def test_get_product_by_id_success(self):
        prod_id = self.insert_mock_product(name="By ID")
        response = self.test_client.get(
            f"/api/products/{prod_id}",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "By ID")
        self.assertEqual(response.json()["message"], "Product found with success")

    def test_get_product_by_id_not_found(self):
        response = self.test_client.get(
            "/api/products/000000000000000000000000",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Product #000000000000000000000000 not found")

    def test_get_products_with_results(self):
        self.insert_mock_product(name="A")
        self.insert_mock_product(name="B")
        response = self.test_client.get(
            "/api/products",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Products found with success")
        self.assertGreaterEqual(len(response.json()["data"]), 2)

    def test_get_products_empty_returns_204(self):
        response = self.test_client.get(
            "/api/products",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 204)

    def test_get_products_expand_tags(self):
        tag = TagModel(name="Tag1", organization_id="org_123")
        tag.save()
        product = ProductModel(
            name="With Tag",
            description="desc",
            organization_id="org_123",
            unit_price=1.0,
            unit_cost=0.5,
            tags=[tag.id],
        )
        product.save()
        response = self.test_client.get(
            "/api/products?expand=tags",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["tags"][0]["name"], "Tag1")

    def test_get_products_count(self):
        self.insert_mock_product(name="One")
        response = self.test_client.get(
            "/api/products/metrics/count",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Products count found with success")
        self.assertEqual(response.json()["data"], 1)
