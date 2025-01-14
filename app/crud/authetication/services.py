from typing import List
from app.api.shared_schemas.token import TokenData
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.users.schemas import CompleteUserInDB, UserInDB
from app.crud.users.repositories import UserRepository


class AuthenticationServices:
    def __init__(
            self,
            user_repository: UserRepository,
            organization_repository: OrganizationRepository
        ) -> None:
        self.__user_repository = user_repository
        self.__organization_repository = organization_repository

    async def get_current_user(self, token: TokenData, expand: List[str] = []) -> UserInDB | CompleteUserInDB:
        user_in_db = await self.__user_repository.select_by_id(id=token.id)

        if not expand:
            return user_in_db

        return await self.__build_complete_user(user=user_in_db, expand=expand)

    async def __build_complete_user(self, user: UserInDB, expand: List[str] = []) -> CompleteUserInDB:
        complete_user = CompleteUserInDB(**user.model_dump())

        if "organizations" in expand:
            organizations = await self.__organization_repository.select_all(user_id=user.user_id)

            for organization in organizations:
                complete_user.organizations.append(organization.id)

        return complete_user
