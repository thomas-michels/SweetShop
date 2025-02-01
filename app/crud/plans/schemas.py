from typing import Optional

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class Plan(GenericModel):
    name: str = Field(example="Advanced")
    description: str = Field(example="Description")
    price: float = Field(example=123)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdatePlan":
        if self.price <= 0:
            raise ValueError("Price should be grater than zero")

        return self

    def validate_updated_fields(self, update_plan: "UpdatePlan") -> bool:
        is_updated = False

        if update_plan.name is not None:
            self.name = update_plan.name
            is_updated = True

        if update_plan.description is not None:
            self.description = update_plan.description
            is_updated = True

        if update_plan.price is not None:
            self.price = update_plan.price
            is_updated = True

        return is_updated


class UpdatePlan(GenericModel):
    name: Optional[str] = Field(default=None, example="Advanced")
    description: Optional[str] = Field(default=None, example="Description")
    price: Optional[float] = Field(default=None, example=123)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdatePlan":
        if self.price <= 0:
            raise ValueError("Price should be grater than zero")

        return self


class PlanInDB(Plan, DatabaseModel):
    ...
