from enum import Enum
from typing import Dict, Optional, Type

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.shared_schemas.address import Address


class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"
    CLIENT = "CLIENT"


class Organization(GenericModel):
    name: str = Field(example="org_123", max_length=100)
    ddd: str | None = Field(default=None, example="047", max_length=3, pattern=r"^\d+$")
    phone_number: str | None = Field(default=None, max_length=9, pattern=r"^\d+$")
    address: Address = Field()

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


class OrganizationInDB(Organization, DatabaseModel):
    users: Dict[str, RoleEnum] | None = Field(default={}, example=RoleEnum.MANAGER)

    @model_validator(mode="after")
    def validate_model(self) -> "OrganizationInDB":
        if self.users is None:
            self.users = {}

        return self
