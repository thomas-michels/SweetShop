import re
from typing import List, Optional, Type

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.validate_document import validate_cnpj, validate_cpf
from app.crud.shared_schemas.address import Address
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.shared_schemas.user_organization import UserOrganization
from app.crud.users.schemas import UserInDB

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


class CompleteUserOrganization(GenericModel):
    user: UserInDB | None = Field(default=None)
    user_id: str = Field(example="user_123", exclude=True)
    role: RoleEnum = Field(example=RoleEnum.ADMIN.value)


class Organization(GenericModel):
    name: str = Field(example="org_123", max_length=100)
    ddd: str | None = Field(default=None, example="047", max_length=3)
    phone_number: str | None = Field(default=None, max_length=9)
    address: Address | None = Field(default=None)
    email: str | None = Field(default=None, example="contact@your_company.com")
    due_day: int | None = Field(default=None, example=10)
    document: str | None = Field(default=None, example="111.555.219-99")

    @model_validator(mode="after")
    def validate_model(self) -> "Organization":
        if self.ddd is not None and self.phone_number is not None:
            if not self.ddd.isdigit() or not self.phone_number.isdigit():
                raise ValueError("DDD or phone number must be only numbers")

            if len(self.ddd) != 3:
                raise ValueError("DDD must have 3 numbers")

            if len(self.phone_number) not in [8, 9]:
                raise ValueError("Phone number must have 8 or 9 digits")

        if self.email is not None:
            if not re.match(EMAIL_REGEX, self.email):
                raise ValueError("Invalid email")

        if self.due_day is not None:
            if self.due_day not in [5, 10, 15, 20]:
                raise ValueError("Due day should be day 5, 10, 15 or 20")

        if self.document is not None:
            self.document = re.sub(r'\D', '', self.document)

            if len(self.document) == 11:
                if not validate_cpf(self.document):
                    raise ValueError("Invalid CPF")

            elif len(self.document) == 14:
                if not validate_cnpj(self.document):
                    raise ValueError("Invalid CNPJ")

            else:
                raise ValueError("Document must be a valid CPF or CNPJ")

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

        if update_organization.email is not None:
            self.email = update_organization.email
            is_updated = True

        if update_organization.due_day is not None:
            self.due_day = update_organization.due_day
            is_updated = True

        if update_organization.document is not None:
            self.document = update_organization.document
            is_updated = True

        return is_updated


class UpdateOrganization(GenericModel):
    name: Optional[str] = Field(default=None, example="org_123", max_length=100)
    ddd: Optional[str] = Field(default=None, example="047", max_length=3, pattern=r"^\d+$")
    phone_number: Optional[str] = Field(default=None, max_length=9, pattern=r"^\d+$")
    email: Optional[str] = Field(default=None)
    address: Optional[Address] = Field(default=None)
    due_day: Optional[int] = Field(default=None)
    document: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdateOrganization":
        if self.ddd is not None and self.phone_number is not None:
            if not self.ddd.isdigit() or not self.phone_number.isdigit():
                raise ValueError("DDD or phone number must be only numbers")

            if len(self.ddd) != 3:
                raise ValueError("DDD must have 3 numbers")

            if len(self.phone_number) not in [8, 9]:
                raise ValueError("Phone number must have 8 or 9 digits")

        if self.email is not None:
            if not re.match(EMAIL_REGEX, self.email):
                raise ValueError("Invalid email")

        if self.due_day is not None:
            if self.due_day not in [5, 10, 15, 20]:
                raise ValueError("Due day should be day 5, 10, 15 or 20")

        if self.document is not None:
            self.document = re.sub(r'\D', '', self.document)

            if len(self.document) == 11:
                if not validate_cpf(self.document):
                    raise ValueError("Invalid CPF")

            elif len(self.document) == 14:
                if not validate_cnpj(self.document):
                    raise ValueError("Invalid CNPJ")

            else:
                raise ValueError("Document must be a valid CPF or CNPJ")

        return self


class OrganizationInDB(Organization, DatabaseModel):
    users: List[UserOrganization] | None = Field(default=[])

    @model_validator(mode="after")
    def validate_model(self) -> "OrganizationInDB":
        if isinstance(self.address, dict):
            self.address = None

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
