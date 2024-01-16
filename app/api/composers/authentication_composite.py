from fastapi import Depends
from app.crud.users.repositories import UserRepository
from app.crud.authetication.services import AuthenticationServices
from app.core.db import get_repository


async def authentication_composer(
        user_repository: UserRepository = Depends(get_repository(UserRepository))
    ) -> AuthenticationServices:
    authentication_services = AuthenticationServices(user_repository=user_repository)
    return authentication_services
