from typing import List

from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.crud.users.repositories import UserRepository
from app.crud.users.schemas import UpdateUser, UserInDB

from .schemas import Organization, OrganizationInDB, RoleEnum, UpdateOrganization
from .repositories import OrganizationRepository
from app.core.configs import get_logger

logger = get_logger(__name__)


class OrganizationServices:

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        user_repository: UserRepository,
    ) -> None:
        self.__organization_repository = organization_repository
        self.__user_repository = user_repository

    async def create(self, organization: Organization, owner: UserInDB) -> OrganizationInDB:
        organization_in_db = await self.__organization_repository.create(organization=organization)

        await self.add_user(
            organization_id=organization_in_db.id,
            user_id=owner.user_id,
            user_making_request=owner.user_id,
            role=RoleEnum.OWNER,
        )

        return await self.search_by_id(id=organization_in_db.id)

    async def update(self, id: str, updated_organization: UpdateOrganization) -> OrganizationInDB:
        organization_in_db = await self.search_by_id(id=id)

        is_updated = organization_in_db.validate_updated_fields(update_organization=updated_organization)

        if is_updated:
            organization_in_db = await self.__organization_repository.update(
                organization_id=organization_in_db.id,
                organization=updated_organization.model_dump(exclude_none=True)
            )

        return organization_in_db

    async def search_by_id(self, id: str) -> OrganizationInDB:
        organization_in_db = await self.__organization_repository.select_by_id(id=id)
        return organization_in_db

    async def search_all(self) -> List[OrganizationInDB]:
        organizations = await self.__organization_repository.select_all()
        return organizations

    async def delete_by_id(self, id: str) -> OrganizationInDB:
        organization_in_db = await self.__organization_repository.delete_by_id(id=id)
        return organization_in_db

    async def add_user(self, organization_id: str, user_making_request: str, user_id: str, role: RoleEnum) -> bool:
        organization_in_db = await self.search_by_id(id=organization_id)
        user_in_db_making_request = await self.__user_repository.select_by_id(id=user_making_request)
        user_in_db = await self.__user_repository.select_by_id(id=user_id)

        if not (organization_in_db and user_in_db_making_request and user_in_db):
            return False

        user_making_request_role = RoleEnum(organization_in_db.users.get(user_making_request)) if organization_in_db.users.get(user_making_request) else None

        if user_making_request_role and user_making_request_role not in {RoleEnum.OWNER, RoleEnum.MANAGER, RoleEnum.ADMIN}:
            raise UnauthorizedException(detail="You cannot change roles!")

        user_organizations = user_in_db.app_metadata.get("organizations", {})
        current_role = RoleEnum(user_organizations.get(organization_id)) if organization_id in user_organizations else None

        if current_role:
            if current_role not in {RoleEnum.OWNER, RoleEnum.MANAGER, RoleEnum.ADMIN}:
                raise UnauthorizedException(detail="You cannot change your role on that organization!")

            if role == RoleEnum.ADMIN:
                raise UnauthorizedException(detail="You cannot assign this role on that organization!")

            if current_role == RoleEnum.MANAGER and role == RoleEnum.OWNER:
                raise UnauthorizedException(detail="You cannot assign this role!")

            if current_role == RoleEnum.OWNER and role == RoleEnum.OWNER:
                raise UnauthorizedException(detail="An organization can only have one owner!")

        if not user_in_db.app_metadata.get("organizations"):
            user_in_db.app_metadata["organizations"] = {}

        user_in_db.app_metadata["organizations"][organization_in_db.id] = role.value
        organization_in_db.users[user_in_db.user_id] = role

        user = UpdateUser(app_metadata=user_in_db.app_metadata)

        await self.__user_repository.update(user_id=user_id, user=user)

        await self.__organization_repository.update(
            organization_id=organization_id,
            organization=organization_in_db.model_dump()
        )

        return True

    async def remove_user(self, organization_id: str, user_making_request: str, user_id: str) -> bool:
        organization_in_db = await self.search_by_id(id=organization_id)

        user_in_db = await self.__user_repository.select_by_id(id=user_id)

        if not user_in_db or not organization_in_db:
            return False

        if user_in_db.app_metadata.get("organizations") and organization_id in user_in_db.app_metadata["organizations"]:
            current_role = RoleEnum(user_in_db.app_metadata["organizations"])

            if current_role in [RoleEnum.OWNER, RoleEnum.ADMIN]:
                raise UnauthorizedException(detail="You cannot remove this user!")

        user_in_db.app_metadata["organizations"].pop(organization_in_db.id)

        user = UpdateUser(app_metadata=user_in_db.app_metadata)

        await self.__user_repository.update(user_id=user_id, user=user)

        return True
