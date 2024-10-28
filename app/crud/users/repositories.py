from datetime import datetime

from typing import List
from mongoengine.errors import NotUniqueError
from app.core.configs import get_logger, get_environment
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.http_client import HTTPClient

from .schemas import User, UserInDB
from .models import UserModel

_logger = get_logger(__name__)
_env = get_environment()


class UserRepository:
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self.headers = {
            "authorization": self.access_token,
            "Content-Type": "application/json",
        }
        self.http_client = HTTPClient(headers=self.headers)

    async def create(self, user: User, password: str) -> UserInDB:
        try:
            user_model = UserModel(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                password=password,
                **user.model_dump()
            )

            user_model.save()

            return UserInDB.model_validate(user_model)

        except NotUniqueError:
            raise UnprocessableEntity(message="Email already used!")

        except Exception as error:
            _logger.error(f"Error on create_user: {str(error)}")
            raise UnprocessableEntity(message="Error on create new user")

    async def update(self, user: UserInDB) -> UserInDB:
        try:
            user_model: UserModel = UserModel.objects(id=user.id, is_active=True).first()

            user_model.update(**user.model_dump())

            return UserInDB.model_validate(user_model)

        except Exception as error:
            _logger.error(f"Error on update_user: {str(error)}")
            raise UnprocessableEntity(message="Error on update user")

    async def select_by_id(self, id: str) -> UserInDB:
        _logger.info("Getting user by ID on Management API")
        try:
            status_code, response = self.http_client.get(
                url=f"{_env.AUTH0_ISSUER}/api/v2/users/{id}"
            )

            if status_code == 200:
                _logger.info("User retrieved successfully.")
                return UserInDB(**response)

            else:
                _logger.info(f"User {id} not found.")

        except Exception as error:
            _logger.error("Error on select_by_id")
            _logger.error(str(error))

            raise NotFoundError(message=f"User #{id} not found")

    async def select_by_email(self, email: str) -> UserInDB:
        try:
            user_model: UserModel = UserModel.objects(email=email, is_active=True).first()

            return UserInDB.model_validate(user_model)

        except Exception as error:
            _logger.error(f"Error on select_by_email: {str(error)}")
            raise NotFoundError(message=f"User with email {email} not found")

    async def select_all(self) -> List[UserInDB]:
        try:
            users = []

            for user_model in UserModel.objects(is_active=True):
                users.append(UserInDB.model_validate(user_model))

            return users

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Users not found")

    async def delete_by_id(self, id: str) -> UserInDB:
        try:
            user_model: UserModel = UserModel.objects(id=id, is_active=True).first()
            user_model.delete()

            return UserInDB.model_validate(user_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"User #{id} not found")
