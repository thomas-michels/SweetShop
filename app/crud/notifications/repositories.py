from datetime import timedelta
from typing import List

from mongoengine.queryset.visitor import Q

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository
from app.core.utils.utc_datetime import UTCDateTime

from .models import NotificationModel
from .schemas import NotificationCreate, NotificationInDB

_logger = get_logger(__name__)


class NotificationRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, notification: NotificationCreate) -> NotificationInDB:
        try:
            notification_model = NotificationModel(
                organization_id=self.organization_id,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
                channels=[channel.value for channel in notification.channels],
                **notification.model_dump(exclude={"channels"}),
            )
            notification_model.save()
            return await self.select_by_id(notification_model.id)
        except Exception as error:
            _logger.error(f"Error on create notification: {str(error)}")
            raise UnprocessableEntity(message="Error on create notification")

    async def select_by_id(self, id: str, raise_404: bool = True) -> NotificationInDB:
        try:
            notification_model = NotificationModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id,
            ).first()

            if notification_model:
                return NotificationInDB.model_validate(notification_model)

            if raise_404:
                raise NotFoundError(message=f"Notification with ID #{id} not found")

        except Exception as error:
            if raise_404:
                raise NotFoundError(message=f"Notification with ID #{id} not found")
            _logger.error(f"Error on select_by_id: {str(error)}")

    async def select_all_by_user(
        self,
        user_id: str,
        only_unread: bool = False,
    ) -> List[NotificationInDB]:
        try:
            query = Q(
                user_id=user_id,
                is_active=True,
                organization_id=self.organization_id,
            )

            if only_unread:
                query &= Q(read=False)

            notifications: List[NotificationInDB] = []
            objects = NotificationModel.objects(query).order_by("-created_at")

            for notification_model in objects:
                notifications.append(NotificationInDB.model_validate(notification_model))

            return notifications
        except Exception as error:
            _logger.error(f"Error on select_all_by_user: {str(error)}")
            raise NotFoundError(message="Notifications not found")

    async def mark_as_read(self, id: str) -> NotificationInDB:
        try:
            notification_model = NotificationModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id,
            ).first()

            if not notification_model:
                raise NotFoundError(message=f"Notification with ID #{id} not found")

            notification_model.update(read=True)
            return await self.select_by_id(id)
        except NotFoundError:
            raise
        except Exception as error:
            _logger.error(f"Error on mark_as_read: {str(error)}")
            raise UnprocessableEntity(message="Error on mark notification as read")

    async def exists_recent_notification(
        self,
        user_id: str,
        notification_type: str,
        interval: timedelta,
    ) -> bool:
        threshold = UTCDateTime.now() - interval
        try:
            notification_model = NotificationModel.objects(
                user_id=user_id,
                notification_type=notification_type,
                organization_id=self.organization_id,
                is_active=True,
                created_at__gte=threshold,
            ).first()

            return bool(notification_model)
        except Exception as error:
            _logger.error(f"Error on exists_recent_notification: {str(error)}")
            return False

    async def delete_by_id(self, id: str) -> NotificationInDB:
        try:
            notification_model = NotificationModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id,
            ).first()

            if notification_model:
                notification_model.delete()
                return NotificationInDB.model_validate(notification_model)

            raise NotFoundError(message=f"Notification with ID #{id} not found")
        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Notification with ID #{id} not found")
