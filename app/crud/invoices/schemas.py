from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class InvoiceStatus(str, Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Invoice(GenericModel):
    organization_plan_id: str = Field(example="org_plan_123")
    integration_id: str = Field(example="org_plan_123")
    integration_type: str = Field(example="org_plan_123")
    amount: float = Field(example=39.9)
    amount_paid: float | None = Field(default=None, example=39.9)
    paid_at: datetime | None = Field(default=None, example=str(datetime.now()))
    status: InvoiceStatus = Field(default=InvoiceStatus.PENDING, example=InvoiceStatus.PENDING)
    observation: dict | None = Field(default=None, example={})

    @model_validator(mode="after")
    def validate_model(self) -> "UpdateInvoice":
        if self.amount < 0:
            raise ValueError("amount should be grater than zero")

        if self.amount_paid and self.amount_paid < 0:
            raise ValueError("amount_paid should be grater than zero")

        return self

    def validate_updated_fields(self, update_invoice: "UpdateInvoice") -> bool:
        is_updated = False

        if update_invoice.integration_id is not None:
            self.integration_id = update_invoice.integration_id
            is_updated = True

        if update_invoice.amount is not None:
            self.amount = update_invoice.amount
            is_updated = True

        if update_invoice.amount_paid is not None:
            self.amount_paid = update_invoice.amount_paid
            is_updated = True

        if update_invoice.paid_at is not None:
            self.paid_at = update_invoice.paid_at
            is_updated = True

        if update_invoice.status is not None:
            self.status = update_invoice.status
            is_updated = True

        if update_invoice.observation is not None:
            self.observation = update_invoice.observation
            is_updated = True

        return is_updated


class UpdateInvoice(GenericModel):
    integration_id: Optional[str] = Field(default=None, example="org_plan_123")
    amount: Optional[float] = Field(default=None, example=39.9)
    amount_paid: Optional[float] = Field(default=None, example=39.9)
    paid_at: Optional[datetime] = Field(default=None, example=str(datetime.now()))
    status: Optional[InvoiceStatus] = Field(default=None, example=InvoiceStatus.PENDING)
    observation: Optional[dict] = Field(default=None, example={})

    @model_validator(mode="after")
    def validate_model(self) -> "UpdateInvoice":
        if self.amount is not None:
            if self.amount <= 0:
                raise ValueError("amount should be grater than zero")

        if self.amount_paid and self.amount_paid <= 0:
            raise ValueError("amount_paid should be grater than zero")

        return self


class InvoiceInDB(Invoice, DatabaseModel): ...
