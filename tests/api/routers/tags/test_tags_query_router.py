
import unittest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.crud.tags.models import TagModel
from tests.payloads import USER_IN_DB


class TestTagsQueryRouter(unittest.TestCase):
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

    def insert_mock_tag(self, name="Mock Tag"):
        tag = TagModel(
            name=name,
            organization_id="org_123",
            is_active=True,
            styling={
                "primary_color": "#111111",
                "secondary_color": "#222222"
            }
        )
        tag.save()
        return str(tag.id)

    def test_get_tag_by_id_success(self):
        tag_id = self.insert_mock_tag(name="By ID")

        response = self.test_client.get(
            f"/api/tags/{tag_id}",
            headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "By ID")
        self.assertEqual(response.json()["message"], "Tag found with success")

    def test_get_tag_by_id_not_found(self):
        response = self.test_client.get(
            "/api/tags/000000000000000000000000",
            headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Tag #000000000000000000000000 not found")

    def test_get_tags_with_results(self):
        self.insert_mock_tag(name="Tag A")
        self.insert_mock_tag(name="Tag B")

        response = self.test_client.get(
            "/api/tags",
            headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Tags found with success")
        self.assertGreaterEqual(len(response.json()["data"]), 2)

    def test_get_tags_empty_returns_204(self):
        response = self.test_client.get(
            "/api/tags",
            headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 204)
