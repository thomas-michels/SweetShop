import sys
import types


class _FakeResendEmails:
    @staticmethod
    def send(params):
        return {"id": "fake-id"}


def _fake_request(*args, **kwargs):
    class _FakeResponse:
        status_code = 200

        def json(self):
            return {}

    return _FakeResponse()


sys.modules.setdefault("resend", types.SimpleNamespace(api_key=None, Emails=_FakeResendEmails))
sys.modules.setdefault(
    "requests",
    types.SimpleNamespace(
        post=_fake_request,
        get=_fake_request,
        put=_fake_request,
        delete=_fake_request,
        patch=_fake_request,
    ),
)

import unittest
from datetime import timedelta
from unittest.mock import patch

import mongomock
from mongoengine import connect, disconnect

from app.core.exceptions import UnprocessableEntity
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.notifications.repositories import NotificationRepository
from app.crud.notifications.schemas import NotificationChannel, NotificationCreate
from app.crud.notifications.services import NotificationServices
from app.crud.users.schemas import UserInDB


class FakeUserRepository:
    def __init__(self, user: UserInDB):
        self.user = user
        self.called_with = []

    async def select_by_id(self, id: str, raise_404: bool = True) -> UserInDB:
        self.called_with.append(id)
        return self.user


class TestNotificationServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repository = NotificationRepository(organization_id="org_123")
        self.user = UserInDB(
            email="user@example.com",
            name="Test User",
            nickname="test",
            picture=None,
            user_id="auth0|123",
            user_metadata=None,
            app_metadata={},
            last_login=UTCDateTime.now(),
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )
        self.user_repository = FakeUserRepository(user=self.user)
        self.services = NotificationServices(
            notification_repository=repository,
            user_repository=self.user_repository,
            deduplication_interval=timedelta(minutes=30),
            email_template_path="./templates/notification-default.html",
        )

    def tearDown(self):
        disconnect()

    @patch("app.crud.notifications.services.send_email")
    async def test_create_notification_sends_email(self, mock_send_email):
        notification = NotificationCreate(
            user_id=self.user.user_id,
            title="Atualizacao",
            content="Seu pedido foi enviado.",
            channels=[NotificationChannel.EMAIL],
            notification_type="ORDER_UPDATE",
        )

        created = await self.services.create(notification=notification)

        self.assertEqual(created.user_id, notification.user_id)
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertIn(self.user.email, kwargs["email_to"])
        self.assertEqual(kwargs["title"], notification.title)
        self.assertIn("Seu pedido foi enviado.", kwargs["message"])

    @patch("app.crud.notifications.services.send_email")
    async def test_create_notification_deduplication(self, mock_send_email):
        notification = NotificationCreate(
            user_id=self.user.user_id,
            title="Atualizacao",
            content="Seu pedido foi enviado.",
            channels=[NotificationChannel.EMAIL],
            notification_type="ORDER_UPDATE",
        )

        await self.services.create(notification=notification)

        with self.assertRaises(UnprocessableEntity):
            await self.services.create(notification=notification)

        mock_send_email.assert_called_once()
