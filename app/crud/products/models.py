from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.core.models import DatabaseModel


class Product(BaseModel):
    name: str = Field(example="Brigadeiro")
    unit_price: float = Field(example=1.5)
    unit_cost: float = Field(example=0.75)

    @model_validator(mode="after")
    def validate_price_and_cost(self) -> "Product":
        if self.unit_cost > self.unit_price:
            raise ValueError("Unit price should be greater than unit cost")

        return self


class UpdateProduct(BaseModel):
    name: Optional[str] = Field(example="Brigadeiro")
    unit_price: Optional[float] = Field(example=1.5)
    unit_cost: Optional[float] = Field(example=0.75)

    @model_validator(mode="after")
    def validate_price_and_cost(self) -> "Product":
        if self.unit_cost > self.unit_price:
            raise ValueError("Unit price should be greater than unit cost")

        return self


class ProductInDB(Product, DatabaseModel):
    is_active: bool = Field(example=True)
