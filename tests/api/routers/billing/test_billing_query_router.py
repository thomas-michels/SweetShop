import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers import billing_composer
from app.application import app
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.billing.services import BillingServices
from app.crud.billing.schemas import (
    Billing,
    DailySale,
    ExpanseCategory,
    ProductProfit,
    SellingProduct,
)
from tests.payloads import USER_IN_DB


class TestBillingQueryRouter(unittest.TestCase):
    def setUp(self):
        def override_dependency(mock):
            def _dependency():
                return mock
            return _dependency

        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)
        self.test_client = TestClient(app)

        app.dependency_overrides[decode_jwt] = override_dependency(USER_IN_DB)
        app.dependency_overrides[check_current_organization] = override_dependency(
            "org_123"
        )
        app.user_middleware.clear()

    def tearDown(self):
        disconnect()
        app.dependency_overrides = {}

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature")
    def test_get_dashboard_billings_success(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        now = UTCDateTime.now()

        mock_order_services = AsyncMock()
        mock_expense_services = AsyncMock()
        mock_fast_order_services = AsyncMock()
        mock_order_services.search_all_without_filters.return_value = []
        mock_expense_services.search_all.return_value = []

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=mock_order_services,
            fast_order_services=mock_fast_order_services,
            expenses_services=mock_expense_services,
        )

        # Patch methods to return a Billing instance with known values
        billing = Billing(
            month=now.month,
            year=now.year,
            total_amount=10,
            total_expanses=2,
            payment_received=8,
            cash_received=5,
            pix_received=3,
        )
        service.get_billing_for_dashboard = AsyncMock(return_value=billing)

        def override_service():
            return service

        app.dependency_overrides[billing_composer] = override_service

        response = self.test_client.get(
            f"/api/billings/dashboard?monthYear={now.month}/{now.year}",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(
            json["message"], "Billings for dashboard found with success"
        )
        self.assertEqual(json["data"]["totalAmount"], 10)

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature")
    def test_get_monthly_billings_success(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=AsyncMock(),
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        service.get_monthly_billings = AsyncMock(
            return_value=[Billing(month=1, year=2024, total_amount=5)]
        )

        app.dependency_overrides[billing_composer] = lambda: service

        response = self.test_client.get(
            "/api/billings/monthly?lastMonths=1",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["message"], "Monthly Billings found with success")
        self.assertEqual(len(json["data"]), 1)

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature")
    def test_get_best_selling_products_success(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=AsyncMock(),
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        service.get_best_selling_products = AsyncMock(
            return_value=[SellingProduct(product_id="p1", product_name="Prod1", quantity=2)]
        )

        app.dependency_overrides[billing_composer] = lambda: service

        response = self.test_client.get(
            "/api/billings/products?monthYear=5/2024",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["message"], "Best selling products found with success")
        self.assertEqual(json["data"][0]["productId"], "p1")

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature")
    def test_get_expanses_categories_success(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=AsyncMock(),
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        service.get_expanses_categories = AsyncMock(
            return_value=[ExpanseCategory(tag_id="t1", tag_name="Tag1", total_paid=30)]
        )

        app.dependency_overrides[billing_composer] = lambda: service

        response = self.test_client.get(
            "/api/billings/expenses/categories?monthYear=5/2024",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["message"], "Expanses categories found with success")
        self.assertEqual(json["data"][0]["totalPaid"], 30)

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature")
    def test_get_products_profit_success(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=AsyncMock(),
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        service.get_products_profit = AsyncMock(
            return_value=[
                ProductProfit(
                    product_id="p1",
                    product_name="Prod1",
                    total_amount=50,
                    total_profit=20,
                    quantity=5,
                )
            ]
        )

        app.dependency_overrides[billing_composer] = lambda: service

        response = self.test_client.get(
            "/api/billings/products/profit?monthYear=5/2024",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["message"], "Products profit found with success")
        self.assertEqual(json["data"][0]["totalProfit"], 20)

    @patch("app.crud.billing.services.RedisManager")
    @patch("app.crud.billing.services.get_plan_feature")
    def test_get_daily_sales_success(self, mock_plan, mock_redis):
        mock_plan.return_value = SimpleNamespace(value="true")
        mock_redis.return_value.get_value.return_value = None

        service = BillingServices(
            product_repository=AsyncMock(),
            order_services=AsyncMock(),
            fast_order_services=AsyncMock(),
            expenses_services=AsyncMock(),
        )

        service.get_daily_sales = AsyncMock(
            return_value=[DailySale(day=1, total_amount=100)]
        )

        app.dependency_overrides[billing_composer] = lambda: service

        response = self.test_client.get(
            "/api/billings/sales/daily?monthYear=5/2024",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["message"], "Daily Sales found with success")
        self.assertEqual(json["data"][0]["totalAmount"], 100)
