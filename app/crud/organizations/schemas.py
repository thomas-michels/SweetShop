import re
from typing import List, Optional, Type

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.validate_document import validate_cnpj, validate_cpf
from app.crud.files.schemas import FileInDB
from app.crud.organization_plans.schemas import OrganizationPlanInDB
from app.crud.shared_schemas.address import Address
from app.crud.shared_schemas.currency import Currency
from app.crud.shared_schemas.distance import UnitDistance
from app.crud.shared_schemas.language import Language
from app.crud.shared_schemas.roles import RoleEnum
from app.crud.shared_schemas.user_organization import UserOrganization
from app.crud.shared_schemas.styling import Styling
from app.crud.users.schemas import UserInDB

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


class CompleteUserOrganization(GenericModel):
    user: UserInDB | None = Field(default=None)
    user_id: str = Field(example="user_123", exclude=True)
    role: RoleEnum = Field(example=RoleEnum.ADMIN.value)


class SocialLinks(GenericModel):
    tiktok: str | None = Field(default=None, example="https://tiktok.com/@your_company")
    instagram: str | None = Field(default=None, example="https://instagram.com/your_company")
    x: str | None = Field(default=None, example="https://x.com/your_company")
    facebook: str | None = Field(default=None, example="https://facebook.com/your_company")
    google_profile: str | None = Field(default=None, example="https://g.page/your_company")


class Organization(GenericModel):
    name: str = Field(example="org_123", max_length=100)
    international_code: str | None = Field(default=None, example="55")
    ddd: str | None = Field(default=None, example="047", max_length=3)
    phone_number: str | None = Field(default=None, max_length=9)
    address: Address | None = Field(default=None)
    email: str | None = Field(default=None, example="contact@your_company.com")
    document: str | None = Field(default=None, example="111.555.219-99")
    currency: Currency | None = Field(default=None, example=Currency.BRL)
    language: Language | None = Field(default=None, example=Language.PORTUGUESE)
    file_id: str | None = Field(default=None, example="file_123")
    unit_distance: UnitDistance | None = Field(default=None, example=UnitDistance.KM)
    tax: float | None = Field(default=0, example=10)
    website: str | None = Field(default=None, example="https://your_company.com")
    social_links: SocialLinks | None = Field(default=None)
    styling: Styling | None = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "Organization":
        if self.international_code is None:
            self.international_code = "55"

        if self.ddd is not None and self.phone_number is not None:
            if not self.ddd.isdigit() or not self.phone_number.isdigit():
                raise ValueError("DDD or phone number must be only numbers")

            if len(self.ddd) != 3:
                raise ValueError("DDD must have 3 numbers")

            if len(self.phone_number) not in [8, 9]:
                raise ValueError("Phone number must have 7, 8 or 9 digits")

        if self.email is not None:
            if not re.match(EMAIL_REGEX, self.email):
                raise ValueError("Invalid email")

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

        if self.tax is not None:
            if self.tax < 0:
                raise ValueError("O imposto deve ser maior ou igual a zero")

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

        if update_organization.file_id is not None:
            self.file_id = update_organization.file_id
            is_updated = True

        if update_organization.document is not None:
            self.document = update_organization.document

        if update_organization.international_code is not None:
            self.international_code = update_organization.international_code

        if update_organization.language is not None:
            self.language = update_organization.language
            is_updated = True

        if update_organization.currency is not None:
            self.currency = update_organization.currency
            is_updated = True

        if update_organization.unit_distance is not None:
            self.unit_distance = update_organization.unit_distance
            is_updated = True

        if update_organization.tax is not None:
            self.tax = update_organization.tax
            is_updated = True

        if update_organization.website is not None:
            self.website = update_organization.website
            is_updated = True

        if update_organization.social_links is not None:
            self.social_links = update_organization.social_links
            is_updated = True

        if update_organization.styling is not None:
            self.styling = update_organization.styling
            is_updated = True

        return is_updated


class UpdateOrganization(GenericModel):
    name: Optional[str] = Field(default=None, example="org_123", max_length=100)
    international_code: Optional[str] = Field(default=None, example="+55")
    ddd: Optional[str] = Field(default=None, example="047", max_length=3, pattern=r"^\d+$")
    phone_number: Optional[str] = Field(default=None, max_length=9, pattern=r"^\d+$")
    email: Optional[str] = Field(default=None)
    address: Optional[Address] = Field(default=None)
    file_id: Optional[str] = Field(default=None)
    document: Optional[str] = Field(default=None)
    language: Optional[Language] = Field(default=None)
    currency: Optional[Currency] = Field(default=None)
    unit_distance: Optional[UnitDistance] = Field(default=None)
    tax: Optional[float] = Field(default=None)
    website: Optional[str] = Field(default=None)
    social_links: Optional[SocialLinks] = Field(default=None)
    styling: Optional[Styling] = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdateOrganization":
        if self.ddd is not None and self.phone_number is not None:
            if not self.ddd.isdigit() or not self.phone_number.isdigit():
                raise ValueError("DDD or phone number must be only numbers")

            if len(self.ddd) != 3:
                raise ValueError("DDD must have 3 numbers")

            if len(self.phone_number) not in [7, 8, 9]:
                raise ValueError("Phone number must have 7, 8 or 9 digits")

        if self.email is not None:
            if not re.match(EMAIL_REGEX, self.email):
                raise ValueError("Invalid email")

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

        if self.tax is not None:
            if self.tax < 0:
                raise ValueError("O imposto deve ser maior ou igual a zero")

        return self


class OrganizationInDB(Organization, DatabaseModel):
    users: List[UserOrganization] | None = Field(default=[])
    plan: OrganizationPlanInDB | None = Field(default=None)
    slug: str = Field(example="doces")

    @model_validator(mode="after")
    def validate_model(self) -> "OrganizationInDB":
        if isinstance(self.address, dict):
            self.address = None

        if self.users is None:
            self.users = []

        if isinstance(self.social_links, dict):
            self.social_links = SocialLinks(**self.social_links)

        if isinstance(self.styling, dict):
            self.styling = Styling(**self.styling)

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
    file: str | None | FileInDB = Field(default=None)
