import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.core.utils.utc_datetime import UTCDateTime
from app.crud.organization_plans.schemas import OrganizationPlanInDB
from app.crud.users.schemas import CompleteUserInDB, UserInDB
from app.crud.users.services import UserServices


class TestUserServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repository = AsyncMock()
        self.cached_complete_users = {}
        self.organization_plan_services = AsyncMock()
        self.organization_plan_services.search_active_plan = AsyncMock()
        self.organization_repository = AsyncMock()
        self.organization_repository.select_by_id = AsyncMock()
        self.service = UserServices(
            user_repository=self.repository,
            cached_complete_users=self.cached_complete_users,
            organization_plan_services=self.organization_plan_services,
            organization_repository=self.organization_repository,
        )

    async def _build_user(self, metadata=None, complete=False, organizations=None) -> UserInDB:
        base_payload = dict(
            user_id="auth0|123",
            email="user@test.com",
            name="Test User",
            nickname="test",
            user_metadata=metadata,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

        if complete:
            return CompleteUserInDB(
                **base_payload,
                organizations=organizations or [],
                organizations_roles={},
            )

        return UserInDB(**base_payload)

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

    async def test_notify_plan_expiration_sends_email_and_updates_metadata(self):
        user = await self._build_user(metadata={"phone": "123"}, complete=True, organizations=["org_1"])
        self.cached_complete_users[user.user_id] = object()

        plan = OrganizationPlanInDB(
            id="org_plan_1",
            plan_id="plan_basic",
            organization_id="org_1",
            start_date=UTCDateTime.now() - timedelta(days=5),
            end_date=UTCDateTime.now() + timedelta(days=2),
            allow_additional=False,
            has_paid_invoice=True,
            created_at=UTCDateTime.now() - timedelta(days=10),
            updated_at=UTCDateTime.now() - timedelta(days=1),
        )

        self.organization_plan_services.search_active_plan.return_value = plan
        self.organization_repository.select_by_id.return_value = SimpleNamespace(name="Org Test")
        self.repository.update.return_value = user

        with patch("app.crud.users.services.send_email") as send_email_mock:
            await self.service.notify_plan_expiration(user=user)

        send_email_mock.assert_called_once()
        self.organization_plan_services.search_active_plan.assert_awaited_once()
        self.organization_repository.select_by_id.assert_awaited_once_with(id="org_1")
        self.repository.update.assert_awaited_once()
        self.assertNotIn(user.user_id, self.cached_complete_users)

        notifications = user.user_metadata.get("plan_expiration_notifications")
        self.assertIn(plan.id, notifications)
        UTCDateTime.validate_datetime(notifications[plan.id])

    async def test_notify_plan_expiration_skips_when_already_notified(self):
        metadata = {"plan_expiration_notifications": {"org_plan_1": str(UTCDateTime.now())}}
        user = await self._build_user(metadata=metadata, complete=True, organizations=["org_1"])

        plan = OrganizationPlanInDB(
            id="org_plan_1",
            plan_id="plan_basic",
            organization_id="org_1",
            start_date=UTCDateTime.now() - timedelta(days=5),
            end_date=UTCDateTime.now() + timedelta(days=3),
            allow_additional=False,
            has_paid_invoice=True,
            created_at=UTCDateTime.now() - timedelta(days=10),
            updated_at=UTCDateTime.now() - timedelta(days=1),
        )

        self.organization_plan_services.search_active_plan.return_value = plan

        with patch("app.crud.users.services.send_email") as send_email_mock:
            await self.service.notify_plan_expiration(user=user)

        send_email_mock.assert_not_called()
        self.repository.update.assert_not_called()

    async def test_notify_plan_expiration_ignores_plans_outside_window(self):
        user = await self._build_user(metadata={}, complete=True, organizations=["org_1"])

        plan = OrganizationPlanInDB(
            id="org_plan_1",
            plan_id="plan_basic",
            organization_id="org_1",
            start_date=UTCDateTime.now() - timedelta(days=5),
            end_date=UTCDateTime.now() + timedelta(days=10),
            allow_additional=False,
            has_paid_invoice=True,
            created_at=UTCDateTime.now() - timedelta(days=10),
            updated_at=UTCDateTime.now() - timedelta(days=1),
        )

        self.organization_plan_services.search_active_plan.return_value = plan

        with patch("app.crud.users.services.send_email") as send_email_mock:
            await self.service.notify_plan_expiration(user=user)

        send_email_mock.assert_not_called()
        self.repository.update.assert_not_called()
