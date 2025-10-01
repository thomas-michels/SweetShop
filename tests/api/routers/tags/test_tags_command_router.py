import unittest

import mongomock
from bson import ObjectId
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect

from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.application import app
from app.core.utils.features import Feature
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.plan_features.schemas import PlanFeatureInDB
from app.crud.tags.models import TagModel
from tests.payloads import USER_IN_DB


class TestTagsCommandRouter(unittest.TestCase):

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

        self.mock_feature = PlanFeatureInDB(
            id=str(ObjectId()),
            additional_price=0,
            allow_additional=False,
            display_name="Max tags",
            display_value="1",
            name=Feature.MAX_TAGS,
            value="2",
            plan_id=str(ObjectId()),
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

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
                "secondary_color": "#222222",
            },
        )
        tag.save()
        return str(tag.id)

    @unittest.mock.patch("app.crud.tags.services.get_plan_feature")
    def test_post_tag_success(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy()

        response = self.test_client.post(
            url="/api/tags",
            json={"name": "Tag 1"},
            headers={"organization-id": "org_123"},
        )

        json = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json["message"], "Tag created with success")
        self.assertIsNotNone(json["data"]["id"])
        self.assertEqual(json["data"]["name"], "Tag 1")

    @unittest.mock.patch("app.crud.tags.services.get_plan_feature")
    def test_post_tag_failure_due_to_limit(self, mock_get_plan_feature):
        mock_get_plan_feature.return_value = self.mock_feature.model_copy()

        # Cria duas tags antes do post
        self.insert_mock_tag(name="Tag A")
        self.insert_mock_tag(name="Tag B")

        response = self.test_client.post(
            url="/api/tags",
            json={"name": "Tag C"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("Maximum number of tags", response.json()["message"])

    def test_put_tag_success(self):
        tag_id = self.insert_mock_tag(name="Old Name")

        response = self.test_client.put(
            f"/api/tags/{tag_id}",
            json={"name": "Updated"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Tag updated with success")

    def test_put_tag_failure(self):
        response = self.test_client.put(
            "/api/tags/invalid_id",
            json={"name": "Fail"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Tag #invalid_id not found")

    def test_delete_tag_success(self):
        tag_id = self.insert_mock_tag(name="To Delete")

        response = self.test_client.delete(
            f"/api/tags/{tag_id}", headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Tag deleted with success")

    def test_delete_tag_not_found(self):
        response = self.test_client.delete(
            "/api/tags/9999", headers={"organization-id": "org_123"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Tag #9999 not found")
