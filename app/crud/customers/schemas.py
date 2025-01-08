from typing import List, Optional

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.shared_schemas.address import Address
from app.crud.tags.schemas import TagInDB


class Customer(GenericModel):
    name: str = Field(example="Ted Mosby")
    ddd: str | None = Field(default=None, example="047", max_length=3)
    phone_number: str | None = Field(default=None, max_length=9)
    addresses: List[Address] = Field(default=[])
    tags: List[str] = Field(default=[])

    @model_validator(mode="after")
    def validate_model(self) -> "Customer":
        if self.ddd is not None and self.phone_number is not None:
            if not self.ddd.isdigit() or not self.phone_number.isdigit():
                raise ValueError("DDD or phone number must be only numbers")

            if len(self.ddd) != 3:
                raise ValueError("DDD must have 3 numbers")

            if len(self.phone_number) not in [8, 9]:
                raise ValueError("Phone number must have 8 or 9 digits")

        return self

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
    ddd: Optional[str] = Field(default=None, example="047", max_length=3)
    phone_number: Optional[str] = Field(default=None, max_length=9)
    addresses: Optional[List[Address]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdateCustomer":
        if self.ddd is not None and self.phone_number is not None:
            if not self.ddd.isdigit() or not self.phone_number.isdigit():
                raise ValueError("DDD or phone number must be only numbers")

            if len(self.ddd) != 3:
                raise ValueError("DDD must have 3 numbers")

            if len(self.phone_number) not in [8, 9]:
                raise ValueError("Phone number must have 8 or 9 digits")

        return self


class CustomerInDB(Customer, DatabaseModel):
    is_active: bool = Field(example=True, exclude=True)
    organization_id: str = Field(example="org_123")


class CompleteCustomerInDB(Customer, DatabaseModel):
    tags: List[str] | List[TagInDB] = Field()
