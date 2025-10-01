import unittest
from datetime import timedelta
from unittest.mock import patch

import mongomock
from mongoengine import connect, disconnect

from app.core.exceptions import UnprocessableEntity
from app.crud.notifications.repositories import NotificationRepository
from app.crud.notifications.schemas import NotificationChannel, NotificationCreate
from app.crud.notifications.services import NotificationServices


class TestNotificationServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repository = NotificationRepository(organization_id="org_123")
        self.services = NotificationServices(
            notification_repository=repository,
            deduplication_interval=timedelta(minutes=30),
            email_template_path="./templates/notification-default.html",
        )

    def tearDown(self):
        disconnect()

    @patch("app.crud.notifications.services.send_email")
    async def test_create_notification_sends_email(self, mock_send_email):
        notification = NotificationCreate(
            user_id="user@example.com",
            title="Atualização",
            content="Seu pedido foi enviado.",
            channels=[NotificationChannel.EMAIL],
            notification_type="ORDER_UPDATE",
        )

        created = await self.services.create(notification=notification)

        self.assertEqual(created.user_id, notification.user_id)
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertIn("user@example.com", kwargs["email_to"])
        self.assertEqual(kwargs["title"], notification.title)
        self.assertIn("Seu pedido foi enviado.", kwargs["message"])

    @patch("app.crud.notifications.services.send_email")
    async def test_create_notification_deduplication(self, mock_send_email):
        notification = NotificationCreate(
            user_id="user@example.com",
            title="Atualização",
            content="Seu pedido foi enviado.",
            channels=[NotificationChannel.EMAIL],
            notification_type="ORDER_UPDATE",
        )

        await self.services.create(notification=notification)

        with self.assertRaises(UnprocessableEntity):
            await self.services.create(notification=notification)

        mock_send_email.assert_called_once()
