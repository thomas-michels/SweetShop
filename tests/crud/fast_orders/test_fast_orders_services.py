from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.exceptions.authentication_exceptions import (
    BadRequestException,
    UnprocessableEntityException,
)
from app.crud.fast_orders.schemas import (
    FastOrderInDB,
    RequestFastOrder,
    RequestedProduct,
    StoredProduct,
    UpdateFastOrder,
)
from app.crud.fast_orders.services import FastOrderServices
from app.core.utils.utc_datetime import UTCDateTime


class TestFastOrderServices(unittest.IsolatedAsyncioTestCase):
    async def _fast_order_in_db(self):
        return FastOrderInDB(
            id="fo1",
            organization_id="org1",
            products=[
                StoredProduct(
                    product_id="p1",
                    name="Cake",
                    unit_price=2.0,
                    unit_cost=1.0,
                    quantity=1,
                )
            ],
            order_date=UTCDateTime.now(),
            description=None,
            additional=0,
            discount=0,
            total_amount=10,
            payments=[],
            is_active=True,
            created_at=UTCDateTime.now(),
            updated_at=UTCDateTime.now(),
        )

    async def test_create_fast_order_duplicate_day_raises(self):
        repo = AsyncMock()
        product_repo = AsyncMock()
        service = FastOrderServices(
            fast_order_repository=repo, product_repository=product_repo
        )
        service.search_all = AsyncMock(return_value=[await self._fast_order_in_db()])
        req = RequestFastOrder(
            products=[RequestedProduct(product_id="p1", quantity=1)],
            order_date=UTCDateTime.now(),
            additional=0,
            discount=0,
        )
        with self.assertRaises(BadRequestException):
            await service.create(req)

    async def test_create_fast_order_success(self):
        repo = AsyncMock()
        repo.create.return_value = await self._fast_order_in_db()
        product_repo = AsyncMock()
        product_repo.select_by_id.return_value = SimpleNamespace(
            name="Cake", unit_cost=1.0, unit_price=2.0
        )
        service = FastOrderServices(
            fast_order_repository=repo, product_repository=product_repo
        )
        service.search_all = AsyncMock(return_value=[])
        service._FastOrderServices__calculate_fast_order_total_amount = AsyncMock(
            return_value=10
        )
        req = RequestFastOrder(
            products=[RequestedProduct(product_id="p1", quantity=1)],
            order_date=UTCDateTime.now(),
            additional=0,
            discount=0,
        )
        result = await service.create(req)
        repo.create.assert_awaited()
        self.assertEqual(result.total_amount, 10)

    async def test_update_fast_order_discount_validation(self):
        repo = AsyncMock()
        product_repo = AsyncMock()
        service = FastOrderServices(
            fast_order_repository=repo, product_repository=product_repo
        )
        service.search_by_id = AsyncMock(return_value=await self._fast_order_in_db())
        service.search_all = AsyncMock(return_value=[])
        service._FastOrderServices__calculate_fast_order_total_amount = AsyncMock(
            return_value=10
        )
        with self.assertRaises(UnprocessableEntityException):
            await service.update("fo1", UpdateFastOrder(discount=20))

    async def test_search_by_id(self):
        repo = AsyncMock()
        repo.select_by_id.return_value = await self._fast_order_in_db()
        service = FastOrderServices(
            fast_order_repository=repo, product_repository=AsyncMock()
        )
        result = await service.search_by_id(id="fo1")
        repo.select_by_id.assert_awaited_with(id="fo1")
        self.assertEqual(result.id, "fo1")

    async def test_search_count(self):
        repo = AsyncMock()
        repo.select_count.return_value = 3
        service = FastOrderServices(
            fast_order_repository=repo, product_repository=AsyncMock()
        )
        count = await service.search_count(day=None, start_date=None, end_date=None)
        self.assertEqual(count, 3)
        repo.select_count.assert_awaited()

    async def test_delete_by_id(self):
        repo = AsyncMock()
        repo.delete_by_id.return_value = await self._fast_order_in_db()
        service = FastOrderServices(
            fast_order_repository=repo, product_repository=AsyncMock()
        )
        result = await service.delete_by_id(id="fo1")
        repo.delete_by_id.assert_awaited_with(id="fo1")
        self.assertEqual(result.id, "fo1")
