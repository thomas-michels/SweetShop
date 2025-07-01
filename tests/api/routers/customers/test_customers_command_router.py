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
from app.crud.customers.models import CustomerModel
from tests.payloads import USER_IN_DB


class TestCustomersCommandRouter(unittest.TestCase):
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
            display_name="Max customers",
            display_value="1",
            name=Feature.MAX_CUSTOMERS,
            value="2",
            plan_id=str(ObjectId()),
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

        app.user_middleware.clear()

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def insert_mock_customer(self, name="Customer"):
        cust = CustomerModel(
            name=name,
            organization_id="org_123",
            addresses=[],
            tags=[],
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        cust.save()
        return str(cust.id)

    @unittest.mock.patch("app.crud.customers.services.get_plan_feature")
    def test_post_customer_success(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy(update={"value": "-"})
        response = self.test_client.post(
            url="/api/customers",
            json={"name": "John"},
            headers={"organization-id": "org_123"},
        )
        json = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json["message"], "Cliente criado com sucesso")
        self.assertIsNotNone(json["data"]["id"])
        self.assertEqual(json["data"]["name"], "John")

    @unittest.mock.patch("app.crud.customers.services.get_plan_feature")
    def test_post_customer_failure_due_to_limit(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy()
        self.insert_mock_customer(name="A")
        self.insert_mock_customer(name="B")
        response = self.test_client.post(
            url="/api/customers",
            json={"name": "C"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("Máximo de clientes", response.json()["message"])

    def test_put_customer_success(self):
        cust_id = self.insert_mock_customer(name="Old")
        response = self.test_client.put(
            f"/api/customers/{cust_id}",
            json={"name": "Updated"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Cliente atualizado com sucesso")

    def test_put_customer_failure(self):
        response = self.test_client.put(
            "/api/customers/invalid",
            json={"name": "Fail"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Cliente com o ID #invalid não foi encontrado")

    def test_delete_customer_success(self):
        cust_id = self.insert_mock_customer(name="Del")
        response = self.test_client.delete(
            f"/api/customers/{cust_id}", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Cliente deletado com sucesso")

    def test_delete_customer_not_found(self):
        response = self.test_client.delete(
            "/api/customers/9999", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Cliente com o ID #9999 não foi encontrado")

    def test_post_customer_invalid_payload_returns_422(self):
        response = self.test_client.post(
            url="/api/customers",
            json={"phoneNumber": "123"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_customer_invalid_payload_returns_422(self):
        cust_id = self.insert_mock_customer(name="Fail")
        response = self.test_client.put(
            f"/api/customers/{cust_id}",
            json={"ddd": "01", "phoneNumber": "abc"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)
