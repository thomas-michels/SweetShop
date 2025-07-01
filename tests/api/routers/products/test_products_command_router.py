import unittest
from bson import ObjectId
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.core.utils.features import Feature
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.plan_features.schemas import PlanFeatureInDB
from app.crud.products.models import ProductModel
from tests.payloads import USER_IN_DB


class TestProductsCommandRouter(unittest.TestCase):
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

        self.mock_feature = PlanFeatureInDB(
            id=str(ObjectId()),
            additional_price=0,
            allow_additional=False,
            display_name="Max products",
            display_value="1",
            name=Feature.MAX_PRODUCTS,
            value="2",
            plan_id=str(ObjectId()),
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

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

    @unittest.mock.patch("app.crud.products.services.get_plan_feature")
    def test_post_product_success(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy(update={"value": "-"})
        response = self.test_client.post(
            url="/api/products",
            json={
                "name": "Prod",
                "description": "desc",
                "unitPrice": 10.0,
                "unitCost": 5.0,
                "tags": []
            },
            headers={"organization-id": "org_123"},
        )
        json = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json["message"], "Product created with success")
        self.assertIsNotNone(json["data"]["id"])
        self.assertEqual(json["data"]["name"], "Prod")

    @unittest.mock.patch("app.crud.products.services.get_plan_feature")
    def test_post_product_failure_due_to_limit(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy()
        self.insert_mock_product(name="A")
        self.insert_mock_product(name="B")
        response = self.test_client.post(
            url="/api/products",
            json={
                "name": "C",
                "description": "desc",
                "unitPrice": 10.0,
                "unitCost": 5.0,
                "tags": []
            },
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("Maximum number of products", response.json()["message"])

    def test_put_product_success(self):
        prod_id = self.insert_mock_product(name="Old")
        response = self.test_client.put(
            f"/api/products/{prod_id}",
            json={"name": "Updated"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Product updated with success")

    def test_put_product_failure(self):
        response = self.test_client.put(
            "/api/products/invalid",
            json={"name": "Fail"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Product #invalid not found")

    def test_delete_product_success(self):
        prod_id = self.insert_mock_product(name="Del")
        response = self.test_client.delete(
            f"/api/products/{prod_id}", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Product deleted with success")

    def test_delete_product_not_found(self):
        response = self.test_client.delete(
            "/api/products/9999", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Product #9999 not found")

    def test_post_product_invalid_payload_returns_422(self):
        response = self.test_client.post(
            url="/api/products",
            json={"name": "Only"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_product_invalid_payload_returns_422(self):
        prod_id = self.insert_mock_product(name="Invalid")
        response = self.test_client.put(
            f"/api/products/{prod_id}",
            json={"unitPrice": "invalid"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)
