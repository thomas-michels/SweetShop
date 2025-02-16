from datetime import date, datetime
from typing import List
from app.core.configs import get_logger
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.repositories.base_repository import Repository

from .models import ExpenseModel
from .schemas import Expense, ExpenseInDB

_logger = get_logger(__name__)


class ExpenseRepository(Repository):
    def __init__(self, organization_id: str) -> None:
        super().__init__()
        self.organization_id = organization_id

    async def create(self, expense: Expense, total_paid: float) -> ExpenseInDB:
        try:
            expense_model = ExpenseModel(
                total_paid=total_paid,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                organization_id=self.organization_id,
                **expense.model_dump()
            )
            expense_model.name = expense_model.name.title()

            expense_model.save()
            _logger.info(f"Expense {expense.name} saved for organization {self.organization_id}")

            return ExpenseInDB.model_validate(expense_model)

        except Exception as error:
            _logger.error(f"Error on create_expense: {str(error)}")
            raise UnprocessableEntity(message="Error on create new expense")

    async def update(self, expense: ExpenseInDB) -> ExpenseInDB:
        try:
            expense_model: ExpenseModel = ExpenseModel.objects(
                id=expense.id,
                is_active=True,
                organization_id=self.organization_id
            ).first()
            expense.name = expense.name.title()

            expense_model.update(**expense.model_dump())

            return await self.select_by_id(id=expense.id)

        except Exception as error:
            _logger.error(f"Error on update_expense: {str(error)}")
            raise UnprocessableEntity(message="Error on update expense")

    async def select_count_by_date(self, start_date: datetime, end_date: datetime) -> int:
        try:
            count = ExpenseModel.objects(
                is_active=True,
                organization_id=self.organization_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()

            return count if count else 0

        except Exception as error:
            _logger.error(f"Error on select_count_by_date: {str(error)}")
            return 0

    async def select_by_id(self, id: str, raise_404: bool = True) -> ExpenseInDB:
        try:
            expense_model: ExpenseModel = ExpenseModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()

            return ExpenseInDB.model_validate(expense_model)

        except Exception as error:
            _logger.error(f"Error on select_by_id: {str(error)}")
            if raise_404:
                raise NotFoundError(message=f"Expense #{id} not found")

    async def select_all(self, query: str, start_date: date = None, end_date: date = None, tags: List[str] = None) -> List[ExpenseInDB]:
        try:
            expenses = []

            query_filter = {
                "is_active": True,
                "organization_id": self.organization_id
            }

            if query:
                query_filter["name__iregex"] = query

            if start_date:
                query_filter["expense_date__gte"] = start_date

            if end_date:
                query_filter["expense_date__lte"] = end_date

            if tags:
                query_filter["tags__in"] = tags

            objects = ExpenseModel.objects(**query_filter).order_by("-expense_date")

            for expense_model in objects:
                expenses.append(ExpenseInDB.model_validate(expense_model))

            return expenses

        except Exception as error:
            _logger.error(f"Error on select_all: {str(error)}")
            raise NotFoundError(message=f"Expenses not found")

    async def delete_by_id(self, id: str) -> ExpenseInDB:
        try:
            expense_model: ExpenseModel = ExpenseModel.objects(
                id=id,
                is_active=True,
                organization_id=self.organization_id
            ).first()
            expense_model.delete()

            return ExpenseInDB.model_validate(expense_model)

        except Exception as error:
            _logger.error(f"Error on delete_by_id: {str(error)}")
            raise NotFoundError(message=f"Expense #{id} not found")
