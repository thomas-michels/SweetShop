from datetime import timedelta

from fastapi import Depends

from app.api.dependencies.get_current_organization import check_current_organization

from app.crud.notifications.repositories import NotificationRepository
from app.crud.notifications.services import NotificationServices


async def notification_composer(
    organization_id: str = Depends(check_current_organization),
) -> NotificationServices:
    notification_repository = NotificationRepository(
        organization_id=organization_id,
    )
    notification_services = NotificationServices(
        notification_repository=notification_repository,
        deduplication_interval=timedelta(minutes=10),
    )
    return notification_services
