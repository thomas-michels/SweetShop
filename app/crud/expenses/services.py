from datetime import date
from typing import List

from app.api.dependencies.get_plan_feature import get_plan_feature
from app.api.exceptions.authentication_exceptions import UnauthorizedException, UnprocessableEntityException
from app.core.utils.features import Feature
from app.core.utils.get_current_month import get_current_month_date_range
from app.crud.shared_schemas.payment import Payment
from app.crud.tags.repositories import TagRepository
from .schemas import CompleteExpense, Expense, ExpenseInDB, UpdateExpense
from .repositories import ExpenseRepository


class ExpenseServices:

    def __init__(
            self,
            expense_repository: ExpenseRepository,
            tag_repository: TagRepository,
        ) -> None:
        self.__expense_repository = expense_repository
        self.__tag_repository = tag_repository

    async def create(self, expense: Expense) -> ExpenseInDB:
        plan_feature = await get_plan_feature(
            organization_id=self.__expense_repository.organization_id,
            feature_name=Feature.MAX_EXPANSES
        )

        start_date, end_date = get_current_month_date_range()

        quantity = await self.__expense_repository.select_count_by_date(
            start_date=start_date,
            end_date=end_date
        )

        if (quantity + 1) >= int(plan_feature.value):
            raise UnauthorizedException(detail=f"Maximum number of expenses reached, Max value: {plan_feature.value}")

        for tag in expense.tags:
            await self.__tag_repository.select_by_id(id=tag)

        total_paid = self.__calculate_total_paid(payment_details=expense.payment_details)

        if total_paid <= 0:
            raise UnprocessableEntityException(detail="Total paid should be grater than zero")

        expense_in_db = await self.__expense_repository.create(
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

            if total_paid <= 0:
                raise UnprocessableEntityException(detail="Total paid should be grater than zero")

        if is_updated:
            if updated_expense.tags is not None:
                for tag in updated_expense.tags:
                    await self.__tag_repository.select_by_id(id=tag)

            expense_in_db = await self.__expense_repository.update(expense=expense_in_db)

        return expense_in_db

    async def search_by_id(self, id: str) -> ExpenseInDB:
        expense_in_db = await self.__expense_repository.select_by_id(id=id)
        return expense_in_db

    async def search_all(self, query: str, start_date: date = None, end_date: date = None, tags: List[str] = [], expand: List[str] = []) -> List[ExpenseInDB | CompleteExpense]:
        expenses = await self.__expense_repository.select_all(
            query=query,
            start_date=start_date,
            end_date=end_date,
            tags=tags
        )

        if not expand:
            return expenses

        complete_expenses = []
        tags = {}

        for expense in expenses:
            complete_expense = CompleteExpense(**expense.model_dump())
            if "tags" in expand:
                complete_expense.tags = []

                for tag in expense.tags:
                    if tags.get(tag):
                        tag_in_db = tags[tag]

                    else:
                        tag_in_db = await self.__tag_repository.select_by_id(
                            id=tag,
                            raise_404=False
                        )
                        if tag_in_db:
                            tags[tag_in_db.id] = tag_in_db

                    complete_expense.tags.append(tag_in_db)

            complete_expenses.append(complete_expense)

        return complete_expenses

    async def delete_by_id(self, id: str) -> ExpenseInDB:
        expense_in_db = await self.__expense_repository.delete_by_id(id=id)
        return expense_in_db

    def __calculate_total_paid(self, payment_details: List[Payment]) -> float:
        total_paid = 0

        for payment in payment_details:
            total_paid += payment.amount

        return total_paid
