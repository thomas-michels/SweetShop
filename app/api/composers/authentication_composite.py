from fastapi import Depends
from app.api.dependencies.get_access_token import get_access_token
from app.crud.authetication.services import AuthenticationServices
from app.crud.users.repositories import UserRepository


async def authentication_composer(
    access_token = Depends(get_access_token)
) -> AuthenticationServices:
    user_repository = UserRepository(access_token=access_token)
    authentication_services = AuthenticationServices(user_repository=user_repository)
    return authentication_services
