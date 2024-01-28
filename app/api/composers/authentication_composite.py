from fastapi import Depends

from app.core.db import get_repository
from app.crud.authetication.services import AuthenticationServices
from app.crud.users.repositories import UserRepository


async def authentication_composer(
    user_repository: UserRepository = Depends(get_repository(UserRepository)),
) -> AuthenticationServices:
    authentication_services = AuthenticationServices(user_repository=user_repository)
    return authentication_services
