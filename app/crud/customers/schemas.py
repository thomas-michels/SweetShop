from typing import List, Optional

from pydantic import Field

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.shared_schemas.address import Address
from app.crud.tags.schemas import TagInDB


class Customer(GenericModel):
    name: str = Field(example="Ted Mosby")
    ddd: str | None = Field(default=None, example="047", max_length=3, pattern=r"^\d+$")
    phone_number: str | None = Field(default=None, max_length=9, pattern=r"^\d+$")
    addresses: List[Address] = Field(default=[])
    tags: List[str] = Field(default=[])

    def validate_updated_fields(self, update_customer: "UpdateCustomer") -> bool:
        is_updated = False

        if update_customer.name is not None:
            self.name = update_customer.name
            is_updated = True

        if update_customer.ddd is not None:
            self.ddd = update_customer.ddd
            is_updated = True

        if update_customer.phone_number is not None:
            self.phone_number = update_customer.phone_number
            is_updated = True

        if update_customer.addresses is not None:
            self.addresses = update_customer.addresses
            is_updated = True

        if update_customer.tags is not None:
            self.tags = update_customer.tags
            is_updated = True

        return is_updated

class UpdateCustomer(GenericModel):
    name: Optional[str] = Field(default=None, example="Ted Mosby")
    ddd: Optional[str] = Field(default=None, example="047", max_length=3, pattern=r"^\d+$")
    phone_number: Optional[str] = Field(default=None, max_length=9, pattern=r"^\d+$")
    addresses: Optional[List[Address]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)


class CustomerInDB(Customer, DatabaseModel):
    is_active: bool = Field(example=True, exclude=True)
    organization_id: str = Field(example="org_123")


class CompleteCustomerInDB(Customer, DatabaseModel):
    tags: List[str] | List[TagInDB] = Field()
