from typing import List
from psycopg import Connection
from psycopg.errors import UniqueViolation
from app.core.repositories.base_repository import Repository
from app.core.configs import get_logger
from app.core.exceptions import UnprocessableEntity, NotFoundError
from .queries import queries
from .models import User, UserInDB

_logger = get_logger(__name__)


class UserRepository(Repository):

    def __init__(self, connection: Connection) -> None:
        super().__init__(connection)
        self.queries = queries

    async def create(self, user: User) -> UserInDB:
        try:
            raw_user = self.queries.create_user(
                conn=self.conn,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                password=user.password
            )

            return self.__build_user(raw_user=raw_user)
        
        except UniqueViolation as error:
            raise UnprocessableEntity(message="Email already in use")

        except Exception as error:
            _logger.error(f"Error on create_user: {str(error)}")
            raise UnprocessableEntity(message="Error on create new user")

    async def update(self, user: UserInDB) -> UserInDB:
        try:
            raw_user = self.queries.update_user_by_id(
                conn=self.conn,
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
            )

            return self.__build_user(raw_user=raw_user)
        
        except UniqueViolation as error:
            raise UnprocessableEntity(message="Email already in use")

        except Exception as error:
            _logger.error(f"Error on update_user: {str(error)}")
            raise UnprocessableEntity(message="Error on update user")

    async def select_by_id(self, id: int) -> UserInDB:
        try:
            raw_user = self.queries.select_user_by_id(
                conn=self.conn,
                id=id
            )

            return self.__build_user(raw_user=raw_user)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            raise NotFoundError(message=f"User #{id} not found")

    async def select_by_email(self, email: str) -> UserInDB:
        try:
            raw_user = self.queries.select_user_by_email(
                conn=self.conn,
                email=email
            )

            return self.__build_user(raw_user=raw_user)

        except Exception as error:
            _logger.error(f"Error on select_by_email: {str(error)}")
            raise NotFoundError(message=f"User with email {email} not found")
    
    async def select_all(self) -> List[UserInDB]:
        try:
            raw_users = self.queries.select_users(conn=self.conn)

            users = []

            for raw_user in raw_users:
                users.append(self.__build_user(raw_user=raw_user))

            return users

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Users not found")

    async def delete_by_id(self, id: int) -> UserInDB:
        try:
            raw_user = self.queries.delete_user_by_id(
                conn=self.conn,
                id=id
            )

            return self.__build_user(raw_user=raw_user)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"User #{id} not found")

    def __build_user(self, raw_user) -> UserInDB:
        return UserInDB(
            id=raw_user[0],
            first_name=raw_user[1],
            last_name=raw_user[2],
            email=raw_user[3],
            password=raw_user[4],
            is_active=raw_user[5],
            created_at=raw_user[6],
            updated_at=raw_user[7],
        )
