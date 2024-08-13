from typing import List
from .schemas import User, UpdateUser, UserInDB, ConfirmPassword
from .repositories import UserRepository


class UserServices:

    def __init__(self, user_repository: UserRepository) -> None:
        self.__repository = user_repository

    async def create(self, user: User, confirm_password: ConfirmPassword) -> UserInDB:
        confirm_password.validate_password()
        user.password = confirm_password.get_password(confirm_password.password.get_secret_value())

        user_in_db = await self.__repository.create(user=user)
        return user_in_db

    async def update(self, id: int, updated_user: UpdateUser) -> UserInDB:
        user_in_db = await self.search_by_id(id=id)

        is_updated = user_in_db.validate_updated_fields(updated_user=updated_user)

        if is_updated:
            user_in_db = await self.__repository.update(user=user_in_db)

        return user_in_db

    async def search_by_id(self, id: int) -> UserInDB:
        user_in_db = await self.__repository.select_by_id(id=id)
        return user_in_db

    async def search_all(self) -> List[UserInDB]:
        users = await self.__repository.select_all()
        return users

    async def delete_by_id(self, id: int) -> UserInDB:
        user_in_db = await self.__repository.delete_by_id(id=id)
        return user_in_db
