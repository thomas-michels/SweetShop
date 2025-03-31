from typing import Optional

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.features import Feature, get_translation


class PlanFeature(GenericModel):
    plan_id: str = Field(example="plan_123")
    name: Feature = Field(example=Feature.DISPLAY_CALENDAR.value)
    display_name: str | None = Field(default=None)
    value: str = Field(example="123")
    display_value: str | None = Field(default=None)
    additional_price: float = Field(example=123)
    allow_additional: bool = Field(default=False, example=False)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdatePlanFeature":
        if self.allow_additional:
            if self.additional_price <= 0:
                raise ValueError("additional_price should be grater than zero")

        else:
            if self.additional_price != 0:
                raise ValueError("additional_price should be zero if additionals are allowed")

        self.display_name = get_translation(name=self.name)

        self.display_value = self.value

        if self.display_value == "-":
            self.display_value = get_translation(name=self.value)

        return self

    def validate_updated_fields(self, update_plan_feature: "UpdatePlanFeature") -> bool:
        is_updated = False

        if update_plan_feature.name is not None:
            self.name = update_plan_feature.name
            is_updated = True

        if update_plan_feature.value is not None:
            self.value = update_plan_feature.value
            is_updated = True

        if update_plan_feature.additional_price is not None:
            self.additional_price = update_plan_feature.additional_price
            is_updated = True

        return is_updated


class UpdatePlanFeature(GenericModel):
    name: Optional[Feature] = Field(default=None, example=Feature.DISPLAY_CALENDAR.value)
    value: Optional[str] = Field(default=None, example="123")
    additional_price: Optional[float] = Field(default=None, example=123)
    allow_additional: Optional[bool] = Field(default=None, example=False)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdatePlanFeature":
        if self.allow_additional is not None and self.additional_price is not None:
            if self.allow_additional:
                if self.additional_price <= 0:
                    raise ValueError("additional_price should be grater than zero")

            else:
                if self.additional_price != 0:
                    raise ValueError("additional_price should be zero if additionals are allowed")

        else:
            if self.allow_additional is not None or self.additional_price is not None:
                raise ValueError("allow_additional and additional_price should set together")


class PlanFeatureInDB(PlanFeature, DatabaseModel):
    ...
