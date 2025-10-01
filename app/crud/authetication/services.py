from typing import Dict

from app.api.shared_schemas.terms_of_use import FilterTermOfUse
from app.api.shared_schemas.token import TokenData
from app.core.configs import get_logger
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.terms_of_use.services import TermOfUseServices
from app.crud.users.repositories import UserRepository
from app.crud.users.schemas import CompleteUserInDB, UserInDB

logger = get_logger(__name__)


class AuthenticationServices:
    def __init__(
            self,
            user_repository: UserRepository,
            organization_repository: OrganizationRepository,
            terms_of_use_services: TermOfUseServices,
            cached_complete_users: Dict[str, CompleteUserInDB]
        ) -> None:
        self.__user_repository = user_repository
        self.__organization_repository = organization_repository
        self.__terms_of_use_services = terms_of_use_services

        self.__cached_complete_users = cached_complete_users

    async def get_current_user(self, token: TokenData) -> CompleteUserInDB:
        cached_user = self.__cached_complete_users.get(token.id)

        if cached_user and cached_user.termsOfUseAccepted:
            logger.debug(f"Getting cached user {token.id}")
            return cached_user

        user_in_db = await self.__user_repository.select_by_id(id=token.id)

        complete_user_in_db = await self.__build_complete_user(user=user_in_db)

        if complete_user_in_db and complete_user_in_db.termsOfUseAccepted:
            self.__cached_complete_users[complete_user_in_db.user_id] = complete_user_in_db
            logger.debug(f"Caching user {token.id}")

        return complete_user_in_db

    async def __build_complete_user(self, user: UserInDB) -> CompleteUserInDB:
        complete_user = CompleteUserInDB(**user.model_dump())

        organizations = await self.__organization_repository.select_all(user_id=user.user_id)

        for organization in organizations:
            complete_user.organizations.append(organization.id)
            complete_user.organizations_roles[organization.id] = organization.get_user_in_organization(user_id=user.user_id)

        current_term_of_use = await self.__terms_of_use_services.search_term_of_use_all(filter=FilterTermOfUse.LATEST)

        acceptance = await self.__terms_of_use_services.search_acceptance_by_id(
            term_of_use_id=current_term_of_use[0].id,
            user_id=user.user_id
        )

        complete_user.termsOfUseAccepted = True if acceptance else False

        return complete_user
