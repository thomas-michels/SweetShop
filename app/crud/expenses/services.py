from datetime import date
from typing import List

from app.crud.shared_schemas.payment import Payment
from .schemas import Expense, ExpenseInDB, UpdateExpense
from .repositories import ExpenseRepository


class ExpenseServices:

    def __init__(self, expense_repository: ExpenseRepository) -> None:
        self.__repository = expense_repository

    async def create(self, expense: Expense) -> ExpenseInDB:
        total_paid = self.__calculate_total_paid(payment_details=expense.payment_details)

        expense_in_db = await self.__repository.create(
            expense=expense,
            total_paid=total_paid
        )

        return expense_in_db

    async def update(self, id: str, updated_expense: UpdateExpense) -> ExpenseInDB:
        expense_in_db = await self.search_by_id(id=id)

        is_updated = expense_in_db.validate_updated_fields(update_expense=updated_expense)

        if updated_expense.payment_details is not None:
            total_paid = self.__calculate_total_paid(payment_details=updated_expense.payment_details)
            expense_in_db.total_paid = total_paid

        if is_updated:
            expense_in_db = await self.__repository.update(expense=expense_in_db)

        return expense_in_db

    async def search_by_id(self, id: str) -> ExpenseInDB:
        expense_in_db = await self.__repository.select_by_id(id=id)
        return expense_in_db

    async def search_all(self, query: str, start_date: date = None, end_date: date = None) -> List[ExpenseInDB]:
        expenses = await self.__repository.select_all(
            query=query,
            start_date=start_date,
            end_date=end_date
        )
        return expenses

    async def delete_by_id(self, id: str) -> ExpenseInDB:
        expense_in_db = await self.__repository.delete_by_id(id=id)
        return expense_in_db

    def __calculate_total_paid(self, payment_details: List[Payment]) -> float:
        total_paid = 0

        for payment in payment_details:
            total_paid += payment.amount

        return total_paid
