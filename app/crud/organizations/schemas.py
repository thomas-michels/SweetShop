from enum import Enum
from typing import Dict, Optional, Type

from pydantic import Field

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"
    CLIENT = "CLIENT"


class Address(GenericModel):
    street: str = Field(example="Rua de Testes")
    number: str = Field(example="123")
    neighborhood: str = Field(example="Bairro")
    city: str = Field(example="Blumenau")


class Organization(GenericModel):
    name: str = Field(example="org_123", max_length=100)
    address: Address = Field()

    def validate_updated_fields(self, update_organization: Type["UpdateOrganization"]) -> bool:
        is_updated = False

        if update_organization.name is not None:
            self.name = update_organization.name
            is_updated = True

        if update_organization.address is not None:
            self.address = update_organization.address
            is_updated = True

        return is_updated


class UpdateOrganization(GenericModel):
    name: Optional[str] = Field(default=None, example="org_123", max_length=100)
    address: Optional[Address] = Field(default=None)


class OrganizationInDB(Organization, DatabaseModel):
    users: Dict[str, RoleEnum] = Field(default={}, example=RoleEnum.MANAGER)
