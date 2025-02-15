from datetime import datetime
from typing import Optional

from pydantic import Field, computed_field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class OrganizationPlan(GenericModel):
    plan_id: str = Field(example="plan_123")
    start_date: datetime = Field(example=str(datetime.now()))
    end_date: datetime = Field(example=str(datetime.now()))
    allow_additional: bool = Field(default=False, example=False)

    @model_validator(mode="after")
    def validate_model(self) -> "OrganizationPlan":
        now = datetime.now()

        if self.end_date < now:
            raise ValueError("End date should be grater than now")

        return self

    def validate_updated_fields(self, update_organization_plan: "UpdateOrganizationPlan") -> bool:
        is_updated = False

        if update_organization_plan.plan_id is not None:
            self.plan_id = update_organization_plan.plan_id
            is_updated = True

        if update_organization_plan.start_date is not None:
            self.start_date = update_organization_plan.start_date
            is_updated = True

        if update_organization_plan.end_date is not None:
            self.end_date = update_organization_plan.end_date
            is_updated = True

        if update_organization_plan.allow_additional is not None:
            self.allow_additional = update_organization_plan.allow_additional
            is_updated = True

        return is_updated


class UpdateOrganizationPlan(GenericModel):
    plan_id: Optional[str] = Field(default=None, example="plan_123")
    start_date: Optional[datetime] = Field(default=None, example=str(datetime.now()))
    end_date: Optional[datetime] = Field(default=None, example=str(datetime.now()))
    allow_additional: Optional[bool] = Field(default=None, example=False)

    @model_validator(mode="after")
    def validate_model(self) -> "UpdateOrganizationPlan":
        now = datetime.now()

        if self.end_date < now:
            raise ValueError("End date should be grater than now")

        return self


class OrganizationPlanInDB(OrganizationPlan, DatabaseModel):
    organization_id: str = Field(example="org_123")
    has_paid_invoice: bool | None = Field(default=None, example=True)

    @computed_field
    @property
    def active_plan(self) -> bool:
        now = datetime.now()
        return self.start_date <= now <= self.end_date
