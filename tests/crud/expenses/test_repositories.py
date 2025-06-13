import pytest

from app.crud.expenses.repositories import ExpenseRepository
from app.crud.expenses.schemas import Expense, ExpenseInDB
from app.core.exceptions import NotFoundError, UnprocessableEntity
from app.crud.shared_schemas.payment import Payment, PaymentMethod
from app.core.utils.utc_datetime import UTCDateTime


class DummyExpenseModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.saved = False
        self.deleted = False

    def save(self):
        self.saved = True

    def update(self, **kwargs):
        self.__dict__.update(kwargs)

    def delete(self):
        self.deleted = True


class DummyQuerySet:
    def __init__(self, result=None, count_value=0, iterable=None):
        self.result = result
        self.count_value = count_value
        self.iterable = iterable or ([result] if result else [])

    def first(self):
        return self.result

    def count(self):
        return self.count_value

    def filter(self, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def skip(self, val):
        self.iterable = self.iterable[val:]
        return self

    def limit(self, val):
        self.iterable = self.iterable[:val]
        return self

    def __iter__(self):
        return iter(self.iterable)


def patch_model(monkeypatch, result=None, count_value=0, iterable=None):
    def objects(**kwargs):
        return DummyQuerySet(result=result, count_value=count_value, iterable=iterable)

    monkeypatch.setattr("app.crud.expenses.repositories.ExpenseModel", DummyExpenseModel)
    monkeypatch.setattr(DummyExpenseModel, "objects", staticmethod(objects))


@pytest.mark.asyncio
async def test_create_success(monkeypatch):
    repo = ExpenseRepository(organization_id="org")
    patch_model(monkeypatch)
    expense = Expense(
        name="market",
        expense_date=UTCDateTime.now(),
        payment_details=[Payment(method=PaymentMethod.CASH, payment_date=UTCDateTime.now(), amount=10)],
        tags=[],
    )
    result = await repo.create(expense=expense, total_paid=10)
    assert isinstance(result, ExpenseInDB)
    assert result.name == "Market"


@pytest.mark.asyncio
async def test_create_error(monkeypatch):
    class ErrorModel(DummyExpenseModel):
        def save(self):
            raise Exception("db error")

    monkeypatch.setattr("app.crud.expenses.repositories.ExpenseModel", ErrorModel)
    repo = ExpenseRepository(organization_id="org")
    expense = Expense(name="market", expense_date=UTCDateTime.now(), payment_details=[], tags=[])
    with pytest.raises(UnprocessableEntity):
        await repo.create(expense=expense, total_paid=10)


@pytest.mark.asyncio
async def test_update_success(monkeypatch):
    existing = DummyExpenseModel(id="e1", name="Store", organization_id="org", expense_date=UTCDateTime.now(), total_paid=5)

    patch_model(monkeypatch, result=existing)
    repo = ExpenseRepository(organization_id="org")
    expense_in_db = ExpenseInDB(id="e1", organization_id="org", name="New", expense_date=existing.expense_date, payment_details=[], tags=[], total_paid=20, created_at=UTCDateTime.now(), updated_at=UTCDateTime.now())
    result = await repo.update(expense=expense_in_db)
    assert isinstance(result, ExpenseInDB)
    assert existing.name == "New"


@pytest.mark.asyncio
async def test_update_error(monkeypatch):
    class ErrorModel(DummyExpenseModel):
        def update(self, **kwargs):
            raise Exception("db error")

    existing = ErrorModel(id="e1", name="Store", organization_id="org", expense_date=UTCDateTime.now(), total_paid=5)

    def objects(**kwargs):
        return DummyQuerySet(result=existing)

    monkeypatch.setattr("app.crud.expenses.repositories.ExpenseModel", ErrorModel)
    monkeypatch.setattr(ErrorModel, "objects", staticmethod(objects))

    repo = ExpenseRepository(organization_id="org")
    expense_in_db = ExpenseInDB(id="e1", organization_id="org", name="New", expense_date=existing.expense_date, payment_details=[], tags=[], total_paid=20, created_at=UTCDateTime.now(), updated_at=UTCDateTime.now())

    with pytest.raises(UnprocessableEntity):
        await repo.update(expense=expense_in_db)


@pytest.mark.asyncio
async def test_select_count_by_date(monkeypatch):
    patch_model(monkeypatch, count_value=4)
    repo = ExpenseRepository(organization_id="org")
    start = UTCDateTime.now()
    end = UTCDateTime.now()
    result = await repo.select_count_by_date(start_date=start, end_date=end)
    assert result == 4


@pytest.mark.asyncio
async def test_select_count_by_date_error(monkeypatch):
    def objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr("app.crud.expenses.repositories.ExpenseModel", DummyExpenseModel)
    monkeypatch.setattr(DummyExpenseModel, "objects", staticmethod(objects))

    repo = ExpenseRepository(organization_id="org")
    start = UTCDateTime.now()
    end = UTCDateTime.now()
    result = await repo.select_count_by_date(start_date=start, end_date=end)
    assert result == 0


@pytest.mark.asyncio
async def test_select_count(monkeypatch):
    patch_model(monkeypatch, count_value=3)
    repo = ExpenseRepository(organization_id="org")
    result = await repo.select_count(query="a")
    assert result == 3


@pytest.mark.asyncio
async def test_select_count_error(monkeypatch):
    def objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr("app.crud.expenses.repositories.ExpenseModel", DummyExpenseModel)
    monkeypatch.setattr(DummyExpenseModel, "objects", staticmethod(objects))
    repo = ExpenseRepository(organization_id="org")
    result = await repo.select_count()
    assert result == 0


@pytest.mark.asyncio
async def test_select_by_id(monkeypatch):
    existing = DummyExpenseModel(id="e1", name="Store", organization_id="org", expense_date=UTCDateTime.now(), total_paid=10)
    patch_model(monkeypatch, result=existing)
    repo = ExpenseRepository(organization_id="org")
    result = await repo.select_by_id(id="e1")
    assert isinstance(result, ExpenseInDB)
    assert result.id == "e1"


@pytest.mark.asyncio
async def test_select_by_id_error(monkeypatch):
    def objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr("app.crud.expenses.repositories.ExpenseModel", DummyExpenseModel)
    monkeypatch.setattr(DummyExpenseModel, "objects", staticmethod(objects))
    repo = ExpenseRepository(organization_id="org")
    with pytest.raises(NotFoundError):
        await repo.select_by_id(id="x")


@pytest.mark.asyncio
async def test_select_all(monkeypatch):
    obj1 = DummyExpenseModel(id="e1", name="Store", organization_id="org", expense_date=UTCDateTime.now(), total_paid=5)
    obj2 = DummyExpenseModel(id="e2", name="Shop", organization_id="org", expense_date=UTCDateTime.now(), total_paid=15)
    patch_model(monkeypatch, iterable=[obj1, obj2])
    repo = ExpenseRepository(organization_id="org")
    result = await repo.select_all(query="", page=None, page_size=None)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_select_all_error(monkeypatch):
    def objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr("app.crud.expenses.repositories.ExpenseModel", DummyExpenseModel)
    monkeypatch.setattr(DummyExpenseModel, "objects", staticmethod(objects))
    repo = ExpenseRepository(organization_id="org")
    with pytest.raises(NotFoundError):
        await repo.select_all(query="")


@pytest.mark.asyncio
async def test_delete_by_id(monkeypatch):
    existing = DummyExpenseModel(id="e1", name="Store", organization_id="org", expense_date=UTCDateTime.now(), total_paid=10)
    patch_model(monkeypatch, result=existing)
    repo = ExpenseRepository(organization_id="org")
    result = await repo.delete_by_id(id="e1")
    assert existing.deleted is True
    assert result.id == "e1"


@pytest.mark.asyncio
async def test_delete_by_id_error(monkeypatch):
    def objects(**kwargs):
        raise Exception("db error")

    monkeypatch.setattr("app.crud.expenses.repositories.ExpenseModel", DummyExpenseModel)
    monkeypatch.setattr(DummyExpenseModel, "objects", staticmethod(objects))
    repo = ExpenseRepository(organization_id="org")
    with pytest.raises(NotFoundError):
        await repo.delete_by_id(id="x")
