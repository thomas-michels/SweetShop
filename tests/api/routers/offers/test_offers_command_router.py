import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.crud.products.models import ProductModel
from tests.payloads import USER_IN_DB


class TestOffersCommandRouter(unittest.TestCase):
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

    def create_offer(self, name="Combo"):
        prod_id = self.insert_mock_product()
        response = self.test_client.post(
            "/api/offers",
            json={
                "name": name,
                "description": "desc",
                "products": [prod_id],
            },
            headers={"organization-id": "org_123"},
        )
        return response.json()["data"]["id"]

    def test_post_offer_success(self):
        prod_id = self.insert_mock_product()
        response = self.test_client.post(
            "/api/offers",
            json={
                "name": "Combo",
                "description": "desc",
                "products": [prod_id],
            },
            headers={"organization-id": "org_123"},
        )
        json = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json["message"], "Offer created with success")
        self.assertIsNotNone(json["data"]["id"])

    def test_post_offer_invalid_payload_returns_422(self):
        response = self.test_client.post(
            "/api/offers",
            json={"name": "Only"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_offer_success(self):
        offer_id = self.create_offer(name="Old")
        response = self.test_client.put(
            f"/api/offers/{offer_id}",
            json={"name": "New"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Offer updated with success")

    def test_put_offer_not_found(self):
        response = self.test_client.put(
            "/api/offers/invalid",
            json={"name": "Fail"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Offer #invalid not found")

    def test_put_offer_invalid_payload_returns_422(self):
        offer_id = self.create_offer(name="Invalid")
        response = self.test_client.put(
            f"/api/offers/{offer_id}",
            json={"products": []},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

    def test_delete_offer_success(self):
        offer_id = self.create_offer(name="Del")
        response = self.test_client.delete(
            f"/api/offers/{offer_id}", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Offer deleted with success")

    def test_delete_offer_not_found(self):
        response = self.test_client.delete(
            "/api/offers/invalid", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Offer #invalid not found")
