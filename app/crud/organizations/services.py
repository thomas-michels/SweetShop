from typing import Dict, List

from app.api.dependencies.email_sender import send_email
from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException, BadRequestException
from app.core.utils.features import Feature
from app.crud.files.repositories import FileRepository
from app.crud.files.schemas import FilePurpose
from app.crud.users.repositories import UserRepository
from app.crud.users.schemas import UserInDB

from .schemas import CompleteOrganization, Organization, OrganizationInDB, RoleEnum, UpdateOrganization, UserOrganization
from .repositories import OrganizationRepository
from app.crud.organization_plans.repositories import OrganizationPlanRepository
from app.core.configs import get_logger

logger = get_logger(__name__)


class OrganizationServices:

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        user_repository: UserRepository,
        organization_plan_repository: OrganizationPlanRepository,
        cached_users: Dict[str, UserInDB]
    ) -> None:
        self.__organization_repository = organization_repository
        self.__organization_plan_repository = organization_plan_repository
        self.__user_repository = user_repository

        self.__cached_users = cached_users

    async def create(self, organization: Organization, owner: UserInDB) -> OrganizationInDB:
        organization_in_db = await self.__organization_repository.create(organization=organization)

        await self.add_user(
            organization_id=organization_in_db.id,
            user_id=owner.user_id,
            user_making_request=owner.user_id,
            role=RoleEnum.OWNER,
        )

        organization_in_db = await self.search_by_id(id=organization_in_db.id)

        with open("./templates/post-register-email.html", mode="r", encoding="UTF-8") as file:
            message = file.read()
            message = message.replace("$USER_NAME$", owner.name.title())

        send_email(email_to=[owner.email], title=f"Bem-vindo à Pedidoz!", message=message)

        return organization_in_db

    async def check_if_can_add_more_users(self, organization_id: str) -> None:
        organization_in_db = await self.search_by_id(id=organization_id)

        plan_feature = await get_plan_feature(
            organization_id=organization_id,
            feature_name=Feature.MAX_USERS
        )

        if not plan_feature or (len(organization_in_db.users) + 1) >= int(plan_feature.value):
            raise UnauthorizedException(detail=f"Maximum number of users reached, Max value: {plan_feature.value}")

    async def update(
            self,
            id: str,
            updated_organization: UpdateOrganization,
            user_making_request: str
        ) -> OrganizationInDB:

        organization_in_db = await self.search_by_id(id=id)

        user_role = organization_in_db.get_user_in_organization(user_id=user_making_request)

        if not user_role or user_role.role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
            raise UnauthorizedException(detail="You cannot update this organization!")

        if updated_organization.file_id is not None:
            file_repository = FileRepository(organization_id=id)
            file_in_db = await file_repository.select_by_id(id=updated_organization.file_id)

            if file_in_db.purpose != FilePurpose.ORGANIZATION:
                raise BadRequestException(detail="Invalid image for the organization")

        is_updated = organization_in_db.validate_updated_fields(update_organization=updated_organization)

        if is_updated:
            organization_in_db = await self.__organization_repository.update(
                organization_id=organization_in_db.id,
                organization=updated_organization.model_dump(exclude_none=True)
            )

        return organization_in_db

    async def search_by_id(self, id: str, expand: List[str] = []) -> CompleteOrganization:
        organization_in_db = await self.__organization_repository.select_by_id(id=id)

        if not expand:
            return organization_in_db

        return await self.__build_complete_organization(
            organization=organization_in_db,
            expand=expand
        )

    async def search_all(self, user_id: str = None, expand: List[str] = []) -> List[CompleteOrganization]:
        organizations = await self.__organization_repository.select_all(user_id=user_id)
        complete_organizations = []

        if not expand:
            return organizations

        for organization in organizations:
            complete_organizations.append(await self.__build_complete_organization(
                organization=organization,
                expand=expand
            ))

        return complete_organizations

    async def delete_by_id(self, id: str, user_making_request: str) -> OrganizationInDB:
        organization_in_db = await self.__organization_repository.select_by_id(id=id)

        user_organization = organization_in_db.get_user_in_organization(user_id=user_making_request)

        if not user_organization:
            return

        if user_organization.role != RoleEnum.OWNER:
            raise UnauthorizedException(detail="Only the owner can delete an organization")

        organization_in_db = await self.__organization_repository.delete_by_id(id=id)

        self.__cached_users.clear()

        return organization_in_db

    async def __build_complete_organization(self, organization: OrganizationInDB, expand: List[str] = []) -> CompleteOrganization:
        complete_organization = CompleteOrganization.model_validate(organization)

        if "users" in expand:
            for user in complete_organization.users:
                user_in_db = await self.__user_repository.select_by_id(id=user.user_id)
                user.user = user_in_db

        if "plan":
            organization_plan = await self.__organization_plan_repository.select_active_plan(organization_id=organization.id)
            complete_organization.plan = organization_plan

        if "file":
            file_repository = FileRepository(organization_id=organization.id)
            complete_organization.file = await file_repository.select_by_id(
                id=complete_organization.file_id,
                raise_404=False
            )

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
            organization=organization_in_db.model_dump(exclude={"plan"})
        )

        self.clear_user_cache(user_id=user_making_request)
        self.clear_user_cache(user_id=user_id)

        return True

    async def update_user_role(self, organization_id: str, user_making_request: str, user_id: str, role: RoleEnum) -> bool:
        organization_in_db = await self.search_by_id(id=organization_id)

        user_in_db_making_request = await self.__user_repository.select_by_id(id=user_making_request)
        user_in_db = await self.__user_repository.select_by_id(id=user_id)

        if not (organization_in_db and user_in_db_making_request and user_in_db):
            return False

        user_making_request_role = organization_in_db.get_user_in_organization(user_making_request).role if organization_in_db.get_user_in_organization(user_making_request) else None

        if not user_making_request_role or user_making_request_role not in {RoleEnum.OWNER, RoleEnum.ADMIN, RoleEnum.MANAGER}:
            raise UnauthorizedException(detail="You cannot change roles!")

        current_role = organization_in_db.get_user_in_organization(user_in_db.user_id).role if organization_in_db.get_user_in_organization(user_in_db.user_id) else None

        if not current_role:
            raise UnauthorizedException(detail="The user is not part of this organization!")

        if current_role == RoleEnum.OWNER and role == RoleEnum.OWNER:
            raise UnauthorizedException(detail="An organization can only have one owner!")

        if role == RoleEnum.ADMIN and user_making_request_role not in {RoleEnum.OWNER}:
            raise UnauthorizedException(detail="Only an owner can assign the admin role!")

        if current_role in {RoleEnum.ADMIN, RoleEnum.MANAGER} and user_making_request_role == RoleEnum.MANAGER:
            raise UnauthorizedException(detail="You cannot change roles for users with higher or equal privileges!")

        if user_making_request_role == RoleEnum.MANAGER and role in {RoleEnum.ADMIN, RoleEnum.OWNER}:
            raise UnauthorizedException(detail="Managers cannot assign these roles!")

        user_organization = organization_in_db.get_user_in_organization(user_id=user_in_db.user_id)
        user_organization.role = role

        organization_in_db.delete_user(user_id=user_id)
        organization_in_db.users.append(user_organization)

        await self.__organization_repository.update(
            organization_id=organization_id,
            organization=organization_in_db.model_dump()
        )

        self.clear_user_cache(user_id=user_id)

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

        organization_in_db.delete_user(user_id=user_in_db.user_id)

        await self.__organization_repository.update(
            organization_id=organization_id,
            organization=organization_in_db.model_dump()
        )

        self.clear_user_cache(user_id=user_making_request)
        self.clear_user_cache(user_id=user_id)

        return True

    async def transfer_ownership(self, organization_id: str, user_making_request: str, user_id: str) -> bool:
        organization_in_db = await self.search_by_id(id=organization_id)

        user_in_db_making_request = await self.__user_repository.select_by_id(id=user_making_request)

        user_in_db = await self.__user_repository.select_by_id(id=user_id)

        if not (organization_in_db and user_in_db_making_request and user_in_db):
            return False

        user_making_request_role = organization_in_db.get_user_in_organization(user_id=user_making_request)
        user_role = organization_in_db.get_user_in_organization(user_id=user_id)

        if not (user_making_request_role and user_role):
            return False

        if not (user_making_request_role.role == RoleEnum.OWNER \
            and user_role.role == RoleEnum.ADMIN):
            raise UnauthorizedException(detail="Ownership can only be transferred to an admin user by the current owner")

        organization_in_db.delete_user(user_id=user_id)
        organization_in_db.delete_user(user_id=user_making_request)

        user_role.role = RoleEnum.OWNER
        user_making_request_role.role = RoleEnum.ADMIN

        organization_in_db.users.append(user_role)
        organization_in_db.users.append(user_making_request_role)

        await self.__organization_repository.update(
            organization_id=organization_id,
            organization=organization_in_db.model_dump()
        )

        self.clear_user_cache(user_id=user_making_request)
        self.clear_user_cache(user_id=user_id)

        return True

    async def leave_the_organization(self, organization_id: str, user_id: str) -> bool:
        organization_in_db = await self.search_by_id(id=organization_id)

        user_in_db = await self.__user_repository.select_by_id(id=user_id)

        if not (organization_in_db and user_in_db):
            return False

        user_role = organization_in_db.get_user_in_organization(user_id=user_id)

        if not user_role:
            return False

        if user_role.role == RoleEnum.OWNER and len(organization_in_db.users) > 1:
            raise UnauthorizedException(detail="The owner of the organization cannot leave")

        if len(organization_in_db.users) == 1:
            return await self.delete_by_id(id=organization_id, user_making_request=user_id)

        else:
            organization_in_db.delete_user(user_id=user_id)

            await self.__organization_repository.update(
                organization_id=organization_id,
                organization=organization_in_db.model_dump()
            )

        self.clear_user_cache(user_id=user_id)

        return True

    def clear_user_cache(self, user_id: str) -> bool:
        if self.__cached_users.get(user_id):
            self.__cached_users.pop(user_id)
            return True

        return False
