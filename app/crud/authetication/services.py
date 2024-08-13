from app.api.shared_schemas.token import TokenData
from app.crud.users.schemas import UserInDB
from app.crud.users.repositories import UserRepository

from .models import UserSignin


class AuthenticationServices:
    def __init__(self, user_repository: UserRepository) -> None:
        self.__user_repository = user_repository

    async def signin(self, user: UserSignin) -> UserInDB:
        user_in_db = await self.__user_repository.select_by_email(email=user.email)

        is_correct = user_in_db.verify_password(user.password.get_secret_value())

        if is_correct:
            return user_in_db

    async def get_current_user(self, token: TokenData) -> UserInDB:
        user_in_db = await self.__user_repository.select_by_id(id=token.id)
        return user_in_db
