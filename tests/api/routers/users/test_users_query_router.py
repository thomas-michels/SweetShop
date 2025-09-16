import unittest

from fastapi.testclient import TestClient

from app.api.composers import user_composer
from app.api.dependencies.auth import decode_jwt
from app.application import app
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.users.schemas import UserInDB


class MockUserServices:
    def __init__(self, response_user: UserInDB):
        self.response_user = response_user
        self.called_with = None

    async def update_last_access(self, user: UserInDB) -> UserInDB:
        self.called_with = user
        return self.response_user


class TestUsersQueryRouter(unittest.TestCase):
    def setUp(self):
        self.current_user = UserInDB(
            user_id="auth0|123",
            email="user@test.com",
            name="Test User",
            nickname="test",
            user_metadata={"phone": "123"},
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

        self.updated_user = UserInDB(
            user_id=self.current_user.user_id,
            email=self.current_user.email,
            name=self.current_user.name,
            nickname=self.current_user.nickname,
            user_metadata={
                **(self.current_user.user_metadata or {}),
                "last_access_at": str(UTCDateTime.now()),
            },
            created_at=self.current_user.created_at,
            updated_at=self.current_user.updated_at,
        )

        self.mock_service = MockUserServices(response_user=self.updated_user)

        self.test_client = TestClient(app)

        def override_decode_jwt():
            return self.current_user

        async def override_user_composer():
            return self.mock_service

        app.dependency_overrides[decode_jwt] = override_decode_jwt
        app.dependency_overrides[user_composer] = override_user_composer
        app.user_middleware.clear()

    def tearDown(self) -> None:
        app.dependency_overrides = {}

    def test_get_current_user_updates_last_access(self):
        response = self.test_client.get("/api/users/me/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["message"], "User found with success")
        self.assertIsNotNone(self.mock_service.called_with)
        self.assertEqual(self.mock_service.called_with.user_id, self.current_user.user_id)

        metadata = payload["data"]["userMetadata"]
        self.assertEqual(payload["data"]["userId"], self.current_user.user_id)
        self.assertEqual(metadata, self.current_user.user_metadata)
        self.assertNotIn("last_access_at", metadata)
