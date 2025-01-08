from typing import List

from app.api.exceptions.authentication_exceptions import UnauthorizedException
from app.crud.users.repositories import UserRepository
from app.crud.users.schemas import UserInDB

from .schemas import CompleteOrganization, Organization, OrganizationInDB, RoleEnum, UpdateOrganization, UserOrganization
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

    async def search_by_id(self, id: str, expand: List[str] = []) -> CompleteOrganization:
        organization_in_db = await self.__organization_repository.select_by_id(id=id)
        return await self.__build_complete_organization(
            organization=organization_in_db,
            expand=expand
        )

    async def search_all(self, expand: List[str] = []) -> List[CompleteOrganization]:
        organizations = await self.__organization_repository.select_all()
        complete_organizations = []

        for organization in organizations:
            complete_organizations.append(await self.__build_complete_organization(
                organization=organization,
                expand=expand
            ))

        return complete_organizations

    async def delete_by_id(self, id: str) -> OrganizationInDB:
        organization_in_db = await self.__organization_repository.delete_by_id(id=id)
        return organization_in_db

    async def __build_complete_organization(self, organization: OrganizationInDB, expand: List[str] = []) -> CompleteOrganization:
        complete_organization = CompleteOrganization.model_validate(organization)

        if "users" in expand:
            for user in complete_organization.users:
                user_in_db = await self.__user_repository.select_by_id(id=user.user_id)
                user.user = user_in_db

        return complete_organization

    async def add_user(self, organization_id: str, user_making_request: str, user_id: str, role: RoleEnum) -> bool:
        organization_in_db = await self.search_by_id(id=organization_id)

        user_in_db_making_request = await self.__user_repository.select_by_id(id=user_making_request)
        user_in_db = await self.__user_repository.select_by_id(id=user_id)

        if not (organization_in_db and user_in_db_making_request and user_in_db):
            return False

        user_making_request_role = organization_in_db.get_user_in_organization(user_making_request).role if organization_in_db.get_user_in_organization(user_making_request) else None

        if user_making_request_role and user_making_request_role not in {RoleEnum.OWNER, RoleEnum.MANAGER, RoleEnum.ADMIN}:
            raise UnauthorizedException(detail="You cannot change roles!")

        current_role = organization_in_db.get_user_in_organization(user_in_db.user_id).role if organization_in_db.get_user_in_organization(user_in_db.user_id) else None

        if current_role:
            if current_role not in {RoleEnum.OWNER, RoleEnum.MANAGER, RoleEnum.ADMIN}:
                raise UnauthorizedException(detail="You cannot change your role on that organization!")

            if role == RoleEnum.ADMIN:
                raise UnauthorizedException(detail="You cannot assign this role on that organization!")

            if current_role == RoleEnum.MANAGER and role == RoleEnum.OWNER:
                raise UnauthorizedException(detail="You cannot assign this role!")

            if current_role == RoleEnum.OWNER and role == RoleEnum.OWNER:
                raise UnauthorizedException(detail="An organization can only have one owner!")

        organization_in_db.users.append(
            UserOrganization(
                user_id=user_in_db.user_id,
                role=role
            )
        )

        await self.__organization_repository.update(
            organization_id=organization_id,
            organization=organization_in_db.model_dump()
        )

        return True

    async def remove_user(self, organization_id: str, user_making_request: str, user_id: str) -> bool:
        organization_in_db = await self.search_by_id(id=organization_id)

        user_in_db_making_request = await self.__user_repository.select_by_id(id=user_making_request)
        user_in_db = await self.__user_repository.select_by_id(id=user_id)

        if not (organization_in_db and user_in_db_making_request and user_in_db):
            return False

        user_making_request_role = organization_in_db.get_user_in_organization(user_making_request).role if organization_in_db.get_user_in_organization(user_making_request) else None

        if user_making_request_role and user_making_request_role not in {RoleEnum.OWNER, RoleEnum.ADMIN}:
            raise UnauthorizedException(detail="You cannot remove users!")

        current_role = organization_in_db.get_user_in_organization(user_in_db.user_id).role if organization_in_db.get_user_in_organization(user_in_db.user_id) else None

        if current_role:
            if current_role == RoleEnum.OWNER:
                raise UnauthorizedException(detail="You cannot remove the owner of the organization!")

            if current_role == RoleEnum.ADMIN and user_making_request_role not in [RoleEnum.OWNER]:
                raise UnauthorizedException(detail="You cannot remove this user!")

            if current_role == RoleEnum.MANAGER and user_making_request_role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
                raise UnauthorizedException(detail="You cannot remove this user!")

        organization_in_db.delete_user(user_in_db)

        await self.__organization_repository.update(
            organization_id=organization_id,
            organization=organization_in_db.model_dump()
        )

        return True
