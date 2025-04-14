import re
from datetime import datetime
from typing import Dict, List
from passlib.context import CryptContext
from pydantic import ConfigDict, Field, SecretStr
from app.core.exceptions import InvalidPassword, UnprocessableEntity
from app.core.models.base_schema import GenericModel
from app.crud.shared_schemas.user_organization import UserOrganization

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()\-=_+{};:\'"\\|,.<>?]).+$'


class ConfirmPassword(GenericModel):
    password: SecretStr = Field(example="abc@1234#", exclude=True)
    repeat_password: SecretStr = Field(example="abc@1234#", exclude=True)

    def validate_password(self) -> None:
        errors = []

        if self.password.get_secret_value() != self.repeat_password.get_secret_value():
            raise UnprocessableEntity(message="Passwords needs to be equals")

        if len(self.password.get_secret_value()) < 8:
            errors.append("Minimum size is 8 characters.")

        if len(self.password.get_secret_value()) > 24:
            errors.append("Maximum size is 24 characters.")

        if not re.match(_PASSWORD_REGEX, self.password.get_secret_value()):
            errors.append(
                "The password must have special characters and uppercase and lowercase letters."
            )

        if errors:
            raise InvalidPassword(message=" ".join(errors))

    def get_password(self, password: str) -> str:
        return _pwd_context.hash(password)


class User(GenericModel):
    email: str = Field(example="test@test.com")
    name: str = Field(example="test")
    nickname: str = Field(example="test")
    picture: str | None = Field(default=None, example="http://localhost")


class UserInDB(User):
    user_id: str = Field(example="id-123")
    user_metadata: dict | None = Field(default=None)
    app_metadata: dict | None = Field(default={})
    last_login: datetime | None = Field(default=None, example=str(datetime.now()))
    created_at: datetime = Field(example=str(datetime.now()))
    updated_at: datetime = Field(example=str(datetime.now()))

    model_config = ConfigDict(extra="allow", from_attributes=True)


class UpdateUser(GenericModel):
    blocked: bool | None = Field(default=None, example=True)
    email: str | None = Field(default=None, example="test@test.com")
    name: str | None= Field(default=None, example="test")
    nickname: str | None = Field(default=None, example="test")
    picture: str | None = Field(default=None, example="http://localhost")
    user_metadata: dict | None = Field(default=None)
    app_metadata: dict | None = Field(default=None)


class CompleteUserInDB(UserInDB):
    organizations: List[str] = Field(default=[])
    organizations_roles: Dict[str, UserOrganization] = Field(default={})
