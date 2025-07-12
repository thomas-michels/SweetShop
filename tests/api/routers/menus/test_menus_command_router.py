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
from app.crud.menus.models import MenuModel
from tests.payloads import USER_IN_DB


class TestMenusCommandRouter(unittest.TestCase):
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
            display_name="Display menu",
            display_value="true",
            name=Feature.DISPLAY_MENU,
            value="true",
            plan_id=str(ObjectId()),
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )
        app.user_middleware.clear()

    def tearDown(self) -> None:
        disconnect()
        app.dependency_overrides = {}

    def insert_mock_menu(self, name="Menu"):
        menu = MenuModel(name=name, description="d", organization_id="org_123")
        menu.save()
        return str(menu.id)

    @unittest.mock.patch("app.crud.menus.services.get_plan_feature")
    def test_post_menu_success(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy(update={"value": "true"})
        response = self.test_client.post(
            url="/api/menus",
            json={"name": "Menu 1", "description": "d"},
            headers={"organization-id": "org_123"},
        )
        json = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json["message"], "Menu created with success")
        self.assertIsNotNone(json["data"]["id"])

    @unittest.mock.patch("app.crud.menus.services.get_plan_feature")
    def test_post_menu_unauthorized(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy(update={"value": "false"})
        response = self.test_client.post(
            url="/api/menus",
            json={"name": "Menu 1", "description": "d"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 403)

    def test_put_menu_success(self):
        menu_id = self.insert_mock_menu(name="Old")
        response = self.test_client.put(
            f"/api/menus/{menu_id}",
            json={"name": "Updated"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Menu updated with success")

    def test_put_menu_failure(self):
        response = self.test_client.put(
            "/api/menus/invalid",
            json={"name": "Fail"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Menu #invalid not found")

    def test_delete_menu_success(self):
        menu_id = self.insert_mock_menu(name="Del")
        response = self.test_client.delete(
            f"/api/menus/{menu_id}", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Menu deleted with success")

    def test_delete_menu_not_found(self):
        response = self.test_client.delete(
            "/api/menus/9999", headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Menu #9999 not found")

    def test_post_menu_invalid_payload_returns_422(self):
        response = self.test_client.post(
            url="/api/menus",
            json={"name": "Only"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_menu_invalid_payload_returns_422(self):
        menu_id = self.insert_mock_menu(name="Invalid")
        response = self.test_client.put(
            f"/api/menus/{menu_id}",
            json={"isVisible": "invalid"},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)
