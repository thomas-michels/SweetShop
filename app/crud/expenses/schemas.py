from typing import List, Optional
from datetime import date
from pydantic import Field

from app.core.models import DatabaseModel
from app.core.models.base_schema import GenericModel
from app.crud.shared_schemas.payment import Payment


class Expense(GenericModel):
    name: str = Field(example="Brasil Atacadista")
    expense_date: date = Field(example=str(date.today()))
    payment_details: List[Payment] = Field(default=[])

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

        return is_updated


class UpdateExpense(GenericModel):
    name: Optional[str] = Field(default=None, example="Brasil Atacadista")
    expense_date: Optional[date] = Field(default=None, example=str(date.today()))
    payment_details: Optional[List[Payment]] = Field(default=None)


class ExpenseInDB(Expense, DatabaseModel):
    organization_id: str = Field(example="org_123")
    is_active: bool = Field(example=True, exclude=True)
    total_paid: float = Field(gt=0, example=150)
