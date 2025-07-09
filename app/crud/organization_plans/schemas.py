from typing import Optional

from pydantic import Field, computed_field

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType


class OrganizationPlan(GenericModel):
    plan_id: str = Field(example="plan_123")
    start_date: UTCDateTimeType = Field(example=str(UTCDateTime.now()))
    end_date: UTCDateTimeType = Field(example=str(UTCDateTime.now()))
    allow_additional: bool = Field(default=False, example=False)

    def validate_updated_fields(
        self, update_organization_plan: "UpdateOrganizationPlan"
    ) -> bool:
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
    start_date: Optional[UTCDateTimeType] = Field(default=None, example=str(UTCDateTime.now()))
    end_date: Optional[UTCDateTimeType] = Field(default=None, example=str(UTCDateTime.now()))
    allow_additional: Optional[bool] = Field(default=None, example=False)


class OrganizationPlanInDB(OrganizationPlan, DatabaseModel):
    organization_id: str = Field(example="org_123")
    has_paid_invoice: bool | None = Field(default=None, example=True)

    @computed_field
    @property
    def active_plan(self) -> bool:
        return self.calculate_active_plan()

    def calculate_active_plan(self) -> bool:
        now = UTCDateTime.now()
        return (self.start_date <= now <= self.end_date) and self.has_paid_invoice
