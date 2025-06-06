from typing import List, Optional

from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.core.utils.utc_datetime import UTCDateTime, UTCDateTimeType
from app.crud.shared_schemas.payment import Payment
from app.crud.tags.schemas import TagInDB


class Expense(GenericModel):
    name: str = Field(example="Brasil Atacadista")
    expense_date: UTCDateTimeType = Field(example=str(UTCDateTime.now()))
    payment_details: List[Payment] = Field(default=[])
    tags: List[str] = Field(default=[])

    @model_validator(mode="after")
    def validate_model(self) -> "Expense":
        if self.expense_date.second != 0:
            self.expense_date = UTCDateTime(
                year=self.expense_date.year,
                month=self.expense_date.month,
                day=self.expense_date.day,
            )

        if len(self.tags) != len(set(self.tags)):
            raise ValueError("Tags must contain unique items.")

        return self

    def validate_updated_fields(self, update_expense: "UpdateExpense") -> bool:
        is_updated = False

        if update_expense.name is not None:
            self.name = update_expense.name
            is_updated = True

        if update_expense.expense_date is not None:
            self.expense_date = update_expense.expense_date
            is_updated = True

        if update_expense.payment_details is not None:
            self.payment_details = update_expense.payment_details
            is_updated = True

        if update_expense.tags is not None:
            self.tags = update_expense.tags
            is_updated = True

        return is_updated


class UpdateExpense(GenericModel):
    name: Optional[str] = Field(default=None, example="Brasil Atacadista")
    expense_date: Optional[UTCDateTimeType] = Field(
        default=None, example=str(UTCDateTime.now())
    )
    payment_details: Optional[List[Payment]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> "Expense":
        if self.expense_date is not None and self.expense_date.second != 0:
            self.expense_date = UTCDateTime(
                year=self.expense_date.year,
                month=self.expense_date.month,
                day=self.expense_date.day,
            )

        if self.tags is not None:
            if len(self.tags) != len(set(self.tags)):
                raise ValueError("Tags must contain unique items.")

        return self


class ExpenseInDB(Expense, DatabaseModel):
    organization_id: str = Field(example="org_123")
    total_paid: float = Field(gt=0, example=150)


class CompleteExpense(ExpenseInDB):
    tags: List[str | TagInDB] = Field(default=[])
