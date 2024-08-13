import re
from typing import Optional, Type

from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from app.core.exceptions import InvalidPassword, UnprocessableEntity
from app.core.models import DatabaseModel

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()\-=_+{};:\'"\\|,.<>?]).+$'


class ConfirmPassword(BaseModel):
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


class User(BaseModel):
    first_name: str = Field(example="FirstName")
    last_name: str = Field(example="LastName")
    email: EmailStr = Field(example="email@mail.com")

    model_config = ConfigDict(extra="allow", from_attributes=True)

    def validate_updated_fields(self, updated_user: Type["UpdateUser"]) -> bool:
        is_updated = False

        if updated_user.first_name:
            self.first_name = updated_user.first_name
            is_updated = True

        if updated_user.last_name:
            self.last_name = updated_user.last_name
            is_updated = True

        if updated_user.email:
            self.email = updated_user.email
            is_updated = True

        return is_updated


class UpdateUser(BaseModel):
    first_name: Optional[str] = Field(default=None, example="FirstName")
    last_name: Optional[str] = Field(default=None, example="LastName")
    email: Optional[EmailStr] = Field(default=None, example="email@mail.com")


class UserInDB(User, DatabaseModel):
    password: SecretStr = Field(example="abc@1234#", exclude=True)
    is_active: bool = Field(example=True, exclude=True)

    def verify_password(self, password: str) -> bool:
        return _pwd_context.verify(password, self.password.get_secret_value())
