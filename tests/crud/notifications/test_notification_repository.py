import unittest
from datetime import timedelta

import mongomock
from mongoengine import connect, disconnect

from app.crud.notifications.repositories import NotificationRepository
from app.crud.notifications.schemas import NotificationChannel, NotificationCreate
from app.crud.notifications.models import NotificationModel
from app.core.utils.utc_datetime import UTCDateTime


class TestNotificationRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repository = NotificationRepository(organization_id="org_123")

    def tearDown(self):
        disconnect()

    async def test_create_and_select_by_id(self):
        notification = NotificationCreate(
            user_id="user@example.com",
            title="Bem-vindo",
            content="Seu cadastro foi realizado com sucesso.",
            channels=[NotificationChannel.EMAIL, NotificationChannel.APP],
            notification_type="WELCOME",
        )

        created = await self.repository.create(notification=notification)

        self.assertEqual(created.user_id, notification.user_id)
        self.assertEqual(created.organization_id, "org_123")
        self.assertEqual(set(created.channels), {NotificationChannel.EMAIL, NotificationChannel.APP})

        fetched = await self.repository.select_by_id(id=created.id)
        self.assertEqual(fetched.id, created.id)
        self.assertFalse(fetched.read)

    async def test_select_all_by_user_with_unread_filter(self):
        notification = NotificationCreate(
            user_id="user@example.com",
            title="Atualização",
            content="Seu pedido foi atualizado.",
            channels=[NotificationChannel.APP],
            notification_type="ORDER_UPDATE",
        )

        created = await self.repository.create(notification=notification)
        await self.repository.mark_as_read(id=created.id)

        notification_in_db = await self.repository.create(notification=notification)

        all_notifications = await self.repository.select_all_by_user(user_id="user@example.com")
        unread_notifications = await self.repository.select_all_by_user(
            user_id="user@example.com",
            only_unread=True,
        )

        self.assertEqual(len(all_notifications), 2)
        self.assertEqual(len(unread_notifications), 1)
        self.assertTrue(all(notif.read is False for notif in unread_notifications))

    async def test_exists_recent_notification(self):
        notification = NotificationCreate(
            user_id="user@example.com",
            title="Aviso",
            content="Você tem uma nova mensagem.",
            channels=[NotificationChannel.APP],
            notification_type="ALERT",
        )

        notification_in_db = await self.repository.create(notification=notification)

        exists = await self.repository.exists_recent_notification(
            user_id="user@example.com",
            notification_type="ALERT",
            interval=timedelta(minutes=5),
        )

        self.assertTrue(exists)

        NotificationModel.objects(id=notification_in_db.id).update(
            set__created_at=UTCDateTime.now() - timedelta(hours=2)
        )

        exists_after_interval = await self.repository.exists_recent_notification(
            user_id="user@example.com",
            notification_type="ALERT",
            interval=timedelta(hours=1),
        )

        self.assertFalse(exists_after_interval)

