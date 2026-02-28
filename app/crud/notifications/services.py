from datetime import timedelta
from pathlib import Path
from typing import List, TYPE_CHECKING

from app.api.dependencies.email_sender import send_email
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.utc_datetime import UTCDateTime

if TYPE_CHECKING:
    from app.crud.users.repositories import UserRepository

from .repositories import NotificationRepository
from .schemas import NotificationChannel, NotificationCreate, NotificationInDB


class NotificationServices:
    def __init__(
        self,
        notification_repository: NotificationRepository,
        user_repository: "UserRepository",
        deduplication_interval: timedelta = timedelta(minutes=1),
        email_template_path: str = "./templates/notification-default.html",
    ) -> None:
        self.__notification_repository = notification_repository
        self.__user_repository = user_repository
        self.__deduplication_interval = deduplication_interval
        self.__email_template_path = Path(email_template_path)

    async def create(self, notification: NotificationCreate) -> NotificationInDB:
        exists = await self.__notification_repository.exists_recent_notification(
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            interval=self.__deduplication_interval,
        )

        if exists:
            raise UnprocessableEntity(
                message="Notification recently sent to this user with the same type"
            )

        notification_in_db = await self.__notification_repository.create(
            notification=notification
        )

        if NotificationChannel.EMAIL in notification.channels:
            user_in_db = await self.__user_repository.select_by_id(
                id=notification.user_id
            )
            email_body = self.__build_email_body(
                title=notification.title,
                content=notification.content,
                created_at=notification_in_db.created_at,
            )
            send_email(
                email_to=[user_in_db.email],
                title=notification.title,
                message=email_body,
            )

        return notification_in_db

    async def search_by_id(self, id: str) -> NotificationInDB:
        notification_in_db = await self.__notification_repository.select_by_id(id=id)
        if not notification_in_db:
            raise NotFoundError(message=f"Notification with ID #{id} not found")
        return notification_in_db

    async def list_by_user(
        self,
        user_id: str,
        only_unread: bool = False,
    ) -> List[NotificationInDB]:
        return await self.__notification_repository.select_all_by_user(
            user_id=user_id,
            only_unread=only_unread,
        )

    async def mark_as_read(self, id: str) -> NotificationInDB:
        return await self.__notification_repository.mark_as_read(id=id)

    async def delete_by_id(self, id: str) -> NotificationInDB:
        return await self.__notification_repository.delete_by_id(id=id)

    def __build_email_body(self, title: str, content: str, created_at: UTCDateTime) -> str:
        if not self.__email_template_path.exists():
            return f"<h1>{title}</h1><p>{content}</p>"

        template = self.__email_template_path.read_text(encoding="utf-8")
        return (
            template
            .replace("$TITLE$", title)
            .replace("$CONTENT$", content)
            .replace("$CREATED_AT$", str(created_at))
        )
