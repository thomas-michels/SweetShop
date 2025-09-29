from __future__ import annotations

import math
from datetime import timedelta
from typing import Dict, List, TYPE_CHECKING

from app.api.dependencies.email_sender import send_email
from app.core.configs import get_logger
from app.core.utils.utc_datetime import UTCDateTime
from .repositories import UserRepository
from .schemas import UpdateUser, User, UserInDB


_logger = get_logger(__name__)


if TYPE_CHECKING:  # pragma: no cover - type checking only
    from app.crud.organization_plans.services import OrganizationPlanServices
    from app.crud.organizations.repositories import OrganizationRepository


class UserServices:

    def __init__(
        self,
        user_repository: UserRepository,
        cached_complete_users: Dict[str, UserInDB],
        organization_plan_services: OrganizationPlanServices | None = None,
        organization_repository: OrganizationRepository | None = None,
    ) -> None:
        self.__repository = user_repository
        self.__cached_complete_users = cached_complete_users
        self.__organization_plan_services = organization_plan_services
        self.__organization_repository = organization_repository

    # async def create(self, user: User) -> UserInDB:
    #     user_in_db = await self.__repository.create(user=user, password=password)
    #     return user_in_db

    async def update(self, id: int, updated_user: UpdateUser) -> UserInDB:
        user_in_db = await self.search_by_id(id=id)

        if user_in_db:
            user_in_db = await self.__repository.update(
                user_id=user_in_db.user_id, user=updated_user
            )

        return user_in_db

    async def search_by_id(self, id: int) -> UserInDB:
        user_in_db = await self.__repository.select_by_id(id=id)
        return user_in_db

    async def search_all(self) -> List[UserInDB]:
        users = await self.__repository.select_all()
        return users

    async def delete_by_id(self, id: int) -> UserInDB:
        if self.__cached_complete_users.get(id):
            self.__cached_complete_users.pop(id)

        user_in_db = await self.__repository.delete_by_id(id=id)
        return user_in_db

    async def update_last_access(self, user: UserInDB) -> UserInDB:
        metadata = dict(user.user_metadata or {})
        metadata["last_access_at"] = str(UTCDateTime.now())

        updated_user = await self.__repository.update(
            user_id=user.user_id,
            user=UpdateUser(user_metadata=metadata)
        )

        self.__cached_complete_users.pop(user.user_id, None)

        if updated_user:
            return updated_user

        user.user_metadata = metadata
        return user

    async def notify_plan_expiration(self, user: UserInDB) -> None:
        if not self.__organization_plan_services:
            return

        organizations = getattr(user, "organizations", []) or []

        if not organizations:
            return

        metadata = dict(user.user_metadata or {})
        raw_notifications = metadata.get("plan_expiration_notifications")

        notifications: Dict[str, str] = {}

        if isinstance(raw_notifications, dict):
            notifications = dict(raw_notifications)

        now = UTCDateTime.now()
        limit = now + timedelta(days=7)
        metadata_updated = False

        for organization_id in organizations:
            try:
                plan = await self.__organization_plan_services.search_active_plan(
                    organization_id=organization_id
                )
            except Exception as error:  # pragma: no cover - defensive
                _logger.error(
                    "Error when checking active plan for organization %s: %s",
                    organization_id,
                    str(error),
                )
                continue

            if not plan or not plan.calculate_active_plan():
                continue

            if plan.end_date < now or plan.end_date > limit:
                continue

            if notifications.get(plan.id):
                continue

            organization_name = organization_id

            if self.__organization_repository:
                try:
                    organization_in_db = await self.__organization_repository.select_by_id(
                        id=organization_id
                    )
                    if organization_in_db:
                        organization_name = getattr(organization_in_db, "name", organization_name)
                except Exception as error:  # pragma: no cover - defensive
                    _logger.warning(
                        "Unable to fetch organization %s name: %s",
                        organization_id,
                        str(error),
                    )

            days_left = max(
                1,
                math.ceil((plan.end_date - now).total_seconds() / 86400),
            )

            message = self.__build_plan_expiration_email(
                user_name=user.name,
                organization_name=organization_name,
                end_date=plan.end_date,
                days_left=days_left,
            )

            if not message:
                continue

            send_email(
                email_to=[user.email],
                title="PedidoZ - Seu plano está quase expirando",
                message=message,
            )

            notifications[plan.id] = str(UTCDateTime.now())
            metadata_updated = True

        if metadata_updated:
            metadata["plan_expiration_notifications"] = notifications
            user.user_metadata = metadata

            await self.__repository.update(
                user_id=user.user_id,
                user=UpdateUser(user_metadata=metadata),
            )

            self.__cached_complete_users.pop(user.user_id, None)

    def __build_plan_expiration_email(
        self,
        user_name: str,
        organization_name: str,
        end_date: UTCDateTime,
        days_left: int,
    ) -> str | None:
        try:
            with open(
                "./templates/organization-plan-expiration-email.html",
                mode="r",
                encoding="UTF-8",
            ) as template_file:
                message = template_file.read()

            return (
                message.replace("$USER_NAME$", user_name.title())
                .replace("$ORGANIZATION_NAME$", organization_name)
                .replace("$PLAN_END_DATE$", end_date.strftime("%d/%m/%Y"))
                .replace("$DAYS_LEFT$", str(days_left))
            )
        except FileNotFoundError:
            _logger.error("Organization plan expiration template not found")
        except Exception as error:  # pragma: no cover - defensive
            _logger.error(
                "Error when building plan expiration email for %s: %s",
                user_name,
                str(error),
            )

        return None
