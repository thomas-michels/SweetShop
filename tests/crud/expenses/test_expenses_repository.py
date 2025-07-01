import unittest
from mongoengine import connect, disconnect
import mongomock

from app.crud.expenses.models import ExpenseModel
from app.crud.expenses.repositories import ExpenseRepository
from app.crud.expenses.schemas import Expense
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.shared_schemas.payment import Payment, PaymentMethod


class TestExpenseRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        self.repo = ExpenseRepository(organization_id="org1")

    def tearDown(self):
        disconnect()

    async def _build_expense(self, name="Expense", amount=10.0):
        expense = Expense(
            name=name,
            expense_date=UTCDateTime.now(),
            payment_details=[
                Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=amount)
            ],
            tags=[],
        )
        return expense

    async def test_create_expense(self):
        expense = await self._build_expense(name="Market")

        result = await self.repo.create(expense=expense, total_paid=10.0)

        self.assertEqual(result.name, "Market")
        self.assertEqual(ExpenseModel.objects.count(), 1)

    async def test_update_expense_name(self):
        expense = await self._build_expense(name="Old")
        created = await self.repo.create(expense=expense, total_paid=10.0)

        created.name = "New"
        updated = await self.repo.update(created)

        self.assertEqual(updated.name, "New")

    async def test_select_by_id_success(self):
        expense = await self._build_expense()
        created = await self.repo.create(expense=expense, total_paid=5.0)

        result = await self.repo.select_by_id(id=created.id)

        self.assertEqual(result.id, created.id)

    async def test_select_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.select_by_id(id="missing")

    async def test_select_count_with_query(self):
        await self.repo.create(expense=await self._build_expense(name="Coffee"), total_paid=5.0)
        await self.repo.create(expense=await self._build_expense(name="Coffee 2"), total_paid=5.0)
        await self.repo.create(expense=await self._build_expense(name="Tea"), total_paid=5.0)

        count = await self.repo.select_count(query="Coffee")

        self.assertEqual(count, 2)

    async def test_select_all_with_pagination(self):
        await self.repo.create(expense=await self._build_expense(name="A"), total_paid=5.0)
        await self.repo.create(expense=await self._build_expense(name="B"), total_paid=5.0)
        await self.repo.create(expense=await self._build_expense(name="C"), total_paid=5.0)

        results = await self.repo.select_all(query=None, page=1, page_size=2)

        self.assertEqual(len(results), 2)

        results_page_2 = await self.repo.select_all(query=None, page=2, page_size=2)

        self.assertEqual(len(results_page_2), 1)
        all_names = {res.name for res in results + results_page_2}
        self.assertEqual(all_names, {"A", "B", "C"})

    async def test_delete_by_id_success(self):
        created = await self.repo.create(expense=await self._build_expense(name="Del"), total_paid=5.0)

        result = await self.repo.delete_by_id(id=created.id)

        self.assertEqual(ExpenseModel.objects(is_active=True).count(), 0)
        self.assertEqual(result.name, "Del")

    async def test_delete_by_id_not_found(self):
        with self.assertRaises(NotFoundError):
            await self.repo.delete_by_id(id="missing")

