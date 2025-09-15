import unittest
from unittest.mock import AsyncMock

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.users.schemas import UserInDB
from app.crud.users.services import UserServices


class TestUserServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repository = AsyncMock()
        self.cached_complete_users = {}
        self.service = UserServices(
            user_repository=self.repository,
            cached_complete_users=self.cached_complete_users,
        )

    async def _build_user(self, metadata=None) -> UserInDB:
        return UserInDB(
            user_id="auth0|123",
            email="user@test.com",
            name="Test User",
            nickname="test",
            user_metadata=metadata,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

    async def test_update_last_access_adds_timestamp_and_clears_cache(self):
        user = await self._build_user(metadata={"phone": "123"})
        self.cached_complete_users[user.user_id] = object()

        updated_metadata = {
            "phone": "123",
            "last_access_at": str(UTCDateTime.now()),
        }
        updated_user = await self._build_user(metadata=updated_metadata)
        self.repository.update.return_value = updated_user

        result = await self.service.update_last_access(user=user)

        self.repository.update.assert_awaited_once()
        call_kwargs = self.repository.update.await_args.kwargs
        self.assertEqual(call_kwargs["user_id"], user.user_id)

        payload_metadata = call_kwargs["user"].user_metadata
        self.assertIn("last_access_at", payload_metadata)
        self.assertEqual(payload_metadata["phone"], "123")
        self.assertIsInstance(payload_metadata["last_access_at"], str)
        UTCDateTime.validate_datetime(payload_metadata["last_access_at"])

        self.assertNotIn(user.user_id, self.cached_complete_users)
        self.assertEqual(result, updated_user)

    async def test_update_last_access_initializes_metadata_when_missing(self):
        user = await self._build_user(metadata=None)

        updated_user = await self._build_user(
            metadata={"last_access_at": str(UTCDateTime.now())}
        )
        self.repository.update.return_value = updated_user

        result = await self.service.update_last_access(user=user)

        payload_metadata = self.repository.update.await_args.kwargs["user"].user_metadata
        self.assertIn("last_access_at", payload_metadata)
        self.assertEqual(result, updated_user)
