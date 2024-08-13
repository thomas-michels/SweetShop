from app.crud.users.repositories import UserRepository
from app.crud.users.services import UserServices


async def user_composer(
) -> UserServices:
    user_repository = UserRepository()
    user_services = UserServices(user_repository=user_repository)
    return user_services
