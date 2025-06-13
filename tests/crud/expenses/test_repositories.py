import os

import pytest
import mongomock
from mongoengine import connect, disconnect

from app.crud.expenses.repositories import ExpenseRepository
from app.crud.expenses.schemas import Expense, ExpenseInDB
from app.crud.expenses.models import ExpenseModel
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.crud.shared_schemas.payment import Payment, PaymentMethod
from app.core.utils.utc_datetime import UTCDateTime


@pytest.fixture(autouse=True)
def mongo_connection():
    connect(
        "mongoenginetest",
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient,
    )
    yield
    ExpenseModel.drop_collection()
    disconnect()


@pytest.fixture
def repo():
    return ExpenseRepository(organization_id="org")


@pytest.mark.asyncio
async def test_create_success(repo):
    expense = Expense(
        name="market",
        expense_date=UTCDateTime.now(),
        payment_details=[
            Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=10)
        ],
        tags=[],
    )
    result = await repo.create(expense=expense, total_paid=10)
    assert isinstance(result, ExpenseInDB)
    assert result.name == "Market"
    assert ExpenseModel.objects(id=result.id).first() is not None


@pytest.mark.asyncio
async def test_create_error(monkeypatch, repo):
    def raise_save(self):
        raise Exception("db error")

    monkeypatch.setattr(ExpenseModel, "save", raise_save)
    expense = Expense(
        name="market",
        expense_date=UTCDateTime.now(),
        payment_details=[],
        tags=[],
    )
    with pytest.raises(UnprocessableEntity):
        await repo.create(expense=expense, total_paid=10)


@pytest.mark.asyncio
async def test_update_success(repo):
    existing = ExpenseModel(
        organization_id="org",
        name="store",
        expense_date=UTCDateTime.now(),
        total_paid=5,
    )
    existing.save()

    expense_in_db = ExpenseInDB(
        id=existing.id,
        organization_id="org",
        name="New",
        expense_date=existing.expense_date,
        payment_details=[],
        tags=[],
        total_paid=20,
        created_at=existing.created_at,
        updated_at=existing.updated_at,
    )
    result = await repo.update(expense=expense_in_db)
    assert isinstance(result, ExpenseInDB)
    assert ExpenseModel.objects(id=existing.id).first().name == "New"


@pytest.mark.asyncio
async def test_update_error(monkeypatch, repo):
    existing = ExpenseModel(
        organization_id="org",
        name="store",
        expense_date=UTCDateTime.now(),
        total_paid=5,
    )
    existing.save()

    def raise_update(self, **kwargs):
        raise Exception("db error")

    monkeypatch.setattr(ExpenseModel, "update", raise_update)

    expense_in_db = ExpenseInDB(
        id=existing.id,
        organization_id="org",
        name="New",
        expense_date=existing.expense_date,
        payment_details=[],
        tags=[],
        total_paid=20,
        created_at=existing.created_at,
        updated_at=existing.updated_at,
    )
    with pytest.raises(UnprocessableEntity):
        await repo.update(expense=expense_in_db)


@pytest.mark.asyncio
async def test_select_count_by_date(repo):
    now = UTCDateTime.now()
    for _ in range(4):
        ExpenseModel(
            organization_id="org",
            name="store",
            expense_date=now,
            total_paid=1,
        ).save()

    result = await repo.select_count_by_date(start_date=now, end_date=now)
    assert result == 4


@pytest.mark.asyncio
async def test_select_count_by_date_error(monkeypatch, repo):
    def raise_objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr(ExpenseModel, "objects", staticmethod(raise_objects))
    now = UTCDateTime.now()
    result = await repo.select_count_by_date(start_date=now, end_date=now)
    assert result == 0


@pytest.mark.asyncio
async def test_select_count(repo):
    ExpenseModel(
        organization_id="org",
        name="Alpha",
        expense_date=UTCDateTime.now(),
        total_paid=1,
    ).save()
    ExpenseModel(
        organization_id="org",
        name="Beta",
        expense_date=UTCDateTime.now(),
        total_paid=1,
    ).save()

    result = await repo.select_count(query="a")
    assert result == 2


@pytest.mark.asyncio
async def test_select_count_error(monkeypatch, repo):
    def raise_objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr(ExpenseModel, "objects", staticmethod(raise_objects))
    result = await repo.select_count()
    assert result == 0


@pytest.mark.asyncio
async def test_select_by_id(repo):
    doc = ExpenseModel(
        organization_id="org",
        name="store",
        expense_date=UTCDateTime.now(),
        total_paid=5,
    )
    doc.save()

    result = await repo.select_by_id(id=doc.id)
    assert isinstance(result, ExpenseInDB)
    assert result.id == doc.id


@pytest.mark.asyncio
async def test_select_by_id_error(monkeypatch, repo):
    def raise_objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr(ExpenseModel, "objects", staticmethod(raise_objects))
    with pytest.raises(NotFoundError):
        await repo.select_by_id(id="x")


@pytest.mark.asyncio
async def test_select_all(repo):
    ExpenseModel(
        organization_id="org",
        name="Store",
        expense_date=UTCDateTime.now(),
        total_paid=5,
    ).save()
    ExpenseModel(
        organization_id="org",
        name="Shop",
        expense_date=UTCDateTime.now(),
        total_paid=15,
    ).save()

    result = await repo.select_all(query="", page=None, page_size=None)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_select_all_error(monkeypatch, repo):
    def raise_objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr(ExpenseModel, "objects", staticmethod(raise_objects))
    with pytest.raises(NotFoundError):
        await repo.select_all(query="")


@pytest.mark.asyncio
async def test_delete_by_id(repo):
    doc = ExpenseModel(
        organization_id="org",
        name="Store",
        expense_date=UTCDateTime.now(),
        total_paid=10,
    )
    doc.save()

    result = await repo.delete_by_id(id=doc.id)
    assert result.id == doc.id
    assert ExpenseModel.objects(id=doc.id).first().is_active is False


@pytest.mark.asyncio
async def test_delete_by_id_error(monkeypatch, repo):
    def raise_objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr(ExpenseModel, "objects", staticmethod(raise_objects))
    with pytest.raises(NotFoundError):
        await repo.delete_by_id(id="x")

