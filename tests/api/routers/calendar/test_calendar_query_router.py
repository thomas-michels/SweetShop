import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.core.utils.utc_datetime import UTCDateTime
from app.core.utils.features import Feature
from app.crud.orders.models import OrderModel
from app.crud.orders.schemas import DeliveryType, OrderStatus, PaymentStatus
from app.crud.customers.models import CustomerModel
from app.crud.customers.repositories import CustomerRepository
from app.crud.plan_features.schemas import PlanFeatureInDB
from bson import ObjectId
from tests.payloads import USER_IN_DB


original_select_by_ids = CustomerRepository.select_by_ids


class TestCalendarQueryRouter(unittest.TestCase):
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

        self.mock_feature = PlanFeatureInDB(
            id=str(ObjectId()),
            additional_price=0,
            allow_additional=False,
            display_name="Display calendar",
            display_value="true",
            name=Feature.DISPLAY_CALENDAR,
            value="true",
            plan_id=str(ObjectId()),
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

        pipeline = [{"$addFields": {"id": "$_id", "payments": []}}, {"$project": {"_id": 0}}]
        patcher = patch("app.crud.orders.models.OrderModel.get_payments", return_value=pipeline)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def insert_order(self, name: str, day: int):
        customer = CustomerModel(name=name, organization_id="org_123")
        customer.save()

        order = OrderModel(
            organization_id="org_123",
            customer_id=str(customer.id),
            status=OrderStatus.PENDING.value,
            payment_status=PaymentStatus.PENDING.value,
            products=[
                {
                    "product_id": "p1",
                    "name": "Prod",
                    "unit_cost": 1.0,
                    "unit_price": 2.0,
                    "quantity": 1,
                }
            ],
            tags=[],
            delivery={"delivery_type": DeliveryType.WITHDRAWAL.value},
            preparation_date=UTCDateTime.now(),
            order_date=UTCDateTime(2023, 9, day),
            total_amount=10.0,
        )
        order.save()

    @patch("app.crud.calendar.services.get_plan_feature", new_callable=AsyncMock)
    @patch("app.crud.orders.services.CustomerRepository.select_by_ids", new_callable=AsyncMock)
    @patch("app.crud.orders.services.CustomerRepository.select_by_id", new_callable=AsyncMock)
    def test_get_calendar_avoids_n_plus_one(
        self, mock_select_by_id, mock_select_by_ids, mock_get_plan_feature
    ):
        async def side_effect_select_by_ids(ids):
            repo = CustomerRepository(organization_id="org_123")
            return await original_select_by_ids(repo, ids)

        mock_select_by_ids.side_effect = side_effect_select_by_ids
        mock_select_by_id.side_effect = Exception("select_by_id should not be called")
        mock_get_plan_feature.return_value = self.mock_feature

        self.insert_order("Alice", 1)
        self.insert_order("Bob", 2)

        response = self.test_client.get(
            "/api/calendars?monthYear=9/2023",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual({d["customerName"] for d in data}, {"Alice", "Bob"})
        self.assertEqual(mock_select_by_id.await_count, 0)
        self.assertEqual(mock_select_by_ids.await_count, 1)

