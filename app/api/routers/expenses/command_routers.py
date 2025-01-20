from fastapi import APIRouter, Depends, Security

from app.api.composers import expense_composer
from app.api.dependencies import build_response, decode_jwt
from app.crud.users import UserInDB
from app.crud.expenses import Expense, ExpenseInDB, UpdateExpense, ExpenseServices

router = APIRouter(tags=["Expenses"])


@router.post("/expenses", responses={201: {"model": ExpenseInDB}})
async def create_expenses(
    expense: Expense,
    current_user: UserInDB = Security(decode_jwt, scopes=["expense:create"]),
    expense_services: ExpenseServices = Depends(expense_composer),
):
    expense_in_db = await expense_services.create(
        expense=expense
    )

    if expense_in_db:
        return build_response(
            status_code=201, message="Expense created with success", data=expense_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on create an expense", data=None
        )


@router.put("/expenses/{expense_id}", responses={200: {"model": ExpenseInDB}})
async def update_expenses(
    expense_id: str,
    expense: UpdateExpense,
    current_user: UserInDB = Security(decode_jwt, scopes=["expense:create"]),
    expense_services: ExpenseServices = Depends(expense_composer),
):
    expense_in_db = await expense_services.update(id=expense_id, updated_expense=expense)

    if expense_in_db:
        return build_response(
            status_code=200, message="Expense updated with success", data=expense_in_db
        )

    else:
        return build_response(
            status_code=400, message="Some error happened on update an expense", data=None
        )


@router.delete("/expenses/{expense_id}", responses={200: {"model": ExpenseInDB}})
async def delete_expenses(
    expense_id: str,
    current_user: UserInDB = Security(decode_jwt, scopes=["expense:delete"]),
    expense_services: ExpenseServices = Depends(expense_composer),
):
    expense_in_db = await expense_services.delete_by_id(id=expense_id)

    if expense_in_db:
        return build_response(
            status_code=200, message="Expense deleted with success", data=expense_in_db
        )

    else:
        return build_response(
            status_code=404, message=f"Expense {expense_id} not found", data=None
        )
