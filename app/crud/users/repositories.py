from datetime import datetime

from typing import List

from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .schemas import User, UserInDB
from .models import UserModel

_logger = get_logger(__name__)


class UserRepository(Repository):
    def __init__(self) -> None:
        super().__init__()

    async def create(self, user: User) -> UserInDB:
        try:
            user_model = UserModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **user.model_dump()
            )

            user_model.save()

            return UserInDB.model_validate(user_model)

        except Exception as error:
            _logger.error(f"Error on create_user: {str(error)}")
            raise UnprocessableEntity(message="Error on create new user")

    async def update(self, user: UserInDB) -> UserInDB:
        try:
            ...

        except Exception as error:
            _logger.error(f"Error on update_user: {str(error)}")
            raise UnprocessableEntity(message="Error on update user")

    async def select_by_id(self, id: int) -> UserInDB:
        try:
            ...

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"User #{id} not found")

    async def select_by_email(self, email: str) -> UserInDB:
        try:
            ...

        except Exception as error:
            _logger.error(f"Error on select_by_email: {str(error)}")
            raise NotFoundError(message=f"User with email {email} not found")

    async def select_all(self) -> List[UserInDB]:
        try:
            ...

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Users not found")

    async def delete_by_id(self, id: int) -> UserInDB:
        try:
            ...

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"User #{id} not found")
