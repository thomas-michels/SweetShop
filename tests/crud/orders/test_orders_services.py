import unittest
from unittest.mock import AsyncMock

from app.crud.orders.schemas import (
    OrderInDB,
    Delivery,
    DeliveryType,
    StoredProduct,
    OrderStatus,
)
from app.crud.orders.services import OrderServices
from app.core.utils.utc_datetime import UTCDateTime
from app.crud.shared_schemas.payment import PaymentStatus


class TestOrderServices(unittest.IsolatedAsyncioTestCase):
    def _order_in_db(self):
        prod = StoredProduct(
            product_id="p1",
            name="Prod1",
            unit_price=2.0,
            unit_cost=1.0,
            quantity=1,
        )
        delivery = Delivery(delivery_type=DeliveryType.WITHDRAWAL)
        now = UTCDateTime.now()
        return OrderInDB(
            id="ord1",
            organization_id="org1",
            customer_id=None,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            products=[prod],
            tags=["tag1"],
            delivery=delivery,
            preparation_date=now,
            order_date=now,
            description=None,
            additional=0,
            discount=0,
            total_amount=2.0,
            tax=0,
            payments=[],
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    async def test_search_by_id(self):
        mock_repo = AsyncMock()
        mock_repo.select_by_id.return_value = self._order_in_db()
        service = OrderServices(
            order_repository=mock_repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
        )
        result = await service.search_by_id(id="ord1")
        self.assertEqual(result.id, "ord1")
        mock_repo.select_by_id.assert_awaited_with(id="ord1")

    async def test_search_count(self):
        mock_repo = AsyncMock()
        mock_repo.select_count.return_value = 4
        service = OrderServices(
            order_repository=mock_repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
        )
        count = await service.search_count(
            status=None,
            payment_status=[],
            delivery_type=None,
            customer_id=None,
            start_date=None,
            end_date=None,
            tags=None,
            min_total_amount=None,
            max_total_amount=None,
        )
        self.assertEqual(count, 4)
        mock_repo.select_count.assert_awaited()

    async def test_search_all(self):
        mock_repo = AsyncMock()
        mock_repo.select_all.return_value = [self._order_in_db()]
        service = OrderServices(
            order_repository=mock_repo,
            product_repository=AsyncMock(),
            tag_repository=AsyncMock(),
            customer_repository=AsyncMock(),
            organization_repository=AsyncMock(),
        )
        results = await service.search_all(
            status=None,
            payment_status=[],
            delivery_type=None,
            customer_id=None,
            start_date=None,
            end_date=None,
            tags=None,
            min_total_amount=None,
            max_total_amount=None,
            expand=[],
        )
        self.assertEqual(len(results), 1)
        mock_repo.select_all.assert_awaited()
