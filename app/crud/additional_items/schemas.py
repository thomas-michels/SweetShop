from typing import Optional

from pydantic import Field
from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.files.schemas import FileInDB

class AdditionalItem(GenericModel):
    position: int = Field(example=1)
    product_id: str | None = Field(default=None, example="prod_123")
    file_id: str | None = Field(default=None, example="file_123")
    label: str = Field(example="Extra")
    unit_price: float = Field(example=0.0)
    unit_cost: float = Field(example=0.0)
    consumption_factor: float = Field(ge=0, le=1, example=1.0)

    def validate_updated_fields(self, update: "UpdateAdditionalItem") -> bool:
        is_updated = False

        if update.position is not None:
            self.position = update.position
            is_updated = True

        if update.product_id is not None:
            self.product_id = update.product_id
            is_updated = True

        if update.file_id is not None:
            self.file_id = update.file_id
            is_updated = True

        if update.label is not None:
            self.label = update.label
            is_updated = True

        if update.unit_price is not None:
            self.unit_price = update.unit_price
            is_updated = True

        if update.unit_cost is not None:
            self.unit_cost = update.unit_cost
            is_updated = True

        if update.consumption_factor is not None:
            self.consumption_factor = update.consumption_factor
            is_updated = True

        return is_updated


class UpdateAdditionalItem(GenericModel):
    position: Optional[int] = Field(default=None, example=1)
    product_id: Optional[str] = Field(default=None, example="prod_123")
    file_id: Optional[str] = Field(default=None, example="file_123")
    label: Optional[str] = Field(default=None, example="Extra")
    unit_price: Optional[float] = Field(default=None, example=0.0)
    unit_cost: Optional[float] = Field(default=None, example=0.0)
    consumption_factor: Optional[float] = Field(default=None, ge=0, le=1, example=1.0)


class AdditionalItemInDB(AdditionalItem, DatabaseModel):
    organization_id: str = Field(example="org_123")
    additional_id: str = Field(example="add_123")


class CompleteAdditionalItem(AdditionalItemInDB):
    file: FileInDB | None = Field(default=None)
