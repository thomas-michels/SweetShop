import traceback
from typing import List
from fastapi.encoders import jsonable_encoder
from app.core.configs import get_logger, get_environment
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.http_client import HTTPClient

from .schemas import UpdateUser, User, UserInDB

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
        _logger.info("Updating user by ID on Management API")
        try:
            raw_user = user.model_dump(exclude_none=True)
            raw_user["password"] = password

            status_code, response = self.http_client.post(
                url=f"{_env.AUTH0_ISSUER}/api/v2/users",
                data=jsonable_encoder(raw_user)
            )

            if status_code == 200:
                _logger.info("User updated successfully.")
                return UserInDB(**response)

            else:
                _logger.info(f"User not created.")

        except Exception as error:
            _logger.error(f"Error on update_user: {str(error)}")
            _logger.error(traceback.format_exc())
            raise UnprocessableEntity(message="Error on create new user")

    async def update(self, user_id: str, user: UpdateUser) -> UserInDB:
        _logger.info("Updating user by ID on Management API")
        try:
            status_code, response = self.http_client.patch(
                url=f"{_env.AUTH0_ISSUER}/api/v2/users/{user_id}",
                data=jsonable_encoder(user.model_dump(exclude_none=True))
            )

            if status_code == 200:
                _logger.info("User updated successfully.")
                return UserInDB(**response)

            else:
                _logger.info(f"User {user_id} not updated.")

        except Exception as error:
            _logger.error(f"Error on update_user: {str(error)}")
            _logger.error(traceback.format_exc())
            raise UnprocessableEntity(message="Error on update user")

    async def select_by_id(self, id: str) -> UserInDB:
        _logger.info("Getting user by ID on Management API")
        try:
            status_code, response = self.http_client.get(
                url=f"{_env.AUTH0_DOMAIN}/api/v2/users/{id}"
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
            status_code, response = self.http_client.get(
                url=f"{_env.AUTH0_ISSUER}/api/v2/users-by-email",
                params={"email": email}
            )

            if status_code == 200:
                _logger.info("User retrieved successfully.")
                return UserInDB(**response[0])

            else:
                _logger.info(f"User with email {email} not found.")

        except Exception as error:
            _logger.error(f"Error on select_by_email: {str(error)}")
            raise NotFoundError(message=f"User with email {email} not found")

    async def select_all(self) -> List[UserInDB]:
        try:
            users = []

            status_code, response = self.http_client.get(
                url=f"{_env.AUTH0_ISSUER}/api/v2/users"
            )

            if status_code == 200:
                _logger.info("Users retrieved successfully.")
                for raw_user in response:
                    users.append(UserInDB(**raw_user))

            return users

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            return []

    async def delete_by_id(self, id: str) -> UserInDB:
        _logger.info("Deleting a user by ID on Management API")
        try:
            status_code, response = self.http_client.delete(
                url=f"{_env.AUTH0_ISSUER}/api/v2/users/{id}"
            )

            if status_code == 204:
                _logger.info("User deleted successfully.")
                return True

            else:
                _logger.info(f"User {id} not deleted.")
                return False

        except Exception as error:
            _logger.error("Error on delete_user_by_id")
            _logger.error(str(error))
            _logger.error(traceback.format_exc())
            return False
