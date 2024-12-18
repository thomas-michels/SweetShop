from typing import Optional

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class Product(GenericModel):
    name: str = Field(example="Brigadeiro")
    description: str = Field(example="Brigadeiro de Leite Ninho")
    unit_price: float = Field(example=1.5)
    unit_cost: float = Field(example=0.75)

    @model_validator(mode="after")
    def validate_price_and_cost(self) -> "Product":
        if self.unit_cost > self.unit_price:
            raise ValueError("Unit price should be greater than unit cost")

        return self

    def validate_updated_fields(self, update_product: "UpdateProduct") -> bool:
        is_updated = False

        if update_product.name is not None:
            self.name = update_product.name
            is_updated = True

        if update_product.description is not None:
            self.description = update_product.description
            is_updated = True

        if update_product.unit_cost is not None:
            self.unit_cost = update_product.unit_cost
            is_updated = True

        if update_product.unit_price is not None:
            self.unit_price = update_product.unit_price
            is_updated = True

        return is_updated

class UpdateProduct(GenericModel):
    name: Optional[str] = Field(default=None, example="Brigadeiro")
    description: Optional[str] = Field(default=None, example="Brigadeiro de Leite Ninho")
    unit_price: Optional[float] = Field(default=None, example=1.5)
    unit_cost: Optional[float] = Field(default=None, example=0.75)

    @model_validator(mode="after")
    def validate_price_and_cost(self) -> "Product":
        if self.unit_cost and self.unit_price:
            if self.unit_cost > self.unit_price:
                raise ValueError("Unit price should be greater than unit cost")

        return self


class ProductInDB(Product, DatabaseModel):
    organization_id: str = Field(example="org_123")
    is_active: bool = Field(example=True, exclude=True)
