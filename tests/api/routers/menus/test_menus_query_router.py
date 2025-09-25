import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.core.utils import slugify
from app.crud.menus.models import MenuModel
from tests.payloads import USER_IN_DB


class TestMenusQueryRouter(unittest.TestCase):
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

    def insert_mock_menu(self, name="Menu"):
        menu = MenuModel(
            name=name,
            slug=slugify(name),
            description="d",
            organization_id="org_123",
        )
        menu.save()
        return str(menu.id)

    def test_get_menu_by_id_success(self):
        menu_id = self.insert_mock_menu(name="By ID")
        response = self.test_client.get(
            f"/api/menus/{menu_id}",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "By ID")
        self.assertFalse(response.json()["data"]["acceptsOutsideBusinessHours"])
        self.assertEqual(response.json()["message"], "Menu found with success")

    def test_get_menu_by_id_not_found(self):
        response = self.test_client.get(
            "/api/menus/000000000000000000000000",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Menu #000000000000000000000000 not found")

    def test_get_menus_empty_returns_204(self):
        response = self.test_client.get(
            "/api/menus",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 204)

    def test_get_menus_query_no_results_returns_204(self):
        self.insert_mock_menu(name="Only")
        response = self.test_client.get(
            "/api/menus?query=Ghost",
            headers={"organization-id": "org_123"}
        )
        self.assertEqual(response.status_code, 204)
