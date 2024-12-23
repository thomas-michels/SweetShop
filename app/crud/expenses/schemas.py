from typing import Optional
from datetime import date
from pydantic import Field, model_validator

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel


class Expense(GenericModel):
    name: str = Field(example="Brasil Atacadista")
    expense_date: date = Field(example=str(date.today()))
    total_paid: float = Field(gt=0, example=150)

    def validate_updated_fields(self, update_expense: "UpdateExpense") -> bool:
        is_updated = False

        if update_expense.name is not None:
            self.name = update_expense.name
            is_updated = True

        if update_expense.expense_date is not None:
            self.expense_date = update_expense.expense_date
            is_updated = True

        if update_expense.total_paid is not None:
            self.total_paid = update_expense.total_paid
            is_updated = True

        return is_updated


class UpdateExpense(GenericModel):
    name: Optional[str] = Field(default=None, example="Brasil Atacadista")
    expense_date: Optional[date] = Field(default=None, example=str(date.today()))
    total_paid: Optional[float] = Field(default=None, example=150)

    @model_validator(mode="after")
    def validate_total_paid(self) -> "UpdateExpense":
        if self.total_paid is not None:
            if self.total_paid < 0:
                raise ValueError("Total paid should be greater than zero")

        return self


class ExpenseInDB(Expense, DatabaseModel):
    organization_id: str = Field(example="org_123")
    is_active: bool = Field(example=True, exclude=True)
