import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
import mongomock

from app.application import app
from app.api.dependencies.auth import decode_jwt
from app.api.dependencies.get_current_organization import check_current_organization
from app.api.composers import organization_composer
from app.api.routers.organizations import query_routers
from app.crud.organizations.models import OrganizationModel
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.organizations.services import OrganizationServices
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.plan_features.schemas import PlanFeatureInDB
from app.core.utils.utc_datetime import UTCDateTime
from app.core.utils.features import Feature
from tests.payloads import USER_IN_DB


class FakeRedis:
    def delete_value(self, key: str):
        pass


class TestOrganizationsQueryRouter(unittest.TestCase):
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

    def insert_org(self, name="Org", with_user=False):
        org = OrganizationModel(name=name)
        if with_user:
            org.users = [{"user_id": USER_IN_DB.user_id, "role": RoleEnum.OWNER}]
        org.save()
        return str(org.id)

    def test_get_organization_by_id_success(self):
        org_id = self.insert_org(name="One", with_user=True)

        response = self.test_client.get(
            f"/api/organizations/{org_id}",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "One")

    def test_get_organization_by_id_not_found(self):
        response = self.test_client.get(
            "/api/organizations/missing",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 404)

    def test_get_organizations_with_results(self):
        self.insert_org(name="A")
        self.insert_org(name="B")

        response = self.test_client.get(
            "/api/organizations",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()["data"]), 2)

    def test_get_organizations_empty_returns_204(self):
        response = self.test_client.get(
            "/api/organizations",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 204)

    def test_get_users_organizations(self):
        org_id = self.insert_org(name="User Org", with_user=True)
        self.insert_org(name="Other")

        response = self.test_client.get(
            f"/api/users/{USER_IN_DB.user_id}/organizations",
            headers={"organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 1)
        self.assertEqual(response.json()["data"][0]["id"], org_id)

    def test_get_users_organizations_empty_returns_204(self):
        response = self.test_client.get(
            f"/api/users/{USER_IN_DB.user_id}/organizations",
            headers={"organization-id": "org_123"},
        )
        self.assertEqual(response.status_code, 204)

    @patch("app.api.routers.organizations.query_routers.get_plan_feature")
    def test_get_organization_feature_success(self, mock_plan_feature):
        org_id = self.insert_org(with_user=True)
        query_routers._env.API_TOKEN = "secret"
        mock_plan_feature.return_value = PlanFeatureInDB(
            id="pf1",
            additional_price=0,
            allow_additional=False,
            display_name="Feature",
            display_value="true",
            name=Feature.DISPLAY_MENU,
            value="true",
            plan_id="p1",
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

        response = self.test_client.get(
            f"/api/organizations/{org_id}/features/{Feature.DISPLAY_MENU.value}",
            headers={"token": "secret", "organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("have this feature", response.json()["message"])

    @patch("app.api.routers.organizations.query_routers.get_plan_feature")
    def test_get_organization_feature_unauthorized(self, mock_plan_feature):
        org_id = self.insert_org(with_user=True)
        query_routers._env.API_TOKEN = "secret"
        mock_plan_feature.return_value = None

        response = self.test_client.get(
            f"/api/organizations/{org_id}/features/{Feature.DISPLAY_MENU.value}",
            headers={"token": "wrong", "organization-id": "org_123"},
        )

        self.assertEqual(response.status_code, 401)
