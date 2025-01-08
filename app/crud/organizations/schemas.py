from enum import Enum
from typing import List, Optional, Type

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.shared_schemas.address import Address
from app.crud.users.schemas import UserInDB


class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"
    CLIENT = "CLIENT"


class UserOrganization(GenericModel):
    user_id: str = Field(example="user_123")
    role: RoleEnum = Field(example=RoleEnum.ADMIN.value)


class CompleteUserOrganization(GenericModel):
    user: UserInDB | None = Field(default=None)
    user_id: str = Field(example="user_123", exclude=True)
    role: RoleEnum = Field(example=RoleEnum.ADMIN.value)


class Organization(GenericModel):
    name: str = Field(example="org_123", max_length=100)
    ddd: str | None = Field(default=None, example="047", max_length=3)
    phone_number: str | None = Field(default=None, max_length=9)
    address: Address = Field()

    @model_validator(mode="after")
    def validate_model(self) -> "Organization":
        if self.ddd is not None and self.phone_number is not None:
            if not self.ddd.isdigit() or not self.phone_number.isdigit():
                raise ValueError("DDD or phone number must be only numbers")

            if len(self.ddd) != 3:
                raise ValueError("DDD must have 3 numbers")

            if len(self.phone_number) not in [8, 9]:
                raise ValueError("Phone number must have 8 or 9 digits")

        return self

    def validate_updated_fields(self, update_organization: Type["UpdateOrganization"]) -> bool:
        is_updated = False

        if update_organization.name is not None:
            self.name = update_organization.name
            is_updated = True

        if update_organization.ddd is not None:
            self.ddd = update_organization.ddd
            is_updated = True

        if update_organization.phone_number is not None:
            self.phone_number = update_organization.phone_number
            is_updated = True

        if update_organization.address is not None:
            self.address = update_organization.address
            is_updated = True

        return is_updated


class UpdateOrganization(GenericModel):
    name: Optional[str] = Field(default=None, example="org_123", max_length=100)
    ddd: Optional[str] = Field(default=None, example="047", max_length=3, pattern=r"^\d+$")
    phone_number: Optional[str] = Field(default=None, max_length=9, pattern=r"^\d+$")
    address: Optional[Address] = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdateOrganization":
        if self.ddd is not None and self.phone_number is not None:
            if not self.ddd.isdigit() or not self.phone_number.isdigit():
                raise ValueError("DDD or phone number must be only numbers")

            if len(self.ddd) != 3:
                raise ValueError("DDD must have 3 numbers")

            if len(self.phone_number) not in [8, 9]:
                raise ValueError("Phone number must have 8 or 9 digits")

        return self


class OrganizationInDB(Organization, DatabaseModel):
    users: List[UserOrganization] | None = Field(default=[])

    @model_validator(mode="after")
    def validate_model(self) -> "OrganizationInDB":
        if self.users is None:
            self.users = []

        return self

    def get_user_in_organization(self, user_id: str) -> UserOrganization:
        for user in self.users:
            if user.user_id == user_id:
                return user

    def delete_user(self, user_id: str) -> bool:
        user = self.get_user_in_organization(user_id=user_id)

        if user:
            self.users.remove(user)
            return True

        return False


class CompleteOrganization(OrganizationInDB):
    users: List[CompleteUserOrganization] | None = Field(default=[])
