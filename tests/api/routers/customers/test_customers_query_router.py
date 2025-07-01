import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.crud.customers.models import CustomerModel
from app.core.utils.utc_datetime import UTCDateTime
from tests.payloads import USER_IN_DB


class TestCustomersQueryRouter(unittest.TestCase):
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

    def insert_mock_customer(self, name="Customer"):
        customer = CustomerModel(
            name=name,
            organization_id="org_123",
            addresses=[],
            tags=[],
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        customer.save()
        return str(customer.id)

    def test_get_customer_by_id_success(self):
        cust_id = self.insert_mock_customer(name="By ID")
        response = self.test_client.get(
            f"/api/customers/{cust_id}",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "By ID")
        self.assertEqual(response.json()["message"], "Cliente encontrado")

    def test_get_customer_by_id_not_found(self):
        response = self.test_client.get(
            "/api/customers/000000000000000000000000",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["message"],
            "Cliente com o ID #000000000000000000000000 não foi encontrado",
        )

    def test_get_customers_with_results(self):
        self.insert_mock_customer(name="A")
        self.insert_mock_customer(name="B")
        response = self.test_client.get(
            "/api/customers",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Clientes encontrados com sucesso")
        self.assertGreaterEqual(len(response.json()["data"]), 2)

    def test_get_customers_empty_returns_204(self):
        response = self.test_client.get(
            "/api/customers",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 204)

    def test_get_customers_expand_tags(self):
        from app.crud.tags.models import TagModel
        tag = TagModel(name="Tag1", organization_id="org_123")
        tag.save()
        customer = CustomerModel(
            name="With Tag",
            organization_id="org_123",
            addresses=[],
            tags=[tag.id],
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
            is_active=True,
        )
        customer.save()
        response = self.test_client.get(
            "/api/customers?expand=tags",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["tags"][0]["name"], "Tag1")

    def test_get_customers_count(self):
        self.insert_mock_customer(name="One")
        response = self.test_client.get(
            "/api/customers/metrics/count",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Contagem de clientes feita com sucesso")
        self.assertEqual(response.json()["data"], 1)
