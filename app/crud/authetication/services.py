import json
from app.api.dependencies.redis_manager import RedisManager
from app.api.shared_schemas.terms_of_use import FilterTermOfUse
from app.api.shared_schemas.token import TokenData
from app.crud.organizations.repositories import OrganizationRepository
from app.crud.terms_of_use.services import TermOfUseServices
from app.crud.users.schemas import CompleteUserInDB, UserInDB
from app.crud.users.repositories import UserRepository


class AuthenticationServices:
    def __init__(
            self,
            user_repository: UserRepository,
            organization_repository: OrganizationRepository,
            terms_of_use_services: TermOfUseServices,
        ) -> None:
        self.__user_repository = user_repository
        self.__organization_repository = organization_repository
        self.__terms_of_use_services = terms_of_use_services
        self.redis_manager = RedisManager()

    async def get_current_user(self, token: TokenData) -> CompleteUserInDB:
        key = f"user:{token.id}"

        cached_user = self.redis_manager.get_value(key=key)

        if cached_user:
            cached_user = json.loads(cached_user)

            return CompleteUserInDB(**cached_user)

        user_in_db = await self.__user_repository.select_by_id(id=token.id)
        complete_user_in_db = await self.__build_complete_user(user=user_in_db)

        self.redis_manager.set_value(
            key=key,
            value=complete_user_in_db.model_dump_json(),
            expiration=3600
        )

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
