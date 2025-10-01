import unittest
from datetime import timedelta
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.business_days.models import BusinessDayModel
from tests.payloads import USER_IN_DB


class TestBusinessDayRouters(unittest.TestCase):
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

    def create_business_day(self, closes_at: UTCDateTime | str):
        business_day = BusinessDayModel(
            organization_id="org_123",
            menu_id="men_123",
            day=UTCDateTime.now().strftime("%Y-%m-%d"),
            closes_at=UTCDateTime.validate_datetime(closes_at),
        )
        business_day.save()
        return business_day

    def test_put_business_day_creates_new_record(self):
        closes_at = str(UTCDateTime.now())

        response = self.test_client.put(
            url="/api/business_day",
            json={"menu_id": "men_123", "closes_at": closes_at},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["message"], "Business day saved with success")
        self.assertEqual(json["data"]["menuId"], "men_123")
        self.assertEqual(json["data"]["organizationId"], "org_123")

        business_day = BusinessDayModel.objects(organization_id="org_123").first()
        self.assertIsNotNone(business_day)
        self.assertEqual(business_day.menu_id, "men_123")

    def test_get_business_day_returns_record(self):
        business_day = self.create_business_day(closes_at=UTCDateTime.now())

        response = self.test_client.get(
            url="/api/business_day",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["message"], "Business day found with success")
        self.assertEqual(json["data"]["id"], str(business_day.id))

    def test_get_business_day_returns_204_when_not_found(self):
        response = self.test_client.get(
            url="/api/business_day",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 204)
