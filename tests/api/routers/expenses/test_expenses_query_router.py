import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.crud.expenses.models import ExpenseModel
from app.core.utils.utc_datetime import UTCDateTime
from tests.payloads import USER_IN_DB


class TestExpensesQueryRouter(unittest.TestCase):
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

    def insert_mock_expense(self, name="Expense"):
        expense = ExpenseModel(
            name=name,
            organization_id="org_123",
            expense_date=UTCDateTime.now(),
            total_paid=10.0,
            payment_details=[],
            tags=[],
            is_active=True,
        )
        expense.save()
        return str(expense.id)

    def test_get_expense_by_id_success(self):
        expense_id = self.insert_mock_expense(name="By ID")

        response = self.test_client.get(
            f"/api/expenses/{expense_id}",
            headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "By ID")
        self.assertEqual(response.json()["message"], "Expense found with success")

    def test_get_expense_by_id_not_found(self):
        response = self.test_client.get(
            "/api/expenses/000000000000000000000000",
            headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Expense #000000000000000000000000 not found")

    def test_get_expenses_with_results(self):
        self.insert_mock_expense(name="A")
        self.insert_mock_expense(name="B")

        response = self.test_client.get(
            "/api/expenses",
            headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Expenses found with success")
        self.assertGreaterEqual(len(response.json()["data"]), 2)

    def test_get_expenses_empty_returns_204(self):
        response = self.test_client.get(
            "/api/expenses",
            headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 204)


    def test_get_expenses_expand_tags(self):
        from app.crud.tags.models import TagModel
        tag = TagModel(name="Tag1", organization_id="org_123")
        tag.save()
        expense = ExpenseModel(
            name="With Tag",
            organization_id="org_123",
            expense_date=UTCDateTime.now(),
            total_paid=1.0,
            payment_details=[],
            tags=[tag.id],
            is_active=True,
        )
        expense.save()

        response = self.test_client.get(
            f"/api/expenses?expand=tags",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["tags"][0]["name"], "Tag1")

