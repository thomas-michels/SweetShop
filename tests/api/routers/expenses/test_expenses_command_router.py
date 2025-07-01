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
from app.crud.expenses.models import ExpenseModel
from tests.payloads import USER_IN_DB


class TestExpensesCommandRouter(unittest.TestCase):
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
            display_name="Max expenses",
            display_value="1",
            name=Feature.MAX_EXPANSES,
            value="2",
            plan_id=str(ObjectId()),
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

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

    @unittest.mock.patch("app.crud.expenses.services.get_plan_feature")
    def test_post_expense_success(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy(update={"value": "-"})

        response = self.test_client.post(
            url="/api/expenses",
            json={
                "name": "Market",
                "expenseDate": str(UTCDateTime.now()),
                "paymentDetails": [
                    {"method": "CASH", "paymentDate": str(UTCDateTime.now()), "amount": 5}
                ],
                "tags": []
            },
            headers={"organization-id": "org_123"},
        )

        json = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json["message"], "Expense created with success")
        self.assertIsNotNone(json["data"]["id"])
        self.assertEqual(json["data"]["totalPaid"], 5)

    @unittest.mock.patch("app.crud.expenses.services.get_plan_feature")
    def test_post_expense_failure_due_to_limit(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy()

        self.insert_mock_expense(name="A")
        self.insert_mock_expense(name="B")

        response = self.test_client.post(
            url="/api/expenses",
            json={
                "name": "C",
                "expenseDate": str(UTCDateTime.now()),
                "paymentDetails": [
                    {"method": "CASH", "paymentDate": str(UTCDateTime.now()), "amount": 5}
                ],
                "tags": []
            },
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("Maximum number of expenses", response.json()["message"])

    def test_put_expense_success(self):
        expense_id = self.insert_mock_expense(name="Old")

        response = self.test_client.put(
            f"/api/expenses/{expense_id}",
            json={"name": "Updated"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Expense updated with success")

    def test_put_expense_failure(self):
        response = self.test_client.put(
            "/api/expenses/invalid",
            json={"name": "Fail"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Expense #invalid not found")

    def test_delete_expense_success(self):
        expense_id = self.insert_mock_expense(name="Del")

        response = self.test_client.delete(
            f"/api/expenses/{expense_id}", headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Expense deleted with success")

    def test_delete_expense_not_found(self):
        response = self.test_client.delete(
            "/api/expenses/9999", headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Expense #9999 not found")

