from fastapi import Depends

from app.core.db import get_repository
from app.crud.users.repositories import UserRepository
from app.crud.users.services import UserServices


async def user_composer(
    user_repository: UserRepository = Depends(get_repository(UserRepository)),
) -> UserServices:
    user_services = UserServices(user_repository=user_repository)
    return user_services
