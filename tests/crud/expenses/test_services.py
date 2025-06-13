import pytest
from unittest.mock import AsyncMock

from app.crud.expenses.services import ExpenseServices
from app.crud.expenses.schemas import Expense, UpdateExpense, ExpenseInDB
from app.crud.shared_schemas.payment import Payment, PaymentMethod
from app.crud.tags.schemas import TagInDB
from app.core.utils.utc_datetime import UTCDateTime


class DummyPlanFeature:
    def __init__(self, value="-"):
        self.value = value


@pytest.mark.asyncio
async def test_create_expense(monkeypatch):
    expense_repo = AsyncMock()
    tag_repo = AsyncMock()
    service = ExpenseServices(expense_repository=expense_repo, tag_repository=tag_repo)

    monkeypatch.setattr(
        "app.crud.expenses.services.get_plan_feature",
        AsyncMock(return_value=DummyPlanFeature(value="-")),
    )
    monkeypatch.setattr(
        "app.crud.expenses.services.get_start_and_end_day_of_month",
        lambda: (UTCDateTime.now(), UTCDateTime.now()),
    )

    expense_repo.select_count_by_date = AsyncMock(return_value=0)
    tag_repo.select_by_id = AsyncMock(return_value=TagInDB(id="t1", name="Tag", organization_id="org"))

    payment_details = [
        Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=60),
        Payment(method=PaymentMethod.PIX, payment_date=UTCDateTime.now(), amount=40),
    ]
    expense = Expense(name="market", expense_date=UTCDateTime.now(), payment_details=payment_details, tags=["t1"])

    created = ExpenseInDB(
        id="e1",
        organization_id="org",
        name="Market",
        expense_date=expense.expense_date,
        payment_details=payment_details,
        tags=["t1"],
        total_paid=100,
        created_at=UTCDateTime.now(),
        updated_at=UTCDateTime.now(),
    )
    expense_repo.create = AsyncMock(return_value=created)

    result = await service.create(expense)

    expense_repo.create.assert_awaited_with(expense=expense, total_paid=100)
    assert result == created


@pytest.mark.asyncio
async def test_create_expense_invalid_total(monkeypatch):
    expense_repo = AsyncMock()
    tag_repo = AsyncMock()
    service = ExpenseServices(expense_repository=expense_repo, tag_repository=tag_repo)

    monkeypatch.setattr(
        "app.crud.expenses.services.get_plan_feature",
        AsyncMock(return_value=DummyPlanFeature(value="-")),
    )
    monkeypatch.setattr(
        "app.crud.expenses.services.get_start_and_end_day_of_month",
        lambda: (UTCDateTime.now(), UTCDateTime.now()),
    )

    expense_repo.select_count_by_date = AsyncMock(return_value=0)
    tag_repo.select_by_id = AsyncMock(return_value=TagInDB(id="t1", name="Tag", organization_id="org"))

    payment_details = [
        Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=0),
    ]
    expense = Expense(name="market", expense_date=UTCDateTime.now(), payment_details=payment_details, tags=["t1"])

    with pytest.raises(Exception):
        await service.create(expense)

    expense_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_expense(monkeypatch):
    expense_repo = AsyncMock()
    tag_repo = AsyncMock()
    service = ExpenseServices(expense_repository=expense_repo, tag_repository=tag_repo)

    existing = ExpenseInDB(
        id="e1",
        organization_id="org",
        name="Market",
        expense_date=UTCDateTime.now(),
        payment_details=[],
        tags=[],
        total_paid=50,
        created_at=UTCDateTime.now(),
        updated_at=UTCDateTime.now(),
    )
    expense_repo.select_by_id = AsyncMock(return_value=existing)

    payment_details = [
        Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=30),
    ]
    update = UpdateExpense(payment_details=payment_details)

    updated = ExpenseInDB(
        id="e1",
        organization_id="org",
        name="Market",
        expense_date=existing.expense_date,
        payment_details=payment_details,
        tags=[],
        total_paid=30,
        created_at=existing.created_at,
        updated_at=UTCDateTime.now(),
    )
    expense_repo.update = AsyncMock(return_value=updated)

    result = await service.update("e1", update)

    expense_repo.update.assert_awaited()
    assert result.total_paid == 30


@pytest.mark.asyncio
async def test_delete_expense():
    expense_repo = AsyncMock()
    tag_repo = AsyncMock()
    service = ExpenseServices(expense_repository=expense_repo, tag_repository=tag_repo)

    deleted = ExpenseInDB(
        id="e1",
        organization_id="org",
        name="Market",
        expense_date=UTCDateTime.now(),
        payment_details=[],
        tags=[],
        total_paid=50,
        created_at=UTCDateTime.now(),
        updated_at=UTCDateTime.now(),
    )
    expense_repo.delete_by_id = AsyncMock(return_value=deleted)

    result = await service.delete_by_id("e1")

    expense_repo.delete_by_id.assert_awaited_with(id="e1")
    assert result == deleted


@pytest.mark.asyncio
async def test_create_expense_plan_limit(monkeypatch):
    expense_repo = AsyncMock()
    tag_repo = AsyncMock()
    service = ExpenseServices(expense_repository=expense_repo, tag_repository=tag_repo)

    monkeypatch.setattr(
        "app.crud.expenses.services.get_plan_feature",
        AsyncMock(return_value=DummyPlanFeature(value="1")),
    )
    monkeypatch.setattr(
        "app.crud.expenses.services.get_start_and_end_day_of_month",
        lambda: (UTCDateTime.now(), UTCDateTime.now()),
    )

    expense_repo.select_count_by_date = AsyncMock(return_value=1)
    expense = Expense(name="test", expense_date=UTCDateTime.now(), payment_details=[], tags=[])

    with pytest.raises(Exception):
        await service.create(expense)


@pytest.mark.asyncio
async def test_update_expense_invalid_total(monkeypatch):
    expense_repo = AsyncMock()
    tag_repo = AsyncMock()
    service = ExpenseServices(expense_repository=expense_repo, tag_repository=tag_repo)

    existing = ExpenseInDB(
        id="e1",
        organization_id="org",
        name="Market",
        expense_date=UTCDateTime.now(),
        payment_details=[],
        tags=[],
        total_paid=50,
        created_at=UTCDateTime.now(),
        updated_at=UTCDateTime.now(),
    )
    expense_repo.select_by_id = AsyncMock(return_value=existing)

    update = UpdateExpense(
        payment_details=[Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=0)]
    )

    with pytest.raises(Exception):
        await service.update("e1", update)


@pytest.mark.asyncio
async def test_delete_expense_not_found(monkeypatch):
    expense_repo = AsyncMock()
    tag_repo = AsyncMock()
    service = ExpenseServices(expense_repository=expense_repo, tag_repository=tag_repo)
    expense_repo.delete_by_id = AsyncMock(side_effect=Exception("not found"))

    with pytest.raises(Exception):
        await service.delete_by_id("e1")


@pytest.mark.asyncio
async def test_search_all_expand(monkeypatch):
    expense_repo = AsyncMock()
    tag_repo = AsyncMock()
    service = ExpenseServices(expense_repository=expense_repo, tag_repository=tag_repo)

    expense = ExpenseInDB(
        id="e1",
        organization_id="org",
        name="Market",
        expense_date=UTCDateTime.now(),
        payment_details=[],
        tags=["t1"],
        total_paid=10,
        created_at=UTCDateTime.now(),
        updated_at=UTCDateTime.now(),
    )

    expense_repo.select_all = AsyncMock(return_value=[expense])
    tag_repo.select_by_id = AsyncMock(return_value=TagInDB(id="t1", name="Tag", organization_id="org"))

    result = await service.search_all(query="", expand=["tags"])
    assert result[0].tags[0].id == "t1"
    tag_repo.select_by_id.assert_awaited_with(id="t1", raise_404=False)
