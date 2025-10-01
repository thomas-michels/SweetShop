from typing import List

from pydantic import Field, ConfigDict

from app.api.shared_schemas.responses import Response, ListResponseSchema
from app.crud.expenses import ExpenseInDB

EXAMPLE_EXPENSE = {
    "id": "exp_123",
    "name": "Brasil Atacadista",
    "expense_date": "2024-01-01T00:00:00Z",
    "payment_details": [],
    "tags": [],
    "organization_id": "org_123",
    "total_paid": 150.0,
}


class GetExpenseResponse(Response):
    data: ExpenseInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Expense found with success", "data": EXAMPLE_EXPENSE}
        }
    )


class GetExpensesResponse(ListResponseSchema):
    data: List[ExpenseInDB] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Expenses found with success",
                "pagination": {"page": 1, "page_size": 2, "total": 2},
                "data": [
                    EXAMPLE_EXPENSE,
                    {**EXAMPLE_EXPENSE, "id": "exp_456", "name": "Outro"},
                ],
            }
        }
    )


class CreateExpenseResponse(Response):
    data: ExpenseInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Expense created with success", "data": EXAMPLE_EXPENSE}
        }
    )


class UpdateExpenseResponse(Response):
    data: ExpenseInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Expense updated with success", "data": EXAMPLE_EXPENSE}
        }
    )


class DeleteExpenseResponse(Response):
    data: ExpenseInDB | None = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Expense deleted with success", "data": EXAMPLE_EXPENSE}
        }
    )
