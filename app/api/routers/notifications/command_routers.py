from fastapi import APIRouter, Depends, status

from app.api.composers import notification_composer
from app.api.dependencies import build_response
from app.crud.notifications import (
    NotificationCreate,
    NotificationInDB,
    NotificationServices,
)

router = APIRouter(tags=["Notifications"])


@router.post("/notifications", responses={status.HTTP_201_CREATED: {"model": NotificationInDB}})
async def create_notification(
    notification: NotificationCreate,
    notification_services: NotificationServices = Depends(notification_composer),
):
    notification_in_db = await notification_services.create(notification=notification)
    return build_response(
        status_code=status.HTTP_201_CREATED,
        message="Notification created with success",
        data=notification_in_db,
    )


@router.patch(
    "/notifications/{notification_id}/read",
    responses={status.HTTP_200_OK: {"model": NotificationInDB}},
)
async def mark_notification_as_read(
    notification_id: str,
    notification_services: NotificationServices = Depends(notification_composer),
):
    notification_in_db = await notification_services.mark_as_read(id=notification_id)
    return build_response(
        status_code=status.HTTP_200_OK,
        message="Notification marked as read",
        data=notification_in_db,
    )
