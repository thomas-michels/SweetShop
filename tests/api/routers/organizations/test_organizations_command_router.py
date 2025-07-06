import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.application import app
from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers import organization_composer
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.services import OrganizationServices
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.organizations.models import OrganizationModel
from tests.payloads import USER_IN_DB


class FakeRedis:
    def delete_value(self, key: str):
        pass


class TestOrganizationsCommandRouter(unittest.TestCase):
    def setUp(self):
        def override_dependency(mock):
            def _dependency():
                return mock
            return _dependency

        disconnect()
        connect(mongo_client_class=mongomock.MongoClient)

        self.repo = OrganizationRepository()
        self.user_repo = AsyncMock()
        self.plan_repo = AsyncMock()

        patcher_email = patch("app.crud.organizations.services.send_email", return_value="id")
        patcher_email.start()
        self.addCleanup(patcher_email.stop)

        self.service = OrganizationServices(
            organization_repository=self.repo,
            user_repository=self.user_repo,
            organization_plan_repository=self.plan_repo,
            cached_users={}
        )

        self.test_client = TestClient(app)
        app.dependency_overrides[decode_jwt] = override_dependency(USER_IN_DB)
        app.dependency_overrides[check_current_organization] = override_dependency("org_123")
        app.dependency_overrides[organization_composer] = override_dependency(self.service)
        app.user_middleware.clear()

    def tearDown(self):
        disconnect()
        app.dependency_overrides = {}

    def insert_org(self, name="Org"):
        org = OrganizationModel(name=name)
        org.save()
        return str(org.id)

    def test_post_organization_success(self):
        self.user_repo.select_by_id.return_value = USER_IN_DB

        response = self.test_client.post(
            "/api/organizations",
            json={"name": "My Org"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Organization created with success")
        self.assertIsNotNone(response.json()["data"]["id"])

    def test_put_organization_success(self):
        org_id = self.insert_org(name="Old")
        OrganizationModel.objects(id=org_id).first().update(users=[{"user_id": USER_IN_DB.user_id, "role": RoleEnum.OWNER}])
        self.user_repo.select_by_id.return_value = USER_IN_DB

        response = self.test_client.put(
            f"/api/organizations/{org_id}",
            json={"name": "Updated"},
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Organization updated with success")

    def test_delete_organization_success(self):
        org_id = self.insert_org(name="Del")
        OrganizationModel.objects(id=org_id).first().update(users=[{"user_id": USER_IN_DB.user_id, "role": RoleEnum.OWNER}])

        response = self.test_client.delete(
            f"/api/organizations/{org_id}",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Organization deleted with success")

    def test_delete_organization_not_found(self):
        response = self.test_client.delete(
            "/api/organizations/missing",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["message"])

    def test_post_organization_invalid_payload_returns_422(self):
        response = self.test_client.post(
            "/api/organizations",
            json={},
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 422)

