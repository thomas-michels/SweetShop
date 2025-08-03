from enum import Enum
from typing import List, Optional

from pydantic import Field

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.additional_items import AdditionalItem
from app.crud.additional_items.schemas import AdditionalItemInDB


class OptionKind(str, Enum):
    RADIO = "RADIO"
    CHECKBOX = "CHECKBOX"
    NUMBER = "NUMBER"


class ProductAdditional(GenericModel):
    name: str = Field(example="Toppings")
    selection_type: OptionKind = Field(example=OptionKind.RADIO)
    min_quantity: int = Field(example=0)
    max_quantity: int = Field(example=1)
    position: int = Field(example=1)
    items: List[AdditionalItem] = Field(default=[], example=[
        {
            "position": 1,
            "product_id": "prod_123",
            "label": "Extra",
            "unit_price": 10,
            "unit_cost": 5,
            "consumption_factor": 1
        }
    ])

    def validate_updated_fields(self, update: "UpdateProductAdditional") -> bool:
        is_updated = False

        if update.name is not None:
            self.name = update.name
            is_updated = True

        if update.selection_type is not None:
            self.selection_type = update.selection_type
            is_updated = True

        if update.min_quantity is not None:
            self.min_quantity = update.min_quantity
            is_updated = True

        if update.max_quantity is not None:
            self.max_quantity = update.max_quantity
            is_updated = True

        if update.position is not None:
            self.position = update.position
            is_updated = True

        if update.items is not None:
            self.items = update.items
            is_updated = True

        return is_updated


class UpdateProductAdditional(GenericModel):
    name: Optional[str] = Field(default=None, example="Toppings")
    selection_type: Optional[OptionKind] = Field(default=None, example=OptionKind.RADIO)
    min_quantity: Optional[int] = Field(default=None, example=0)
    max_quantity: Optional[int] = Field(default=None, example=1)
    position: Optional[int] = Field(default=None, example=1)
    items: Optional[List[AdditionalItem]] = Field(default=None)


class ProductAdditionalInDB(ProductAdditional, DatabaseModel):
    organization_id: str = Field(example="org_123")
    product_id: str = Field(example="prod_123")
    items: List[AdditionalItemInDB] = Field(default=[], example=[
        {
            "position": 1,
            "product_id": "prod_123",
            "label": "Extra",
            "unit_price": 10,
            "unit_cost": 5,
            "consumption_factor": 1
        }
    ])
