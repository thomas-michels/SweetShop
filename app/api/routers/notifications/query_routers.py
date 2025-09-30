from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.api.composers import notification_composer
from app.api.dependencies import build_response
from app.crud.notifications import (
    NotificationInDB,
    NotificationServices,
)

router = APIRouter(tags=["Notifications"])


@router.get(
    "/notifications/{notification_id}",
    responses={status.HTTP_200_OK: {"model": NotificationInDB}},
)
async def get_notification_by_id(
    notification_id: str,
    notification_services: NotificationServices = Depends(notification_composer),
):
    notification_in_db = await notification_services.search_by_id(id=notification_id)
    return build_response(
        status_code=status.HTTP_200_OK,
        message="Notification found with success",
        data=notification_in_db,
    )


@router.get(
    "/notifications",
    responses={status.HTTP_200_OK: {"model": List[NotificationInDB]}},
)
async def list_notifications(
    user_id: str = Query(..., alias="userId"),
    only_unread: bool = Query(default=False, alias="onlyUnread"),
    notification_services: NotificationServices = Depends(notification_composer),
):
    notifications = await notification_services.list_by_user(
        user_id=user_id,
        only_unread=only_unread,
    )
    return build_response(
        status_code=status.HTTP_200_OK,
        message="Notifications retrieved with success",
        data=notifications,
    )
