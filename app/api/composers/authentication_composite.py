from app.crud.authetication.services import AuthenticationServices
from app.crud.users.repositories import UserRepository


async def authentication_composer(
) -> AuthenticationServices:
    user_repository = UserRepository()
    authentication_services = AuthenticationServices(user_repository=user_repository)
    return authentication_services
