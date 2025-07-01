import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from mongoengine import connect, disconnect
import mongomock

from app.crud.expenses.repositories import ExpenseRepository
from app.crud.expenses.schemas import Expense, ExpenseInDB, UpdateExpense
from app.crud.expenses.services import ExpenseServices
from app.crud.shared_schemas.payment import Payment, PaymentMethod
from app.api.exceptions.authentication_exceptions import UnauthorizedException, UnprocessableEntityException
from app.core.utils.utc_datetime import UTCDateTime


class TestExpenseServices(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="default",
        )
        repo = ExpenseRepository(organization_id="org1")
        tag_repo = AsyncMock()
        self.service = ExpenseServices(expense_repository=repo, tag_repository=tag_repo)

    def tearDown(self):
        disconnect()

    async def _expense(self, amount=10.0):
        return Expense(
            name="Market",
            expense_date=UTCDateTime.now(),
            payment_details=[
                Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=amount)
            ],
            tags=[],
        )

    @patch("app.crud.expenses.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_expense_respects_plan_limit(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="2")
        await self.service.create(await self._expense())

        with self.assertRaises(UnauthorizedException):
            await self.service.create(await self._expense())

    @patch("app.crud.expenses.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_expense_success(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")

        result = await self.service.create(await self._expense(amount=5))

        self.assertIsInstance(result, ExpenseInDB)
        self.assertEqual(result.total_paid, 5)

    @patch("app.crud.expenses.services.get_plan_feature", new_callable=AsyncMock)
    async def test_update_expense(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        created = await self.service.create(await self._expense())

        updated = await self.service.update(id=created.id, updated_expense=UpdateExpense(name="New"))

        self.assertEqual(updated.name, "New")

    async def test_update_without_real_change(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = ExpenseInDB(
            id="1",
            name="Same",
            expense_date=UTCDateTime.now(),
            payment_details=[],
            tags=[],
            organization_id="org1",
            total_paid=5.0,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )
        mock_repo.update.return_value = mock_repo.select_by_id.return_value
        service = ExpenseServices(expense_repository=mock_repo, tag_repository=AsyncMock())

        result = await service.update(id="1", updated_expense=UpdateExpense())

        self.assertEqual(result.name, "Same")
        mock_repo.update.assert_not_awaited()

    async def test_search_by_id_calls_repo(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = "expense"
        service = ExpenseServices(expense_repository=mock_repo, tag_repository=AsyncMock())

        result = await service.search_by_id(id="x")

        self.assertEqual(result, "expense")
        mock_repo.select_by_id.assert_awaited_with(id="x")

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = ["expense"]
        service = ExpenseServices(expense_repository=mock_repo, tag_repository=AsyncMock())

        result = await service.search_all(query=None)

        self.assertEqual(result, ["expense"])
        mock_repo.select_all.assert_awaited()

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 3
        service = ExpenseServices(expense_repository=mock_repo, tag_repository=AsyncMock())

        count = await service.search_count(query="a")

        self.assertEqual(count, 3)
        mock_repo.select_count.assert_awaited_with(query="a", start_date=None, end_date=None, tags=[])

    async def test_delete_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.delete_by_id.return_value = "deleted"
        service = ExpenseServices(expense_repository=mock_repo, tag_repository=AsyncMock())

        result = await service.delete_by_id(id="d")

        self.assertEqual(result, "deleted")
        mock_repo.delete_by_id.assert_awaited_with(id="d")


    @patch("app.crud.expenses.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_expense_invalid_total_paid(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        expense = await self._expense(amount=5)
        expense.payment_details[0].amount = -5
        with self.assertRaises(UnprocessableEntityException):
            await self.service.create(expense)

    @patch("app.crud.expenses.services.get_plan_feature", new_callable=AsyncMock)
    async def test_update_expense_invalid_total_paid(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        created = await self.service.create(await self._expense())
        payment = Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=1)
        payment.amount = 0
        with self.assertRaises(UnprocessableEntityException):
            await self.service.update(
                id=created.id,
                updated_expense=UpdateExpense(payment_details=[payment])
            )

    @patch("app.crud.expenses.services.get_plan_feature", new_callable=AsyncMock)
    async def test_create_expense_validates_tags(self, mock_plan):
        mock_plan.return_value = SimpleNamespace(value="-")
        self.service._ExpenseServices__tag_repository.select_by_id = AsyncMock()
        expense = await self._expense()
        expense.tags = ["t1", "t2"]
        await self.service.create(expense)
        self.service._ExpenseServices__tag_repository.select_by_id.assert_any_await(id="t1")
        self.service._ExpenseServices__tag_repository.select_by_id.assert_any_await(id="t2")

    async def test_search_all_expand_tags(self):
        from app.crud.tags.schemas import TagInDB
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = [
            ExpenseInDB(
                id="1",
                name="A",
                expense_date=UTCDateTime.now(),
                payment_details=[],
                tags=["tag1"],
                organization_id="org1",
                total_paid=5.0,
                created_at=UTCDateTime.now(),
                updated_at=UTCDateTime.now(),
            )
        ]
        mock_tag_repo = AsyncMock()
        mock_tag_repo.select_by_id.return_value = TagInDB(id="tag1", name="Tag 1", organization_id="org1")
        service = ExpenseServices(expense_repository=mock_repo, tag_repository=mock_tag_repo)
        result = await service.search_all(query=None, expand=["tags"])
        self.assertEqual(result[0].tags[0].name, "Tag 1")
        mock_tag_repo.select_by_id.assert_awaited_with(id="tag1", raise_404=False)

