from datetime import timedelta

from fastapi import Depends

from app.api.dependencies.cache_users import get_cached_users
from app.api.dependencies.get_access_token import get_access_token
from app.api.dependencies.get_current_organization import check_current_organization

from app.crud.notifications.repositories import NotificationRepository
from app.crud.notifications.services import NotificationServices
from app.crud.users.repositories import UserRepository


async def notification_composer(
    organization_id: str = Depends(check_current_organization),
    access_token: str = Depends(get_access_token),
    cached_users=Depends(get_cached_users),
) -> NotificationServices:
    notification_repository = NotificationRepository(
        organization_id=organization_id,
    )
    user_repository = UserRepository(
        access_token=access_token,
        cache_users=cached_users,
    )
    notification_services = NotificationServices(
        notification_repository=notification_repository,
        user_repository=user_repository,
        deduplication_interval=timedelta(minutes=1),
    )
    return notification_services
