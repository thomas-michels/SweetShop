from typing import Optional

from pydantic import Field

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class Customer(GenericModel):
    name: str = Field(example="Ted Mosby")

    def validate_updated_fields(self, update_customer: "UpdateCustomer") -> bool:
        is_updated = False

        if update_customer.name:
            self.name = update_customer.name
            is_updated = True

        return is_updated

class UpdateCustomer(GenericModel):
    name: Optional[str] = Field(example="Ted Mosby")


class CustomerInDB(Customer, DatabaseModel):
    is_active: bool = Field(example=True, exclude=True)
